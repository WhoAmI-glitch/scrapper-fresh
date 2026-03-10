---
description: "Multi-agent deep research with parallel web search, triangulation, and adversarial review"
argument-hint: "[topic] [--depth shallow|medium|deep]"
---

# Deep Research

Enhanced multi-agent research workflow coordinating researcher, analyst, devils-advocate, and deep-worker agents. Parallel web research, source triangulation, adversarial review, and structured synthesis.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/deep-research/` before starting the next phase.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure, halt immediately and present the error.
5. Mark uncertain claims with [uncertain]. Never fabricate sources or statistics.
6. Attribute all claims to specific sources with URLs where available.

## Pre-flight

Check if `.claude/state/workflows/deep-research/state.json` exists:
- If `status: "in_progress"`: offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/deep-research/state.json`:
```json
{
  "topic": "$ARGUMENTS",
  "status": "in_progress",
  "depth": "medium",
  "current_phase": "scope",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--depth`: `shallow` (3 queries, 5 sources, skip adversarial), `medium` (5 queries, 10 sources), `deep` (8 queries, 15+ sources, iterative refinement).

---

## Phase 1: Scope Definition

Ask the user (max 3 questions):
1. **Focus area**: What specific aspect of {topic} matters most?
2. **Output purpose**: Decision support, learning, competitive analysis, technical evaluation?
3. **Known constraints**: Sources to prioritize or avoid? Existing knowledge?

Generate: 3-5 key research questions, search query plan, success criteria.

Write to `.claude/state/workflows/deep-research/01-scope.md`.

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present research plan (questions, queries). Options:
1. Approve -- launch research
2. Refine -- adjust questions or queries
3. Pause -- save progress and stop

---

## Phase 2: Parallel Web Research

Dispatch to **researcher** agent using `dispatching-parallel-agents` skill: execute search queries in parallel. For each query: search, fetch top 3-5 results, extract claims with source attribution, rate source credibility (high/medium/low).

Write raw findings to `.claude/state/workflows/deep-research/02-raw-findings.md`.

For `deep` depth: identify gaps, generate 2-3 follow-up queries, execute second pass.

---

## Phase 3: Source Analysis and Triangulation

Dispatch to **analyst** agent: analyze raw findings for patterns and contradictions.

Perform: consensus mapping (claims supported by multiple sources), contradiction identification, gap analysis, recency weighting, quantitative data extraction into tables.

Write to `.claude/state/workflows/deep-research/03-analysis.md`.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present consensus items, contradictions, gaps. Options:
1. Approve -- proceed to adversarial review
2. Fill gaps -- additional research on weak areas
3. Pause -- save progress and stop

---

## Phase 4: Adversarial Review

Skip if depth is `shallow`.

Dispatch to **devils-advocate** agent: challenge the analysis for confirmation bias, source quality issues, missing perspectives, logical gaps, and unstated assumptions.

Write challenges and recommended caveats to `.claude/state/workflows/deep-research/04-adversarial-review.md`.

---

## Phase 5: Synthesis

Dispatch to **deep-worker** agent: read all prior outputs and synthesize into `.claude/state/workflows/deep-research/05-report.md` with: executive summary (3-5 sentences), key findings with attribution and confidence, comparison table (if applicable), contradictions and caveats, ranked recommendations, numbered source list with URLs and credibility, open questions.

Update `state.json`: `current_phase: "checkpoint-3"`.

### PHASE CHECKPOINT 3

Present executive summary and recommendations. Options:
1. Accept report -- finalize
2. Deepen specific sections
3. Pause -- save progress and stop

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary with paths to all five output files.

Next steps: review report, follow up on open questions, use findings to inform decisions.
