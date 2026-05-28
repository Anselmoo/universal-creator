#!/usr/bin/env python
"""Validate generated prompt output files (*.prompt.md).

Checks each file for:
  - Valid YAML frontmatter present
  - `name` or `technique` field declared in frontmatter
  - At least one eval scenario section (heading containing "eval", "test",
    "example", or "scenario") in the body

Exit 0 if all files are valid; exit 1 if any violation is found.

Usage:
    python validate_prompt_output.py [path]
    python -m skills.prompt-generator.scripts.validate_prompt_output [path]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml  # pyyaml is declared in requirements.txt for every skill

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Headings that indicate an eval/test section
_EVAL_HEADING_RE = re.compile(
    r"^#{1,3}\s+.*(eval|test|example|scenario|use\s+case|sample)",
    re.IGNORECASE | re.MULTILINE,
)

# Required frontmatter fields: at least one of these must be present
_REQUIRED_FM_FIELDS = {"name", "technique", "model"}


def _parse_frontmatter(text: str) -> tuple[dict | None, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    raw_yaml = match.group(1)
    body = text[match.end() :]
    try:
        return yaml.safe_load(raw_yaml) or {}, body
    except yaml.YAMLError:
        return None, text


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    frontmatter, body = _parse_frontmatter(text)

    # 1. Frontmatter must be parseable
    if frontmatter is None:
        errors.append("missing or unparseable YAML frontmatter")
        return errors  # Can't check anything else without frontmatter

    # 2. At least one required metadata field present
    present_fields = set(frontmatter.keys()) & _REQUIRED_FM_FIELDS
    if not present_fields:
        errors.append(
            f"frontmatter is missing required fields — at least one of "
            f"{sorted(_REQUIRED_FM_FIELDS)} must be declared"
        )

    # 3. Eval / test scenario section
    if not _EVAL_HEADING_RE.search(body):
        errors.append(
            "no eval scenario section found — add a heading like "
            "'## Eval scenarios', '## Examples', or '## Test cases'"
        )

    return errors


def main(search_path: Path = Path(".")) -> int:
    if search_path.is_file():
        files = [search_path]
    else:
        files = sorted(search_path.rglob("*.prompt.md"))

    if not files:
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
