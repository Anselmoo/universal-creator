#!/usr/bin/env python
"""Validate generated hook output files.

Scans a directory (default: CWD) for .md and .json files, extracts JSON
hook blocks from markdown code fences, and validates each block against the
known Claude Code hook schema.

Exit 0 if all blocks are valid; exit 1 if any violation is found.

Usage:
    python validate_hook_output.py [path]
    python -m skills.hook-generator.scripts.validate_hook_output [path]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Known valid values (sourced from docs/events.md)
# ---------------------------------------------------------------------------

VALID_EVENTS = {
    # Session-level
    "SessionStart",
    "Setup",
    "InstructionsLoaded",
    "SessionEnd",
    # Turn-level
    "UserPromptSubmit",
    "UserPromptExpansion",
    "Elicitation",
    "ElicitationResult",
    "TeammateIdle",
    # Agentic loop
    "PreToolUse",
    "PostToolUse",
    "PostToolBatch",
    "PostToolUseFailure",
    "PermissionRequest",
    "PermissionDenied",
    # Stop
    "Stop",
    "StopFailure",
    "TaskCreated",
    "TaskCompleted",
    # Sub-agent
    "SubagentStart",
    "SubagentStop",
    # Compaction
    "PreCompact",
    "PostCompact",
    # Filesystem / config
    "FileChanged",
    "ConfigChange",
    "CwdChanged",
    "WorktreeCreate",
    "WorktreeRemove",
    # Notifications
    "Notification",
}

VALID_HOOK_TYPES = {"command", "http", "mcp_tool", "prompt", "agent"}

# Events that support blocking (require a specific output schema)
BLOCKING_EVENTS = {
    "PreToolUse",  # permissionDecision
    "PostToolUse",  # decision: block
    "Stop",  # decision: block
    "SubagentStop",  # decision: block
    "PermissionRequest",  # hookSpecificOutput.decision
    "ConfigChange",  # exit code 2
}

# Regex to find ```json ... ``` fences in markdown
_JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)

# Regex to find a top-level hooks structure  {"hooks": {...}}
_HOOKS_KEY_RE = re.compile(r'"hooks"\s*:', re.IGNORECASE)


def _extract_json_blocks(text: str) -> list[dict]:
    """Extract all parseable JSON objects from markdown code fences."""
    blocks = []
    for match in _JSON_FENCE_RE.finditer(text):
        raw = match.group(1).strip()
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                blocks.append(obj)
        except json.JSONDecodeError:
            pass
    return blocks


def _flatten_hook_entries(obj: dict) -> list[tuple[str, dict]]:
    """Yield (event_name, hook_entry) pairs from a settings-level hooks dict.

    Handles both bare event→list structures and the wrapped
    {"hooks": {event: [{matcher: ..., hooks: [...]}]}} shape.
    """
    pairs = []
    hooks_section = obj.get("hooks", obj)
    if not isinstance(hooks_section, dict):
        return pairs
    for event_name, event_entries in hooks_section.items():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            if isinstance(entry, dict):
                inner_hooks = entry.get("hooks", [entry])
                for hook in inner_hooks:
                    if isinstance(hook, dict):
                        pairs.append((event_name, hook))
    return pairs


# ---------------------------------------------------------------------------
# Security advisory patterns (non-blocking WARNs)
# ---------------------------------------------------------------------------

_DANGEROUS_COMMAND_PATTERNS: list[tuple[str, str]] = [
    ("rm -rf", "destructive recursive delete"),
    ("git push --force", "force push can overwrite remote history"),
    ("git reset --hard", "hard reset discards uncommitted changes"),
    ("chmod 777", "world-writable permissions"),
    ("sudo ", "elevated privilege execution"),
    ("Bearer ", "possible hardcoded bearer token"),
    ("sk-", "possible hardcoded API key (sk- prefix)"),
    ("ghp_", "possible hardcoded GitHub personal access token"),
]


def _check_command_safety(command_str: str) -> list[str]:
    """Return advisory WARN strings for dangerous patterns in a command string.

    These are non-blocking: they do not affect the exit code, but are
    printed alongside errors so authors can review them before shipping.
    """
    warnings = []
    for pattern, reason in _DANGEROUS_COMMAND_PATTERNS:
        if pattern in command_str:
            warnings.append(f"WARN: command contains '{pattern}' — {reason}")
    return warnings


def validate_block(event_name: str, hook: dict) -> list[str]:
    """Return a list of validation error strings (empty = valid).

    The list may also contain WARN: prefixed advisory lines from
    _check_command_safety — these are non-blocking but surfaced for review.
    """
    errors = []

    if event_name not in VALID_EVENTS:
        errors.append(
            f"unknown event '{event_name}' (not in known Claude Code event set)"
        )

    hook_type = hook.get("type")
    if hook_type is None:
        errors.append("hook entry is missing required 'type' field")
    elif hook_type not in VALID_HOOK_TYPES:
        errors.append(
            f"invalid hook type '{hook_type}'; expected one of {sorted(VALID_HOOK_TYPES)}"
        )

    if hook_type == "command" and not hook.get("command"):
        errors.append("command hook is missing 'command' field")

    if hook_type == "http" and not hook.get("url"):
        errors.append("http hook is missing 'url' field")

    if hook_type == "mcp_tool" and not hook.get("tool"):
        errors.append("mcp_tool hook is missing 'tool' field")

    if hook_type == "prompt" and not hook.get("prompt"):
        errors.append("prompt hook is missing 'prompt' field")

    if hook_type == "agent" and not hook.get("agent"):
        errors.append("agent hook is missing 'agent' field")

    # Security advisory — non-blocking
    if hook_type == "command":
        cmd = hook.get("command", "")
        if isinstance(cmd, str):
            errors.extend(_check_command_safety(cmd))

    return errors


def validate_file(path: Path) -> list[str]:
    """Validate all hook blocks in a single file. Returns error strings."""
    text = path.read_text(encoding="utf-8")

    # For .json files, try to parse the whole thing directly.
    if path.suffix == ".json":
        try:
            obj = json.loads(text)
            blocks = [obj] if isinstance(obj, dict) else []
        except json.JSONDecodeError as exc:
            return [f"invalid JSON: {exc}"]
    else:
        blocks = _extract_json_blocks(text)

    if not blocks:
        return []  # No hook blocks found — not an error for this validator.

    errors = []
    for block in blocks:
        for event_name, hook in _flatten_hook_entries(block):
            block_errors = validate_block(event_name, hook)
            for err in block_errors:
                errors.append(f"[{event_name}] {err}")

    return errors


def main(search_path: Path = Path(".")) -> int:
    if search_path.is_file():
        files = [search_path]
    else:
        files = sorted(
            list(search_path.rglob("*.md")) + list(search_path.rglob("*.json"))
        )

    if not files:
        print(f"No .md or .json files found under {search_path}")
        return 0

    any_failure = False
    for path in files:
        errors = validate_file(path)
        rel = path.relative_to(search_path) if search_path.is_dir() else path
        if errors:
            any_failure = True
            print(f"  ✗ {rel}")
            for err in errors:
                print(f"    - {err}")
        else:
            # Only print ✓ for files that actually contained hook blocks.
            text = path.read_text(encoding="utf-8")
            if _HOOKS_KEY_RE.search(text) or (
                path.suffix == ".json" and '"type"' in text
            ):
                print(f"  ✓ {rel}")

    return 1 if any_failure else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(main(target))
