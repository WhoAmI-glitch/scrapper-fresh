Execute the full quality gate validation for the current project or a specific artifact.

Steps:

1. **Lint**: Run available linters (eslint, pyflakes, etc.) for the project's language.
2. **Type check**: Run type checkers if available (tsc, mypy, etc.).
3. **Tests**: Run the test suite. Report pass/fail counts.
4. **Security scan**: Check for known vulnerability patterns (hardcoded secrets, injection risks).
5. **Schema validation**: If state/ artifacts exist, validate them against .claude/schemas/.
6. **Dependency check**: Flag outdated or vulnerable dependencies.

Output a quality report:
```
## Quality Gate Report
- Lint: [pass/fail] — [N issues]
- Types: [pass/fail] — [N errors]
- Tests: [X passed, Y failed, Z skipped]
- Security: [N findings by severity]
- Schemas: [N valid, M invalid]
- Dependencies: [N outdated, M vulnerable]
- Verdict: [PASS / PASS WITH WARNINGS / FAIL]
```

If any check fails, list the specific failures with file paths and line numbers.
Use `systematic-debugging` for investigating test failures.
