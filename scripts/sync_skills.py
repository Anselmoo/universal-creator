#!/usr/bin/env python3
"""Mirror `skills/` into `.github/skills/`.

This keeps the GitHub-visible copy in sync with the repository's canonical
skill definitions.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "skills"
    destination = repo_root / ".github" / "skills"

    if not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")

    _copy_tree(source, destination)
    print(
        f"Synced {source.relative_to(repo_root)} -> {destination.relative_to(repo_root)}"
    )


if __name__ == "__main__":
    main()
