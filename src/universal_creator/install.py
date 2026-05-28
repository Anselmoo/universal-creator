"""Install a bundled skill or agent to the correct directory for a given host and scope.

Hosts and their target paths:
    Skills:
        claude  · local   → <cwd>/.claude/skills/<name>/
        claude  · global  → ~/.claude/skills/<name>/
        copilot · local   → <cwd>/.github/skills/<name>/
        copilot · global  → ~/.copilot/skills/<name>/
        gemini  · local   → <cwd>/.agents/skills/<name>/
        gemini  · global  → ~/.agents/skills/<name>/
        codex   · local   → <cwd>/.agents/skills/<name>/
        codex   · global  → ~/.agents/skills/<name>/
    Agents:
        claude  · local   → <cwd>/.claude/agents/<name>.agent.md
        claude  · global  → ~/.claude/agents/<name>.agent.md
        copilot · local   → <cwd>/.github/agents/<name>.agent.md
        copilot · global  → ~/.copilot/agents/<name>.agent.md
        gemini  · local   → <cwd>/.agents/agents/<name>.agent.md
        gemini  · global  → ~/.agents/agents/<name>.agent.md
        codex   · local   → <cwd>/.agents/agents/<name>.agent.md
        codex   · global  → ~/.agents/agents/<name>.agent.md
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from universal_creator.resources import (
    get_bundled_agents_dir,
    get_bundled_skills_dir,
    list_bundled_agents,
    list_bundled_skills,
)


def _host_paths() -> dict[str, dict[str, Path]]:
    """Return host → scope path mapping for skill installation.

    ``Path.home()`` is resolved at call time so tests can patch it safely.
    """
    return {
        "claude": {
            "local": Path(".claude") / "skills",
            "global": Path.home() / ".claude" / "skills",
        },
        "copilot": {
            "local": Path(".github") / "skills",
            "global": Path.home() / ".copilot" / "skills",
        },
        "gemini": {
            "local": Path(".agents") / "skills",
            "global": Path.home() / ".agents" / "skills",
        },
        "codex": {
            "local": Path(".agents") / "skills",
            "global": Path.home() / ".agents" / "skills",
        },
    }


def _agent_host_paths() -> dict[str, dict[str, Path]]:
    """Return host → scope path mapping for agent installation.

    ``Path.home()`` is resolved at call time so tests can patch it safely.
    """
    return {
        "claude": {
            "local": Path(".claude") / "agents",
            "global": Path.home() / ".claude" / "agents",
        },
        "copilot": {
            "local": Path(".github") / "agents",
            "global": Path.home() / ".copilot" / "agents",
        },
        "gemini": {
            "local": Path(".agents") / "agents",
            "global": Path.home() / ".agents" / "agents",
        },
        "codex": {
            "local": Path(".agents") / "agents",
            "global": Path.home() / ".agents" / "agents",
        },
    }


def get_default_skill_output_dir(
    host: str, scope: str, name: str | None = None
) -> Path:
    """Return the default relative output directory for scaffolding a skill.

    This centralizes the mapping used by CLI scaffolders so hosts agree on where
    skills and host-specific instruction artifacts land.
    ``name`` may be used to special-case instruction skills which belong under
    .github/ (repository-level instructions).
    """
    host_l = host.lower()
    if name and "instruction" in name.lower():
        # Repository-level instructions live under .github/
        return Path(".github")
    if host_l == "copilot":
        return Path(".github") / "skills"
    if host_l in ("gemini", "codex"):
        return Path(".agents") / "skills"
    return Path(f".{host_l}") / "skills"


def resolve_target(host: str, scope: str, cwd: Path | None = None) -> Path:
    """Return the absolute target directory for the given host + scope."""
    base = _host_paths()[host][scope]
    if scope == "local" and cwd:
        base = cwd / base
    return base.resolve()


def resolve_agent_target(host: str, scope: str, cwd: Path | None = None) -> Path:
    """Return the absolute agents directory for the given host + scope."""
    base = _agent_host_paths()[host][scope]
    if scope == "local" and cwd:
        base = cwd / base
    return base.resolve()


def _read_skill_dependencies(skill_src: Path) -> list[str]:
    """Parse the YAML frontmatter of a SKILL.md and return its dependencies list."""
    skill_md = skill_src / "SKILL.md"
    if not skill_md.is_file():
        return []
    try:
        content = skill_md.read_text(encoding="utf-8")
        # Extract content between the first pair of --- markers
        parts = content.split("---", 2)
        if len(parts) < 3:
            return []
        import re

        # Simple key: list parser for the dependencies field (avoids a hard yaml dep here)
        # Format expected:
        #   dependencies:
        #     - shared
        match = re.search(
            r"^dependencies:\s*\n((?:\s+-\s+\S+\n?)+)", parts[1], re.MULTILINE
        )
        if not match:
            return []
        items = re.findall(r"^\s+-\s+(\S+)", match.group(1), re.MULTILINE)
        return items
    except Exception:
        return []


def install_skill(
    skill_name: str,
    host: str,
    scope: str,
    cwd: Path | None = None,
    overwrite: bool = False,
) -> int:
    """Copy a bundled skill to the target directory.

    Dependencies declared in the skill's SKILL.md frontmatter are installed first
    using overwrite=True so that a shared dependency (e.g. 'shared') is refreshed
    rather than causing an error when multiple skills depend on it.

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

    # Auto-install dependencies before copying this skill.
    for dep in _read_skill_dependencies(src):
        dep_rc = install_skill(dep, host, scope, cwd, overwrite=True)
        if dep_rc != 0:
            print(
                f"ERROR: Failed to install dependency '{dep}' for '{skill_name}'",
                file=sys.stderr,
            )
            return 1

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


def install_all(
    host: str,
    scope: str,
    cwd: Path | None = None,
) -> int:
    """Install all bundled skills to the target host and scope.

    Always uses overwrite=True internally: shared dependencies are installed by
    multiple skills' dep resolution before the direct loop reaches them, so
    idempotency requires treating every install as a replacement.

    Returns 0 if all skills install successfully, 1 if any skill fails.
    """
    results: list[tuple[str, int]] = []
    for skill_name in list_bundled_skills():
        rc = install_skill(skill_name, host, scope, cwd, overwrite=True)
        results.append((skill_name, rc))
    failed = [name for name, rc in results if rc != 0]
    if failed:
        print(f"ERROR: Failed to install: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def install_agent(
    agent_name: str,
    host: str,
    scope: str,
    cwd: Path | None = None,
    overwrite: bool = False,
) -> int:
    """Copy a bundled agent definition file to the target agents directory.

    Returns 0 on success, 1 on error.
    """
    available = list_bundled_agents()
    if agent_name not in available:
        print(
            f"ERROR: Agent '{agent_name}' not found. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        return 1

    src = get_bundled_agents_dir() / f"{agent_name}.agent.md"
    target_dir = resolve_agent_target(host, scope, cwd or Path.cwd())
    dest = target_dir / f"{agent_name}.agent.md"

    if dest.exists():
        if not overwrite:
            print(
                f"ERROR: {dest} already exists. Pass --overwrite to replace.",
                file=sys.stderr,
            )
            return 1
        dest.unlink()

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"Installed '{agent_name}' → {dest}")
    return 0
