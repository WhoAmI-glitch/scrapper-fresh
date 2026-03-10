#!/usr/bin/env bash
set -euo pipefail

# Check for references to non-existent agents in command and agent files.
# Looks for **agent-name** bold references and validates against registry.

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AGENTS_DIR="$ROOT/.claude/agents"
COMMANDS_DIR="$ROOT/.claude/commands"
REGISTRY="$ROOT/.claude/agents/REGISTRY.json"

echo "--- Checking agent references ---"

if [[ ! -f "$REGISTRY" ]]; then
    echo "  FAIL  Registry not found at $REGISTRY"
    exit 1
fi

# Build list of valid agent names
valid_names="$(jq -r '.agents[].name' "$REGISTRY")"

# Also collect skill names (bold references to skills are valid)
# Search both s-tier and a-tier subdirectories
skill_names=""
SKILLS_DIR="$ROOT/.claude/skills"
if [[ -d "$SKILLS_DIR" ]]; then
    skill_names="$(find "$SKILLS_DIR" -mindepth 2 -maxdepth 3 -name "SKILL.md" -exec dirname {} \; 2>/dev/null | xargs -I{} basename {} | sort -u)"
fi

failures=0
checked=0

# Scan all markdown files in agents and commands dirs
for dir in "$AGENTS_DIR" "$COMMANDS_DIR"; do
    for md_file in "$dir"/*.md; do
        [[ -f "$md_file" ]] || continue

        # Extract bold references that look like agent names (lowercase, with hyphens)
        # Pattern: **some-agent-name** where the name is lowercase with hyphens
        refs="$(grep -oE '\*\*[a-z][a-z0-9-]+\*\*' "$md_file" 2>/dev/null | sed 's/\*\*//g' | sort -u || true)"

        for ref in $refs; do
            # Skip common bold words that are not agent names
            case "$ref" in
                not|never|always|must|shall|what|why|how|the|and|or|do|if|no|yes|true|false|pass|fail|note|warning|error|important|required|optional)
                    continue
                    ;;
            esac

            checked=$((checked + 1))

            # Check if this is a valid agent or skill reference
            if echo "$valid_names" | grep -qx "$ref"; then
                # Valid agent reference
                :
            elif [[ -n "$skill_names" ]] && echo "$skill_names" | grep -qx "$ref"; then
                # Valid skill reference
                :
            elif [[ "$ref" == *-* ]]; then
                # Has a hyphen, likely intended as an agent name
                rel_path="$(basename "$(dirname "$md_file")")/$(basename "$md_file")"
                echo "  FAIL  '$ref' referenced in $rel_path but not in registry"
                failures=$((failures + 1))
            fi
        done
    done
done

echo ""
echo "Checked $checked bold references, $failures broken"

if [[ $failures -gt 0 ]]; then
    exit 1
else
    echo "  PASS  All agent references are valid"
fi
