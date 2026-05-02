# Hook: Notify Slack when Claude stops

**Scenario:** Send a Slack webhook message when a Claude session ends or goes idle.

**Event:** `Stop`
**Hook type:** `command`
**Why `Stop`:** Fires when the Claude agent finishes responding, making it suitable for completion notifications.

## Hook configuration

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -X POST \"$SLACK_WEBHOOK_URL\" -H 'Content-type: application/json' -d '{\"text\":\"Claude session completed.\"}'"
          }
        ]
      }
    ]
  }
}
```

## Notes

- `$SLACK_WEBHOOK_URL` must be set as an environment variable before launching Claude.
- The `Stop` event does not receive tool context, so `$TOOL_INPUT` / `$TOOL_RESPONSE` are not available.
- Keep the `curl` command non-blocking; the hook runner does not gate Claude's shutdown on hook completion.
- To include session metadata, pipe `$CLAUDE_SESSION_ID` if the runtime exposes it.

## Security considerations

- Do not hardcode the webhook URL in the settings file — use an environment variable or secret manager reference.
- Restrict webhook URL scope to a private, internal channel.
