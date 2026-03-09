# /status — Check system state

When the user runs /status, report:

1. **Active Tasks**: Read all .json files in .claude/state/tasks/ and show:
   - ID, title, status, assigned agent, created date
   - Group by status (in_progress > assigned > pending > review > done)

2. **Recent Decisions**: Last 5 decisions from .claude/state/decisions/

3. **Quality Summary**: Latest quality reports from .claude/quality/reports/

4. **Pending Proposals**: Any proposals in .claude/policy/proposals/ with status "pending"

## Output Format
Use a clean table format. If no state files exist, report "System is idle — no active tasks."
