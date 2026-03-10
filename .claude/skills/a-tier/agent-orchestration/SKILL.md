---
name: agent-orchestration
description: >-
  Strategy patterns for multi-agent coordination including team composition,
  task decomposition, parallel dispatch, and result aggregation. Use when deciding
  whether to use teams vs sequential dispatch, selecting team presets, decomposing
  tasks for parallel execution, or resolving conflicting agent outputs. Complements
  dispatching-parallel-agents (mechanics) with strategic guidance.
---

# Agent Orchestration Patterns

Strategic patterns for coordinating multiple agents effectively. This skill covers
WHEN and WHY to use multi-agent teams, not the mechanical HOW (see dispatching-parallel-agents).

## Decision: Teams vs Sequential Dispatch

| Situation                          | Use Teams              | Use Sequential          |
|------------------------------------|------------------------|-------------------------|
| Independent concerns               | Yes (parallel review)  | No                      |
| Dependent steps                    | No                     | Yes (pipeline)          |
| Multiple plausible root causes     | Yes (competing hypotheses)| No                   |
| Feature with separable components  | Yes (file ownership)   | No                      |
| Exploratory research               | Yes (different angles) | No                      |
| Single file changes                | No                     | Yes                     |
| Sequential logic chain             | No                     | Yes                     |

**Rule of thumb:** Use teams when work can be divided into independent units with
clear ownership boundaries. Use sequential dispatch when each step depends on the
output of the previous step.

## Team Presets

### Review Team (3 agents)

Purpose: Multi-dimensional code quality assessment.
Agents: 3x reviewer, each assigned a different dimension.
Default dimensions: security, performance, architecture.
When to use: Code changes touch multiple concerns or are high-risk.

### Debug Team (3 agents)

Purpose: Parallel hypothesis investigation.
Agents: 3x debugger, each investigating a competing hypothesis.
Method: Analysis of Competing Hypotheses (ACH).
When to use: Bug with multiple plausible root causes, initial debugging stalled.

### Feature Team (3-4 agents)

Purpose: Parallel feature implementation.
Agents: 1x lead (coordinator) + 2-3x implementer.
Split by: Layer (frontend/backend/test) or component (module boundaries).
When to use: Feature can be decomposed into parallel work streams with clear file ownership.

### Security Team (4 agents)

Purpose: Comprehensive security audit.
Agents: 4x reviewer across attack surfaces.
Dimensions: OWASP/vulnerabilities, auth/access, dependencies/supply chain, secrets/config.
When to use: Pre-release security review, sensitive feature changes.

### Research Team (3 agents)

Purpose: Parallel information gathering.
Agents: 3x read-only explorer.
Split by: Different research questions, modules, or topics.
When to use: Understanding a codebase, comparing approaches, gathering information.

## Task Decomposition Strategies

### By Layer

Split by architectural layer: frontend, backend, database, tests.
Best for full-stack features and vertical slices.

### By Component

Split by functional module: auth, profiles, notifications.
Best for microservices and modular architectures.

### By Concern

Split by cross-cutting concern: security, performance, architecture.
Best for code reviews and audits.

### By File Ownership

Split by file/directory boundaries. Each agent owns specific paths.
Best for parallel implementation where avoiding merge conflicts is critical.

**Key rule:** Every task must have explicit file ownership. Two agents must never
modify the same file simultaneously.

## Dependency Graph Design

Prefer wide, shallow graphs over deep chains for maximum parallelism:

```
Independent (best):     Diamond (good):        Chain (worst):
A ---|                     |- B -|
B ---+-> Integration    A -|     |-> D         A -> B -> C -> D
C ---|                     |- C -|
```

Principles:
- Minimize chain depth (longest chain = minimum completion time)
- Use blockers sparingly (only truly required dependencies)
- Avoid circular dependencies (deadlock)

## Result Aggregation

### For Reviews

Merge findings from all reviewers:
1. Deduplicate (same issue found by multiple reviewers)
2. Promote severity (if reviewers disagree, use the higher severity)
3. Consolidate (group related findings)
4. Produce unified summary with verdict

### For Debugging

Arbitrate between competing hypotheses:
1. Categorize: confirmed, plausible, falsified, inconclusive
2. Rank confirmed hypotheses by evidence strength
3. If one dominates: declare root cause
4. If multiple equally likely: may be compound issue
5. If none confirmed: generate new hypotheses from gathered evidence

### For Implementation

Integrate parallel work streams:
1. Verify file ownership was respected (no conflicts)
2. Run integration tests across all streams
3. Check interface contracts between components
4. Resolve any API mismatches before merging

## Conflict Resolution

When agents produce contradictory outputs:

| Conflict Type           | Resolution                                    |
|------------------------|-----------------------------------------------|
| Different severity     | Use higher severity, note disagreement        |
| Contradictory fixes    | Prefer the fix with more evidence             |
| Scope disagreement     | Defer to the agent with domain expertise      |
| Architectural conflict | Escalate to human or architect agent          |

## Team Sizing Heuristics

| Complexity    | Team Size | Rationale                                    |
|--------------|-----------|----------------------------------------------|
| Simple       | 1-2       | Coordination overhead exceeds parallelism gain|
| Moderate     | 2-3       | Good parallelism, manageable coordination    |
| Complex      | 3-4       | Sweet spot for most tasks                    |
| Very complex | 4-5       | Maximum practical size; beyond 5, overhead dominates|

**Start small.** Add agents only when you can define clear, independent work units
for each one. An idle agent is wasted cost.
