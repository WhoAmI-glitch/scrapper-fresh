#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
QUALITY_DIR="$PROJECT_ROOT/.claude/quality"
REPORTS_DIR="$QUALITY_DIR/reports"

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
Usage: quality-report.sh --finding-id ID --task-id ID [--checks JSON]

Creates a quality report by running validation checks and recording results.
Output conforms to quality-report.schema.json.

If --checks is not provided, runs the validate.sh quality gate and builds
the report from its results.

Check format (JSON array):
  [{"name":"correctness","passed":true,"weight":0.2,"details":"..."},...]

Valid check names:
  correctness, completeness, regressions, duplication,
  contracts, tests, runnability, documentation
USAGE
  exit 1
}

main() {
  local finding_id="" task_id="" checks_json=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --finding-id) finding_id="$2"; shift 2 ;;
      --task-id)    task_id="$2"; shift 2 ;;
      --checks)     checks_json="$2"; shift 2 ;;
      --help|-h)    usage ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$finding_id" || -z "$task_id" ]]; then
    echo "Error: --finding-id and --task-id are required." >&2
    usage
  fi

  # If no checks provided, run automated gate
  if [[ -z "$checks_json" ]]; then
    checks_json="$(run_automated_checks)"
  fi

  # Validate checks is a JSON array
  if ! echo "$checks_json" | jq 'type == "array"' 2>/dev/null | grep -q true; then
    echo "Error: checks must be a valid JSON array" >&2; exit 1
  fi

  local id
  id="$(generate_id "qr")"
  local ts
  ts="$(now_iso)"

  # Calculate weighted score
  local score
  score="$(echo "$checks_json" | jq '
    [.[] | select(.weight > 0)] |
    if length == 0 then 0
    else
      (map(if .passed then .weight else 0 end) | add) /
      (map(.weight) | add) * 100
    end | round
  ')"

  # Determine verdict based on score threshold
  local threshold=80
  if [[ -f "$QUALITY_DIR/gates.json" ]]; then
    threshold="$(jq -r '.threshold // 80' "$QUALITY_DIR/gates.json" 2>/dev/null || echo 80)"
  fi

  local verdict
  if (( score >= threshold )); then
    verdict="accept"
  else
    verdict="reject"
  fi

  # Extract blocking issues (failed checks)
  local blocking_issues
  blocking_issues="$(echo "$checks_json" | jq '[.[] | select(.passed == false) | .name + ": " + (.details // "failed")]')"

  # Non-blocking notes
  local notes='[]'

  mkdir -p "$REPORTS_DIR"

  # Output conforms to .claude/schemas/quality-report.schema.json
  jq -n \
    --arg id "$id" \
    --arg finding_id "$finding_id" \
    --arg task_id "$task_id" \
    --argjson checks "$checks_json" \
    --argjson score "$score" \
    --arg verdict "$verdict" \
    --argjson blocking_issues "$blocking_issues" \
    --argjson notes "$notes" \
    --arg created_at "$ts" \
    '{
      id: $id,
      finding_id: $finding_id,
      task_id: $task_id,
      checks: $checks,
      score: $score,
      verdict: $verdict,
      blocking_issues: $blocking_issues,
      notes: $notes,
      created_at: $created_at
    }' > "$REPORTS_DIR/${id}.json"

  echo "Quality report: $id"
  echo "  Score: $score / 100 (threshold: $threshold)"
  echo "  Verdict: $verdict"
  echo "  File: $REPORTS_DIR/${id}.json"
}

run_automated_checks() {
  local checks="[]"
  local validate_script="$QUALITY_DIR/scripts/validate.sh"

  # Check definitions with weights matching quality-report.schema.json
  local check_names=("correctness" "regressions" "contracts" "runnability")
  local check_weights=(0.3 0.25 0.25 0.2)

  for i in "${!check_names[@]}"; do
    local name="${check_names[$i]}"
    local weight="${check_weights[$i]}"
    local passed=true
    local details="passed"

    if [[ -f "$validate_script" ]]; then
      if ! bash "$validate_script" "$name" > /dev/null 2>&1; then
        passed=false
        details="failed — run 'bash $validate_script $name' for details"
      fi
    else
      details="validate.sh not found; skipped"
    fi

    checks="$(echo "$checks" | jq \
      --arg name "$name" \
      --argjson passed "$passed" \
      --argjson weight "$weight" \
      --arg details "$details" \
      '. += [{ name: $name, passed: $passed, weight: $weight, details: $details }]'
    )"
  done

  echo "$checks"
}

if [[ $# -lt 1 || "$1" == "--help" || "$1" == "-h" ]]; then
  usage
fi

main "$@"
