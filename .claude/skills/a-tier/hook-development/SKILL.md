---
name: hook-development
description: >-
  Practical guide to building Claude Code hooks with configuration patterns,
  best practices, and concrete examples. Use when creating new hooks, debugging
  hook behavior, or configuring hook-based automations for Claude Code sessions.
---

# Hook Development

A practical guide to building Claude Code hooks -- trigger-based automations that fire
on specific tool call and session lifecycle events.

## Hook Types

| Type              | Fires When                        | Common Uses                          |
|-------------------|-----------------------------------|--------------------------------------|
| `PreToolUse`      | Before a tool executes            | Validation, reminders, blocking      |
| `PostToolUse`     | After a tool finishes             | Formatting, type checking, warnings  |
| `UserPromptSubmit`| User sends a message              | Input transformation, context loading|
| `SessionStart`    | New session begins                | State restoration, environment setup |
| `Stop`            | Claude finishes responding        | Cleanup, state persistence, checks   |
| `PreCompact`      | Before context compaction         | State saving before memory loss      |
| `Notification`    | Permission request events         | Custom notification routing          |

## Hook Configuration Structure

Hooks are defined in `.claude/settings.json` (user level) or `.claude/settings.local.json`
(project level):

```json
{
  "hooks": {
    "<HookType>": [
      {
        "matcher": "<pattern>",
        "hooks": [
          {
            "type": "command",
            "command": "<shell command>",
            "async": false,
            "timeout": 30
          }
        ],
        "description": "Human-readable description of what this hook does"
      }
    ]
  }
}
```

### Matcher Patterns

- `"*"` -- matches all tools/events
- `"Bash"` -- matches specific tool name
- `"Edit|Write"` -- matches multiple tools (OR)
- `"Edit|Write|MultiEdit"` -- matches any of several tools
- Expression syntax: `tool == "Bash" && tool_input.command matches "(npm|yarn)"`

### Configuration Fields

| Field       | Required | Default | Description                          |
|-------------|----------|---------|--------------------------------------|
| `type`      | yes      | --      | Always `"command"`                   |
| `command`   | yes      | --      | Shell command to execute             |
| `async`     | no       | `false` | Run without blocking Claude          |
| `timeout`   | no       | 30      | Seconds before hook is killed        |

## Hook Input/Output Protocol

Hooks receive context via stdin as JSON and communicate back via:

- **stdout**: Message shown to Claude (appears as hook feedback)
- **stderr**: Message shown to the user (diagnostic output)
- **exit code 0**: Success, continue normally
- **exit code 2**: Block the tool call (PreToolUse only)
- **non-zero exit (not 2)**: Error, logged but does not block

## Best Practices

1. **Keep hooks fast.** Synchronous hooks block Claude. Target < 1 second for sync hooks.
   Use `"async": true` for anything slow (formatting, type checking, network calls).

2. **Use timeouts.** Always set a timeout for async hooks. A hung hook consumes resources.
   10 seconds for lightweight checks, 30 seconds for build/format operations.

3. **Prefer scripts over inline commands.** Complex logic belongs in a script file,
   not a long command string. Easier to debug and version control.

4. **Use environment variables.** `$CLAUDE_PLUGIN_ROOT` for plugin-relative paths.
   `$CLAUDE_PROJECT_DIR` for project-relative paths.

5. **Handle errors gracefully.** A crashing hook should not break Claude's workflow.
   Always catch errors and exit cleanly with informative stderr output.

6. **Scope matchers narrowly.** Match only the tools you need. A `"*"` matcher on
   a slow synchronous hook will degrade every tool call.

## Example 1: Auto-Format After Edits

Format JavaScript/TypeScript files after Claude edits them:

```json
{
  "PostToolUse": [
    {
      "matcher": "Edit",
      "hooks": [
        {
          "type": "command",
          "command": "node scripts/hooks/post-edit-format.js",
          "async": true,
          "timeout": 30
        }
      ],
      "description": "Auto-format JS/TS files after edits"
    }
  ]
}
```

The script reads the edited file path from stdin JSON, checks if it is a
JS/TS file, and runs the project's formatter (Prettier or Biome).

## Example 2: Block Accidental Documentation Files

Prevent Claude from creating stray markdown files:

```json
{
  "PreToolUse": [
    {
      "matcher": "Write",
      "hooks": [
        {
          "type": "command",
          "command": "node scripts/hooks/doc-file-warning.js"
        }
      ],
      "description": "Warn about non-standard documentation files"
    }
  ]
}
```

The script checks if the target file is a `.md` file outside of approved
locations (README.md, CLAUDE.md, docs/). Exits with code 2 to block, or 0
with a stderr warning.

## Example 3: Session State Persistence

Save and restore session state across conversations:

```json
{
  "SessionStart": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "node scripts/hooks/session-start.js"
        }
      ],
      "description": "Load previous context on session start"
    }
  ],
  "Stop": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "node scripts/hooks/session-end.js",
          "async": true,
          "timeout": 10
        }
      ],
      "description": "Persist session state after each response"
    }
  ]
}
```

SessionStart loads previous task state, git branch, and pending items.
Stop hook saves current state for the next session.

## Example 4: Continuous Learning Observer

Capture tool usage for pattern extraction (async, non-blocking):

```json
{
  "PreToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash hooks/observe.sh",
          "async": true,
          "timeout": 10
        }
      ],
      "description": "Capture tool use observations for learning"
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash hooks/observe.sh",
          "async": true,
          "timeout": 10
        }
      ],
      "description": "Capture tool results for learning"
    }
  ]
}
```

Both hooks are async with short timeouts so they never block Claude's workflow.

## Common Patterns

| Pattern                 | Hook Type     | Async | Matcher         |
|------------------------|---------------|-------|-----------------|
| Auto-format code       | PostToolUse   | yes   | `Edit`          |
| Type check after edit  | PostToolUse   | yes   | `Edit`          |
| Block bad file writes  | PreToolUse    | no    | `Write`         |
| Tmux reminder          | PreToolUse    | no    | `Bash`          |
| Git push review        | PreToolUse    | no    | `Bash`          |
| Console.log warning    | PostToolUse   | no    | `Edit`          |
| Session persistence    | Stop          | yes   | `*`             |
| Context loading        | SessionStart  | no    | `*`             |
| Pre-compaction save    | PreCompact    | no    | `*`             |
| Build analysis         | PostToolUse   | yes   | `Bash`          |

## Debugging Hooks

When a hook is not firing or behaving unexpectedly:

1. Check matcher pattern matches the tool name exactly (case-sensitive)
2. Verify the command path is correct (use absolute paths or `$CLAUDE_PLUGIN_ROOT`)
3. Test the command standalone: `echo '{}' | node your-hook.js`
4. Check stderr output for error messages
5. Verify exit codes: 0 = success, 2 = block, other = error
6. Check timeout -- async hooks that exceed timeout are killed silently
