#!/usr/bin/env bash
set -euo pipefail

# Validate all SKILL.md files in .claude/skills/{s-tier,a-tier}/*/
# Checks: YAML frontmatter contains name, description
# Description contains "Use when" or "Use this skill when"
# File is under 500 lines

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILLS_DIR="$ROOT/.claude/skills"

echo "--- Checking skill files ---"

# Vendor/Anthropic-provided skills — exempt from description and line-count rules
VENDOR_SKILLS="docx gws-gmail webapp-testing pdf pptx xlsx mcp-builder skill-creator telegram"

failures=0
checked=0

# Search both s-tier and a-tier subdirectories
for skill_file in "$SKILLS_DIR"/s-tier/*/SKILL.md "$SKILLS_DIR"/a-tier/*/SKILL.md; do
    [[ -f "$skill_file" ]] || continue
    checked=$((checked + 1))
    skill_name="$(basename "$(dirname "$skill_file")")"
    ok=true

    # Extract YAML frontmatter
    frontmatter="$(sed -n '/^---$/,/^---$/p' "$skill_file" | sed '1d;$d')"

    if [[ -z "$frontmatter" ]]; then
        echo "  FAIL  $skill_name: No YAML frontmatter found"
        failures=$((failures + 1))
        continue
    fi

    # Extract fields
    name="$(echo "$frontmatter" | grep -E '^name:' | sed 's/^name:[[:space:]]*//' | head -1)"
    # Handle multi-line YAML descriptions (>- or | syntax)
    description="$(echo "$frontmatter" | awk '/^description:/{found=1; sub(/^description:[[:space:]]*/, ""); if($0 != "" && $0 !~ /^[>|]-?$/) print; next} found && /^[[:space:]]/{print; next} found{exit}')"
    if [[ -z "$description" ]]; then
        description="$(echo "$frontmatter" | grep -E '^description:' | sed 's/^description:[[:space:]]*//' | head -1)"
    fi

    # Check name
    if [[ -z "$name" ]]; then
        echo "  FAIL  $skill_name: Missing 'name' in frontmatter"
        ok=false
    fi

    # Check if vendor skill (exempt from trigger and line-count rules)
    is_vendor=false
    for vs in $VENDOR_SKILLS; do
        [[ "$skill_name" == "$vs" ]] && is_vendor=true && break
    done

    # Check description exists and contains activation trigger
    if [[ -z "$description" ]]; then
        echo "  FAIL  $skill_name: Missing 'description' in frontmatter"
        ok=false
    elif [[ "$is_vendor" == "false" ]] && [[ ! "$description" =~ Use\ when ]] && [[ ! "$description" =~ Use\ this\ skill\ when ]] && [[ ! "$description" =~ Use\ this\ skill ]]; then
        echo "  FAIL  $skill_name: Description missing activation trigger ('Use when' / 'Use this skill when')"
        ok=false
    fi

    # Check line count (exempt vendor skills)
    line_count="$(wc -l < "$skill_file" | tr -d ' ')"
    if [[ "$is_vendor" == "false" ]] && [[ "$line_count" -ge 500 ]]; then
        echo "  FAIL  $skill_name: $line_count lines (max 500)"
        ok=false
    fi

    if [[ "$ok" == "false" ]]; then
        failures=$((failures + 1))
    else
        echo "  PASS  $skill_name ($line_count lines)"
    fi
done

echo ""
echo "Checked $checked skill files, $failures failures"

if [[ $failures -gt 0 ]]; then
    exit 1
fi
