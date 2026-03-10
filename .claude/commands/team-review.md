---
description: "Launch parallel multi-agent code review with independent findings and unified report"
argument-hint: "[path-or-pr] [--reviewers security,quality,architecture,devlead] [--base-branch main]"
---

# Team Review

Orchestrate a parallel multi-agent code review where each reviewer evaluates independently along a specific quality dimension. Produces a consolidated, deduplicated report organized by severity.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/team-review/` before starting the next phase.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure, halt immediately and present the error.
5. Each reviewer operates independently -- do not share findings between reviewers before consolidation.

## Pre-flight

Check if `.claude/state/workflows/team-review/state.json` exists:
- If `status: "in_progress"`: display current phase and offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/team-review/state.json`:
```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "reviewers": ["security-auditor", "qa-reviewer", "architect", "dev-lead"],
  "base_branch": "main",
  "current_phase": "resolve",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS`:
- First positional arg: file path, directory, or PR identifier (e.g., `#123` or `main...HEAD`)
- `--reviewers`: comma-separated list mapping to agents: `security` -> **security-auditor**, `quality` -> **qa-reviewer**, `architecture` -> **architect**, `devlead` -> **dev-lead**
- `--base-branch`: base branch for diff comparison (default: `main`)

---

## Phase 1: Target Resolution

Determine the target type and collect review material:

- **File or Directory**: read contents directly using Glob and Read
- **Git diff range** (e.g., `main...HEAD`): run `git diff {range}` to get the full diff and `git diff {range} --name-only` for file list
- **PR number** (e.g., `#123`): run `gh pr diff {number}` for full diff and `gh pr diff {number} --name-only` for file list

Write the review scope (file list, diff summary, line count) to `.claude/state/workflows/team-review/01-scope.md`.

Present to user: "{N} files to review across {M} dimensions ({reviewer names})".

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present review scope. Options:
1. Approve -- launch reviewers
2. Adjust scope -- add/remove files or reviewers
3. Pause -- save progress and stop

---

## Phase 2: Parallel Review

Launch each reviewer in parallel using the `dispatching-parallel-agents` skill.

For each reviewer, dispatch to the corresponding agent with the diff content and file list:

**security-auditor**: Review for injection vulnerabilities, auth flaws, credential exposure, insecure configurations, OWASP Top 10 issues. Produce findings as structured list with severity, file, line, description, and recommendation.

**qa-reviewer**: Review for test coverage gaps, edge cases, error handling, code quality, maintainability, naming conventions, documentation completeness. Produce findings with severity.

**architect**: Review for design pattern violations, coupling issues, API contract consistency, scalability concerns, separation of concerns, dependency direction. Produce findings with severity.

**dev-lead**: Review for code style, performance hotspots, unnecessary complexity, missing abstractions, dead code, incomplete implementations. Produce findings with severity.

Write each reviewer's raw findings to `.claude/state/workflows/team-review/02-{reviewer-name}-findings.md`.

Track progress and report: "{completed}/{total} reviews complete".

---

## Phase 3: Consolidation

Read all finding files from Phase 2.

1. **Deduplicate**: Merge findings that reference the same file and line range.
2. **Resolve conflicts**: If reviewers disagree on severity, use the higher rating.
3. **Cross-reference**: Note findings flagged by multiple reviewers (higher confidence).
4. **Organize by severity**: Group as Critical, High, Medium, Low, Informational.

Write consolidated findings to `.claude/state/workflows/team-review/03-consolidated.md`.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present consolidated findings summary (counts by severity, top 5 critical/high items). Options:
1. Accept report -- generate final output
2. Request deeper analysis on specific findings
3. Pause -- save progress and stop

---

## Phase 4: Final Report

Generate the unified review report in `.claude/state/workflows/team-review/04-report.md`:

```
## Code Review Report: {target}

Reviewed by: {reviewer names}
Files reviewed: {count}
Date: {ISO_TIMESTAMP}

### Critical ({count})
[findings with file, line, description, reviewer(s), recommendation]

### High ({count})
[findings...]

### Medium ({count})
[findings...]

### Low ({count})
[findings...]

### Summary
Total findings: {count} (Critical: N, High: N, Medium: N, Low: N)
Cross-reviewer consensus items: {count}
```

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary:
- Scope: `.claude/state/workflows/team-review/01-scope.md`
- Individual findings: `.claude/state/workflows/team-review/02-*-findings.md`
- Consolidated: `.claude/state/workflows/team-review/03-consolidated.md`
- Final Report: `.claude/state/workflows/team-review/04-report.md`

Next steps: address Critical and High findings, create follow-up tasks for Medium items.
