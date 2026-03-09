# /dispatch — Create and dispatch a task

When the user runs /dispatch, follow this workflow:

1. Parse the user's request into a structured task
2. Create a task.json file in .claude/state/tasks/ conforming to task.schema.json
3. Determine the appropriate agent(s) by consulting .claude/agents/REGISTRY.json
4. If the task spans multiple agents, decompose into subtasks
5. Create handoff.json file(s) in .claude/state/handoffs/ for each assigned agent
6. Update task status to "assigned"
7. Report the dispatch plan to the user

## ID Generation
- Task: task-YYYYMMDD-{random 6 alphanumeric}
- Handoff: handoff-YYYYMMDD-{random 6 alphanumeric}

## Output Format
```
Task dispatched:
- ID: {task_id}
- Agent: {agent_name}
- Objective: {one-line summary}
- Handoff: {handoff_id}
```

## Multi-agent decomposition
If the task requires multiple agents:
1. Create parent task
2. Create subtasks with parent_task_id set
3. Set depends_on for sequential work
4. Dispatch independent subtasks in parallel
