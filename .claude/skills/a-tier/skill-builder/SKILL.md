---
name: "Skill Builder"
description: "Create new Claude Code Skills with proper YAML frontmatter, progressive disclosure structure, and complete directory organization. Use when you need to build custom skills for specific workflows, generate skill templates, or understand the Claude Skills specification."
---

# Skill Builder

Creates production-ready Claude Code Skills with proper YAML frontmatter, progressive disclosure architecture, and complete file/folder structure.

## Prerequisites

- Claude Code 2.0+ or Claude.ai with Skills support
- Basic understanding of Markdown and YAML

## Quick Start

```bash
# 1. Create skill directory
mkdir -p ~/.claude/skills/my-first-skill

# 2. Create SKILL.md with proper format
cat > ~/.claude/skills/my-first-skill/SKILL.md << 'EOF'
---
name: "My First Skill"
description: "Brief description of what this skill does and when Claude should use it. Maximum 1024 characters."
---

# My First Skill

## What This Skill Does
[Your instructions here]

## Quick Start
[Basic usage]
EOF
```

## YAML Frontmatter (REQUIRED)

Every SKILL.md must start with exactly two required fields:

```yaml
---
name: "Skill Name"                    # REQUIRED: Max 64 chars
description: "What this skill does    # REQUIRED: Max 1024 chars
and when Claude should use it."       # Include BOTH what & when
---
```

**`name`**: Human-friendly display name, Title Case, max 64 chars.
**`description`**: Must include what the skill does AND when to invoke it. Front-load key trigger words.

Only `name` and `description` are used by Claude. Additional fields are ignored.

## Directory Structure

```
~/.claude/skills/              # Personal skills (all projects)
<project>/.claude/skills/      # Project skills (version controlled)
  └── my-skill/                # MUST be directly under skills/
      ├── SKILL.md             # REQUIRED
      ├── scripts/             # Optional executables
      ├── resources/           # Optional templates, examples, schemas
      └── docs/                # Optional additional documentation
```

**IMPORTANT**: Skills must be directly under the skills directory. No nested subdirectories.

## Progressive Disclosure (3 Levels)

**Level 1 - Metadata** (always loaded, ~200 chars): Name + description in YAML frontmatter. Enables autonomous skill matching across all 100+ skills with minimal context.

**Level 2 - SKILL.md Body** (loaded when triggered, ~1-10KB): Main instructions and procedures. Keep lean.

**Level 3 - Referenced Files** (loaded on-demand): Deep reference, examples, schemas in `docs/`, `resources/`. Claude loads only when needed.

## SKILL.md Content Structure

```markdown
---
name: "Your Skill Name"
description: "What it does and when to use it"
---

# Your Skill Name

## Level 1: Overview
Brief 2-3 sentence description.

## Prerequisites
- Requirement 1

## Quick Start
```bash
command --option value
```

## Step-by-Step Guide

### Step 1: Setup
[Instructions]

### Step 2: Usage
[Instructions]

## Advanced Options
See [docs/ADVANCED.md](docs/ADVANCED.md)

## Troubleshooting
- **Issue**: Description -> **Solution**: Fix
```

## Content Best Practices

**Descriptions** - Front-load keywords, include trigger conditions, be specific about technologies:
```yaml
# Good
description: "Generate TypeScript interfaces from JSON schema. Use when converting schemas, creating types, or building API clients."
# Bad
description: "Helps with JSON schema work."
```

**Progressive Disclosure** - Keep Level 1 brief (one sentence), Level 2 for common paths (80% use case), Level 3 for details, Level 4 for edge cases via separate files.

**SKILL.md size**: Target 2-5KB. Move lengthy content to separate files and reference them.

## Validation Checklist

- [ ] YAML: starts/ends with `---`, has `name` (max 64) and `description` (max 1024) with what+when
- [ ] Directory directly under `~/.claude/skills/` or `.claude/skills/`
- [ ] Content: brief overview, quick start, step-by-step, troubleshooting
- [ ] Examples are concrete and runnable
- [ ] Advanced content in separate docs, large resources in resources/
- [ ] Skill appears in Claude's skill list and triggers on relevant queries

## Templates

### Basic Skill

```markdown
---
name: "My Basic Skill"
description: "One sentence what. One sentence when to use."
---

# My Basic Skill

## What This Skill Does
[2-3 sentences]

## Quick Start
```bash
# Single command
```

## Step-by-Step Guide
### Step 1: Setup
### Step 2: Usage
### Step 3: Verify

## Troubleshooting
- **Issue**: Problem -> **Solution**: Fix
```

### Intermediate Skill (With Scripts)

```markdown
---
name: "My Intermediate Skill"
description: "Detailed what with features. When to use with triggers."
---

# My Intermediate Skill

## Prerequisites
- Requirement 1

## Quick Start
```bash
./scripts/setup.sh
./scripts/generate.sh my-project
```

## Configuration
Edit `config.json`

## Step-by-Step Guide
### Basic Usage
### Advanced Usage

## Scripts
- `scripts/setup.sh` - Initial setup
- `scripts/generate.sh` - Code generation

## Troubleshooting
[Common issues]
```

## Resources

- [Anthropic Agent Skills Documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
- [Skills Marketplace](https://github.com/anthropics/skills)
