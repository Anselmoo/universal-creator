"""Install a bundled skill to the correct directory for a given host and scope.

Hosts and their target paths:
    claude  · local   → <cwd>/.claude/skills/<name>/
    claude  · global  → ~/.claude/skills/<name>/
    copilot · local   → <cwd>/.github/skills/<name>/
    copilot · global  → ~/.copilot/skills/<name>/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from universal_creator.resources import get_bundled_skills_dir, list_bundled_skills

_HOST_PATHS: dict[str, dict[str, Path]] = {
    "claude": {
        "local": Path(".claude") / "skills",
        "global": Path.home() / ".claude" / "skills",
    },
    "copilot": {
        "local": Path(".github") / "skills",
        "global": Path.home() / ".copilot" / "skills",
    },
}


def resolve_target(host: str, scope: str, cwd: Path | None = None) -> Path:
    """Return the absolute target directory for the given host + scope."""
    base = _HOST_PATHS[host][scope]
    if scope == "local" and cwd:
        base = cwd / base
    return base.resolve()


def install_skill(
    skill_name: str,
    host: str,
    scope: str,
    cwd: Path | None = None,
    overwrite: bool = False,
) -> int:
    """Copy a bundled skill to the target directory.

    Returns 0 on success, 1 on error.
    """
    available = list_bundled_skills()
    if skill_name not in available:
        print(
            f"ERROR: Skill '{skill_name}' not found. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        return 1

    src = get_bundled_skills_dir() / skill_name
    target_dir = resolve_target(host, scope, cwd or Path.cwd())
    dest = target_dir / skill_name

    if dest.exists():
        if not overwrite:
            print(
                f"ERROR: {dest} already exists. Pass --overwrite to replace.",
                file=sys.stderr,
            )
            return 1
        shutil.rmtree(dest)

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    print(f"Installed '{skill_name}' → {dest}")
    return 0
