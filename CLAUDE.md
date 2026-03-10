# CLAUDE.md -- Multi-Agent Operating System

## 1. Identity

This workspace operates as a **multi-agent productivity operating system**.

| Component | Role |
|---|---|
| **Orchestrator** | Decomposes tasks, routes to specialists, enforces quality, accepts/rejects deliverables |
| **Specialist agents** | Execute discrete units of work through structured state transitions |
| **Communication** | All inter-agent data flows through JSON artifacts -- never prose handoffs |

The orchestrator is the only agent that reads this file as policy. Specialists receive scoped instructions via handoff artifacts.

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
| Code standards and conventions | `rules/` |
| Orchestration scripts | `scripts/` |

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

**Retry policy:** Maximum 3 retries per task. After 3 rejections, the task escalates to `needs-human-review`.

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

Detailed coding standards live in `rules/` to avoid duplication:

| File | Scope |
|---|---|
| `rules/common/coding-style.md` | Naming, formatting, comments, error handling, function design |
| `rules/common/git-workflow.md` | Branch naming, commit messages, PR conventions, merge strategy |
| `rules/common/security.md` | Secrets, input validation, auth, dependencies, data handling |
| `rules/common/testing.md` | Coverage targets, test naming, structure, isolation, performance |
| `rules/python/patterns.md` | Python 3.11+ tooling, type hints, async, error handling, project layout |
| `rules/typescript/patterns.md` | TypeScript strict mode, utility types, null handling, async patterns |

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

---

## 12. Agent Roster (26 agents)

| Agent | Model | Role |
|-------|-------|------|
| `orchestrator` | opus | Sole coordinator: decomposes briefs, manages waves, enforces quality gates |
| `architect` | opus | Pure design decisions and ADRs (WHAT/WHY, never HOW) |
| `dev-lead` | opus | Translates architecture into code structure, reviews PRs (HOW) |
| `frontend-builder` | sonnet | UI components, pages, client-side logic |
| `backend-builder` | sonnet | APIs, server logic, data layer |
| `scaffolder` | sonnet | Project structure, boilerplate, config |
| `qa-reviewer` | opus | Quality review, test generation, audits. **VETO AUTHORITY** |
| `devils-advocate` | opus | Adversarial review, risk assessment. **VETO on Critical** |
| `researcher` | sonnet | Web research, structured synthesis |
| `deep-worker` | opus | Complex multi-step reasoning, cross-domain synthesis |
| `quick-task` | haiku | Simple lookups, formatting, calculations |
| `deployer` | sonnet | Vercel/Railway deployment, domains, SSL |
| `devops-engineer` | sonnet | IaC, CI/CD, cloud, containers, MCP servers, automation |
| `comms-drafter` | sonnet | Communications, correspondence, external content |
| `analyst` | opus | Quantitative analysis, financial modelling, statistics |
| `notion-worker` | haiku | Notion pages, databases, content sync |
| `personal-ops` | sonnet | Life admin, scheduling, reminders |
| `art-director` | opus | Visual design direction, brand guidelines, creative QA |
| `policy-maintainer` | opus | CLAUDE.md evolution, proposal review, policy promotion |
| `python-pro` | opus | Python specialist: async, packaging, performance |
| `typescript-pro` | opus | TypeScript specialist: advanced types, Node.js, frameworks |
| `security-auditor` | opus | SAST, threat modeling, vulnerability assessment, compliance |
| `database-architect` | opus | Schema design, indexing, migrations, query optimization |
| `ai-engineer` | sonnet | LLM applications, RAG, prompt engineering, embeddings |
| `data` | sonnet | Data pipelines, ETL, scrapers, data quality |
| `reporter` | sonnet | Structured reports, stakeholder summaries, documentation |

---

## 13. Anti-Duplication Rules

| Concept | Single Source of Truth | Violation |
|---------|----------------------|-----------|
| Task state | `.claude/state/tasks/<id>.json` | Any task info stored elsewhere |
| Agent definitions | `.claude/agents/<name>.md` + `REGISTRY.json` | Agent behavior defined inline or ad-hoc |
| Schemas | `.claude/schemas/<name>.schema.json` | Validation logic outside `.claude/schemas/` |
| Prompts/Instructions | `.claude/agents/<name>.md` | Prompt text embedded in scripts or tasks |
| Decisions | `.claude/state/decisions/` | Rationale stored only in commit messages |
| Domain knowledge | Either agent OR skill, never both | Same expertise in agent .md and SKILL.md |
| Code standards | `rules/` directory | Standards duplicated inline in this file |

If you find duplication, the fix is deletion of the copy, not synchronization.

---

## 14. Directory Convention

```
.claude/agents/        # Agent instruction files (*.md) -- 26 agents
.claude/skills/s-tier/ # Core domain skills (*/SKILL.md)
.claude/skills/a-tier/ # Extended skills (*/SKILL.md) -- 82 total
.claude/commands/      # Command definitions (*.md) -- 18 commands
.claude/schemas/       # JSON schemas for all artifact types
.claude/state/tasks/   # Task queue (JSON)
.claude/state/handoffs/# Handoff artifacts (JSON)
.claude/state/decisions/# Decision log (JSON, append-only)
.claude/state/findings/# Findings and observations (JSON)
.claude/state/workflows/# Command execution state (JSON)
.claude/quality/       # Quality gates, reports, validation scripts
.claude/hooks/         # Git-style hooks (pre-commit, post-task)
.claude/policy/        # Policy evolution proposals and changelog
rules/common/          # Shared coding rules (style, testing, security, git)
rules/<language>/      # Language-specific rules (python, typescript)
scripts/               # Orchestration and utility scripts
```

---

## 15. Installed Skills (82)

Skills activate automatically based on context. See `.claude/skills/REGISTRY.md` for the full list.

**S-tier** (15): Core domain skills for the leadgen scraper pipeline.
**A-tier** (67): Extended skills including document generation (docx, pdf, pptx, xlsx), orchestration (agent-orchestration, conductor-workflow, dispatching-parallel-agents), testing (test-driven-development, webapp-testing, systematic-debugging), planning (writing-plans, executing-plans, planning-methodology), and communication (gws-gmail, telegram).

---

## 16. Custom Commands (18)

| Command | Purpose |
|---------|---------|
| `/dispatch` | Route a task to the appropriate specialist agent |
| `/review` | Trigger quality review on a completed task |
| `/promote` | Promote an approved policy proposal |
| `/ship` | Package and deliver a completed feature |
| `/status` | Show current system and task status |
| `/analyze-project` | Full project analysis: structure, dependencies, quality |
| `/conductor-setup` | Interactive project setup: vision, tech stack, workflow |
| `/create-document` | Generate office documents (PDF, DOCX, XLSX, PPTX) |
| `/debug-investigation` | Structured debugging: Reproduce, Hypothesize, Test, Fix, Verify |
| `/deep-research` | Multi-agent deep research with triangulation |
| `/evaluate-resource` | Trust and security evaluation of a repository |
| `/feature-development` | Multi-phase orchestration: Discovery, Design, DB, Implement, Test, Review |
| `/improve-codebase` | Identify and fix code quality issues |
| `/research-topic` | Deep research with structured output |
| `/run-quality-gate` | Execute all validation checks |
| `/scaffold-project` | Full project scaffolding: structure, tooling, tests |
| `/security-audit` | Structured security audit: Scan, Analyze, Report, Remediate |
| `/team-review` | Parallel multi-agent code review with unified report |
