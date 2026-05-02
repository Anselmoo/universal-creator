#!/usr/bin/env python
"""Scaffold a minimal *.agent.md definition from a template.

Reads the agent-system-prompt.md template from the skill's templates/ directory,
fills in the name, description, and tools list, and writes a ready-to-edit
*.agent.md stub.

Usage:
    python generate_agent_stub.py --name doc-writer \
        --description "Writes technical docs from source code" \
        --tools "read_file,semantic_search" [--scope bounded|open] [--out FILE]

Outputs to stdout unless --out is given.  When stdout is a tty and --out is
omitted, writes to <name>.agent.md in the current directory.

Scope:
    bounded  — locks the agent to only the declared tools; adds an
               ## Out of scope placeholder reminding the author to list
               what this agent must hand back.
    open     — leaves tools unrestricted; removes the ## Out of scope
               placeholder from the stub.  (default: bounded)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _SKILL_ROOT / "templates" / "agent-system-prompt.md"

# Placeholders exactly as they appear in the template
_NAME_PLACEHOLDER = "<role-name>"
_TITLE_PLACEHOLDER = "<Role Name>"


def _kebab(name: str) -> str:
    """Normalise an agent name to kebab-case."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _title(name: str) -> str:
    """Convert kebab-case name to Title Case for the heading."""
    return " ".join(word.capitalize() for word in name.split("-"))


def _build_tools_yaml(tools: list[str]) -> str:
    """Return a YAML-formatted tools list block (without leading 'tools:' key)."""
    lines = [f"  - {t.strip()}" for t in tools if t.strip()]
    # Remove the comment lines that may be in the template (added separately)
    return "\n".join(lines)


def scaffold(
    name: str,
    description: str,
    tools: list[str],
    scope: str,
) -> str:
    """Return the filled-in agent stub content."""
    if not _TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {_TEMPLATE}")

    template = _TEMPLATE.read_text(encoding="utf-8")
    safe_name = _kebab(name)
    title = _title(safe_name)

    # --- Frontmatter substitutions ---

    # Replace name placeholder
    result = template.replace(_NAME_PLACEHOLDER, safe_name)

    # Replace the multi-line description placeholder (everything between
    # `description: >-\n` and the next key) with the supplied description.
    result = re.sub(
        r"(description: >-\n).*?(?=\ntools:)",
        rf"\1  {description}",
        result,
        flags=re.DOTALL,
    )

    # Replace tools placeholder block with actual tools
    tool_lines = _build_tools_yaml(tools)
    result = re.sub(
        r"(tools:\n)(?:  - .*\n|  #.*\n)+",
        rf"tools:\n{tool_lines}\n",
        result,
    )

    # --- Body substitutions ---

    # Replace <Role Name> heading placeholder
    result = result.replace(_TITLE_PLACEHOLDER, title)

    # For 'open' scope: replace the ## Out of scope placeholder with a notice
    if scope == "open":
        result = re.sub(
            r"## Out of scope\n.*?(?=\n## |\Z)",
            "",
            result,
            flags=re.DOTALL,
        )

    # Strip YAML comment lines inside the frontmatter block (lines starting with #
    # that live between the --- delimiters)
    lines = result.splitlines(keepends=True)
    in_frontmatter = False
    fm_count = 0
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            fm_count += 1
            in_frontmatter = fm_count == 1
            if fm_count == 2:
                in_frontmatter = False
            cleaned.append(line)
        elif in_frontmatter and stripped.startswith("#"):
            pass  # drop YAML comment lines
        else:
            cleaned.append(line)

    return "".join(cleaned)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a *.agent.md definition file from the skill template.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Agent name in kebab-case (e.g. 'doc-writer', 'test-runner')",
    )
    parser.add_argument(
        "--description",
        required=True,
        help="One-line third-person description of what the agent does and when to use it",
    )
    parser.add_argument(
        "--tools",
        required=True,
        help="Comma-separated list of tool names the agent requires (e.g. 'read_file,grep_search')",
    )
    parser.add_argument(
        "--scope",
        choices=["bounded", "open"],
        default="bounded",
        help=(
            "bounded: restrict agent to declared tools + include ## Out of scope placeholder; "
            "open: unrestricted tools, no Out of scope section"
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write output to this file path. Defaults to '<name>.agent.md' in CWD when stdout is a tty.",
    )

    args = parser.parse_args()
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    try:
        content = scaffold(args.name, args.description, tools, args.scope)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path: Path | None = None
    if args.out:
        out_path = Path(args.out)
    elif sys.stdout.isatty():
        safe_name = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-")
        out_path = Path(f"{safe_name}.agent.md")

    if out_path:
        out_path.write_text(content, encoding="utf-8")
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(content, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
