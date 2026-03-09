# /promote — Promote a policy proposal

When the user runs /promote [proposal-id]:

1. Read the proposal from .claude/policy/proposals/
2. Invoke the policy-maintainer agent evaluation:
   a. Check mandatory requirements from policy/criteria.json
   b. Score against weighted criteria
   c. Determine verdict (promote/defer/reject)
3. If promoted:
   a. Apply the diff to the target file (usually CLAUDE.md)
   b. Update proposal status to "promoted"
   c. Write decision.json to .claude/state/decisions/
   d. Add entry to policy/CHANGELOG.md
4. If deferred or rejected:
   a. Update proposal status
   b. Write decision.json with reasoning
   c. Report feedback to user
