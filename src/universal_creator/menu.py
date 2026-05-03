"""Interactive terminal menu using Rich.

Invoked when ``universal-creator`` is run without a subcommand,
or explicitly via ``universal-creator menu`` / ``poe menu``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import questionary
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from universal_creator import __version__

console = Console()


# ── helpers ───────────────────────────────────────────────────────────────────


def _header() -> None:
    console.print(
        Panel.fit(
            f"[bold cyan]universal-creator[/bold cyan]  [dim]v{__version__}[/dim]",
            subtitle="[dim]skill scaffolding & installation[/dim]",
        )
    )


def _ask(prompt: str, choices: list[Any]) -> str:
    """Show an arrow-key select via questionary; SystemExit on cancel."""
    result = questionary.select(prompt, choices=choices).ask()
    if result is None:
        raise SystemExit(0)
    return str(result)


def _confirm(prompt: str, default: bool = True) -> bool:
    """Show a yes/no confirm via questionary; returns False on cancel."""
    result = questionary.confirm(prompt, default=default).ask()
    return bool(result)


def _confirm_replace(path: Path, kind: str) -> bool:
    """Ask whether an existing install/scaffold target should be replaced."""
    console.print(f"[yellow]{kind} already exists:[/yellow] [dim]{path}[/dim]")
    return _confirm(f"Replace existing {kind.lower()}?", default=False)


# ── option 1: install skill ───────────────────────────────────────────────────


def _menu_install() -> None:
    from universal_creator.install import install_skill, resolve_target
    from universal_creator.models import SkillInstallConfig
    from universal_creator.resources import list_bundled_skills

    available = list_bundled_skills()
    if not available:
        console.print("[red]No bundled skills found.[/red]")
        return

    console.rule("[bold]Install a skill[/bold]")

    skill = _ask("Select skill", available)
    host = cast(
        Literal["claude", "copilot"], _ask("Install for", ["claude", "copilot"])
    )
    scope = _ask(
        "Scope",
        [
            questionary.Choice("local  (current project)", value="local"),
            questionary.Choice("global (user home)", value="global"),
        ],
    )
    scope_val = cast(Literal["local", "global"], scope)

    try:
        cfg = SkillInstallConfig(skill=skill, host=host, scope=scope_val)
    except ValidationError as exc:
        console.print(f"[red]Validation error:[/red] {exc}")
        return

    dest_label = (
        f"[dim].{host}/skills/{skill}/[/dim]"
        if scope_val == "local"
        else f"[dim]~/.{host}/skills/{skill}/[/dim]"
    )
    dest = resolve_target(cfg.host, cfg.scope, cwd=Path.cwd()) / cfg.skill
    console.print(f"\nInstall [bold]{skill}[/bold] → {dest_label}")
    overwrite = False
    if dest.exists():
        if not _confirm_replace(dest, "installation"):
            console.print("[dim]Cancelled.[/dim]")
            return
        overwrite = True
    elif not _confirm("Proceed?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    code = install_skill(
        cfg.skill, cfg.host, cfg.scope, cwd=Path.cwd(), overwrite=overwrite
    )
    if code == 0:
        console.print("[green]Done.[/green]")


# ── option 2: install agent ───────────────────────────────────────────────────


def _menu_install_agent() -> None:
    from universal_creator.install import install_agent, resolve_agent_target
    from universal_creator.models import AgentInstallConfig
    from universal_creator.resources import list_bundled_agents

    available = list_bundled_agents()
    if not available:
        console.print("[red]No bundled agents found.[/red]")
        return

    console.rule("[bold]Install an agent[/bold]")

    agent = _ask("Select agent", available)
    host = cast(
        Literal["claude", "copilot"], _ask("Install for", ["claude", "copilot"])
    )
    scope = _ask(
        "Scope",
        [
            questionary.Choice("local  (current project)", value="local"),
            questionary.Choice("global (user home)", value="global"),
        ],
    )
    scope_val = cast(Literal["local", "global"], scope)

    try:
        cfg = AgentInstallConfig(agent=agent, host=host, scope=scope_val)
    except ValidationError as exc:
        console.print(f"[red]Validation error:[/red] {exc}")
        return

    dest_label = (
        f"[dim].{host}/agents/{agent}.agent.md[/dim]"
        if scope_val == "local"
        else f"[dim]~/.{host}/agents/{agent}.agent.md[/dim]"
    )
    dest = (
        resolve_agent_target(cfg.host, cfg.scope, cwd=Path.cwd())
        / f"{cfg.agent}.agent.md"
    )
    console.print(f"\nInstall [bold]{agent}[/bold] → {dest_label}")
    overwrite = False
    if dest.exists():
        if not _confirm_replace(dest, "installation"):
            console.print("[dim]Cancelled.[/dim]")
            return
        overwrite = True
    elif not _confirm("Proceed?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    code = install_agent(
        cfg.agent, cfg.host, cfg.scope, cwd=Path.cwd(), overwrite=overwrite
    )
    if code == 0:
        console.print("[green]Done.[/green]")


# ── option 3: scaffold new skill ─────────────────────────────────────────────


def _menu_scaffold() -> None:
    from universal_creator.generate import scaffold_skill
    from universal_creator.models import ScaffoldConfig

    console.rule("[bold]Create a new skill[/bold]")

    raw_name = questionary.text("Skill name (kebab-case)").ask()
    if raw_name is None:
        return

    try:
        cfg = ScaffoldConfig(name=raw_name)
    except ValidationError as exc:
        console.print(f"[red]{exc.errors()[0]['msg']}[/red]")
        return

    mode = _ask(
        "Scaffold mode",
        [
            questionary.Choice(
                "empty      (SKILL.md stub + requirements.txt only)", value="empty"
            ),
            questionary.Choice(
                "boilerplate (full scaffold with scripts + agent stubs)",
                value="boilerplate",
            ),
        ],
    )

    console.print(
        f"\nCreate [bold]{cfg.name}[/bold] "
        f"([dim]{mode}[/dim]) in [dim]skills/{cfg.name}/[/dim]"
    )
    skill_dir = Path("skills") / cfg.name
    overwrite = False
    if skill_dir.exists():
        if not _confirm_replace(skill_dir.resolve(), "scaffold target"):
            console.print("[dim]Cancelled.[/dim]")
            return
        overwrite = True
    elif not _confirm("Proceed?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    code = scaffold_skill(cfg.name, mode, overwrite=overwrite)
    if code == 0:
        console.print("[green]Done.[/green]")


# ── main entry point ──────────────────────────────────────────────────────────


def run_menu() -> None:
    _header()

    console.print()
    choice = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice(
                "Install a skill  (Claude / GitHub Copilot · local / global)",
                value="install",
            ),
            questionary.Choice(
                "Install an agent  (Claude / GitHub Copilot · local / global)",
                value="install-agent",
            ),
            questionary.Choice(
                "Create a new skill  (empty boilerplate)", value="scaffold"
            ),
            questionary.Choice("Quit", value="quit"),
        ],
    ).ask()

    if choice is None or choice == "quit":
        raise SystemExit(0)
    elif choice == "install":
        _menu_install()
    elif choice == "install-agent":
        _menu_install_agent()
    else:
        _menu_scaffold()
