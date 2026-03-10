#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
FINDINGS_DIR="$STATE_DIR/findings"

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
Usage: finding.sh <command> [options]

Commands:
  create  --handoff-id ID --agent AGENT --status STATUS --summary TEXT
          [--files-changed JSON] [--risks "r1,r2"] [--follow-up "t1,t2"]
          [--severity LEVEL] [--category CAT] [--recommendation TEXT]

  status: completed | partial | blocked | failed
  severity: critical | high | medium | low | info
  category: bug | security | performance | duplication | design | policy | regression

Creates a finding artifact conforming to finding.schema.json.
Findings are immutable — corrections produce new versioned artifacts.
USAGE
  exit 1
}

cmd_create() {
  local handoff_id="" agent="" find_status="" summary="" files_changed="[]"
  local risks="" follow_up="" severity="" category="" recommendation=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --handoff-id)     handoff_id="$2"; shift 2 ;;
      --agent)          agent="$2"; shift 2 ;;
      --status)         find_status="$2"; shift 2 ;;
      --summary)        summary="$2"; shift 2 ;;
      --files-changed)  files_changed="$2"; shift 2 ;;
      --risks)          risks="$2"; shift 2 ;;
      --follow-up)      follow_up="$2"; shift 2 ;;
      --severity)       severity="$2"; shift 2 ;;
      --category)       category="$2"; shift 2 ;;
      --recommendation) recommendation="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$handoff_id" || -z "$agent" || -z "$find_status" || -z "$summary" ]]; then
    echo "Error: --handoff-id, --agent, --status, and --summary are required." >&2
    usage
  fi

  # Validate status enum (matches finding.schema.json)
  case "$find_status" in
    completed|partial|blocked|failed) ;;
    *) echo "Error: --status must be completed|partial|blocked|failed" >&2; exit 1 ;;
  esac

  # Validate severity if provided
  if [[ -n "$severity" ]]; then
    case "$severity" in
      critical|high|medium|low|info) ;;
      *) echo "Error: --severity must be critical|high|medium|low|info" >&2; exit 1 ;;
    esac
  fi

  # Validate category if provided
  if [[ -n "$category" ]]; then
    case "$category" in
      bug|security|performance|duplication|design|policy|regression) ;;
      *) echo "Error: --category must be bug|security|performance|duplication|design|policy|regression" >&2; exit 1 ;;
    esac
  fi

  # Validate files_changed is valid JSON array
  if ! echo "$files_changed" | jq 'type == "array"' 2>/dev/null | grep -q true; then
    echo "Error: --files-changed must be a valid JSON array" >&2; exit 1
  fi

  # Convert comma-separated lists to JSON arrays
  csv_to_json() {
    if [[ -n "$1" ]]; then
      echo "$1" | jq -R 'split(",") | map(ltrimstr(" ") | rtrimstr(" ")) | map(select(length > 0))'
    else
      echo "[]"
    fi
  }

  local risks_json follow_up_json
  risks_json="$(csv_to_json "$risks")"
  follow_up_json="$(csv_to_json "$follow_up")"

  local id
  id="$(generate_id "finding")"
  local ts
  ts="$(now_iso)"

  mkdir -p "$FINDINGS_DIR"

  # Build jq args — optional fields added conditionally
  local jq_args=(
    --arg id "$id"
    --arg handoff_id "$handoff_id"
    --arg agent "$agent"
    --arg status "$find_status"
    --arg summary "$summary"
    --argjson files_changed "$files_changed"
    --argjson risks "$risks_json"
    --argjson follow_up_tasks "$follow_up_json"
    --arg created_at "$ts"
  )

  local jq_filter='{
    id: $id,
    handoff_id: $handoff_id,
    agent: $agent,
    status: $status,
    summary: $summary,
    files_changed: $files_changed,
    acceptance_results: [],
    risks: $risks,
    follow_up_tasks: $follow_up_tasks,
    created_at: $created_at
  }'

  # Add optional fields
  if [[ -n "$severity" ]]; then
    jq_args+=(--arg severity "$severity")
    jq_filter="$jq_filter | .severity = \$severity"
  fi
  if [[ -n "$category" ]]; then
    jq_args+=(--arg category "$category")
    jq_filter="$jq_filter | .category = \$category"
  fi
  if [[ -n "$recommendation" ]]; then
    jq_args+=(--arg recommendation "$recommendation")
    jq_filter="$jq_filter | .recommendation = \$recommendation"
  fi

  # Output conforms to .claude/schemas/finding.schema.json
  jq -n "${jq_args[@]}" "$jq_filter" > "$FINDINGS_DIR/${id}.json"

  echo "Created finding: $id"
  echo "  Agent: $agent | Status: $find_status"
  echo "  File: $FINDINGS_DIR/${id}.json"
}

# --- Main dispatch ---
if [[ $# -lt 1 ]]; then
  usage
fi

command="$1"; shift

case "$command" in
  create)      cmd_create "$@" ;;
  help|--help|-h) usage ;;
  *) echo "Unknown command: $command" >&2; usage ;;
esac
