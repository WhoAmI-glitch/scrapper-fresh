Identify and fix code quality issues in the current project.

Steps:

1. **Scan**: Read the codebase and identify issues in these categories:
   - Dead code and unused imports
   - Functions over 50 lines
   - Missing error handling at system boundaries
   - Inconsistent naming conventions
   - Security anti-patterns (hardcoded secrets, SQL injection risks, XSS vectors)
   - Missing or broken tests

2. **Prioritize**: Rank issues by impact:
   - Critical: security vulnerabilities, data loss risks
   - High: bugs, broken error handling
   - Medium: maintainability, complexity
   - Low: style, naming

3. **Fix**: Address issues starting from Critical. For each fix:
   - Explain what was wrong
   - Show the fix
   - Verify the fix doesn't break existing tests

4. **Report**: Produce a summary of:
   - Issues found (by severity)
   - Issues fixed
   - Issues deferred (with reason)
   - Suggested follow-ups

Use `test-driven-development` skill when adding missing test coverage.
Use `systematic-debugging` skill when investigating complex issues.
Do not refactor working code unless it has a concrete quality problem.
