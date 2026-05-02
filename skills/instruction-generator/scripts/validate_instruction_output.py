#!/usr/bin/env python
"""Validate generated instruction output files (*.instructions.md).

Checks each file for:
  - Valid YAML frontmatter with a usable `applyTo` glob
  - No soft-rule language ("should", "prefer", "try to", "consider", "might")
  - Line budget respected (≤20 for concise, ≤60 for extended)

Exit 0 if all files are valid; exit 1 if any violation is found.

Usage:
    python validate_instruction_output.py [path]
    python -m skills.instruction-generator.scripts.validate_instruction_output [path]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml  # pyyaml is declared in requirements.txt for every skill

# ---------------------------------------------------------------------------
# Soft-rule words that make rules unverifiable
# ---------------------------------------------------------------------------

_SOFT_RULE_RE = re.compile(
    r"\b(should|prefer|try to|consider|might|maybe|ideally|where possible|if possible|whenever possible)\b",
    re.IGNORECASE,
)

# Frontmatter fence
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Line budget thresholds
_CONCISE_LIMIT = 20
_EXTENDED_LIMIT = 60


def _parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body_text) or (None, full_text) if no frontmatter."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    raw_yaml = match.group(1)
    body = text[match.end() :]
    try:
        return yaml.safe_load(raw_yaml) or {}, body
    except yaml.YAMLError:
        return None, text


def _count_rule_lines(body: str) -> int:
    """Count non-blank, non-heading lines in the instruction body."""
    return sum(
        1
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    # 1. Frontmatter presence
    frontmatter, body = _parse_frontmatter(text)
    if frontmatter is None:
        errors.append("missing or unparseable YAML frontmatter")
    else:
        apply_to = frontmatter.get("applyTo")
        if apply_to is not None:
            # applyTo should be a non-empty string
            if not isinstance(apply_to, str) or not apply_to.strip():
                errors.append("`applyTo` is present but empty or non-string")
            elif apply_to.strip() in ("<glob>", "glob", "<pattern>"):
                errors.append(
                    "`applyTo` still contains placeholder value — replace with a real glob"
                )

    # 2. Soft-rule detection
    soft_hits: list[str] = []
    for lineno, line in enumerate(body.splitlines(), start=1):
        # Only check lines that look like rules (start with - or *)
        stripped = line.strip()
        if stripped.startswith(("-", "*")):
            m = _SOFT_RULE_RE.search(stripped)
            if m:
                soft_hits.append(
                    f"line {lineno}: soft-rule word '{m.group(0)}' in rule '{stripped[:80]}'"
                )

    if soft_hits:
        errors.append(
            "rules contain unverifiable soft language — rewrite in imperative form:\n      "
            + "\n      ".join(soft_hits)
        )

    # 3. Line budget
    rule_line_count = _count_rule_lines(body)
    if rule_line_count > _EXTENDED_LIMIT:
        errors.append(
            f"body has {rule_line_count} content lines (limit: {_EXTENDED_LIMIT}). "
            "Split extended rules into a separate reference file."
        )
    elif rule_line_count > _CONCISE_LIMIT:
        pass  # Extended variant is valid; no error, just in the extended range.

    return errors


def main(search_path: Path = Path(".")) -> int:
    if search_path.is_file():
        files = [search_path]
    else:
        files = sorted(search_path.rglob("*.instructions.md"))

    if not files:
        # Pre-commit: invoked without specific path — nothing to check.
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
            print(f"  ✓ {rel}")

    return 1 if any_failure else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(main(target))
