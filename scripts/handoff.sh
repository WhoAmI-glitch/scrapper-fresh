#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
HANDOFFS_DIR="$STATE_DIR/handoffs"
TASKS_DIR="$STATE_DIR/tasks"

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
  create      --from AGENT --to AGENT --task-id ID --objective TEXT
              --criteria "c1,c2,c3" [--constraints "c1,c2"] [--files "f1,f2"]
              [--skills "s1,s2"] [--iteration N] [--feedback TEXT]

Creates a handoff artifact conforming to handoff.schema.json.
Handoffs are immutable — corrections produce new artifacts.
USAGE
  exit 1
}

cmd_create() {
  local from_agent="" to_agent="" task_id="" objective="" criteria=""
  local constraints="" files="" skills="" iteration=1 feedback=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from)        from_agent="$2"; shift 2 ;;
      --to)          to_agent="$2"; shift 2 ;;
      --task-id)     task_id="$2"; shift 2 ;;
      --objective)   objective="$2"; shift 2 ;;
      --criteria)    criteria="$2"; shift 2 ;;
      --constraints) constraints="$2"; shift 2 ;;
      --files)       files="$2"; shift 2 ;;
      --skills)      skills="$2"; shift 2 ;;
      --iteration)   iteration="$2"; shift 2 ;;
      --feedback)    feedback="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$from_agent" || -z "$to_agent" || -z "$task_id" || -z "$objective" || -z "$criteria" ]]; then
    echo "Error: --from, --to, --task-id, --objective, and --criteria are required." >&2
    usage
  fi

  # Convert comma-separated lists to JSON arrays
  csv_to_json() {
    if [[ -n "$1" ]]; then
      echo "$1" | jq -R 'split(",") | map(ltrimstr(" ") | rtrimstr(" ")) | map(select(length > 0))'
    else
      echo "[]"
    fi
  }

  local criteria_json constraints_json files_json skills_json
  criteria_json="$(csv_to_json "$criteria")"
  constraints_json="$(csv_to_json "$constraints")"
  files_json="$(csv_to_json "$files")"
  skills_json="$(csv_to_json "$skills")"

  # Handle nullable feedback
  local feedback_json="null"
  if [[ -n "$feedback" ]]; then
    feedback_json="$(printf '%s' "$feedback" | jq -Rs '.')"
  fi

  local id
  id="$(generate_id "handoff")"
  local ts
  ts="$(now_iso)"

  mkdir -p "$HANDOFFS_DIR"

  # Output conforms to .claude/schemas/handoff.schema.json
  jq -n \
    --arg id "$id" \
    --arg task_id "$task_id" \
    --arg from_agent "$from_agent" \
    --arg to_agent "$to_agent" \
    --arg objective "$objective" \
    --argjson acceptance_criteria "$criteria_json" \
    --argjson constraints "$constraints_json" \
    --argjson relevant_files "$files_json" \
    --argjson skills "$skills_json" \
    --argjson iteration "$iteration" \
    --argjson feedback_from_review "$feedback_json" \
    --arg created_at "$ts" \
    '{
      id: $id,
      task_id: $task_id,
      from_agent: $from_agent,
      to_agent: $to_agent,
      context: {
        objective: $objective,
        acceptance_criteria: $acceptance_criteria,
        constraints: $constraints,
        relevant_files: $relevant_files,
        prior_findings: [],
        skills: $skills
      },
      iteration: $iteration,
      feedback_from_review: $feedback_from_review,
      created_at: $created_at
    }' > "$HANDOFFS_DIR/${id}.json"

  # Update task with handoff reference
  local task_file="$TASKS_DIR/${task_id}.json"
  if [[ -f "$task_file" ]]; then
    jq --arg hid "$id" --arg ts "$ts" \
      '.handoff_id = $hid | .updated_at = $ts' \
      "$task_file" > "$task_file.tmp" && mv "$task_file.tmp" "$task_file"
  fi

  echo "Created handoff: $id"
  echo "  From: $from_agent -> To: $to_agent"
  echo "  File: $HANDOFFS_DIR/${id}.json"
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
