"""
Single source of truth for validation error codes.

Used by quick_validate.py and any other scripts that emit structured errors.
Format: E<category><index>
  E1xx — structure / file presence
  E2xx — YAML frontmatter
  E3xx — field content / value
"""

from __future__ import annotations


class EvalError:
    # E1xx — Structure
    SKILL_MD_NOT_FOUND = "E101"
    NO_FRONTMATTER = "E102"
    INVALID_FRONTMATTER_FORMAT = "E103"
    FRONTMATTER_NOT_DICT = "E104"

    # E2xx — Unexpected / missing keys
    UNEXPECTED_KEYS = "E201"
    MISSING_NAME = "E202"
    MISSING_DESCRIPTION = "E203"

    # E3xx — Field content
    NAME_NOT_STRING = "E301"
    NAME_INVALID_FORMAT = "E302"
    NAME_HYPHEN_ERROR = "E303"
    NAME_TOO_LONG = "E304"
    DESCRIPTION_NOT_STRING = "E305"
    DESCRIPTION_INVALID_CHARS = "E306"
    DESCRIPTION_TOO_LONG = "E307"
    COMPATIBILITY_NOT_STRING = "E308"
    COMPATIBILITY_TOO_LONG = "E309"


# Human-readable message templates (use .format(**kwargs) to fill placeholders)
MESSAGES: dict[str, str] = {
    EvalError.SKILL_MD_NOT_FOUND: "SKILL.md not found",
    EvalError.NO_FRONTMATTER: "No YAML frontmatter found",
    EvalError.INVALID_FRONTMATTER_FORMAT: "Invalid frontmatter format",
    EvalError.FRONTMATTER_NOT_DICT: "Frontmatter must be a YAML dictionary",
    EvalError.UNEXPECTED_KEYS: (
        "Unexpected key(s) in SKILL.md frontmatter: {unexpected}. "
        "Allowed properties are: {allowed}"
    ),
    EvalError.MISSING_NAME: "Missing 'name' in frontmatter",
    EvalError.MISSING_DESCRIPTION: "Missing 'description' in frontmatter",
    EvalError.NAME_NOT_STRING: "Name must be a string, got {type}",
    EvalError.NAME_INVALID_FORMAT: "Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)",
    EvalError.NAME_HYPHEN_ERROR: "Name '{name}' cannot start/end with hyphen or contain consecutive hyphens",
    EvalError.NAME_TOO_LONG: "Name is too long ({length} characters). Maximum is 64 characters.",
    EvalError.DESCRIPTION_NOT_STRING: "Description must be a string, got {type}",
    EvalError.DESCRIPTION_INVALID_CHARS: "Description cannot contain angle brackets (< or >)",
    EvalError.DESCRIPTION_TOO_LONG: "Description is too long ({length} characters). Maximum is 1024 characters.",
    EvalError.COMPATIBILITY_NOT_STRING: "Compatibility must be a string, got {type}",
    EvalError.COMPATIBILITY_TOO_LONG: "Compatibility is too long ({length} characters). Maximum is 500 characters.",
}


def message(code: str, **kwargs: object) -> str:
    """Return the formatted error message for a given error code."""
    template = MESSAGES.get(code, f"Unknown error {code}")
    return template.format(**kwargs) if kwargs else template
