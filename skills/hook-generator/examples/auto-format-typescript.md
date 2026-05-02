# Hook Example: Auto-format TypeScript on edit

## Scenario
Auto-run Prettier after Claude edits any `.ts` or `.tsx` file.

## settings.json

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "if": "tool_input.path matches '\\.(ts|tsx)$'",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$(jq -r '.tool_input.path')\" 2>&1 || echo 'Prettier not installed, skipping format'"
          }
        ]
      }
    ]
  }
}
```

## Notes
- Uses `PostToolUse` (not `PreToolUse`) because formatting runs after the file exists.
- The `if` field narrows the matcher to only `.ts`/`.tsx` files — prevents running on JSON edits.
- The `|| echo` fallback prevents hook failure from blocking Claude.
- Safe to commit to `.claude/settings.json` (no secrets).
