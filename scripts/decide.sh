#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
DECISIONS_DIR="$STATE_DIR/decisions"

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
Usage: decide.sh --context CONTEXT --decision DECISION --rationale RATIONALE --decided-by AGENT
                 [--alternatives "alt1,alt2"] [--status active|superseded|revoked]
                 [--related-tasks "id1,id2"]

Creates a decision log entry in .claude/state/decisions/.
USAGE
  exit 1
}

main() {
  local context="" decision="" rationale="" decided_by="" alternatives="" status="active" related_tasks=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --context)       context="$2"; shift 2 ;;
      --decision)      decision="$2"; shift 2 ;;
      --rationale)     rationale="$2"; shift 2 ;;
      --decided-by)    decided_by="$2"; shift 2 ;;
      --alternatives)  alternatives="$2"; shift 2 ;;
      --status)        status="$2"; shift 2 ;;
      --related-tasks) related_tasks="$2"; shift 2 ;;
      --help|-h)       usage ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$context" || -z "$decision" || -z "$rationale" || -z "$decided_by" ]]; then
    echo "Error: --context, --decision, --rationale, and --decided-by are all required." >&2
    usage
  fi

  # Validate status enum
  case "$status" in
    active|superseded|revoked) ;;
    *) echo "Error: --status must be active|superseded|revoked" >&2; exit 1 ;;
  esac

  local id
  id="$(generate_id "decision")"
  local ts
  ts="$(now_iso)"

  # Convert comma-separated alternatives to JSON array
  local alternatives_json="[]"
  if [[ -n "$alternatives" ]]; then
    alternatives_json="$(echo "$alternatives" | jq -R 'split(",") | map(ltrimstr(" ") | rtrimstr(" ")) | map(select(length > 0))')"
  fi

  # Convert comma-separated related task IDs to JSON array
  local related_tasks_json="[]"
  if [[ -n "$related_tasks" ]]; then
    related_tasks_json="$(echo "$related_tasks" | jq -R 'split(",") | map(ltrimstr(" ") | rtrimstr(" ")) | map(select(length > 0))')"
  fi

  mkdir -p "$DECISIONS_DIR"

  jq -n \
    --arg id "$id" \
    --arg context "$context" \
    --arg decision "$decision" \
    --argjson alternatives_considered "$alternatives_json" \
    --arg rationale "$rationale" \
    --arg decided_by "$decided_by" \
    --arg status "$status" \
    --argjson related_tasks "$related_tasks_json" \
    --arg created_at "$ts" \
    '{
      id: $id,
      context: $context,
      decision: $decision,
      alternatives_considered: $alternatives_considered,
      rationale: $rationale,
      decided_by: $decided_by,
      status: $status,
      related_tasks: $related_tasks,
      created_at: $created_at
    }' > "$DECISIONS_DIR/${id}.json"

  echo "Decision logged: $id"
  echo "  Decision: $decision"
  echo "  File: $DECISIONS_DIR/${id}.json"
}

if [[ $# -lt 1 || "$1" == "--help" || "$1" == "-h" ]]; then
  usage
fi

main "$@"
