import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from universal_creator.resources import list_bundled_agents, list_bundled_skills


def backup_paths(paths: List[Path], backup_root: Path) -> Path:
    """
    Create a timestamped backup directory under backup_root and copy given files/dirs there.
    Returns the backup directory path.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for p in paths:
        dest = backup_dir / p.name
        if p.is_dir():
            shutil.copytree(p, dest)
        elif p.is_file():
            shutil.copy2(p, dest)
    return backup_dir


@contextmanager
def stage_dir():
    """
    Context manager for a temporary staging directory. Yields Path. Cleans up on exit.
    """
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def resolve_install_target(name: str) -> Tuple[str, str]:
    """
    If name is a bundled skill, return ("skill", name). If agent, return ("agent", name). Else raise ValueError.
    """
    skills = list_bundled_skills()
    agents = list_bundled_agents()
    if name in skills:
        return ("skill", name)
    elif name in agents:
        return ("agent", name)
    raise ValueError(f"No bundled skill or agent named '{name}'")


def prompt_confirmation(
    summary: str, default: bool = True, force: bool = False
) -> bool:
    """
    Interactive prompt for confirmation. If not a tty or force is True, auto-confirm.
    """
    if force or not sys.stdin.isatty():
        return default
    prompt = f"{summary} [{'Y/n' if default else 'y/N'}]: "
    while True:
        resp = input(prompt).strip().lower()
        if not resp:
            return default
        if resp in ("y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
