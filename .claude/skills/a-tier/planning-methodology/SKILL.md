---
name: planning-methodology
description: >-
  Structured methodology for creating implementation plans with phased breakdown,
  dependency tracking, risk assessment, and testing strategy. Use when creating a
  detailed implementation plan for a feature, refactor, or complex bug fix. Complements
  the writing-plans skill (which covers WHEN to plan) with HOW to plan.
---

# Planning Methodology

A structured approach to creating implementation plans that are specific, actionable,
and enable confident incremental delivery.

## Plan Structure

Every plan follows this skeleton:

```
Overview -> Requirements -> Architecture Changes -> Phases -> Testing -> Risks -> Success Criteria
```

## Phase Breakdown

Break work into independently deliverable phases:

| Phase    | Purpose                                        |
|----------|------------------------------------------------|
| Phase 1  | Minimum viable -- smallest slice with value    |
| Phase 2  | Core experience -- complete happy path         |
| Phase 3  | Edge cases -- error handling, validation, polish|
| Phase 4  | Optimization -- performance, monitoring        |

Each phase MUST be mergeable independently. Avoid plans requiring all phases to complete
before anything works.

### Step Format

Each step within a phase must include:

```
**[Step Name]** (File: path/to/file.ts)
  - Action: Specific action to take
  - Why: Reason for this step
  - Dependencies: None / Requires step X
  - Risk: Low / Medium / High
```

Rules:
- Use exact file paths, function names, variable names
- Every step must be independently verifiable
- Steps within a phase are ordered by dependency
- Keep steps atomic -- one logical change per step

## Risk Assessment Matrix

Evaluate risks on two dimensions:

| Risk Category       | Impact  | Likelihood | Priority |
|---------------------|---------|------------|----------|
| Data loss/corruption| High    | Any        | Block    |
| Security bypass     | High    | Any        | Block    |
| Webhook/async failure| Medium | Medium     | Mitigate |
| Performance regression| Medium| Low        | Monitor  |
| UI inconsistency    | Low     | High       | Accept   |

For each risk, document:
- **Risk**: What could go wrong
- **Mitigation**: Concrete action to prevent or handle it

## Testing Strategy

Define testing at three levels:

| Level       | What to Test                     | When to Write |
|-------------|----------------------------------|---------------|
| Unit        | Individual functions, edge cases | During phase  |
| Integration | Component interactions, API flows| After phase   |
| E2E         | Full user journeys               | After all phases|

Coverage target: Define a percentage (typically 80%) and which paths are critical.

## Success Criteria Checklist

End every plan with measurable criteria:

```
- [ ] User can [perform action] via [interface]
- [ ] [System component] correctly handles [edge case]
- [ ] All tests pass with [X]% coverage
- [ ] No CRITICAL or HIGH issues in code review
```

Criteria must be:
- Specific (not "works correctly")
- Testable (can be verified by running something)
- Complete (covers both happy path and failure modes)

## Worked Example: API Rate Limiting

```markdown
# Implementation Plan: API Rate Limiting

## Overview
Add per-user rate limiting to public API endpoints to prevent abuse.
Use sliding window counter stored in Redis.

## Requirements
- 100 requests/minute per authenticated user
- 1000 requests/minute per API key (service accounts)
- Return 429 with Retry-After header when exceeded

## Architecture Changes
- New middleware: src/middleware/rate-limit.ts
- New Redis key pattern: rate:{userId}:{window}
- Update: src/app/api/[...route]/route.ts (apply middleware)

## Phase 1: Core Limiter (2 files)
1. **Create rate limit middleware** (File: src/middleware/rate-limit.ts)
   - Action: Sliding window counter using Redis INCR + EXPIRE
   - Why: Sliding window is more fair than fixed window
   - Dependencies: None
   - Risk: Medium -- must handle Redis connection failures gracefully

2. **Apply to API routes** (File: src/app/api/[...route]/route.ts)
   - Action: Add rate limit middleware to route handler chain
   - Why: Central application point for all API routes
   - Dependencies: Step 1
   - Risk: Low

## Phase 2: Headers and Errors (1 file)
3. **Add rate limit response headers** (File: src/middleware/rate-limit.ts)
   - Action: X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After
   - Why: Clients need to know their limits and when to retry
   - Dependencies: Step 1
   - Risk: Low

## Testing Strategy
- Unit: Window calculation, Redis key generation, header formatting
- Integration: Middleware chain with mock Redis
- E2E: Hit endpoint 101 times, verify 429 on 101st

## Risks
- **Risk**: Redis unavailable
  - Mitigation: Fail open (allow request) with alert, not fail closed

## Success Criteria
- [ ] Authenticated user gets 429 after 100 requests/minute
- [ ] Response includes correct rate limit headers
- [ ] Redis failure does not block API requests
- [ ] Unit tests cover window edge cases
```

## Red Flags in Plans

Watch for these problems:
- Steps without file paths (too vague to execute)
- Phases that cannot be delivered independently
- No testing strategy
- Missing error/edge case handling
- Large functions planned (> 50 lines) without extraction plan
- Plans with no risk assessment
- Hardcoded values without configuration plan
