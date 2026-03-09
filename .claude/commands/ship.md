# /ship — End-to-end feature delivery

When the user runs /ship [description]:

1. **Decompose**: Create a parent task, identify required agents from REGISTRY.json
2. **Plan**: Architect agent produces design finding (if non-trivial)
3. **Implement**: Backend/frontend/data agents work per handoffs
4. **Test**: QA agent runs quality gate on each finding
5. **Integrate**: If multiple findings, coordinator merges and runs final quality gate
6. **Document**: Reporter agent updates relevant documentation
7. **Commit**: Create atomic commit(s) following conventional commit format

## Parallel Execution
- Independent implementation tasks run in parallel
- QA reviews happen after each implementation finding
- Documentation runs in parallel with final QA

## Abort Conditions
- Any quality gate scores below reject threshold
- Missing acceptance criteria that cannot be inferred
- Dependency conflict between subtasks
