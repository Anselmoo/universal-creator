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

from universal_creator.install_helpers import (
    backup_paths,
    prompt_confirmation,
    stage_dir,
)
from universal_creator.manifest import (
    MANIFEST_RELATIVE_PATH,
    compute_tree_manifest,
    decide_action,
    read_manifest,
    sha256_of_file,
    write_manifest,
)
from universal_creator.resources import (
    get_bundled_agents_dir,
    get_bundled_skills_dir,
    list_bundled_agents,
    list_bundled_skills,
)

# Files in skills/shared/agents/ that are fanned out to the host's
# top-level agents directory when the ``shared`` skill is installed. Mirrors
# ``SHARED_TRIO`` in ``scripts/sync_agents.py`` but excludes the
# ``_memory-guardrails.md`` snippet, which is referenced from inside the
# agent files via relative link and does not need a top-level deploy.
SHARED_TRIO_AGENT_FILES: tuple[str, ...] = (
    "validation-reviewer.agent.md",
    "artifact-router.agent.md",
    "prompt-strategist.agent.md",
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


def _shared_lock_path(host: str, scope: str, cwd: Path | None = None) -> Path:
    """Return the absolute path of ``shared.lock`` for the given host + scope.

    The lock lives at ``<host_root>/.universal-creator/shared.lock`` where
    ``host_root`` is the parent of both the host's ``skills/`` and ``agents/``
    directories (e.g. ``~/.claude`` for claude-global). That placement lets a
    single manifest cover both the contents of the installed ``shared/``
    directory and the trio agents fanned out to ``agents/``.
    """
    return resolve_target(host, scope, cwd).parent / MANIFEST_RELATIVE_PATH


def _shared_deployed_manifest(shared_dest: Path, agents_target: Path) -> dict[str, str]:
    """Hash the currently deployed ``shared`` install + fanned trio agents."""
    out: dict[str, str] = {}
    if shared_dest.is_dir():
        for path in sorted(shared_dest.rglob("*")):
            if path.is_file():
                rel = path.relative_to(shared_dest).as_posix()
                out[f"skills/shared/{rel}"] = sha256_of_file(path)
    for name in SHARED_TRIO_AGENT_FILES:
        deploy = agents_target / name
        if deploy.is_file():
            out[f"agents/{name}"] = sha256_of_file(deploy)
    return out


def _install_shared(
    src: Path,
    shared_dest: Path,
    agents_target: Path,
    lock_path: Path,
    force_shared: bool,
) -> int:
    """Install the ``shared`` skill with per-file edit protection.

    Algorithm:
      1. If ``force_shared`` is set, full ``rmtree`` + ``copytree`` and rewrite
         the manifest from the freshly deployed files.
      2. If no manifest exists and the destination is empty, fresh install.
      3. If no manifest exists but files are present, refuse — the user is
         responsible for those files and we won't take ownership silently.
      4. If a manifest exists, reconcile per-file: idempotent / safe_upgrade /
         user_modified / user_deleted, preserving user-modified files and
         warning about each preserved path.
    """
    bundled_files = compute_tree_manifest(src)
    if not bundled_files:
        print(
            f"ERROR: Bundled shared source is empty: {src}",
            file=sys.stderr,
        )
        return 1

    if force_shared:
        if shared_dest.exists():
            shutil.rmtree(shared_dest)
        shared_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, shared_dest)
        agents_target.mkdir(parents=True, exist_ok=True)
        for name in SHARED_TRIO_AGENT_FILES:
            agent_src = src / "agents" / name
            if agent_src.is_file():
                shutil.copy2(agent_src, agents_target / name)
        write_manifest(lock_path, _shared_deployed_manifest(shared_dest, agents_target))
        print(
            f"Force-installed 'shared' → {shared_dest} (trio agents → {agents_target})"
        )
        return 0

    existing = read_manifest(lock_path)

    if existing is None:
        if shared_dest.exists() and any(shared_dest.iterdir()):
            print(
                f"ERROR: {shared_dest} exists but no shared.lock found at "
                f"{lock_path}. Pass --force-shared to take ownership.",
                file=sys.stderr,
            )
            return 1
        shared_dest.parent.mkdir(parents=True, exist_ok=True)
        if shared_dest.exists():
            shutil.rmtree(shared_dest)
        shutil.copytree(src, shared_dest)
        agents_target.mkdir(parents=True, exist_ok=True)
        for name in SHARED_TRIO_AGENT_FILES:
            agent_src = src / "agents" / name
            if agent_src.is_file():
                shutil.copy2(agent_src, agents_target / name)
        write_manifest(lock_path, _shared_deployed_manifest(shared_dest, agents_target))
        print(f"Installed 'shared' → {shared_dest}")
        return 0

    warnings: list[str] = []
    updated: dict[str, str] = {}

    # Reconcile every bundled file under skills/shared/.
    for rel, bundled_hash in bundled_files.items():
        key = f"skills/shared/{rel}"
        deploy = shared_dest / rel
        manifest_hash = existing.get(key)
        disk_hash = sha256_of_file(deploy) if deploy.is_file() else None
        action = decide_action(bundled_hash, manifest_hash, disk_hash)

        if action == "idempotent":
            updated[key] = bundled_hash
        elif action in ("fresh", "safe_upgrade", "user_deleted"):
            deploy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / rel, deploy)
            updated[key] = bundled_hash
            if action == "user_deleted":
                warnings.append(f"restored user-deleted {key}")
        elif action == "user_modified":
            warnings.append(f"preserved user-modified {key}")
            updated[key] = manifest_hash or bundled_hash

    # Reconcile the trio fan-out into <host_root>/agents/.
    for name in SHARED_TRIO_AGENT_FILES:
        agent_src = src / "agents" / name
        if not agent_src.is_file():
            continue
        bundled_hash = sha256_of_file(agent_src)
        key = f"agents/{name}"
        deploy = agents_target / name
        manifest_hash = existing.get(key)
        disk_hash = sha256_of_file(deploy) if deploy.is_file() else None
        action = decide_action(bundled_hash, manifest_hash, disk_hash)

        if action == "idempotent":
            updated[key] = bundled_hash
        elif action in ("fresh", "safe_upgrade", "user_deleted"):
            agents_target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(agent_src, deploy)
            updated[key] = bundled_hash
            if action == "user_deleted":
                warnings.append(f"restored user-deleted {key}")
        elif action == "user_modified":
            warnings.append(f"preserved user-modified {key}")
            updated[key] = manifest_hash or bundled_hash

    # Handle entries that were in the prior manifest but no longer in the
    # bundle (upstream removed). Remove cleanly if on-disk hash matches the
    # manifest; otherwise preserve the user's copy and keep tracking it.
    for stale_key, stale_hash in existing.items():
        if stale_key in updated:
            continue
        if stale_key.startswith("skills/shared/"):
            rel = stale_key.removeprefix("skills/shared/")
            disk = shared_dest / rel
        elif stale_key.startswith("agents/"):
            disk = agents_target / stale_key.removeprefix("agents/")
        else:
            continue
        if not disk.is_file():
            continue  # already gone, drop silently
        disk_hash = sha256_of_file(disk)
        if disk_hash == stale_hash:
            disk.unlink()
        else:
            warnings.append(
                f"preserved user-modified {stale_key} (no longer in bundle)"
            )
            updated[stale_key] = stale_hash

    write_manifest(lock_path, updated)

    for w in warnings:
        print(f"WARNING: {w}; pass --force-shared to overwrite.", file=sys.stderr)
    print(
        f"Reinstalled 'shared' → {shared_dest} "
        f"({len(updated)} files tracked, {len(warnings)} preserved)"
    )
    return 0


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


