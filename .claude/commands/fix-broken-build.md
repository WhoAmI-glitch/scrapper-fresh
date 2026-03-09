# Command: /fix-broken-build

## Description
Diagnose and fix a broken build, failing tests, or CI pipeline issues.

## Usage
```
/fix-broken-build [--scope frontend|backend|infra|ci|all] [--error "error message"]
```

## Workflow

### Phase 1: Diagnosis
1. Run the full build/test suite to capture all errors.
2. Categorize errors:
   - **Type errors** — TypeScript / Python type issues
   - **Lint errors** — code style violations
   - **Test failures** — failing assertions
   - **Build errors** — compilation / bundling issues
   - **Dependency errors** — missing or incompatible packages
   - **CI errors** — pipeline configuration issues
3. Determine root cause vs. symptoms.
4. Check recent git history for likely culprit commits.

### Phase 2: Triage
1. Sort errors by dependency (fix upstream errors first).
2. Identify quick fixes vs. deeper issues.
3. Create a fix plan ordered by impact.

### Phase 3: Fix
1. Apply fixes starting from the root cause.
2. After each fix, re-run the relevant validation to confirm progress.
3. Ensure fixes do not introduce new issues.
4. If a fix requires a design decision, document the trade-off.

### Phase 4: Verify
1. Run the complete validation suite:
   - `pnpm lint`
   - `pnpm typecheck`
   - `pnpm test`
   - `pnpm build`
2. Verify CI pipeline passes (if applicable).
3. Check that no tests were disabled or skipped to "fix" the build.

### Phase 5: Report
1. Document what was broken and why.
2. Document what was fixed and how.
3. Suggest preventive measures (better tests, stricter types, etc.).
4. Commit fixes with clear messages referencing the issue.

## Acceptance Criteria
- [ ] All build errors resolved
- [ ] All tests passing
- [ ] Lint and type-check passing
- [ ] No tests skipped or disabled as a "fix"
- [ ] Root cause documented
- [ ] Preventive measures suggested
- [ ] Fix committed with descriptive message
