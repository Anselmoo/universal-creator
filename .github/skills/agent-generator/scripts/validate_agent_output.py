#!/usr/bin/env python
"""Validate generated agent definition files (*.agent.md).

Checks each file for:
  - Valid YAML frontmatter (parseable, required fields present)
  - `name` field: kebab-case, ≤60 characters
  - `description` field: present, ≤1024 characters (Copilot scope limit, per template)
  - Non-blocking advisory when >70 characters (Copilot mode label truncates around 70)
  - `tools` field: non-empty list
  - Body: at least one ## heading present
  - Body: one of ## Scope / ## Role / ## System / ## Task / ## Mission heading
  - Body: ## Output format (or ## Output) heading

Non-blocking advisories (printed but don't affect exit code):
  - Description >70 characters (Copilot chat mode label truncates around 70)
  - Missing ## Completion criteria (or ## Done when) — recommended but optional

Exit 0 if all hard checks pass; exit 1 if any hard violation is found.

Usage:
    python validate_agent_output.py [path]
    python -m skills.agent-generator.scripts.validate_agent_output [path]
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

# Valid kebab-case name: lowercase letters, digits, hyphens only
_KEBAB_RE = re.compile(r"^[a-z][a-z0-9\-]*$")

# Hard-required body headings: at least one of these groups
_SCOPE_HEADINGS = re.compile(r"^##\s+(Scope|Role|System|Task|Mission)\b", re.MULTILINE)
_OUTPUT_HEADINGS = re.compile(r"^##\s+(Output format|Output)\b", re.MULTILINE)

# Advisory-only headings
_COMPLETION_HEADINGS = re.compile(
    r"^##\s+(Completion criteria|Done when|Done|Completion)\b", re.MULTILINE
)

# Any heading at all
_ANY_HEADING_RE = re.compile(r"^##\s+\S", re.MULTILINE)

# Description advisory threshold (Copilot mode list truncates at ~70 chars)
_DESC_ADVISORY_LIMIT = 70
_DESC_HARD_LIMIT = 1024  # documented max in the skill template


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


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, advisories) for the given file."""
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    advisories: list[str] = []

    frontmatter, body = _parse_frontmatter(text)

    # 1. Frontmatter must be parseable
    if frontmatter is None:
        errors.append("missing or unparseable YAML frontmatter")
        return errors, advisories  # can't check anything else

    # 2. name field
    name = frontmatter.get("name")
    if not name:
        errors.append("frontmatter is missing required 'name' field")
    else:
        if not isinstance(name, str):
            errors.append(f"'name' must be a string, got {type(name).__name__}")
        else:
            if not _KEBAB_RE.match(str(name)):
                errors.append(
                    f"'name' must be kebab-case (lowercase, hyphens only): '{name}'"
                )
            if len(str(name)) > 60:
                errors.append(f"'name' exceeds 60 characters: '{name}'")

    # 3. description field
    desc = frontmatter.get("description")
    if not desc:
        errors.append("frontmatter is missing required 'description' field")
    else:
        desc_str = str(desc).strip()
        if len(desc_str) > _DESC_HARD_LIMIT:
            errors.append(
                f"'description' exceeds {_DESC_HARD_LIMIT} characters "
                f"({len(desc_str)} chars) — exceeds Copilot maximum"
            )
        elif len(desc_str) > _DESC_ADVISORY_LIMIT:
            advisories.append(
                f"'description' is {len(desc_str)} chars; "
                f"Copilot mode labels truncate around {_DESC_ADVISORY_LIMIT} chars — consider shortening"
            )

    # 4. tools field
    tools = frontmatter.get("tools")
    if not tools:
        errors.append(
            "frontmatter is missing 'tools' list — declare at minimum the tools this agent requires"
        )
    elif not isinstance(tools, list) or len(tools) == 0:
        errors.append("'tools' must be a non-empty list")

    # 5. Body: at least one heading
    if not _ANY_HEADING_RE.search(body):
        errors.append(
            "body has no section headings — add ## Scope / ## Mission / ## Output format etc."
        )
        return errors, advisories  # no point checking headings if none at all

    # 6. Body: scope/role/system/task/mission heading
    if not _SCOPE_HEADINGS.search(body):
        errors.append(
            "body is missing a scope-defining heading — add one of: "
            "## Scope, ## Role, ## System, ## Task, ## Mission"
        )

    # 7. Body: output format heading
    if not _OUTPUT_HEADINGS.search(body):
        errors.append(
            "body is missing an output heading — add ## Output format or ## Output"
        )

    # 8. Advisory: completion criteria
    if not _COMPLETION_HEADINGS.search(body):
        advisories.append(
            "no ## Completion criteria section found — "
            "recommended to tell the agent when to call task_complete"
        )

    return errors, advisories


def main(search_path: Path = Path(".")) -> int:
    if search_path.is_file():
        files = [search_path]
    else:
        files = sorted(search_path.rglob("*.agent.md"))

    if not files:
        return 0

    any_failure = False
    for path in files:
        errors, advisories = validate_file(path)
        rel = path.relative_to(search_path) if search_path.is_dir() else path
        if errors:
            any_failure = True
            print(f"  ✗ {rel}")
            for err in errors:
                print(f"    - {err}")
        elif advisories:
            print(f"  △ {rel}")
        else:
            print(f"  ✓ {rel}")
        for adv in advisories:
            print(f"    advisory: {adv}")

    return 1 if any_failure else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(main(target))