def install_entrypoint(
    name: str,
    host: str,
    scope: str,
    cwd: Path | None = None,
    overwrite: bool = False,
    force_shared: bool = False,
    skip_deps: bool = False,
    backup: bool = True,
    interactive: bool = True,
) -> int:
    """Unified installer for skills and agents with backup, staging, and overwrite policies."""
    # Determine if name is a skill or agent
    bundled_skills = list_bundled_skills()
    bundled_agents = list_bundled_agents()
    is_skill = name in bundled_skills
    is_agent = name in bundled_agents
    if not (is_skill or is_agent):
        print(f"ERROR: '{name}' not found as skill or agent.", file=sys.stderr)
        return 1
    # Resolve install target
    if is_skill:
        target_dir = resolve_target(host, scope, cwd or Path.cwd()) / name
    else:
        target_dir = (
            resolve_agent_target(host, scope, cwd or Path.cwd()) / f"{name}.agent.md"
        )
    # Backup if requested and target exists
    if backup and target_dir.exists():
        backup_paths([target_dir])
    # Prompt if not overwrite and exists
    if target_dir.exists() and not overwrite:
        if interactive and not prompt_confirmation(f"Overwrite {target_dir}?"):
            print("Install cancelled by user.")
            return 1
    # Use staging for atomic install
    with stage_dir():
        if is_skill:
            rc = install_skill(
                name,
                host,
                scope,
                cwd,
                overwrite=True,
                force_shared=force_shared,
                skip_deps=skip_deps,
            )
        else:
            rc = install_agent(
                name, host, scope, cwd, overwrite=True, skip_deps=skip_deps
            )
        if rc != 0:
            print(f"ERROR: Failed to install {name}.", file=sys.stderr)
            return rc
    return 0


