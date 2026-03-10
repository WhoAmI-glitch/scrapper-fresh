#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
HANDOFFS_DIR="$STATE_DIR/handoffs"

generate_id() {
  local prefix="$1"
  local datestamp
  datestamp="$(date -u +%Y%m%d)"
  local random6
  random6="$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)"
  echo "${prefix}-${datestamp}-${random6}"
}

now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

usage() {
  cat <<'USAGE'
Usage: handoff.sh <command> [options]

Commands:
  create      --from AGENT --to AGENT --task-id ID --type TYPE [--payload JSON]
  acknowledge --id ID
  complete    --id ID

Payload types: implementation, review_request, revision, findings, escalation
USAGE
  exit 1
}

cmd_create() {
  local from_agent="" to_agent="" task_id="" payload_type="" payload="{}"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from)    from_agent="$2"; shift 2 ;;
      --to)      to_agent="$2"; shift 2 ;;
      --task-id) task_id="$2"; shift 2 ;;
      --type)    payload_type="$2"; shift 2 ;;
      --payload) payload="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$from_agent" || -z "$to_agent" || -z "$task_id" || -z "$payload_type" ]]; then
    echo "Error: --from, --to, --task-id, and --type are required." >&2
    usage
  fi

  # Validate payload_type enum
  case "$payload_type" in
    implementation|review_request|revision|findings|escalation) ;;
    *) echo "Error: --type must be one of: implementation, review_request, revision, findings, escalation" >&2; exit 1 ;;
  esac

  # Validate payload is valid JSON
  if ! echo "$payload" | jq empty 2>/dev/null; then
    echo "Error: --payload must be valid JSON" >&2; exit 1
  fi

  local id
  id="$(generate_id "handoff")"
  local ts
  ts="$(now_iso)"

  mkdir -p "$HANDOFFS_DIR"

  jq -n \
    --arg id "$id" \
    --arg from_agent "$from_agent" \
    --arg to_agent "$to_agent" \
    --arg task_id "$task_id" \
    --arg payload_type "$payload_type" \
    --argjson payload "$payload" \
    --arg status "pending" \
    --arg created_at "$ts" \
    '{
      id: $id,
      from_agent: $from_agent,
      to_agent: $to_agent,
      task_id: $task_id,
      payload_type: $payload_type,
      payload: $payload,
      status: $status,
      created_at: $created_at
    }' > "$HANDOFFS_DIR/${id}.json"

  echo "Created handoff: $id"
  echo "  From: $from_agent -> To: $to_agent"
  echo "  File: $HANDOFFS_DIR/${id}.json"
}

cmd_acknowledge() {
  local id=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id) id="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$id" ]]; then
    echo "Error: --id is required." >&2; usage
  fi

  local handoff_file="$HANDOFFS_DIR/${id}.json"
  if [[ ! -f "$handoff_file" ]]; then
    echo "Error: handoff $id not found." >&2; exit 1
  fi

  jq '.status = "acknowledged"' "$handoff_file" > "$handoff_file.tmp" \
    && mv "$handoff_file.tmp" "$handoff_file"

  echo "Handoff $id acknowledged"
}

cmd_complete() {
  local id=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id) id="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$id" ]]; then
    echo "Error: --id is required." >&2; usage
  fi

  local handoff_file="$HANDOFFS_DIR/${id}.json"
  if [[ ! -f "$handoff_file" ]]; then
    echo "Error: handoff $id not found." >&2; exit 1
  fi

  jq '.status = "completed"' "$handoff_file" > "$handoff_file.tmp" \
    && mv "$handoff_file.tmp" "$handoff_file"

  echo "Handoff $id completed"
}

# --- Main dispatch ---
if [[ $# -lt 1 ]]; then
  usage
fi

command="$1"; shift

case "$command" in
  create)      cmd_create "$@" ;;
  acknowledge) cmd_acknowledge "$@" ;;
  complete)    cmd_complete "$@" ;;
  help|--help|-h) usage ;;
  *) echo "Unknown command: $command" >&2; usage ;;
esac
