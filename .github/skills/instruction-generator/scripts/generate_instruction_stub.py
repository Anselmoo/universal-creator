#!/usr/bin/env python
"""Scaffold a minimal instruction file from a template.

Reads the concise or extended template from the skill's templates/ directory
and fills in the title and applyTo glob, writing a ready-to-edit
*.instructions.md stub.

Usage:
    python generate_instruction_stub.py --apply-to "**/*.ts" --title "TypeScript rules" [--variant concise|extended] [--out <file>]
    python generate_instruction_stub.py --apply-to "src/**" --title "Source conventions" --variant extended

Outputs to stdout unless --out is given.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _SKILL_ROOT / "templates"

_CONCISE_TEMPLATE = _TEMPLATES_DIR / "instructions-concise.md"
_EXTENDED_TEMPLATE = _TEMPLATES_DIR / "instructions-extended.md"


def _safe_filename(title: str) -> str:
    """Convert a title to a safe kebab-case filename stem."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def scaffold(apply_to: str, title: str, variant: str) -> str:
    """Return the filled-in instruction file content."""
    template_path = _CONCISE_TEMPLATE if variant == "concise" else _EXTENDED_TEMPLATE
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template = template_path.read_text(encoding="utf-8")

    # Replace the applyTo placeholder with the real glob
    # The concise template has:  applyTo: "<glob>"
    # The extended template has: applyTo: "<glob>"
    result = template.replace('applyTo: "<glob>"', f'applyTo: "{apply_to}"')

    # Replace the title placeholder
    result = result.replace("# <Short Title>", f"# {title}")
    result = result.replace("# <Title>", f"# {title}")

    # Strip YAML comment lines from inside the frontmatter block
    lines = result.splitlines(keepends=True)
    in_frontmatter = False
    frontmatter_count = 0
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            if frontmatter_count == 2:
                in_frontmatter = False
            cleaned.append(line)
        elif in_frontmatter and stripped.startswith("#"):
            pass  # Skip YAML comment lines in frontmatter
        else:
            cleaned.append(line)

    return "".join(cleaned)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a *.instructions.md file from a template.",
    )
    parser.add_argument(
        "--apply-to",
        required=True,
        help="Glob pattern for applyTo field (e.g. '**/*.ts', 'src/**', '**')",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Short title for the instruction set (e.g. 'TypeScript rules')",
    )
    parser.add_argument(
        "--variant",
        choices=["concise", "extended"],
        default="concise",
        help="Template variant: concise (≤20 rule lines) or extended (20-60 rule lines)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Write output to this file. "
            "Defaults to '<title-kebab>.instructions.md' in CWD when --out is omitted "
            "and stdout is a tty."
        ),
    )

    args = parser.parse_args()

    try:
        content = scaffold(args.apply_to, args.title, args.variant)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path: Path | None = None
    if args.out:
        out_path = Path(args.out)
    elif sys.stdout.isatty():
        stem = _safe_filename(args.title)
        out_path = Path(f"{stem}.instructions.md")

    if out_path:
        out_path.write_text(content, encoding="utf-8")
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(content, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
