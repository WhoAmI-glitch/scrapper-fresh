---
name: code-review-patterns
description: >-
  Confidence-based code review methodology with severity tiers, consolidation rules,
  and structured output format. Use when reviewing code changes, performing quality
  assessments, or establishing review standards for a project.
---

# Code Review Patterns

A methodology for conducting effective code reviews that prioritize real problems,
minimize noise, and produce actionable findings.

## Confidence-Based Filtering

The single most important review principle: only report issues you are confident about.

| Confidence | Action                                              |
|------------|-----------------------------------------------------|
| > 80%      | **Report** -- include in findings                   |
| 50-80%     | **Note** -- mention only if pattern is widespread   |
| < 50%      | **Skip** -- do not include in review                |

Additional filters:
- **Skip** stylistic preferences unless they violate documented project conventions
- **Skip** issues in unchanged code unless they are CRITICAL security issues
- **Consolidate** similar issues ("5 functions missing error handling" not 5 findings)
- **Prioritize** issues that could cause bugs, security vulnerabilities, or data loss

## Severity Tiers

### CRITICAL (Security)

Must be flagged -- these cause real damage:
- Hardcoded credentials (API keys, passwords, tokens)
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication/authorization bypasses
- Path traversal with user-controlled input
- Secrets exposed in logs
- Insecure dependencies with known CVEs

### HIGH (Correctness)

Likely to cause bugs or maintenance problems:
- Missing error handling (unhandled rejections, empty catch blocks)
- Large functions (> 50 lines) or files (> 800 lines)
- Deep nesting (> 4 levels)
- Dead code (commented-out code, unused imports)
- Missing tests for new code paths
- Mutation of shared state where immutability is expected

### MEDIUM (Quality)

Performance and maintainability concerns:
- Inefficient algorithms (O(n^2) when O(n) is possible)
- Missing caching for repeated expensive operations
- Large bundle imports when tree-shakeable alternatives exist
- N+1 query patterns
- Synchronous I/O in async contexts

### LOW (Style)

Minor issues, report only if they violate project conventions:
- TODO/FIXME without issue references
- Poor naming (single-letter variables in non-trivial contexts)
- Magic numbers without named constants
- Missing documentation on public APIs

## Review Process

### 1. Gather Context

- Read the diff (staged and unstaged changes)
- Identify which files changed and what feature/fix they relate to
- Understand the scope of the change

### 2. Read Surrounding Code

Do not review changes in isolation:
- Read the full file, not just the diff hunks
- Check imports, dependencies, and call sites
- Understand how the changed code fits into the larger system

### 3. Apply Checklist by Severity

Work through severity tiers in order: CRITICAL, HIGH, MEDIUM, LOW.
Stop at LOW if the review is already long -- consolidate rather than enumerate.

### 4. Report Findings

Use this format for each finding:

```
[SEVERITY] Short description
File: path/to/file.ts:42
Issue: What is wrong and why it matters.
Fix: Concrete suggestion for resolution.
```

### 5. Summarize

End every review with a summary table and verdict:

```
| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0     | pass   |
| HIGH     | 2     | warn   |
| MEDIUM   | 3     | info   |
| LOW      | 1     | note   |

Verdict: [APPROVE | WARNING | BLOCK]
```

## Verdict Rules

| Condition                    | Verdict   |
|------------------------------|-----------|
| No CRITICAL or HIGH issues   | APPROVE   |
| HIGH issues only             | WARNING   |
| Any CRITICAL issue           | BLOCK     |

## Consolidation Rules

Group related findings to avoid noise:

- Multiple instances of the same pattern: Report once with count
  ("7 functions lack error handling in src/api/")
- Related issues in the same file: Combine into one finding
- Systemic patterns: Call out the pattern, not each instance

## Framework-Specific Checks

When reviewing code in specific frameworks, add relevant checks:

**React/Next.js**: Missing dependency arrays, state updates in render,
index-as-key in reorderable lists, client/server boundary violations.

**Node.js/Backend**: Unvalidated input, missing rate limiting, unbounded queries,
N+1 patterns, missing timeouts on external calls.

Adapt checks to the project's established patterns. When in doubt, match what
the rest of the codebase does.

## AI-Generated Code Addendum

When reviewing AI-generated changes, additionally check:
- Behavioral regressions and missed edge cases
- Hidden coupling or accidental architecture drift
- Unnecessary complexity that inflates model costs
- Security assumptions and trust boundary violations
