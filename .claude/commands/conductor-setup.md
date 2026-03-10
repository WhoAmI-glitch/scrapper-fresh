---
description: "Interactive project setup: product vision, tech stack, workflow rules, and style guides"
argument-hint: "[--resume]"
---

# Conductor Setup

Multi-phase interactive workflow that creates foundational project documentation through guided Q&A. Coordinates architect and dev-lead agents for technical decisions.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Ask ONE question per turn. Wait for the user's response before proceeding.
3. Offer 2-3 suggested answers plus a "Type your own" option for each question.
4. Write each phase output to `.claude/state/workflows/conductor-setup/` before starting the next phase.
5. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
6. On any failure (file write error, missing input), halt immediately and present the error.

## Pre-flight

Check if `.claude/state/workflows/conductor-setup/state.json` exists:
- If `status: "in_progress"`: display current phase and offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Detect project type by scanning for existing indicators:
- **Greenfield**: No .git, no package.json, no requirements.txt, no go.mod, no src/ directory
- **Brownfield**: Any of the above exist -- note detected files for later context

Initialize `.claude/state/workflows/conductor-setup/state.json`:
```json
{
  "status": "in_progress",
  "project_type": "greenfield|brownfield",
  "current_phase": "product-vision",
  "completed_phases": [],
  "answers": {},
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--resume` flag.

---

## Phase 1: Product Vision and Goals

Ask these questions one at a time (max 5):

1. **Project Name** -- Infer from directory name or package manifest if brownfield.
2. **One-sentence Description** -- What does this project do?
3. **Problem Statement** -- What problem does it solve and for whom?
4. **Target Users** -- Who are the primary users?
5. **Key Goals** -- List 2-3 measurable goals. (Press enter to skip.)

Write answers to `.claude/state/workflows/conductor-setup/01-product-vision.md` as structured markdown with sections for each answer.

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present product vision summary. Options:
1. Approve -- proceed to tech stack
2. Revise -- edit specific answers
3. Pause -- save progress and stop

---

## Phase 2: Tech Stack Selection

For brownfield projects, first scan for package.json, requirements.txt, go.mod, Cargo.toml, pyproject.toml. Present detected stack and ask for confirmation.

Dispatch to **architect** agent: given the product vision from `.claude/state/workflows/conductor-setup/01-product-vision.md`, recommend a tech stack. The architect evaluates trade-offs and produces a recommendation.

Then ask the user to confirm or override (max 4 questions):

1. **Primary Language(s)** -- TypeScript, Python, Go, Rust, or detected languages.
2. **Frontend Framework** -- React, Next.js, Vue, None/CLI.
3. **Backend Framework** -- Express/Fastify, FastAPI/Django, Go stdlib, None.
4. **Database and Infrastructure** -- PostgreSQL, MongoDB, SQLite, deployment target.

Write to `.claude/state/workflows/conductor-setup/02-tech-stack.md`.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present tech stack summary alongside architect's rationale. Options:
1. Approve -- proceed to workflow rules
2. Revise -- change specific choices
3. Pause -- save progress and stop

---

## Phase 3: Workflow Rules and Conventions

Dispatch to **dev-lead** agent: given the product vision and tech stack documents, recommend workflow conventions covering TDD policy, commit strategy, code review requirements, and verification checkpoints.

Then ask the user to confirm or override (max 4 questions):

1. **TDD Strictness** -- Strict (tests first), Moderate (tests encouraged), Flexible.
2. **Commit Strategy** -- Conventional Commits, descriptive messages, squash per task.
3. **Code Review Policy** -- Required for all, required for non-trivial, optional.
4. **Verification Checkpoints** -- After each phase, after each task, only at completion.

Write to `.claude/state/workflows/conductor-setup/03-workflow.md`.

Update `state.json`: `current_phase: "checkpoint-3"`.

### PHASE CHECKPOINT 3

Present workflow rules summary. Options:
1. Approve -- proceed to style guides
2. Revise -- change specific rules
3. Pause -- save progress and stop

---

## Phase 4: Code Style Guides

Based on the languages selected in Phase 2, generate style guide documents.

Ask the user (max 2 questions):

1. **Languages to generate guides for** -- pre-select from Phase 2 choices.
2. **Existing conventions** -- For brownfield: "I found .eslintrc/.prettierrc/ruff.toml. Incorporate these?" For greenfield: "Generate fresh guides?"

Generate one style guide file per language under `.claude/state/workflows/conductor-setup/04-style-guides/`. Include naming conventions, formatting rules, import ordering, error handling patterns, and testing conventions.

Write index to `.claude/state/workflows/conductor-setup/04-style-guides.md`.

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary:

- Product Vision: `.claude/state/workflows/conductor-setup/01-product-vision.md`
- Tech Stack: `.claude/state/workflows/conductor-setup/02-tech-stack.md`
- Workflow Rules: `.claude/state/workflows/conductor-setup/03-workflow.md`
- Style Guides: `.claude/state/workflows/conductor-setup/04-style-guides.md`

Next steps: review generated files and customize as needed, then run `/scaffold-project` to create the project structure.

## Resume Handling

If `--resume` or resuming from state:
1. Load `state.json`
2. Skip completed phases
3. Resume from `current_phase`
4. Verify previously created files still exist; offer to regenerate if missing
