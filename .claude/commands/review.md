# /review — Run quality gate on a finding

When the user runs /review [finding-id], or /review to review the latest finding:

1. Locate the finding in .claude/state/findings/
2. Run .claude/quality/scripts/validate.sh all
3. Run .claude/quality/scripts/check-duplication.sh
4. Evaluate each check from .claude/quality/gates.json
5. Calculate weighted score
6. Determine verdict (accept/reject/accept_with_notes) based on thresholds
7. Write quality-report.json to .claude/quality/reports/
8. Write decision.json to .claude/state/decisions/
9. Update the task status based on verdict

## Verdict Actions
- **accept**: Task status → done, finding accepted
- **accept_with_notes**: Task status → done, notes recorded for follow-up
- **reject**: Task status → in_progress, create new handoff with feedback
