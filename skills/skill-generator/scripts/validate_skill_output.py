#!/usr/bin/env python
"""Validate a skill directory against universal-creator structural conventions.

Checks the skill directory (or a single SKILL.md file) for:

Hard errors (exit 1):
  - SKILL.md missing or unparseable YAML frontmatter
  - `name` field: missing, non-kebab-case, or >64 characters
  - `description` field: missing or <20 characters
  - SKILL.md body: no ## headings at all
  - SKILL.md body: missing ## Workflow heading
  - SKILL.md body: missing ## Anti-patterns heading
  - SKILL.md body: missing ## Output format heading
  - requirements.txt missing or does not declare pyyaml
  - No agent file in agents/ (at least one .md required)
  - evals/evals.json missing

Advisories (printed but never affect exit code):
  - description has no "DO NOT USE" clause (recommended for discoverability)
  - description >200 characters (may be truncated in some UIs)
  - SKILL.md body: missing ## Conventions heading
  - No examples/ files found
  - Domain scripts (generate_*.py / validate_*.py) not found in scripts/

Exit 0 if all hard checks pass; exit 1 if any hard violation is found.

Usage:
    python validate_skill_output.py [path]
    # path can be a skill directory or a single SKILL.md file
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

# Hard-required body headings
_WORKFLOW_HEADING = re.compile(r"^##\s+Workflow\b", re.MULTILINE)
_ANTIPATTERNS_HEADING = re.compile(
    r"^##\s+Anti.patterns\b", re.MULTILINE | re.IGNORECASE
)
_OUTPUT_HEADING = re.compile(r"^##\s+(Output format|Output)\b", re.MULTILINE)

# Advisory-only headings
_CONVENTIONS_HEADING = re.compile(r"^##\s+Conventions\b", re.MULTILINE | re.IGNORECASE)

# Advisory: DO NOT USE clause in description
_DO_NOT_USE_RE = re.compile(r"DO NOT USE", re.IGNORECASE)

# Any heading at all
_ANY_HEADING_RE = re.compile(r"^##\s+\S", re.MULTILINE)

_DESC_HARD_MIN = 20
_DESC_ADVISORY_MAX = 200
_NAME_HARD_MAX = 64


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


def validate_skill_md(skill_md: Path) -> tuple[list[str], list[str]]:
    """Validate a single SKILL.md file.  Returns (errors, advisories)."""
    text = skill_md.read_text(encoding="utf-8")
    errors: list[str] = []
    advisories: list[str] = []

    frontmatter, body = _parse_frontmatter(text)

    # 1. Frontmatter parseable
    if frontmatter is None:
        errors.append("missing or unparseable YAML frontmatter")
        return errors, advisories

    # 2. name field
    name = frontmatter.get("name")
    if not name:
        errors.append("frontmatter missing required 'name' field")
    else:
        if not isinstance(name, str):
            errors.append(f"'name' must be a string, got {type(name).__name__}")
        else:
            if not _KEBAB_RE.match(str(name)):
                errors.append(
                    f"'name' must be kebab-case (lowercase, hyphens only): '{name}'"
                )
            if len(str(name)) > _NAME_HARD_MAX:
                errors.append(f"'name' exceeds {_NAME_HARD_MAX} characters: '{name}'")

    # 3. description field
    desc = frontmatter.get("description")
    if not desc:
        errors.append("frontmatter missing required 'description' field")
    else:
        desc_str = str(desc).strip()
        if len(desc_str) < _DESC_HARD_MIN:
            errors.append(
                f"'description' is too short ({len(desc_str)} chars, min {_DESC_HARD_MIN}) "
                "— add trigger phrases, artifact type, and DO NOT USE clauses"
            )
        if len(desc_str) > _DESC_ADVISORY_MAX:
            advisories.append(
                f"'description' is {len(desc_str)} chars; "
                f"some UIs truncate around {_DESC_ADVISORY_MAX} chars"
            )
        if not _DO_NOT_USE_RE.search(desc_str):
            advisories.append(
                "'description' has no 'DO NOT USE' clause — "
                "add one to prevent triggering when a neighboring skill is more appropriate"
            )

    # 4. Body: at least one heading
    if not _ANY_HEADING_RE.search(body):
        errors.append(
            "SKILL.md body has no section headings — "
            "add ## Workflow, ## Anti-patterns, ## Output format at minimum"
        )
        return errors, advisories

    # 5. Body: ## Workflow
    if not _WORKFLOW_HEADING.search(body):
        errors.append(
            "SKILL.md body missing ## Workflow section — "
            "add numbered steps describing what the skill does"
        )

    # 6. Body: ## Anti-patterns
    if not _ANTIPATTERNS_HEADING.search(body):
        errors.append(
            "SKILL.md body missing ## Anti-patterns section — "
            "list at least three failure modes and why each is harmful"
        )

    # 7. Body: ## Output format
    if not _OUTPUT_HEADING.search(body):
        errors.append(
            "SKILL.md body missing ## Output format section — "
            "specify the exact files this skill produces"
        )

    # Advisory: ## Conventions
    if not _CONVENTIONS_HEADING.search(body):
        advisories.append(
            "no ## Conventions section found — "
            "recommended to define domain quality rules for generated artifacts"
        )

    return errors, advisories


def validate_skill_dir(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Validate a full skill directory.  Returns (errors, advisories)."""
    errors: list[str] = []
    advisories: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"SKILL.md not found in {skill_dir}")
        return errors, advisories

    md_errors, md_advisories = validate_skill_md(skill_md)
    errors.extend(md_errors)
    advisories.extend(md_advisories)

    # requirements.txt
    req = skill_dir / "requirements.txt"
    if not req.exists():
        errors.append("missing requirements.txt")
    else:
        entries = {
            line.strip().lower()
            for line in req.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        if not any(e.startswith("pyyaml") for e in entries):
            errors.append("requirements.txt must declare pyyaml>=6.0")

    # agents/ — at least one .md file
    agents_dir = skill_dir / "agents"
    if not agents_dir.is_dir() or not list(agents_dir.glob("*.md")):
        errors.append(
            "agents/ directory is missing or empty — "
            "add at least grader.md to support evaluation"
        )

    # evals/evals.json
    evals_json = skill_dir / "evals" / "evals.json"
    if not evals_json.exists():
        errors.append("evals/evals.json missing — add at least a minimal evals file")

    # Advisory: examples/
    examples_dir = skill_dir / "examples"
    if not examples_dir.is_dir() or not list(examples_dir.iterdir()):
        advisories.append(
            "examples/ directory is empty — "
            "add at least one real-quality example artifact"
        )

    # Advisory: domain scripts
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        gen_scripts = list(scripts_dir.glob("generate_*.py"))
        val_scripts = list(scripts_dir.glob("validate_*.py"))
        if not gen_scripts:
            advisories.append(
                "no generate_*.py script found in scripts/ — "
                "add a generate_<name>_stub.py for artifact scaffolding"
            )
        if not val_scripts:
            advisories.append(
                "no validate_*.py script found in scripts/ — "
                "add a validate_<name>_output.py to check generated artifacts"
            )

    return errors, advisories


def main(search_path: Path = Path(".")) -> int:
    if search_path.is_file() and search_path.name == "SKILL.md":
        # Single-file mode
        errors, advisories = validate_skill_md(search_path)
        label = search_path
        if errors:
            print(f"  ✗ {label}")
            for err in errors:
                print(f"    - {err}")
        elif advisories:
            print(f"  △ {label}")
        else:
            print(f"  ✓ {label}")
        for adv in advisories:
            print(f"    advisory: {adv}")
        return 1 if errors else 0

    # Directory mode: treat the path itself as a skill directory if it has SKILL.md,
    # otherwise recurse looking for skill directories one level deep.
    if (search_path / "SKILL.md").exists():
        skill_dirs = [search_path]
    else:
        skill_dirs = sorted(
            p for p in search_path.iterdir() if p.is_dir() and (p / "SKILL.md").exists()
        )

    if not skill_dirs:
        # No skill found — nothing to validate, that's OK.
        return 0

    any_failure = False
    for skill_dir in skill_dirs:
        errors, advisories = validate_skill_dir(skill_dir)
        label = skill_dir.name
        if errors:
            any_failure = True
            print(f"  ✗ {label}")
            for err in errors:
                print(f"    - {err}")
        elif advisories:
            print(f"  △ {label}")
        else:
            print(f"  ✓ {label}")
        for adv in advisories:
            print(f"    advisory: {adv}")

    return 1 if any_failure else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(main(target))
