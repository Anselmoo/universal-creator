#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import importlib
import re
import sys
from pathlib import Path

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

errors_module = importlib.import_module("scripts.errors")
EvalError = errors_module.EvalError
message = errors_module.message


def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, message(EvalError.SKILL_MD_NOT_FOUND)

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, message(EvalError.NO_FRONTMATTER)

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, message(EvalError.INVALID_FRONTMATTER_FORMAT)

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, message(EvalError.FRONTMATTER_NOT_DICT)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {
        "name",
        "description",
        "license",
        "allowed-tools",
        "metadata",
        "compatibility",
    }

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, message(
            EvalError.UNEXPECTED_KEYS,
            unexpected=", ".join(sorted(unexpected_keys)),
            allowed=", ".join(sorted(ALLOWED_PROPERTIES)),
        )

    # Check required fields
    if "name" not in frontmatter:
        return False, message(EvalError.MISSING_NAME)
    if "description" not in frontmatter:
        return False, message(EvalError.MISSING_DESCRIPTION)

    # Extract name for validation
    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, message(EvalError.NAME_NOT_STRING, type=type(name).__name__)
    name = name.strip()
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            return False, message(EvalError.NAME_INVALID_FORMAT, name=name)
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return False, message(EvalError.NAME_HYPHEN_ERROR, name=name)
        if len(name) > 64:
            return False, message(EvalError.NAME_TOO_LONG, length=len(name))

    # Extract and validate description
    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, message(
            EvalError.DESCRIPTION_NOT_STRING, type=type(description).__name__
        )
    description = description.strip()
    if description:
        if "<" in description or ">" in description:
            return False, message(EvalError.DESCRIPTION_INVALID_CHARS)
        if len(description) > 1024:
            return False, message(
                EvalError.DESCRIPTION_TOO_LONG, length=len(description)
            )

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get("compatibility", "")
    if compatibility:
        if not isinstance(compatibility, str):
            return False, message(
                EvalError.COMPATIBILITY_NOT_STRING, type=type(compatibility).__name__
            )
        if len(compatibility) > 500:
            return False, message(
                EvalError.COMPATIBILITY_TOO_LONG, length=len(compatibility)
            )

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, validation_message = validate_skill(sys.argv[1])
    print(validation_message)
    sys.exit(0 if valid else 1)
