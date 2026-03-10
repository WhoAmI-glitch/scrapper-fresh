#!/usr/bin/env bash
set -euo pipefail

# Validate all command .md files in .claude/commands/
# Checks: first line is not empty, file has substantive content
# Note: command files use prose instructions, not YAML frontmatter.
# We check that the file is non-empty and has a clear description/purpose.

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
COMMANDS_DIR="$ROOT/.claude/commands"

echo "--- Checking command files ---"

failures=0
checked=0

for cmd_file in "$COMMANDS_DIR"/*.md; do
    [[ -f "$cmd_file" ]] || continue
    checked=$((checked + 1))
    cmd_name="$(basename "$cmd_file" .md)"
    ok=true

    # Check file is non-empty
    if [[ ! -s "$cmd_file" ]]; then
        echo "  FAIL  $cmd_name: File is empty"
        ok=false
    fi

    # Check file has at least 3 lines of content
    line_count="$(wc -l < "$cmd_file" | tr -d ' ')"
    if [[ "$line_count" -lt 3 ]]; then
        echo "  FAIL  $cmd_name: Too short ($line_count lines, need at least 3)"
        ok=false
    fi

    # Check first non-empty line exists and is descriptive
    first_line="$(grep -m1 '[^ ]' "$cmd_file" 2>/dev/null || true)"
    if [[ -z "$first_line" ]]; then
        echo "  FAIL  $cmd_name: No content found"
        ok=false
    fi

    # Check for YAML frontmatter if present
    if head -1 "$cmd_file" | grep -q '^---$'; then
        frontmatter="$(sed -n '/^---$/,/^---$/p' "$cmd_file" | sed '1d;$d')"
        if [[ -n "$frontmatter" ]]; then
            desc="$(echo "$frontmatter" | grep -E '^description:' | sed 's/^description:[[:space:]]*//' | head -1)"
            if [[ -z "$desc" ]]; then
                echo "  WARN  $cmd_name: Has frontmatter but missing 'description' field"
            fi
        fi
    fi

    if [[ "$ok" == "false" ]]; then
        failures=$((failures + 1))
    else
        echo "  PASS  $cmd_name"
    fi
done

echo ""
echo "Checked $checked command files, $failures failures"

if [[ $failures -gt 0 ]]; then
    exit 1
fi
