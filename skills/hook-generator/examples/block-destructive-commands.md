# Hook Example: Block destructive commands

## Scenario
Deny any `Bash` tool call that contains `rm -rf`, `git push --force`, or `DROP TABLE`.

## settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "if": "tool_input.command contains 'rm -rf' or tool_input.command contains 'git push --force' or tool_input.command contains 'DROP TABLE'",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"permissionDecision\":{\"behavior\":\"deny\",\"message\":\"Destructive command blocked by policy. Run manually if you're sure.\"}}'",
          }
        ]
      }
    ]
  }
}
```

## Notes
- `PreToolUse` with `behavior: "deny"` hard-blocks — Claude cannot proceed without explicit user override.
- The `message` field is shown to Claude and surfaced in the UI.
- Narrow the `if` pattern to avoid blocking legitimate commands.
- For softer behavior, use `"behavior": "ask"` instead of `"deny"`.
