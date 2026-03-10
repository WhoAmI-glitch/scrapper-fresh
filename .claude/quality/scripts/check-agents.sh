#!/usr/bin/env bash
set -euo pipefail

# Validate all agent .md files in .claude/agents/
# Checks: YAML frontmatter contains name, description, model
# Model must be one of: opus, sonnet, haiku
# Description must start with "Use when"
# Agent must exist in .claude/agents/REGISTRY.json

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AGENTS_DIR="$ROOT/.claude/agents"
REGISTRY="$ROOT/.claude/agents/REGISTRY.json"

echo "--- Checking agent files ---"

failures=0
checked=0

# Get registry names for cross-check
registry_names=""
if [[ -f "$REGISTRY" ]]; then
    registry_names="$(jq -r '.agents[].name' "$REGISTRY")"
fi

for agent_file in "$AGENTS_DIR"/*.md; do
    [[ -f "$agent_file" ]] || continue
    checked=$((checked + 1))
    basename="$(basename "$agent_file" .md)"
    ok=true

    # Extract YAML frontmatter (between first pair of ---)
    frontmatter="$(sed -n '/^---$/,/^---$/p' "$agent_file" | sed '1d;$d')"

    if [[ -z "$frontmatter" ]]; then
        echo "  FAIL  $basename: No YAML frontmatter found"
        failures=$((failures + 1))
        continue
    fi

    # Extract fields from frontmatter
    name="$(echo "$frontmatter" | grep -E '^name:' | sed 's/^name:[[:space:]]*//' | head -1)"
    description="$(echo "$frontmatter" | grep -E '^description:' | sed 's/^description:[[:space:]]*//' | head -1)"
    model="$(echo "$frontmatter" | grep -E '^model:' | sed 's/^model:[[:space:]]*//' | head -1)"

    # Check name exists
    if [[ -z "$name" ]]; then
        echo "  FAIL  $basename: Missing 'name' in frontmatter"
        ok=false
    fi

    # Check description exists and starts with "Use when"
    if [[ -z "$description" ]]; then
        echo "  FAIL  $basename: Missing 'description' in frontmatter"
        ok=false
    elif [[ ! "$description" =~ ^Use\ when ]]; then
        echo "  FAIL  $basename: Description does not start with 'Use when' (got: ${description:0:40}...)"
        ok=false
    fi

    # Check model exists and is valid
    if [[ -z "$model" ]]; then
        echo "  FAIL  $basename: Missing 'model' in frontmatter"
        ok=false
    elif [[ "$model" != "opus" && "$model" != "sonnet" && "$model" != "haiku" ]]; then
        echo "  FAIL  $basename: Invalid model '$model' (must be opus, sonnet, or haiku)"
        ok=false
    fi

    # Cross-check against registry
    if [[ -n "$registry_names" && -n "$name" ]]; then
        if ! echo "$registry_names" | grep -qx "$name"; then
            echo "  FAIL  $basename: Agent '$name' not found in registry"
            ok=false
        fi
    fi

    if [[ "$ok" == "false" ]]; then
        failures=$((failures + 1))
    else
        echo "  PASS  $basename"
    fi
done

echo ""
echo "Checked $checked agent files, $failures failures"

if [[ $failures -gt 0 ]]; then
    exit 1
fi
