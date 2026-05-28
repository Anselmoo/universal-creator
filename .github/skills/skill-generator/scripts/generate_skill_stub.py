#!/usr/bin/env python
"""Scaffold a minimal SKILL.md stub for a new universal-creator skill.

Reads the skill-workflow.md template from the skill's templates/ directory,
fills in the skill name, artifact type, and description, and writes a
ready-to-edit SKILL.md stub.

Usage:
    python generate_skill_stub.py \
        --name sql-migrator \
        --artifact-type "SQL migration file" \
        --description "Generates SQL migration files from schema diffs" \
        [--out FILE]

Outputs to stdout unless --out is given.  When stdout is a tty and --out is
omitted, writes to <name>.SKILL.md in the current directory.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _SKILL_ROOT / "templates" / "skill-workflow.md"

# Placeholder tokens as they appear in the template
_NAME_PLACEHOLDER = "{{SKILL_NAME}}"
_ARTIFACT_PLACEHOLDER = "{{ARTIFACT_TYPE}}"
_DESC_PLACEHOLDER = "{{SKILL_DESCRIPTION}}"
_TITLE_PLACEHOLDER = "{{SKILL_TITLE}}"


def _kebab(name: str) -> str:
    """Normalise a skill name to kebab-case."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _title(name: str) -> str:
    """Convert kebab-case name to Title Case for the # heading."""
    return " ".join(word.capitalize() for word in name.split("-"))


def scaffold(name: str, artifact_type: str, description: str) -> str:
    """Return filled-in SKILL.md stub content."""
    if not _TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {_TEMPLATE}")

    template = _TEMPLATE.read_text(encoding="utf-8")
    safe_name = _kebab(name)

    result = template
    result = result.replace(_NAME_PLACEHOLDER, safe_name)
    result = result.replace(_TITLE_PLACEHOLDER, _title(safe_name))
    result = result.replace(_ARTIFACT_PLACEHOLDER, artifact_type)
    result = result.replace(_DESC_PLACEHOLDER, description)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a SKILL.md stub for a new universal-creator skill.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Skill name in kebab-case (e.g. 'sql-migrator', 'markdown-renderer')",
    )
    parser.add_argument(
        "--artifact-type",
        required=True,
        help="The type of artifact this skill generates (e.g. 'SQL migration file')",
    )
    parser.add_argument(
        "--description",
        required=True,
        help="One-line description of what the skill does and when to use it",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write output to this file path. Defaults to '<name>.SKILL.md' in CWD when stdout is a tty.",
    )

    args = parser.parse_args()

    try:
        content = scaffold(args.name, args.artifact_type, args.description)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path: Path | None = None
    if args.out:
        out_path = Path(args.out)
    elif sys.stdout.isatty():
        safe_name = _kebab(args.name)
        out_path = Path(f"{safe_name}.SKILL.md")

    if out_path:
        out_path.write_text(content, encoding="utf-8")
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(content, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
