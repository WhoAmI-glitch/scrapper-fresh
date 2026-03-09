# CLAUDE.md -- Multi-Agent Operating System

## 1. Identity

This workspace operates as a **multi-agent productivity operating system**.

| Component | Role |
|---|---|
| **Coordinator** | Decomposes tasks, routes to specialists, enforces quality, accepts/rejects deliverables |
| **Specialist agents** | Execute discrete units of work through structured state transitions |
| **Communication** | All inter-agent data flows through JSON artifacts -- never prose handoffs |

The coordinator is the only agent that reads this file as policy. Specialists receive scoped instructions via handoff artifacts.

---

## 2. Architecture Reference

Do NOT duplicate definitions here. The single source of truth for each concern:

| Concern | Location |
|---|---|
| Agent definitions and routing | `.claude/agents/REGISTRY.json` |
| Data contracts (task, handoff, finding, report) | `.claude/schemas/` |
| Runtime state (tasks, locks, queues) | `.claude/state/` |
| Quality gates and validation scripts | `.claude/quality/` |
| Evolution rules and proposals | `.claude/policy/` |

If a directory does not yet exist, the first agent that needs it creates it with the correct schema scaffolding.

---

## 3. Immutable Rules

These ten rules cannot be overridden by any agent, task, or policy proposal.

| # | Rule |
|---|---|
| 1 | Never commit secrets. If a key or token is detected in staged files, abort the commit and alert the coordinator. |
| 2 | Never force-push to `main` or `production`. |
| 3 | Run the quality gate before declaring any task complete. |
| 4 | Create new commits. Never amend unless the user explicitly instructs it. |
| 5 | Never skip git hooks (`--no-verify` is forbidden). |
| 6 | Atomic commits -- one logical change per commit. |
| 7 | Conventional commit format: `type(scope): description`. |
| 8 | No dead code -- remove unused imports, variables, and functions. |
| 9 | All inter-agent communication through schema-validated state files in `.claude/state/`. |
| 10 | Policy changes only through the promotion lifecycle (Section 7). Direct edits to this file are forbidden. |

---

## 4. Task Lifecycle

Every task is a JSON file in `.claude/state/tasks/` conforming to `task.schema.json`.

**State machine:**

```
pending --> assigned --> in_progress --> review --> done
                                    \-> failed
```

**Transition conditions:**

| From | To | Requires |
|---|---|---|
| `pending` | `assigned` | Coordinator sets `assignee` and creates `handoff.json` |
| `assigned` | `in_progress` | Specialist acknowledges handoff, begins work |
| `in_progress` | `review` | Specialist creates `finding.json` with deliverables |
| `review` | `done` | Quality gate passes, coordinator creates `decision.json` with `accept` |
| `review` | `failed` | Quality gate fails or coordinator creates `decision.json` with `reject` |
| `failed` | `assigned` | Coordinator reassigns with updated handoff containing failure context |

No transition may skip a state. No state may be entered without its precondition.

---

## 5. Communication Protocol

All artifacts conform to schemas in `.claude/schemas/`.

**Artifact flow:**

1. **Coordinator** creates `handoff.json` -- task ID, assignee, scope, acceptance criteria, constraints
2. **Specialist** creates `finding.json` -- task ID, deliverables (files changed, tests added), self-assessment
3. **QA gate** produces `quality-report.json` -- checklist results, score, pass/fail, defect list
4. **Coordinator** creates `decision.json` -- task ID, verdict (`accept`|`reject`), reasoning, next action

Artifacts are written to their type-specific directory (`state/handoffs/`, `state/findings/`, `state/decisions/`) and are immutable once created. Corrections produce new versioned artifacts, never overwrites.

---

## 6. Quality Gate Protocol

1. Every meaningful change triggers `.claude/quality/scripts/validate.sh`
2. The script checks against gates defined in `.claude/quality/gates.json`

**Gate checks:**

| Check | What it validates |
|---|---|
| Correctness | Compiles without errors, tests pass |
| Completeness | All acceptance criteria from handoff addressed |
| Regressions | No existing tests broken |
| Duplication | No copy-pasted logic or redundant code |
| Contracts | Public interfaces validated, schemas enforced |

3. Results written to `.claude/quality/reports/` as `quality-report.json`
4. Changes scoring below the threshold in `gates.json` are rejected -- the task transitions to `failed`

---

## 7. Policy Evolution Protocol

Rules in this file evolve through a controlled promotion lifecycle, never through direct edits.

1. Any agent proposes a change by writing `proposal.json` to `.claude/policy/proposals/`
2. The `policy-maintainer` agent evaluates against `.claude/policy/criteria.json` (impact, reversibility, scope)
3. **Approved**: promoted into this file with a CHANGELOG entry in `.claude/policy/CHANGELOG.md`
4. **Rejected**: archived to `.claude/policy/archive/` with reasoning in the proposal record

---

## 8. Code Standards

### TypeScript
- `strict: true`, no `any` without branded utility + comment
- Structured logger only -- no `console.log` in production
- Runtime validation with `zod`

### Python
- Type hints on all signatures, `pydantic` for data models
- `ruff format` + `ruff check`, async-first for I/O-bound code

### SQL
- Parameterized queries only -- never string concatenation
- All migrations must be reversible

### Shell
- `set -euo pipefail` at top of every script
- All variables quoted, `shellcheck` compliant

---

## 9. Working Style

1. **Plan before code** -- numbered checklist, max 8 steps per phase; split if larger
2. **Build order** -- types/interfaces first, then implementation, then tests
3. **Composition over inheritance**, pure functions over stateful classes
4. **Early returns** to reduce nesting, readable names over abbreviations
5. **Concise communication** -- lead with result, follow with reasoning, bullet points over paragraphs
6. **Assumptions** and **risks** must be called out explicitly when present

---

## 10. Deliverable Standard

A task is DONE only when ALL of the following hold:

| # | Criterion |
|---|---|
| 1 | Compiles / interprets without errors |
| 2 | Passes linting and type-checking for the relevant language |
| 3 | Passes all existing tests plus new tests covering new behavior |
| 4 | Contains no hardcoded secrets, tokens, or environment-specific values |
| 5 | Handles errors gracefully with meaningful messages |
| 6 | All public interfaces have validated inputs |

If any criterion fails, the task remains in `review` or transitions to `failed`.

---

## 11. Project Context

This workspace currently hosts a **Russian construction company lead generation scraper**:
a two-stage pipeline (discovery + enrichment) that finds companies, resolves them on
russprofile.ru, scrapes structured business data (INN, OGRN, contacts, revenue), and
stores enriched leads in PostgreSQL. A FastAPI dashboard provides one-click operation
and Excel export. See `ARCHITECTURE.md`, `QUICKSTART.md`, and `DEPLOYMENT_GUIDE.md`
for full project details. This section is the only project-specific content in this file.
