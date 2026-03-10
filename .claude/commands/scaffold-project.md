---
description: "Scaffold a complete project with structure, tooling, tests, and deployment config"
argument-hint: "[project-name] [--stack react|fastapi|nextjs|go|express|django|library|cli]"
---

# Scaffold Project

Multi-phase project scaffolding workflow coordinating architect, scaffolder, devops-engineer, qa-reviewer, and deployer agents. Generates a production-ready project structure with tooling, tests, and deployment configuration.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/scaffold-project/` before starting the next phase.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure, halt immediately and present the error.
5. Never overwrite existing project files without explicit user consent.

## Pre-flight

Check if `.claude/state/workflows/scaffold-project/state.json` exists:
- If `status: "in_progress"`: display current phase and offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/scaffold-project/state.json`:
```json
{
  "project_name": "",
  "stack": "",
  "status": "in_progress",
  "current_phase": "stack-selection",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS`:
- First positional arg: project name
- `--stack`: technology stack choice

If project name is missing, ask the user. If stack is missing, proceed to Phase 1 for interactive selection.

---

## Phase 1: Stack Selection

If `--stack` was provided, validate it against supported options and skip to checkpoint.

Otherwise, dispatch to **architect** agent: given the project name, analyze what stack would be appropriate. If `.claude/state/workflows/conductor-setup/` exists, read product vision and tech stack docs for context.

Present the architect's recommendation, then ask the user:

1. **Stack choice**: React (Vite SPA), Next.js (SSR/SSG full-stack), FastAPI (Python API), Django (Python full-stack), Go (Go API/CLI), Express (Node.js API), Library (reusable package), CLI (command-line tool).
2. **Package manager preference**: pnpm, npm, yarn, uv (Python), go modules.
3. **Additional features**: auth, database ORM, Docker, CI/CD, monitoring.

Write decisions to `.claude/state/workflows/scaffold-project/01-stack-selection.md`.

Update `state.json`: `current_phase: "checkpoint-1"`, populate `project_name` and `stack`.

### PHASE CHECKPOINT 1

Present stack selection summary. Options:
1. Approve -- proceed to project generation
2. Change stack -- select different options
3. Pause -- save progress and stop

---

## Phase 2: Project Structure Generation

Dispatch to **scaffolder** agent: generate the complete project directory structure based on the selected stack. Must create: directory tree, entry point files, package manifest, type config, .gitignore, .env.example, and README.md with setup instructions.

Write file manifest to `.claude/state/workflows/scaffold-project/02-structure.md`.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present generated file tree and key configuration choices. Options:
1. Approve -- proceed to tooling setup
2. Request changes -- modify structure
3. Pause -- save progress and stop

---

## Phase 3: Tooling Configuration

Dispatch to **devops-engineer** agent: configure linting (ESLint/Ruff/golangci-lint), formatting (Prettier/Ruff/gofmt), testing (Vitest/pytest/go test) with coverage, pre-commit hooks, GitHub Actions CI pipeline, and a Makefile with common commands (dev, test, lint, build, clean).

Write tooling summary to `.claude/state/workflows/scaffold-project/03-tooling.md`.

---

## Phase 4: Initial Tests

Dispatch to **qa-reviewer** agent: create health check smoke test, example unit test demonstrating conventions, and coverage baseline. Run the test suite to verify it passes.

Write test summary to `.claude/state/workflows/scaffold-project/04-tests.md`.

Update `state.json`: `current_phase: "checkpoint-3"`.

### PHASE CHECKPOINT 3

Present tooling and test results. Options:
1. Approve -- proceed to deployment config
2. Fix issues -- address test failures
3. Pause -- save progress and stop

---

## Phase 5: Deployment Configuration

Dispatch to **deployer** agent: create Dockerfile (multi-stage), docker-compose.yml for local dev, platform config (vercel.json/railway.json), health check endpoint, and environment variable documentation.

Write deployment summary to `.claude/state/workflows/scaffold-project/05-deployment.md`.

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary:
- Stack Selection: `.claude/state/workflows/scaffold-project/01-stack-selection.md`
- Project Structure: `.claude/state/workflows/scaffold-project/02-structure.md`
- Tooling: `.claude/state/workflows/scaffold-project/03-tooling.md`
- Tests: `.claude/state/workflows/scaffold-project/04-tests.md`
- Deployment: `.claude/state/workflows/scaffold-project/05-deployment.md`

Next steps: review generated project, install dependencies, run the dev server, customize as needed.
