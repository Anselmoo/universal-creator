"""CLI entry point — powered by Typer.

Usage (after ``uv sync``):
    universal-creator              # opens interactive menu
    universal-creator menu         # same
    universal-creator new-skill --name my-skill --mode empty
    universal-creator install --skill agent-generator --host copilot --scope global
    universal-creator sync [--from agent-generator]
    universal-creator package --skill NAME
    universal-creator eval --skill NAME
    poe menu / poe new-skill / poe install-skill / ...
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Annotated, Literal, Optional, cast

import typer
from pydantic import ValidationError

app = typer.Typer(
    name="universal-creator",
    help="Skill scaffolding and artifact generation for VS Code Copilot / Claude / Gemini / Codex agents.",
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
)


# ── fallback to menu when called with no subcommand ───────────────────────────


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        from universal_creator.menu import run_menu

        run_menu()


# ── menu (explicit) ───────────────────────────────────────────────────────────


@app.command("menu")
def cmd_menu() -> None:
    """Open the interactive skill menu."""
    from universal_creator.menu import run_menu

    run_menu()


# ── new-skill ─────────────────────────────────────────────────────────────────


@app.command("new-skill")
def cmd_new_skill(
    name: Annotated[str, typer.Option("--name", "-n", help="Skill name (kebab-case)")],
    mode: Annotated[
        str, typer.Option("--mode", "-m", help="empty | boilerplate")
    ] = "empty",
    host: Annotated[
        str, typer.Option("--host", help="claude | copilot | gemini | codex")
    ] = "claude",
    scope: Annotated[str, typer.Option("--scope", help="local | global")] = "local",
    output_dir: Annotated[
        str | None, typer.Option("--output-dir", help="Parent dir (default: host-specific)")
    ] = None,
    ask_location: Annotated[
        bool, typer.Option("--ask-location/--no-ask-location", help="Ask where to write the skill interactively")
    ] = False,
    remember: Annotated[
        bool, typer.Option("--remember/--no-remember", help="Remember chosen location for next time")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite/--no-overwrite", help="Replace existing skill")
    ] = False,
) -> None:
    """Scaffold a new skill directory. By default, writes to a host-appropriate repo-local path (e.g. .claude/skills/)."""
    from universal_creator.generate import scaffold_skill
    from universal_creator.models import ScaffoldConfig

    # Determine default output_dir based on host/scope when not explicitly provided
    if output_dir is None:
        from universal_creator.install import get_default_skill_output_dir

        default_path = get_default_skill_output_dir(host, scope, name)

        # Interactive prompt when requested
        if ask_location:
            typer.echo("Choose where to write the new skill:")
            opts = [str(default_path), str(default_path / "skills")]
            for i, o in enumerate(opts, start=1):
                typer.echo(f"  {i}. {o}")
            choice = typer.prompt("Enter choice number (or custom path)")
            # simple numeric selection
            if choice.isdigit() and 1 <= int(choice) <= len(opts):
                output_dir = opts[int(choice) - 1]
            else:
                output_dir = choice

            if remember:
                try:
                    import json

                    cfg_path = Path.home() / ".universal_creator_choices.json"
                    data = {"last_output_dir": output_dir}
                    cfg_path.write_text(json.dumps(data))
                except Exception:
                    typer.echo("Warning: failed to persist choice", err=True)
        else:
            # non-interactive default
            output_dir = str(default_path)

    try:
        cfg = ScaffoldConfig(
            name=name,
            mode=cast(Literal["empty", "boilerplate"], mode),
            output_dir=output_dir,
            overwrite=overwrite,
        )
    except ValidationError as exc:
        typer.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        raise typer.Exit(1)

    # Pass host/scope through so scaffold_skill can derive host-aware defaults
    raise typer.Exit(scaffold_skill(cfg.name, cfg.mode, cfg.output_dir, cfg.overwrite, host=host, scope=scope))


# ── install ───────────────────────────────────────────────────────────────────


@app.command("install")
def cmd_install(
    skill: Annotated[str, typer.Option("--skill", "-s", help="Skill name to install")],
    host: Annotated[
        str, typer.Option("--host", help="claude | copilot | gemini | codex")
    ] = "copilot",
    scope: Annotated[str, typer.Option("--scope", help="local | global")] = "local",
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
) -> None:
    """Install a bundled skill to Claude, Copilot, Gemini, or Codex."""
    from universal_creator.install import install_skill
    from universal_creator.models import SkillInstallConfig

    try:
        cfg = SkillInstallConfig(
            skill=skill,
            host=cast(Literal["claude", "copilot", "gemini", "codex"], host),
            scope=cast(Literal["local", "global"], scope),
            overwrite=overwrite,
        )
    except ValidationError as exc:
        typer.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        raise typer.Exit(1)

    raise typer.Exit(
        install_skill(cfg.skill, cfg.host, cfg.scope, Path.cwd(), cfg.overwrite)
    )


# ── install-agent ─────────────────────────────────────────────────────────────


@app.command("install-agent")
def cmd_install_agent(
    agent: Annotated[str, typer.Option("--agent", "-a", help="Agent name to install")],
    host: Annotated[
        str, typer.Option("--host", help="claude | copilot | gemini | codex")
    ] = "claude",
    scope: Annotated[str, typer.Option("--scope", help="local | global")] = "local",
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
) -> None:
    """Install a bundled agent definition to Claude, Copilot, Gemini, or Codex."""
    from universal_creator.install import install_agent
    from universal_creator.models import AgentInstallConfig

    try:
        cfg = AgentInstallConfig(
            agent=agent,
            host=cast(Literal["claude", "copilot", "gemini", "codex"], host),
            scope=cast(Literal["local", "global"], scope),
            overwrite=overwrite,
        )
    except ValidationError as exc:
        typer.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        raise typer.Exit(1)

    raise typer.Exit(
        install_agent(cfg.agent, cfg.host, cfg.scope, Path.cwd(), cfg.overwrite)
    )


# ── sync ──────────────────────────────────────────────────────────────────────


@app.command("sync")
def cmd_sync(
    from_skill: Annotated[
        str, typer.Option("--from", help="Canonical skill to copy scripts from")
    ] = "agent-generator",
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = True,
) -> None:
    """Sync canonical scripts from one skill to all others."""
    from universal_creator.sync import sync_scripts

    raise typer.Exit(sync_scripts(canonical=from_skill, overwrite=overwrite))


# ── package ───────────────────────────────────────────────────────────────────


@app.command("package")
def cmd_package(
    skill: Annotated[str, typer.Option("--skill", "-s", help="Skill name to package")],
) -> None:
    """Package a skill into a distributable zip (delegates to the skill's own script)."""
    script = Path("skills") / skill / "scripts" / "package_skill.py"
    if not script.exists():
        typer.echo(f"Error: {script} not found", err=True)
        raise typer.Exit(1)
    result = subprocess.run(
        [sys.executable, str(script)], cwd=str(Path("skills") / skill)
    )
    raise typer.Exit(result.returncode)


# ── eval ──────────────────────────────────────────────────────────────────────


@app.command("eval")
def cmd_eval(
    skill: Annotated[str, typer.Option("--skill", "-s", help="Skill name to evaluate")],
) -> None:
    """Run evals for a skill (delegates to the skill's own run_eval.py)."""
    script = Path("skills") / skill / "scripts" / "run_eval.py"
    if not script.exists():
        typer.echo(f"Error: {script} not found", err=True)
        raise typer.Exit(1)
    result = subprocess.run(
        [sys.executable, str(script)], cwd=str(Path("skills") / skill)
    )
    raise typer.Exit(result.returncode)


# ── list ──────────────────────────────────────────────────────────────────────


@app.command("list")
def cmd_list(
    installed: Annotated[
        str | None,
        typer.Option(
            "--installed",
            help="Show installed skills for: claude | copilot | gemini | codex",
        ),
    ] = None,
) -> None:
    """List bundled skills, or skills already installed for a given host."""
    from universal_creator.resources import list_bundled_skills

    if installed:
        host = installed.lower()
        if host not in ("claude", "copilot", "gemini", "codex"):
            typer.echo(
                "Error: --installed must be 'claude', 'copilot', 'gemini', or 'codex'",
                err=True,
            )
            raise typer.Exit(1)
        from universal_creator.install import resolve_target

        for scope in ("local", "global"):
            target = resolve_target(host, scope)
            skills = (
                sorted(d.name for d in target.iterdir() if d.is_dir())
                if target.is_dir()
                else []
            )
            if scope == "global":
                label = (
                    "~/.agents/skills/"
                    if host in ("gemini", "codex")
                    else f"~/.{host}/skills/"
                )
            elif host == "copilot":
                label = ".github/skills/"
            elif host in ("gemini", "codex"):
                label = ".agents/skills/"
            else:
                label = f".{host}/skills/"
            typer.echo(f"\n{label}")
            for s in skills:
                typer.echo(f"  {s}")
            if not skills:
                typer.echo("  (none)")
    else:
        typer.echo("Bundled skills:")
        for s in list_bundled_skills():
            typer.echo(f"  {s}")


# ── entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    app()
