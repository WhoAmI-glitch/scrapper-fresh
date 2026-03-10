---
name: continuous-learning
description: >-
  Methodology for extracting reusable knowledge from coding sessions through observation,
  instinct formation, and evolution. Use when setting up pattern extraction from sessions,
  tuning confidence thresholds, reviewing learned behaviors, or evolving instincts into
  skills, commands, or agents.
---

# Continuous Learning Methodology

A framework for turning coding sessions into reusable knowledge through atomic "instincts" --
small learned behaviors with confidence scoring that evolve into skills, commands, or agents.

## Core Lifecycle

```
Observe -> Extract -> Score -> Evolve
```

### 1. Observe

Capture patterns from session activity:
- User corrections (changed approach after AI suggestion)
- Error resolutions (how a problem was ultimately fixed)
- Repeated workflows (same sequence of actions across sessions)
- Tool usage patterns (preferred tool chains for specific tasks)

Observations should be captured automatically via hooks (PreToolUse/PostToolUse),
not manually. Hook-based capture is 100% reliable; skill-based observation is probabilistic.

### 2. Extract Instincts

An instinct is an atomic learned behavior with one trigger and one action:

```yaml
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
scope: project          # or "global"
```

Properties of a well-formed instinct:
- **Atomic**: One trigger, one action -- not a compound rule
- **Evidence-backed**: Tracks which observations created it
- **Domain-tagged**: code-style, testing, git, debugging, workflow, tooling
- **Scope-aware**: Project-scoped (default) or global

### 3. Confidence Scoring

| Score | Meaning      | Behavior                          |
|-------|-------------|-----------------------------------|
| 0.3   | Tentative   | Suggested but not enforced        |
| 0.5   | Moderate    | Applied when relevant             |
| 0.7   | Strong      | Auto-approved for application     |
| 0.9   | Near-certain| Core behavior, rarely overridden  |

Confidence increases when:
- Pattern is repeatedly observed across sessions
- User does not correct the suggested behavior
- Similar instincts from other sources agree

Confidence decreases when:
- User explicitly corrects the behavior
- Pattern is not observed for extended periods
- Contradicting evidence appears

### 4. Scope Decision

| Pattern Type                    | Scope       |
|---------------------------------|-------------|
| Language/framework conventions  | project     |
| File structure preferences      | project     |
| Code style                      | project     |
| Security practices              | **global**  |
| General best practices          | **global**  |
| Tool workflow preferences       | **global**  |
| Git practices                   | **global**  |

Default to project scope. Promote to global when the same instinct appears in 2+ projects
with average confidence >= 0.8.

### 5. Evolve

When related instincts cluster, evolve them into higher-order artifacts:

| Cluster Size | Evolution Target | Example                              |
|-------------|-----------------|--------------------------------------|
| 3-5 related | Command          | `/test-react` from React testing instincts |
| 5-8 related | Skill            | `tdd-workflow` from TDD instincts    |
| 8+ related  | Agent            | `refactor-specialist` from refactoring instincts |

Evolution criteria:
- Instincts share a domain tag
- Average confidence across cluster >= 0.7
- Instincts are complementary (not contradictory)

## Anti-Patterns

- **Cross-project contamination**: React patterns leaking into Python projects.
  Fix: Scope instincts to projects by default.
- **Low-confidence accumulation**: Keeping instincts below 0.3 indefinitely.
  Fix: Prune instincts below 0.3 after 30 days without reinforcement.
- **Over-specification**: Instincts so specific they never trigger.
  Fix: Generalize trigger conditions when patterns repeat across contexts.

## Integration Points

- Hooks capture observations (PreToolUse, PostToolUse)
- Background analysis extracts instincts from observations
- Instinct libraries can be exported and imported across environments
- Evolution produces artifacts compatible with the skills/commands/agents system
