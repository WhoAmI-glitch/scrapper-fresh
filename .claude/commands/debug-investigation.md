---
description: "Structured debugging investigation from reproduction through verified fix"
argument-hint: "<bug description or error message> [--environment dev|staging|production] [--pattern intermittent|consistent]"
---

# Debug Investigation Orchestrator

Five-phase workflow coordinating deep-worker, backend-builder, qa-reviewer, and analyst agents for systematic root cause analysis and fix verification.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/debug-investigation/` before starting the next phase. Read prior output files rather than relying on context.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure, halt immediately and present the error.
5. Never guess at root causes. Every hypothesis must have falsification criteria.

## Pre-flight

Check if `.claude/state/workflows/debug-investigation/state.json` exists:
- If `status: "in_progress"`: display current phase and offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/debug-investigation/state.json`:
```json
{
  "bug": "$ARGUMENTS",
  "status": "in_progress",
  "environment": "dev",
  "pattern": "consistent",
  "current_phase": "reproduce",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--environment` and `--pattern` flags.

---

## Phase 1: Reproduce

### Step 1 -- Issue Parsing

Parse `$ARGUMENTS` to extract: error messages or stack traces, reproduction steps (if provided), affected components or services, environment details, failure pattern (intermittent or consistent).

### Step 2 -- Reproduction and Context Gathering

Dispatch to **deep-worker** agent with `systematic-debugging` skill: attempt to reproduce the issue locally.

Gather: relevant error logs, stack traces with full context, recent code changes in affected area (git log), dependency versions, configuration state, related test results. If the issue is in production/staging, collect observability data (traces, metrics, logs).

Write to `.claude/state/workflows/debug-investigation/01-reproduction.md`: reproduction status (confirmed/unconfirmed), exact reproduction steps, environment details, collected evidence.

---

## Phase 2: Hypothesize

### Step 3 -- Hypothesis Generation

Dispatch to **deep-worker** agent: generate 3-5 ranked hypotheses based on reproduction evidence.

For each hypothesis document:
- Description of the suspected cause
- Probability score (0-100%) with reasoning
- Supporting evidence from logs, traces, or code
- Falsification criteria -- what would disprove this hypothesis
- Testing approach to confirm or reject
- Expected symptoms if true

Categories to consider: logic errors (race conditions, null handling), state management (stale cache, incorrect transitions), integration failures (API changes, timeouts, auth), resource exhaustion (memory leaks, connection pools), configuration drift (env vars, feature flags), data issues (schema mismatches, encoding).

Write to `.claude/state/workflows/debug-investigation/02-hypotheses.md`.

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present ranked hypotheses with probability scores. Options:
1. Approve -- test hypotheses in order
2. Adjust -- reorder or add hypotheses
3. Pause -- save progress and stop

---

## Phase 3: Test

### Step 4 -- Hypothesis Testing

For each hypothesis (highest probability first), dispatch to **deep-worker** agent with `systematic-debugging` skill:

1. Apply the testing approach defined in the hypothesis
2. Examine the code path in detail -- trace execution flow, check variable state at decision points
3. Add targeted instrumentation or logging if needed
4. Run the falsification test
5. Record result: confirmed, rejected, or inconclusive with evidence

Stop testing when a hypothesis is confirmed. If all are rejected, generate new hypotheses and return to PHASE CHECKPOINT 1.

Write to `.claude/state/workflows/debug-investigation/03-test-results.md`: tested hypotheses, results with evidence, confirmed root cause.

### Step 5 -- Impact Analysis

Dispatch to **analyst** agent: assess the scope of the confirmed root cause.

Determine: all code paths affected, data integrity implications, other features that share the same pattern, frequency and user impact, how long the bug has existed (git blame analysis).

Write to `.claude/state/workflows/debug-investigation/04-impact.md`.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present confirmed root cause and impact analysis. Options:
1. Approve -- proceed to fix
2. Investigate further -- specific area needs more depth
3. Pause -- save progress and stop

---

## Phase 4: Fix

### Step 6 -- Fix Implementation

Dispatch to **backend-builder** (or **frontend-builder** if UI issue) agent: implement the minimal correct fix.

Requirements:
1. Fix the confirmed root cause, not just the symptom
2. Handle all affected code paths identified in impact analysis
3. Add inline comments explaining why the fix is needed
4. Write a regression test that would have caught this bug
5. Verify existing tests still pass

Write to `.claude/state/workflows/debug-investigation/05-fix.md`: code changes, regression test, risk assessment.

---

## Phase 5: Verify

### Step 7 -- Fix Verification

Dispatch to **qa-reviewer** agent: verify the fix thoroughly.

1. Confirm original reproduction steps no longer trigger the bug
2. Run the new regression test
3. Run the full test suite -- confirm no regressions
4. If intermittent: run reproduction scenario multiple times
5. Review fix for unintended side effects

Write to `.claude/state/workflows/debug-investigation/06-verification.md`.

### Step 8 -- Prevention

Dispatch to **deep-worker** agent: identify preventive measures.

Document: what monitoring or alerts would detect this earlier, whether linting or static analysis rules could catch similar patterns, whether the test suite has gaps that allowed this to ship, any architectural improvements to prevent the class of bug.

Write to `.claude/state/workflows/debug-investigation/07-prevention.md`.

Run `.claude/quality/scripts/validate.sh` against all artifacts if available.

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

---

## Completion

Present summary:
- Reproduction: `.claude/state/workflows/debug-investigation/01-reproduction.md`
- Hypotheses: `.claude/state/workflows/debug-investigation/02-hypotheses.md`
- Test Results: `.claude/state/workflows/debug-investigation/03-test-results.md`
- Impact Analysis: `.claude/state/workflows/debug-investigation/04-impact.md`
- Fix: `.claude/state/workflows/debug-investigation/05-fix.md`
- Verification: `.claude/state/workflows/debug-investigation/06-verification.md`
- Prevention: `.claude/state/workflows/debug-investigation/07-prevention.md`

Next steps: deploy the fix, add suggested monitoring, address prevention recommendations.
