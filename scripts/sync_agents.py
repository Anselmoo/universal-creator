#!/usr/bin/env python3
"""Mirror `.github/agents` into `agents`.

This script is intended to run from pre-commit so the mirrored `agents/`
directory stays in sync before commits.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("SYNC.md"),
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / ".github" / "agents"
    destination = repo_root / "agents"

    if not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")

    _copy_tree(source, destination)
    print(
        f"Synced {source.relative_to(repo_root)} -> {destination.relative_to(repo_root)}"
    )


if __name__ == "__main__":
    main()
