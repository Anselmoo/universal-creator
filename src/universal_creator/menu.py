"""Interactive terminal menu using Rich.

Invoked when ``universal-creator`` is run without a subcommand,
or explicitly via ``universal-creator menu`` / ``poe menu``.
"""

from __future__ import annotations

from pathlib import Path

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


def _ask(prompt: str, choices: list[str]) -> str:
    """Show an arrow-key select via questionary; SystemExit on cancel."""
    result = questionary.select(prompt, choices=choices).ask()
    if result is None:
        raise SystemExit(0)
    return result


def _confirm(prompt: str, default: bool = True) -> bool:
    """Show a yes/no confirm via questionary; returns False on cancel."""
    result = questionary.confirm(prompt, default=default).ask()
    return bool(result)


# ── option 1: install skill ───────────────────────────────────────────────────


def _menu_install() -> None:
    from universal_creator.install import install_skill
    from universal_creator.models import SkillInstallConfig
    from universal_creator.resources import list_bundled_skills

    available = list_bundled_skills()
    if not available:
        console.print("[red]No bundled skills found.[/red]")
        return

    console.rule("[bold]Install a skill[/bold]")

    skill = _ask("Select skill", available)
    host = _ask("Install for", ["claude", "copilot"])
    scope = _ask(
        "Scope",
        [
            questionary.Choice("local  (current project)", value="local"),
            questionary.Choice("global (user home)", value="global"),
        ],
    )
    scope_val = scope  # validated against Literal["local", "global"] by Choice values

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
    console.print(f"\nInstall [bold]{skill}[/bold] → {dest_label}")
    if not _confirm("Proceed?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    code = install_skill(cfg.skill, cfg.host, cfg.scope, cwd=Path.cwd())
    if code == 0:
        console.print("[green]Done.[/green]")


# ── option 2: scaffold new skill ─────────────────────────────────────────────


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
    if not _confirm("Proceed?", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return

    code = scaffold_skill(cfg.name, mode, overwrite=False)
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
                "Create a new skill  (empty boilerplate)", value="scaffold"
            ),
            questionary.Choice("Quit", value="quit"),
        ],
    ).ask()

    if choice is None or choice == "quit":
        raise SystemExit(0)
    elif choice == "install":
        _menu_install()
    else:
        _menu_scaffold()
