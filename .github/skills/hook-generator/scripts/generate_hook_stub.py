#!/usr/bin/env python
"""Scaffold a minimal valid Claude Code hook block from arguments.

Reads the canonical hook-block.json template and fills in the requested event,
hook type, and intent — producing a ready-to-paste JSON snippet.

Usage:
    python generate_hook_stub.py --event PostToolUse --type command --intent "run prettier on the edited file"
    python generate_hook_stub.py --event PreToolUse --type prompt --intent "ask Claude to confirm before deleting"
    python generate_hook_stub.py --event Stop --type agent --intent "verify all tasks completed"

Outputs to stdout.  Redirect to a file to save:
    python generate_hook_stub.py --event SessionStart --type command --intent "echo project context" > my-hook.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Event → default output schema (what the hook command should emit)
# ---------------------------------------------------------------------------

_SKILL_ROOT = Path(__file__).resolve().parent.parent

_EVENT_OUTPUT_HINTS: dict[str, str] = {
    "PreToolUse": '{"permissionDecision":{"behavior":"allow"}}',
    "PermissionRequest": '{"hookSpecificOutput":{"decision":{"behavior":"allow"}}}',
    "PostToolUse": '{"decision":"block","reason":"<reason>"}',
    "Stop": '{"decision":"block","reason":"<reason>"}',
    "SubagentStop": '{"decision":"block","reason":"<reason>"}',
    "UserPromptSubmit": '{"additionalContext":"<context injected into Claude>"}',
    "SessionStart": "<text output — becomes part of Claude's context>",
    "PostCompact": "<text output — reinjected as context>",
}

_HOOK_TYPE_REQUIRED_FIELD: dict[str, str] = {
    "command": "command",
    "http": "url",
    "mcp_tool": "tool",
    "prompt": "prompt",
    "agent": "agent",
}

# Events where blocking is meaningful (add matcher by default)
_EVENTS_WITH_MATCHER = {
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PermissionRequest",
    "PermissionDenied",
    "SessionStart",
    "SessionEnd",
    "ConfigChange",
    "FileChanged",
    "SubagentStart",
    "SubagentStop",
    "StopFailure",
    "InstructionsLoaded",
    "Notification",
}


def _build_inner_hook(hook_type: str, intent: str) -> dict:
    """Build the inner hook object dict."""
    hook: dict = {"type": hook_type}
    field = _HOOK_TYPE_REQUIRED_FIELD.get(hook_type, "command")

    if hook_type == "command":
        # Produce a placeholder command with a comment about the intent.
        hook["command"] = f"# {intent}\necho 'hook fired'"
    elif hook_type == "http":
        hook["url"] = "https://example.com/webhook"
        hook["headers"] = {"Content-Type": "application/json"}
        hook["body"] = f'{{"intent": "{intent}"}}'
    elif hook_type == "mcp_tool":
        hook["tool"] = "<mcp-server-name>__<tool-name>"
        hook["input"] = {"intent": intent}
    elif hook_type == "prompt":
        hook["prompt"] = (
            f"{intent}. "
            'If Claude should proceed normally, respond with {"ok": true}. '
            'If not, respond with {"ok": false, "reason": "<explanation>"}.'
        )
    elif hook_type == "agent":
        hook["agent"] = "<agent-name>"
        hook["prompt"] = (
            f"{intent}. "
            'Return {"ok": true} if satisfied, or {"ok": false, "reason": "..."}.'
        )
    else:
        hook[field] = f"<{field}>"

    return hook


def build_hook_block(event: str, hook_type: str, intent: str) -> dict:
    """Produce the full settings-level hook JSON structure."""
    inner = _build_inner_hook(hook_type, intent)

    entry: dict = {"hooks": [inner]}
    if event in _EVENTS_WITH_MATCHER:
        entry["matcher"] = ""  # User should narrow this

    output_hint = _EVENT_OUTPUT_HINTS.get(event)

    # Wrap in the full settings structure
    block: dict = {
        "_comment": (
            f"Paste inside the 'hooks' key of .claude/settings.json or "
            f"~/.claude/settings.json.  "
            f"Event: {event}  |  Type: {hook_type}  |  Intent: {intent}"
        ),
        "hooks": {event: [entry]},
    }
    if output_hint:
        block["_output_hint"] = f"Expected output schema for {event}: {output_hint}"

    return block


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a minimal Claude Code hook JSON block.",
    )
    parser.add_argument(
        "--event",
        required=True,
        help="Claude Code lifecycle event (e.g. PostToolUse, PreToolUse, Stop)",
    )
    parser.add_argument(
        "--type",
        required=True,
        dest="hook_type",
        choices=["command", "http", "mcp_tool", "prompt", "agent"],
        help="Hook type",
    )
    parser.add_argument(
        "--intent",
        required=True,
        help="One-sentence description of what this hook should do",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write output to this file instead of stdout",
    )

    args = parser.parse_args()

    block = build_hook_block(args.event, args.hook_type, args.intent)
    output = json.dumps(block, indent=2)

    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
        print(f"Written to {args.out}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
