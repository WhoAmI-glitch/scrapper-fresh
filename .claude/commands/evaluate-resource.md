---
description: "Trust and security evaluation of a repository or resource with structured scoring"
argument-hint: "[github-url-or-path]"
---

# Evaluate Resource

Multi-phase evaluation coordinating deep-worker, security-auditor, qa-reviewer, and devils-advocate agents. Produces a scored report with a trust recommendation.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/evaluate-resource/` before starting the next phase.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure, halt immediately and present the error.
5. READ-ONLY evaluation. Do not modify, install, or execute any code in the target.
6. When uncertain, prefer explicit uncertainty over confident speculation.

## Pre-flight

Check if `.claude/state/workflows/evaluate-resource/state.json` exists:
- If `status: "in_progress"`: offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/evaluate-resource/state.json`:
```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "current_phase": "quality",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Resolve target: if GitHub URL, clone to temporary read-only location. If local path, verify existence.

---

## Phase 1: Code Quality Assessment

Dispatch to **deep-worker** agent: static read-only review. Score each 1-10 with justification:
- **Structure**: directory organization, separation of concerns, module boundaries
- **Readability**: naming, comments, function size, complexity
- **Correctness**: bugs, edge cases, error handling
- **Consistency**: uniform patterns, style adherence
- **Test coverage**: presence and quality of tests

Write overall Code Quality score (1-10) to `.claude/state/workflows/evaluate-resource/01-code-quality.md`.

---

## Phase 2: Security Review

Dispatch to **security-auditor** agent: security-focused static analysis.

Evaluate: file system access, network access, shell execution, implicit execution (hooks, lifecycle scripts, postinstall), credential handling, dependency CVEs, trust boundaries (declared vs. actual permissions).

For Claude Code ecosystem resources, check: hook definitions, shell script execution by hooks/commands, persistent state files, implicit execution without confirmation, safe defaults, disable mechanisms.

Produce Security score (1-10) with permissions matrix (declared vs. inferred).

Write to `.claude/state/workflows/evaluate-resource/02-security.md`.

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present quality and security scores with top findings. Options:
1. Approve -- proceed to documentation and risk review
2. Deep-dive -- detailed analysis of specific findings
3. Pause -- save progress and stop

---

## Phase 3: Documentation Accuracy

Dispatch to **qa-reviewer** agent: compare documentation claims against implementation.

Evaluate: README accuracy, API docs vs. actual interfaces, configuration completeness, changelog maintenance, license presence.

Produce Documentation score (1-10) with specific discrepancies.

Write to `.claude/state/workflows/evaluate-resource/03-documentation.md`.

---

## Phase 4: Risk Assessment

Dispatch to **devils-advocate** agent: adversarial review of findings from Phases 1-3.

Evaluate: red flags (malware, undisclosed execution, exfiltration), claim-vs-reality mismatches, supply chain risk, maintenance risk (last commit, issue response), blast radius.

Mark speculative claims with explicit uncertainty.

Write to `.claude/state/workflows/evaluate-resource/04-risk-assessment.md`.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present all four scores and risk findings. Options:
1. Accept -- generate final report
2. Investigate further -- deep-dive specific concerns
3. Pause -- save progress and stop

---

## Phase 5: Final Report

Compile into `.claude/state/workflows/evaluate-resource/05-report.md` with: scores table (Code Quality, Security, Documentation, Risk, Overall), recommendation (Recommend / Recommend with caveats / Needs further review / Reject), top 5 findings ranked by severity, permissions summary, red flags, and improvement suggestions.

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary with paths to all five output files.

Next steps: act on recommendation -- integrate, investigate further, or reject.
