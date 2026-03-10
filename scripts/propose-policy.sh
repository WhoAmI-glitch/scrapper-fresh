#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.claude/state}"
PROPOSALS_DIR="$STATE_DIR/proposals"

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
Usage: propose-policy.sh <command> [options]

Commands:
  create  --title TITLE --proposed-by AGENT --change-type TYPE
          --rationale TEXT --after TEXT [--before TEXT] [--section SECTION]
          [--target-file PATH] [--evidence "ref1,ref2"] [--risk-assessment TEXT]

  review  --id ID --verdict approve|reject|request_changes --reviewer AGENT
          [--comment TEXT]

  promote --id ID

  change-type: add_rule | modify_rule | remove_rule | add_section | modify_section | add_agent | modify_agent
USAGE
  exit 1
}

cmd_create() {
  local title="" proposed_by="" change_type="" before_text="" after_text=""
  local section="" target_file="CLAUDE.md" rationale="" evidence="" risk_assessment=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --title)           title="$2"; shift 2 ;;
      --proposed-by)     proposed_by="$2"; shift 2 ;;
      --change-type)     change_type="$2"; shift 2 ;;
      --before)          before_text="$2"; shift 2 ;;
      --after)           after_text="$2"; shift 2 ;;
      --section)         section="$2"; shift 2 ;;
      --target-file)     target_file="$2"; shift 2 ;;
      --rationale)       rationale="$2"; shift 2 ;;
      --evidence)        evidence="$2"; shift 2 ;;
      --risk-assessment) risk_assessment="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$title" || -z "$proposed_by" || -z "$change_type" || -z "$after_text" || -z "$rationale" ]]; then
    echo "Error: --title, --proposed-by, --change-type, --after, and --rationale are required." >&2
    usage
  fi

  # Validate change_type enum (matches proposal.schema.json)
  case "$change_type" in
    add_rule|modify_rule|remove_rule|add_section|modify_section|add_agent|modify_agent) ;;
    *) echo "Error: --change-type must be add_rule|modify_rule|remove_rule|add_section|modify_section|add_agent|modify_agent" >&2; exit 1 ;;
  esac

  local id
  id="$(generate_id "proposal")"
  local ts
  ts="$(now_iso)"

  # Convert comma-separated evidence to JSON array
  local evidence_json="[]"
  if [[ -n "$evidence" ]]; then
    evidence_json="$(echo "$evidence" | jq -R 'split(",") | map(ltrimstr(" ") | rtrimstr(" ")) | map(select(length > 0))')"
  fi

  mkdir -p "$PROPOSALS_DIR"

  # Build the diff object (schema requires before + after)
  local before_json
  before_json="$(printf '%s' "$before_text" | jq -Rs '.')"
  local after_json
  after_json="$(printf '%s' "$after_text" | jq -Rs '.')"
  local section_json="null"
  if [[ -n "$section" ]]; then
    section_json="$(printf '%s' "$section" | jq -Rs '.')"
  fi

  # Handle optional risk_assessment
  local risk_json="null"
  if [[ -n "$risk_assessment" ]]; then
    risk_json="$(printf '%s' "$risk_assessment" | jq -Rs '.')"
  fi

  # Output conforms to .claude/schemas/proposal.schema.json
  jq -n \
    --arg id "$id" \
    --arg title "$title" \
    --arg proposed_by "$proposed_by" \
    --arg change_type "$change_type" \
    --arg target_file "$target_file" \
    --arg rationale "$rationale" \
    --argjson before "$before_json" \
    --argjson after "$after_json" \
    --argjson section "$section_json" \
    --argjson evidence "$evidence_json" \
    --argjson risk_assessment "$risk_json" \
    --arg status "pending" \
    --arg created_at "$ts" \
    '{
      id: $id,
      title: $title,
      proposed_by: $proposed_by,
      change_type: $change_type,
      target_file: $target_file,
      rationale: $rationale,
      diff: {
        before: $before,
        after: $after,
        section: $section
      },
      evidence: $evidence,
      risk_assessment: $risk_assessment,
      reviews: [],
      status: $status,
      created_at: $created_at
    }' > "$PROPOSALS_DIR/${id}.json"

  echo "Created proposal: $id"
  echo "  Title: $title"
  echo "  File: $PROPOSALS_DIR/${id}.json"
}

cmd_review() {
  local id="" verdict="" reviewer="" comment=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id)       id="$2"; shift 2 ;;
      --verdict)  verdict="$2"; shift 2 ;;
      --reviewer) reviewer="$2"; shift 2 ;;
      --comment)  comment="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$id" || -z "$verdict" || -z "$reviewer" ]]; then
    echo "Error: --id, --verdict, and --reviewer are required." >&2
    usage
  fi

  case "$verdict" in
    approve|reject|request_changes) ;;
    *) echo "Error: --verdict must be approve|reject|request_changes" >&2; exit 1 ;;
  esac

  local proposal_file="$PROPOSALS_DIR/${id}.json"
  if [[ ! -f "$proposal_file" ]]; then
    echo "Error: proposal $id not found." >&2; exit 1
  fi

  # Map verdict to schema status enum
  local new_status
  case "$verdict" in
    approve)         new_status="approved" ;;
    reject)          new_status="rejected" ;;
    request_changes) new_status="evaluating" ;;
  esac

  jq --arg verdict "$verdict" \
     --arg reviewer "$reviewer" \
     --arg comment "$comment" \
     --arg new_status "$new_status" \
    '.reviews += [{
       reviewer: $reviewer,
       verdict: $verdict,
       comment: $comment
     }]
     | .status = $new_status' \
    "$proposal_file" > "$proposal_file.tmp" && mv "$proposal_file.tmp" "$proposal_file"

  echo "Proposal $id reviewed: $verdict by $reviewer"
}

cmd_promote() {
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

  local proposal_file="$PROPOSALS_DIR/${id}.json"
  if [[ ! -f "$proposal_file" ]]; then
    echo "Error: proposal $id not found." >&2; exit 1
  fi

  local current_status
  current_status="$(jq -r '.status' "$proposal_file")"

  if [[ "$current_status" != "approved" ]]; then
    echo "Error: proposal $id has status '$current_status'; only approved proposals can be promoted." >&2
    exit 1
  fi

  jq '.status = "promoted"' \
    "$proposal_file" > "$proposal_file.tmp" && mv "$proposal_file.tmp" "$proposal_file"

  local after_text target_file
  target_file="$(jq -r '.target_file // "CLAUDE.md"' "$proposal_file")"
  after_text="$(jq -r '.diff.after // "(no text provided)"' "$proposal_file")"

  echo "Proposal $id promoted."
  echo ""
  echo "=== Policy change ready for policy-maintainer agent ==="
  echo "Target: $target_file"
  echo "Proposed text:"
  echo "$after_text"
  echo ""
  echo "The policy-maintainer agent should now apply this change to CLAUDE.md."
}

# --- Main dispatch ---
if [[ $# -lt 1 ]]; then
  usage
fi

command="$1"; shift

case "$command" in
  create)  cmd_create "$@" ;;
  review)  cmd_review "$@" ;;
  promote) cmd_promote "$@" ;;
  help|--help|-h) usage ;;
  *) echo "Unknown command: $command" >&2; usage ;;
esac
