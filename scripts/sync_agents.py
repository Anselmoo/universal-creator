#!/usr/bin/env python3
"""Mirror `.github/agents` into the consumer directories.

Run from pre-commit so all mirrors stay in sync before commits.

Two fan-outs:

1. ``.github/agents/`` → ``agents/`` (repo-root mirror, all files, excluding
   ``SYNC.md``). Consumed by the IDE / agents-folder convention.

2. The reusable trio + shared memory-guardrails snippet are also copied from
   ``.github/agents/`` into ``skills/shared/agents/`` so the universal-creator
   CLI can ship them as part of the ``shared`` skill dependency. The list is
   the ``SHARED_TRIO`` constant below; add to it when a new agent becomes
   eligible for reuse across generator skills.

The canonical source of truth for every agent file is ``.github/agents/``;
the mirrors are sync targets and should not be hand-edited.
"""

from __future__ import annotations

import shutil
from pathlib import Path

SHARED_TRIO: tuple[str, ...] = (
    "validation-reviewer.agent.md",
    "artifact-router.agent.md",
    "prompt-strategist.agent.md",
    "_memory-guardrails.md",
)


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("SYNC.md"),
    )


def _fan_out_shared(source: Path, destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    existing = {p.name for p in destination.iterdir() if p.is_file()}
    desired = set(SHARED_TRIO)

    for stale_name in existing - desired:
        (destination / stale_name).unlink()

    copied: list[str] = []
    for name in SHARED_TRIO:
        src_file = source / name
        if not src_file.is_file():
            raise SystemExit(
                f"Expected shared agent file not found in {source}: {name}"
            )
        shutil.copy2(src_file, destination / name)
        copied.append(name)
    return copied


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / ".github" / "agents"
    repo_mirror = repo_root / "agents"
    shared_mirror = repo_root / "skills" / "shared" / "agents"

    if not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")

    _copy_tree(source, repo_mirror)
    print(
        f"Synced {source.relative_to(repo_root)} -> "
        f"{repo_mirror.relative_to(repo_root)}"
    )

    copied = _fan_out_shared(source, shared_mirror)
    print(
        f"Fanned {len(copied)} shared file(s) -> "
        f"{shared_mirror.relative_to(repo_root)}: {', '.join(copied)}"
    )


if __name__ == "__main__":
    main()
