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
Usage: decide.sh --type TYPE --reference-id ID --decision DECISION
                 --reasoning TEXT --decided-by AGENT
                 [--follow-up TEXT] [--alternatives "alt1,alt2"]

Creates a decision record conforming to decision.schema.json.

  --type:         task_completion | task_rejection | policy_promotion | policy_rejection
  --decision:     accept | reject | defer
  --decided-by:   coordinator | policy-maintainer
USAGE
  exit 1
}

main() {
  local type="" reference_id="" decision="" reasoning="" decided_by=""
  local follow_up="" alternatives=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --type)          type="$2"; shift 2 ;;
      --reference-id)  reference_id="$2"; shift 2 ;;
      --decision)      decision="$2"; shift 2 ;;
      --reasoning)     reasoning="$2"; shift 2 ;;
      --decided-by)    decided_by="$2"; shift 2 ;;
      --follow-up)     follow_up="$2"; shift 2 ;;
      --alternatives)  alternatives="$2"; shift 2 ;;
      --help|-h)       usage ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$type" || -z "$reference_id" || -z "$decision" || -z "$reasoning" || -z "$decided_by" ]]; then
    echo "Error: --type, --reference-id, --decision, --reasoning, and --decided-by are all required." >&2
    usage
  fi

  # Validate type enum (matches decision.schema.json)
  case "$type" in
    task_completion|task_rejection|policy_promotion|policy_rejection) ;;
    *) echo "Error: --type must be task_completion|task_rejection|policy_promotion|policy_rejection" >&2; exit 1 ;;
  esac

  # Validate decision enum (matches decision.schema.json)
  case "$decision" in
    accept|reject|defer) ;;
    *) echo "Error: --decision must be accept|reject|defer" >&2; exit 1 ;;
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

  # Handle nullable follow_up
  local follow_up_json="null"
  if [[ -n "$follow_up" ]]; then
    follow_up_json="$(printf '%s' "$follow_up" | jq -Rs '.')"
  fi

  mkdir -p "$DECISIONS_DIR"

  # Output conforms to .claude/schemas/decision.schema.json
  jq -n \
    --arg id "$id" \
    --arg type "$type" \
    --arg reference_id "$reference_id" \
    --arg decision "$decision" \
    --arg reasoning "$reasoning" \
    --arg decided_by "$decided_by" \
    --argjson follow_up "$follow_up_json" \
    --argjson alternatives_considered "$alternatives_json" \
    --arg created_at "$ts" \
    '{
      id: $id,
      type: $type,
      reference_id: $reference_id,
      decision: $decision,
      reasoning: $reasoning,
      decided_by: $decided_by,
      follow_up: $follow_up,
      alternatives_considered: $alternatives_considered,
      created_at: $created_at
    }' > "$DECISIONS_DIR/${id}.json"

  echo "Decision logged: $id"
  echo "  Type: $type | Decision: $decision"
  echo "  File: $DECISIONS_DIR/${id}.json"
}

if [[ $# -lt 1 || "$1" == "--help" || "$1" == "-h" ]]; then
  usage
fi

main "$@"
