"""Locate bundled skills for both wheel and editable installs."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _looks_like_skills_container(path: Path) -> bool:
    """Return True when a directory contains bundled skill directories."""
    if not path.is_dir():
        return False

    try:
        return any(
            child.is_dir() and (child / "SKILL.md").is_file()
            for child in path.iterdir()
        )
    except OSError:
        return False


def _candidate_skill_roots() -> list[Path]:
    """Return candidate directories that may contain bundled skills.

    In wheel installs, uv_build data files are installed into ``purelib``
    alongside the package, so skills appear as top-level directories next to
    ``universal_creator``.
    """
    candidates: list[Path] = []

    # Installed package root (wheel / uvx / uv tool install).
    try:
        from importlib.resources import as_file, files

        with as_file(files("universal_creator")) as package_dir:
            pkg_path = Path(package_dir)
            candidates.append(pkg_path.parent)

            # Backward-compatible fallback for older layouts.
            candidates.append(
                pkg_path.parent.parent / "share" / "universal-creator" / "skills"
            )
    except Exception:
        pass

    # Editable install / local development repository layout.
    candidates.append(_REPO_ROOT / "skills")
    return candidates


def get_bundled_skills_dir() -> Path:
    """Return the directory that contains the bundled skills.

    Resolution order:
    1. Installed wheel/tool: skill directories are available in ``purelib``
       alongside the package.
    2. Editable install: fall back to the repository's ``skills/`` directory.
    """
    for candidate in _candidate_skill_roots():
        if _looks_like_skills_container(candidate):
            return candidate

    print(
        "ERROR: Cannot locate bundled skills in the installed package. "
        "Reinstall `universal-creator` and try again.",
        file=sys.stderr,
    )
    sys.exit(1)


def list_bundled_skills() -> list[str]:
    """Return sorted list of available skill names."""
    skills_dir = get_bundled_skills_dir()
    return sorted(
        d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    )