def install_skill(
    skill_name: str,
    host: str,
    scope: str,
    cwd: Path | None = None,
    overwrite: bool = False,
    force_shared: bool = False,
    skip_deps: bool = False,
) -> int:
    """Copy a bundled skill to the target directory.

    Dependencies declared in the skill's SKILL.md frontmatter are installed
    first. The ``shared`` dependency uses a manifest-aware install path that
    preserves user edits to examples, the fanned trio agents, and other
    shared files; pass ``force_shared=True`` to bypass that protection. All
    other dependencies install with ``overwrite=True`` (idempotent for the
    framework-owned content they ship).

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
    cwd_resolved = cwd or Path.cwd()

    # The ``shared`` skill has a different install discipline: it ships
    # user-editable surface (examples + trio agents) and we must not clobber
    # local edits silently.
    if skill_name == "shared":
        shared_dest = resolve_target(host, scope, cwd_resolved) / "shared"
        agents_target = resolve_agent_target(host, scope, cwd_resolved)
        lock_path = _shared_lock_path(host, scope, cwd_resolved)
        return _install_shared(src, shared_dest, agents_target, lock_path, force_shared)

    # Auto-install dependencies before copying this skill.
    if not skip_deps:
        for dep in _read_skill_dependencies(src):
            if dep == "shared":
                dep_rc = install_skill(dep, host, scope, cwd, force_shared=force_shared)
            else:
                dep_rc = install_skill(dep, host, scope, cwd, overwrite=True)
            if dep_rc != 0:
                print(
                    f"ERROR: Failed to install dependency '{dep}' for '{skill_name}'",
                    file=sys.stderr,
                )
                return 1

    target_dir = resolve_target(host, scope, cwd_resolved)
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
    force_shared: bool = False,
    backup: bool = True,
    interactive: bool = True,
) -> int:
    """Install all bundled skills to the target host and scope.

    Always uses overwrite=True internally for non-``shared`` skills: shared
    dependencies are installed by multiple skills' dep resolution before the
    direct loop reaches them, so idempotency requires treating every install
    as a replacement. The ``shared`` skill itself follows the manifest-aware
    install path; pass ``force_shared=True`` to override its edit protection.

    Returns 0 if all skills install successfully, 1 if any skill fails.
    """
    results: list[tuple[str, int]] = []
    for skill_name in list_bundled_skills():
        rc = install_entrypoint(
            skill_name,
            host,
            scope,
            cwd,
            overwrite=True,
            force_shared=force_shared,
            backup=backup,
            interactive=interactive,
        )
        results.append((skill_name, rc))
    failed = [name for name, rc in results if rc != 0]
    if failed:
        print(f"ERROR: Failed to install: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def _parse_agent_family(path: Path) -> str | None:
    """Parse a bundled agent file for a top-level `family: <name>` field.

    Looks in the YAML frontmatter if present, otherwise scans the first 40
    lines for a `family:` key. Returns the family name or None if not found.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    # Frontmatter style: ---\nkey: value\n---
    parts = text.split("---", 2)
    fm = parts[1] if len(parts) >= 3 else "\n".join(text.splitlines()[:40])
    for line in fm.splitlines():
        line = line.strip()
        if line.startswith("family:"):
            _, val = line.split(":", 1)
            return val.strip()
    return None


def install_agent(
    agent_name: str,
    host: str,
    scope: str,
    cwd: Path | None = None,
    overwrite: bool = False,
    skip_deps: bool = False,
) -> int:
    """Copy a bundled agent definition file to the target agents directory.

    When an agent declares a `family: <name>` field in its frontmatter, install
    will expand and deploy all agents that share the same family name. This
    allows a single request like ``--agent universal-plan`` to install an
    orchestrator plus its companion agents.

    Returns 0 on success, 1 on error.
    """
    available = list_bundled_agents()
    if agent_name not in available:
        print(
            f"ERROR: Agent '{agent_name}' not found. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        return 1

    agents_dir = get_bundled_agents_dir()
    src = agents_dir / f"{agent_name}.agent.md"

    # Determine if this agent is part of a family. If so, collect all members.
    family = _parse_agent_family(src)
    to_install: list[str]
    if family:
        to_install = []
        for child in agents_dir.iterdir():
            if (
                not child.is_file()
                or child.suffix != ".md"
                or not child.stem.endswith(".agent")
            ):
                continue
            f = _parse_agent_family(child)
            if f == family:
                to_install.append(child.stem.removesuffix(".agent"))
        # Always ensure the requested agent is present and preserve ordering
        if agent_name not in to_install:
            to_install.append(agent_name)
        to_install = sorted(dict.fromkeys(to_install))
    else:
        to_install = [agent_name]

    target_dir = resolve_agent_target(host, scope, cwd or Path.cwd())
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    for name in to_install:
        src_path = agents_dir / f"{name}.agent.md"
        if not src_path.is_file():
            print(f"ERROR: Agent source not found: {src_path}", file=sys.stderr)
            return 1
        dest = target_dir / f"{name}.agent.md"
        if dest.exists():
            if not overwrite:
                print(
                    f"Skipped '{name}' (exists at {dest}); pass --overwrite to replace.",
                    file=sys.stderr,
                )
                continue
            dest.unlink()
        shutil.copy2(src_path, dest)
        installed.append(dest)
        print(f"Installed '{name}' → {dest}")

    if not installed:
        print("No agents were installed.", file=sys.stderr)
        return 1
    # Success
    return 0
