#!/usr/bin/env bash
set -euo pipefail

# post-task.sh — Trigger quality gate after task completion
# Called by the coordinator when a task moves to "review" status.

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_DIR="${REPO_ROOT}/.claude"
TASK_ID="${1:-}"

if [ -z "${TASK_ID}" ]; then
  echo "Usage: post-task.sh <task-id>"
  exit 1
fi

TASK_FILE="${CLAUDE_DIR}/state/tasks/${TASK_ID}.json"
if [ ! -f "${TASK_FILE}" ]; then
  echo "Task not found: ${TASK_FILE}"
  exit 1
fi

echo "=== Post-task quality gate for ${TASK_ID} ==="

# Get the finding ID from the task
FINDING_ID=$(python3 -c "import json; print(json.load(open('${TASK_FILE}')).get('finding_id', ''))" 2>/dev/null)

if [ -z "${FINDING_ID}" ]; then
  echo "No finding linked to task. Skipping quality gate."
  exit 0
fi

# Run the quality gate scorer
"${CLAUDE_DIR}/quality/scripts/score-change.sh" "${FINDING_ID}"
