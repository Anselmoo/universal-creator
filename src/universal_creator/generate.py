"""Skill scaffolding engine for universal-creator.

Two modes:
  empty       — SKILL.md stub + requirements.txt only (minimal skeleton)
  boilerplate — Full scaffold: scripts copied from canonical skill, stub
                agents/evals/examples/references/templates/assets created.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

try:
    from jinja2 import Environment, PackageLoader, select_autoescape

    _HAS_JINJA2 = True
except ImportError:
    _HAS_JINJA2 = False

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TEMPLATES_DIR = Path(__file__).resolve().parent / "_templates"
_CANONICAL_SKILL = "agent-generator"

# Sub-directories created in every scaffold mode
_EMPTY_DIRS = [
    "agents",
    "assets",
    "evals",
    "eval-viewer",
    "examples",
    "references",
    "scripts",
    "templates",
]

# Files rendered from Jinja2 templates for empty mode
_EMPTY_TEMPLATES = {
    "SKILL.md": "skill/SKILL.md.j2",
    "requirements.txt": "skill/requirements.txt.j2",
}

# Additional files rendered for boilerplate mode
_BOILERPLATE_TEMPLATES = {
    "agents/analyzer.md": "skill/agents/analyzer.md.j2",
    "agents/comparator.md": "skill/agents/comparator.md.j2",
    "agents/grader.md": "skill/agents/grader.md.j2",
    "evals/evals.json": "skill/evals/evals.json.j2",
}


def _get_jinja_env() -> "Environment":
    if not _HAS_JINJA2:
        print(
            "ERROR: jinja2 is not installed. Run `uv sync` or `pip install jinja2`",
            file=sys.stderr,
        )
        sys.exit(1)
    return Environment(
        loader=PackageLoader("universal_creator", "_templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )


def _render_template(env: "Environment", template_path: str, ctx: dict) -> str:
    tmpl = env.get_template(template_path)
    return tmpl.render(**ctx)


def scaffold_skill(
    name: str,
    mode: str = "empty",
    output_dir: str | None = None,
    overwrite: bool = False,
    host: str | None = None,
    scope: str = "local",
) -> int:
    """Create a new skill directory under output_dir/name.

    If output_dir is None and host is provided, derive a host-aware default
    path (e.g. .claude/skills, .github/skills, .agents/skills) via
    universal_creator.install.get_default_skill_output_dir.

    Returns 0 on success, 1 on error.
    """
    # Determine actual output_dir when not provided
    if output_dir is None:
        if host:
            try:
                from universal_creator.install import get_default_skill_output_dir

                default_path = get_default_skill_output_dir(host, scope, name)
                output_dir = str(default_path)
            except Exception:
                # Fallback to legacy 'skills' when anything goes wrong
                output_dir = "skills"
        else:
            output_dir = "skills"

    skill_dir = _REPO_ROOT / output_dir / name

    if skill_dir.exists():
        if not overwrite:
            print(
                f"ERROR: {skill_dir} already exists. Pass --overwrite to replace.",
                file=sys.stderr,
            )
            return 1
        shutil.rmtree(skill_dir)
        print(f"Removed existing {skill_dir}")

    skill_dir.mkdir(parents=True)
    for sub in _EMPTY_DIRS:
        (skill_dir / sub).mkdir()

    env = _get_jinja_env()
    ctx = {"name": name, "mode": mode}

    for rel_path, template_path in _EMPTY_TEMPLATES.items():
        dest = skill_dir / rel_path
        dest.write_text(_render_template(env, template_path, ctx))
        print(f"  created {dest.relative_to(_REPO_ROOT)}")

    if mode == "boilerplate":
        _scaffold_boilerplate(skill_dir, name, env, ctx)

    print(f"\nScaffolded '{name}' ({mode}) at {skill_dir.relative_to(_REPO_ROOT)}")
    return 0


def _scaffold_boilerplate(
    skill_dir: Path, name: str, env: "Environment", ctx: dict
) -> None:
    """Populate the boilerplate scaffold: copy canonical scripts, render stubs."""
    # Render stub agents / evals
    for rel_path, template_path in _BOILERPLATE_TEMPLATES.items():
        dest = skill_dir / rel_path
        dest.write_text(_render_template(env, template_path, ctx))
        print(f"  created {dest.relative_to(_REPO_ROOT)}")

    # Copy scripts from canonical skill
    canonical_scripts = _REPO_ROOT / "skills" / _CANONICAL_SKILL / "scripts"
    if not canonical_scripts.is_dir():
        print(
            f"WARNING: canonical scripts directory not found at {canonical_scripts}",
            file=sys.stderr,
        )
        return

    dest_scripts = skill_dir / "scripts"
    for src_file in sorted(canonical_scripts.glob("*.py")):
        dest_file = dest_scripts / src_file.name
        shutil.copy2(src_file, dest_file)
        print(f"  copied  {dest_file.relative_to(_REPO_ROOT)}")
