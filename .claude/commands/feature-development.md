---
description: "Orchestrate end-to-end feature development from requirements through deployment (backend-only or full-stack)"
argument-hint: "<feature description> [--scope backend|frontend|fullstack] [--methodology tdd|bdd|traditional] [--complexity simple|medium|complex]"
---

# Feature Development Orchestrator

Multi-phase workflow coordinating architect, database-architect, backend-builder, frontend-builder, qa-reviewer, and deployer agents. Handles both backend-only and full-stack features -- use the `--scope` flag to control which phases execute (defaults to fullstack).

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/feature-development/` before starting the next phase. Read prior output files rather than relying on context.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure (agent error, test failure, missing dependency), halt immediately and present the error.

## Pre-flight

Check if `.claude/state/workflows/feature-development/state.json` exists:
- If `status: "in_progress"`: display current phase and offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/feature-development/state.json`:
```json
{
  "feature": "$ARGUMENTS",
  "status": "in_progress",
  "scope": "fullstack",
  "methodology": "traditional",
  "complexity": "medium",
  "current_phase": "discovery",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--scope`, `--methodology`, and `--complexity` flags.

---

## Phase 1: Discovery

### Step 1 -- Requirements Gathering

Ask the user one question at a time:
1. What problem does this feature solve? Who is the user?
2. What are the acceptance criteria?
3. What is explicitly out of scope?
4. Any technical constraints (auth system, DB, latency)?
5. Dependencies on other features or services?

Write answers to `.claude/state/workflows/feature-development/01-requirements.md`.

### Step 2 -- Architecture Design

Dispatch to **architect** agent: design service boundaries, API endpoints, data model, security considerations, and integration points based on the requirements document.

Write output to `.claude/state/workflows/feature-development/02-architecture.md`.

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present architecture summary. Options:
1. Approve -- proceed to implementation
2. Request changes -- revise architecture
3. Pause -- save progress and stop

---

## Phase 2: Database Design

### Step 3 -- Data Model and Schema

Dispatch to **database-architect** agent: design the database schema, migrations, indexes, and constraints based on the approved architecture. Define entity relationships, normalization strategy, query patterns, and performance considerations (indexes, partitioning).

If the feature requires no new data storage, write a skip note in `.claude/state/workflows/feature-development/03-database.md` and continue.

Write output to `.claude/state/workflows/feature-development/03-database.md`.

---

## Phase 3: Implement

### Step 4 -- Backend Implementation

Dispatch to **backend-builder** agent: implement API endpoints, business logic, data access layer, input validation, and error handling per the approved architecture. If methodology is TDD, write failing tests first.

Write summary to `.claude/state/workflows/feature-development/04-backend.md`.

### Step 5 -- Frontend Implementation

Dispatch to **frontend-builder** agent: build UI components integrating with backend endpoints, implement state management, form handling, error states, loading states, and responsive design.

If the feature is backend-only, write a skip note in `.claude/state/workflows/feature-development/05-frontend.md` and continue.

Write summary to `.claude/state/workflows/feature-development/05-frontend.md`.

### Step 6 -- Testing and Validation

Launch in parallel using `dispatching-parallel-agents` skill:

**6a. Test Suite** -- Dispatch to **qa-reviewer** agent: create unit tests for backend, integration tests for API, component tests for frontend. Target 80%+ coverage. Use `test-driven-development` skill.

**6b. Security Review** -- Dispatch to **devils-advocate** agent: review for OWASP Top 10, auth flaws, input validation gaps, data protection issues. Provide findings with severity and fix recommendations.

**6c. Architecture Review** -- Dispatch to **dev-lead** agent: verify implementation matches approved architecture, check for performance concerns (N+1 queries, missing indexes, large payloads).

Consolidate results into `.claude/state/workflows/feature-development/06-validation.md` with sections: Test Suite, Security Findings, Architecture Findings, Action Items.

Address any Critical or High findings before proceeding.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present validation summary (test coverage, security findings by severity, architecture concerns). Options:
1. Approve -- proceed to review and delivery
2. Request changes -- fix specific issues
3. Pause -- save progress and stop

---

## Phase 4: Review

### Step 7 -- Quality Gate

Run `.claude/quality/scripts/validate.sh` against all artifacts if available. Dispatch to **qa-reviewer** agent for final acceptance review: verify acceptance criteria from requirements, confirm test coverage, check for regressions.

Write report to `.claude/state/workflows/feature-development/07-quality-gate.md`.

### Step 8 -- Deployment Preparation

Dispatch to **deployer** agent: create or update CI/CD configuration, define health checks, configure feature flags for gradual rollout, write deployment runbook with rollback steps.

Write output to `.claude/state/workflows/feature-development/08-deployment.md`.

Update `state.json`: `current_phase: "checkpoint-3"`.

### PHASE CHECKPOINT 3

Present quality gate results and deployment plan. Options:
1. Approve -- finalize
2. Request changes
3. Pause

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary:
- Requirements: `.claude/state/workflows/feature-development/01-requirements.md`
- Architecture: `.claude/state/workflows/feature-development/02-architecture.md`
- Database: `.claude/state/workflows/feature-development/03-database.md`
- Backend: `.claude/state/workflows/feature-development/04-backend.md`
- Frontend: `.claude/state/workflows/feature-development/05-frontend.md`
- Validation: `.claude/state/workflows/feature-development/06-validation.md`
- Quality Gate: `.claude/state/workflows/feature-development/07-quality-gate.md`
- Deployment: `.claude/state/workflows/feature-development/08-deployment.md`

Next steps: review generated code, run full test suite, create pull request, deploy using runbook.
