"""Locate bundled skills whether the package is installed (uvx) or editable (uv sync)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_bundled_skills_dir() -> Path:
    """Return the directory that contains the bundled skills.

    Resolution order:
    1. Installed wheel: skills land in the wheel's .data/ directory, accessible
       via importlib.metadata / sys.prefix after ``uvx`` / ``uv tool install``.
    2. Editable install (``uv sync``): fall back to the repo's own skills/ dir.
    """
    # Try importlib.resources path first (wheel install)
    try:
        from importlib.resources import files

        pkg_data = files("universal_creator")
        # When built with uv_build data=["skills"], the skills dir is placed
        # adjacent to the package under <prefix>/share/universal-creator/skills/
        # We navigate from the package location to find it.
        candidate = (
            Path(str(pkg_data)).parent.parent / "share" / "universal-creator" / "skills"
        )
        if candidate.is_dir():
            return candidate
    except Exception:
        pass

    # Editable install: skills/ lives at repo root
    editable = _REPO_ROOT / "skills"
    if editable.is_dir():
        return editable

    print(
        "ERROR: Cannot locate bundled skills directory. "
        "Run `uv sync` or reinstall the package.",
        file=sys.stderr,
    )
    sys.exit(1)


def list_bundled_skills() -> list[str]:
    """Return sorted list of available skill names."""
    skills_dir = get_bundled_skills_dir()
    return sorted(
        d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    )
