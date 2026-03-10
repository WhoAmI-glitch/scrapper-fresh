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
  create  --proposer AGENT --target-file PATH --change-type TYPE
          --proposed-text TEXT --rationale RATIONALE
          [--current-text TEXT] [--evidence "ref1,ref2"]
          change-type: add_rule|modify_rule|remove_rule|add_agent|modify_agent
  review  --id ID --verdict approve|reject|revise --reviewer AGENT
          [--comment "review comment"]
  promote --id ID
USAGE
  exit 1
}

cmd_create() {
  local proposer="" target_file="" change_type="" current_text="" proposed_text="" rationale="" evidence=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --proposer)      proposer="$2"; shift 2 ;;
      --target-file)   target_file="$2"; shift 2 ;;
      --change-type)   change_type="$2"; shift 2 ;;
      --current-text)  current_text="$2"; shift 2 ;;
      --proposed-text) proposed_text="$2"; shift 2 ;;
      --rationale)     rationale="$2"; shift 2 ;;
      --evidence)      evidence="$2"; shift 2 ;;
      *) echo "Unknown option: $1" >&2; usage ;;
    esac
  done

  if [[ -z "$proposer" || -z "$target_file" || -z "$change_type" || -z "$proposed_text" || -z "$rationale" ]]; then
    echo "Error: --proposer, --target-file, --change-type, --proposed-text, and --rationale are required." >&2
    usage
  fi

  # Validate change_type enum
  case "$change_type" in
    add_rule|modify_rule|remove_rule|add_agent|modify_agent) ;;
    *) echo "Error: --change-type must be add_rule|modify_rule|remove_rule|add_agent|modify_agent" >&2; exit 1 ;;
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

  # Handle nullable current_text
  local current_text_json="null"
  if [[ -n "$current_text" ]]; then
    current_text_json="$(printf '%s' "$current_text" | jq -Rs '.')"
  fi

  mkdir -p "$PROPOSALS_DIR"

  jq -n \
    --arg id "$id" \
    --arg proposer "$proposer" \
    --arg target_file "$target_file" \
    --arg change_type "$change_type" \
    --argjson current_text "$current_text_json" \
    --arg proposed_text "$proposed_text" \
    --arg rationale "$rationale" \
    --argjson evidence "$evidence_json" \
    --arg status "draft" \
    --arg created_at "$ts" \
    '{
      id: $id,
      proposer: $proposer,
      target_file: $target_file,
      change_type: $change_type,
      current_text: $current_text,
      proposed_text: $proposed_text,
      rationale: $rationale,
      evidence: $evidence,
      status: $status,
      reviews: [],
      created_at: $created_at,
      promoted_at: null
    }' > "$PROPOSALS_DIR/${id}.json"

  echo "Created proposal: $id"
  echo "  Target: $target_file"
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

  local ts
  ts="$(now_iso)"

  # Build review entry and append it; update status based on verdict
  local new_status
  case "$verdict" in
    approve)         new_status="approved" ;;
    reject)          new_status="rejected" ;;
    request_changes) new_status="under_review" ;;
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

  local status
  status="$(jq -r '.status' "$proposal_file")"

  if [[ "$status" != "approved" ]]; then
    echo "Error: proposal $id has status '$status'; only approved proposals can be promoted." >&2
    exit 1
  fi

  local proposed_text target_file
  target_file="$(jq -r '.target_file' "$proposal_file")"
  proposed_text="$(jq -r '.proposed_text // "(no text provided)"' "$proposal_file")"

  local ts
  ts="$(now_iso)"

  jq --arg ts "$ts" '.status = "promoted" | .promoted_at = $ts' \
    "$proposal_file" > "$proposal_file.tmp" && mv "$proposal_file.tmp" "$proposal_file"

  echo "Proposal $id promoted."
  echo ""
  echo "=== Policy change ready for policy-maintainer agent ==="
  echo "Target: $target_file"
  echo "Proposed text:"
  echo "$proposed_text"
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
