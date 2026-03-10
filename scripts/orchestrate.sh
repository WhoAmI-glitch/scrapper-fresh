#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
TASKS_DIR="$STATE_DIR/tasks"
QUALITY_DIR="$PROJECT_ROOT/.claude/quality/scripts"

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
Usage: orchestrate.sh <command> [options]

Commands:
  create-task   --title TITLE --priority PRIORITY --description DESC
                [--tags "t1,t2"] [--created-by AGENT]
  assign-task   --id ID --to AGENT
  complete-task --id ID
  validate-task --id ID
  list-tasks    [--status STATUS]
  show-task     --id ID
USAGE
  exit 1
}

cmd_create_task() {
  local title="" priority="" description="" tags="" created_by="orchestrator"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --title)       title="$2"; shift 2 ;;
      --priority)    priority="$2"; shift 2 ;;
      --description) description="$2"; shift 2 ;;
      --tags)        tags="$2"; shift 2 ;;
      --created-by)  created_by="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$title" || -z "$priority" || -z "$description" ]]; then
    echo "Error: --title, --priority, and --description are required." >&2
    usage
  fi

  # Validate priority enum (matches task.schema.json)
  case "$priority" in
    critical|high|normal|low) ;;
    *) echo "Error: priority must be critical|high|normal|low" >&2; exit 1 ;;
  esac

  local id
  id="$(generate_id "task")"
  local ts
  ts="$(now_iso)"

  # Convert comma-separated tags into JSON array
  local tags_json="[]"
  if [[ -n "$tags" ]]; then
    tags_json="$(echo "$tags" | jq -R 'split(",")|map(ltrimstr(" ")|rtrimstr(" "))|map(select(length>0))')"
  fi

  mkdir -p "$TASKS_DIR"

  # Output conforms to .claude/schemas/task.schema.json
  jq -n \
    --arg id "$id" \
    --arg title "$title" \
    --arg description "$description" \
    --arg status "pending" \
    --arg created_by "$created_by" \
    --arg priority "$priority" \
    --argjson tags "$tags_json" \
    --arg created_at "$ts" \
    --arg updated_at "$ts" \
    '{
      id: $id,
      title: $title,
      description: $description,
      status: $status,
      assigned_agent: null,
      created_by: $created_by,
      priority: $priority,
      tags: $tags,
      parent_task_id: null,
      subtask_ids: [],
      depends_on: [],
      handoff_id: null,
      finding_id: null,
      quality_report_id: null,
      created_at: $created_at,
      updated_at: $updated_at
    }' > "$TASKS_DIR/${id}.json"

  echo "Created task: $id"
  echo "  File: $TASKS_DIR/${id}.json"
}

cmd_assign_task() {
  local id="" agent=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id) id="$2"; shift 2 ;;
      --to) agent="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$id" || -z "$agent" ]]; then
    echo "Error: --id and --to are required." >&2; usage
  fi

  local task_file="$TASKS_DIR/${id}.json"
  if [[ ! -f "$task_file" ]]; then
    echo "Error: task $id not found." >&2; exit 1
  fi

  local ts
  ts="$(now_iso)"

  jq --arg agent "$agent" --arg ts "$ts" \
    '.status = "assigned" | .assigned_agent = $agent | .updated_at = $ts' \
    "$task_file" > "$task_file.tmp" && mv "$task_file.tmp" "$task_file"

  echo "Task $id assigned to $agent"
}

cmd_complete_task() {
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

  local task_file="$TASKS_DIR/${id}.json"
  if [[ ! -f "$task_file" ]]; then
    echo "Error: task $id not found." >&2; exit 1
  fi

  local ts
  ts="$(now_iso)"

  jq --arg ts "$ts" \
    '.status = "review" | .updated_at = $ts' \
    "$task_file" > "$task_file.tmp" && mv "$task_file.tmp" "$task_file"

  echo "Task $id moved to review"
}

cmd_validate_task() {
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

  exec "$QUALITY_DIR/validate.sh" "$id"
}

cmd_list_tasks() {
  local filter_status=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --status) filter_status="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ ! -d "$TASKS_DIR" ]] || [ -z "$(ls -A "$TASKS_DIR" 2>/dev/null)" ]; then
    echo "No tasks found."
    return
  fi

  printf "%-38s %-12s %-10s %s\n" "ID" "STATUS" "PRIORITY" "TITLE"
  printf "%-38s %-12s %-10s %s\n" "---" "------" "--------" "-----"

  for f in "$TASKS_DIR"/*.json; do
    local row
    row="$(jq -r '[.id, .status, .priority, .title] | @tsv' "$f")"
    local s
    s="$(echo "$row" | cut -f2)"

    if [[ -n "$filter_status" && "$s" != "$filter_status" ]]; then
      continue
    fi

    printf "%-38s %-12s %-10s %s\n" \
      "$(echo "$row" | cut -f1)" \
      "$s" \
      "$(echo "$row" | cut -f3)" \
      "$(echo "$row" | cut -f4)"
  done
}

cmd_show_task() {
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

  local task_file="$TASKS_DIR/${id}.json"
  if [[ ! -f "$task_file" ]]; then
    echo "Error: task $id not found." >&2; exit 1
  fi

  jq '.' "$task_file"
}

# --- Main dispatch ---
if [[ $# -lt 1 ]]; then
  usage
fi

command="$1"; shift

case "$command" in
  create-task)   cmd_create_task "$@" ;;
  assign-task)   cmd_assign_task "$@" ;;
  complete-task) cmd_complete_task "$@" ;;
  validate-task) cmd_validate_task "$@" ;;
  list-tasks)    cmd_list_tasks "$@" ;;
  show-task)     cmd_show_task "$@" ;;
  help|--help|-h) usage ;;
  *) echo "Unknown command: $command" >&2; usage ;;
esac
