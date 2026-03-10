---
name: conductor-workflow
description: >-
  Context-driven development workflow for managing projects through structured
  context artifacts, track-based feature development, and phased implementation
  with verification checkpoints. Use when setting up project context, creating
  feature tracks, managing spec-plan-implement cycles, or coordinating multi-session
  development.
---

# Conductor Workflow

A methodology for context-driven development where project context is a managed artifact
alongside code, enabling consistent AI interactions and structured feature delivery.

## Core Principle

**Context precedes code.** Define what you are building and how before implementation.
Context artifacts are living documents that evolve with the project.

## The Workflow

```
Context Setup -> Spec & Plan -> Implement -> Verify -> Update Context
```

### 1. Context Setup

Establish five context artifacts in a `conductor/` directory:

| Artifact                | Defines           | Update Trigger                     |
|------------------------|-------------------|------------------------------------|
| `product.md`           | WHAT and WHY      | Vision change, new major features  |
| `product-guidelines.md`| HOW to communicate| Brand/terminology changes          |
| `tech-stack.md`        | WITH WHAT         | New dependencies, version upgrades |
| `workflow.md`          | HOW to work       | Process changes, new quality gates |
| `tracks.md`            | WHAT is happening | Track creation, status changes     |

For new projects: Answer interactive questions about product vision, tech preferences,
and workflow conventions. For existing projects: Analyze existing code, configs, and
documentation to pre-populate artifacts.

### 2. Track-Based Development

A track is a logical work unit (feature, bug, refactor, chore) that follows a lifecycle:

```
Create -> Specify -> Plan -> Implement -> Verify -> Complete
```

**Track structure:**

```
conductor/tracks/<track-id>/
  spec.md        # Requirements and acceptance criteria
  plan.md        # Phased task breakdown
  metadata.json  # Status, assignee, progress
```

**Track ID format:** `{shortname}_{YYYYMMDD}` (e.g., `user-auth_20250115`)

**Sizing guidelines:**
- Right-sized: 1-5 days, 2-4 phases, 8-20 tasks
- Too large (> 5 phases, > 25 tasks): Split into multiple tracks
- Too small (single phase, 1-2 tasks): Combine with related work

### 3. Spec-Plan-Implement Cycle

**Specification (spec.md):**
- Functional requirements with acceptance criteria
- Non-functional requirements with measurable targets
- Explicit in-scope and out-of-scope boundaries
- Dependencies (hard, soft, external)
- Risk assessment with mitigations

**Plan (plan.md):**
- Phased task breakdown (each phase independently testable)
- Verification tasks after each phase
- Status markers: `[ ]` pending, `[~]` in-progress, `[x]` complete, `[!]` blocked, `[-]` skipped
- Commit SHAs recorded for completed tasks

**Implementation:**
- Follow TDD workflow per task
- Mark task status as you work
- Record checkpoint SHAs at phase boundaries
- Wait for verification approval before proceeding to next phase

### 4. Context Maintenance

Keep artifacts synchronized:
- New feature in product.md -> update tech-stack.md if new dependencies needed
- Completed track -> update product.md to reflect new capabilities
- Workflow change -> update all affected track plans

**Validation checklist before starting any track:**
- [ ] product.md reflects current product vision
- [ ] tech-stack.md lists all current dependencies with accurate versions
- [ ] workflow.md describes current practices
- [ ] tracks.md shows all active work with correct statuses

### 5. Session Continuity

For multi-session development:

**Starting a session:** Read index.md, check tracks.md for active work, review
the relevant track's plan.md for current task.

**Ending a session:** Update plan.md with progress, note blockers, commit
work-in-progress, update tracks.md if status changed.

**Handling interruptions:** Mark task as `[~]` with note about stopping point,
commit WIP to feature branch, document uncommitted decisions.

## Semantic Revert

Tracks enable granular revert capability:
- Revert an entire track (all commits associated with that track)
- Revert a single phase (commits within one phase)
- Revert a single task (individual commit)

This works because every completed task records its commit SHA.

## Anti-Patterns

| Anti-Pattern         | Problem                              | Fix                                  |
|---------------------|--------------------------------------|--------------------------------------|
| Stale context       | Documents become outdated, misleading| Update context as part of each track |
| Context sprawl      | Information scattered everywhere     | Use defined artifact structure only  |
| Implicit context    | Relying on undocumented knowledge    | Add to appropriate artifact          |
| Over-specification  | Context too detailed to maintain     | Focus on decisions that affect behavior|

## Common Track Patterns

**Feature:** Foundation (models, migrations) -> Core logic (business rules) -> Integration (UI, API docs, E2E)

**Bug fix:** Reproduction (failing test) -> Fix (implementation, verify) -> Verification (manual check, docs)

**Refactor:** Preparation (characterization tests) -> Refactoring (incremental, green tests) -> Cleanup (dead code, docs)
