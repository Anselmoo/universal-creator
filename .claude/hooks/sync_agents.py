#!/usr/bin/env python3
"""Mirror agent files across repository agent roots.

This script ensures agent files present in any recognized agent root
(`.github/agents`, `.claude/agents`, `agents`, `.codex/agents`, `.gemini/agents`)
are copied into other existing roots. It is conservative: files are added/updated
but not removed to avoid accidental deletions.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_agent_dirs(root: Path) -> List[Path]:
    return [
        root / ".github" / "agents",
        root / ".claude" / "agents",
        root / "agents",
        root / ".codex" / "agents",
        root / ".gemini" / "agents",
    ]


def sync_agents() -> int:
    root = _repo_root()
    candidate_dirs = _candidate_agent_dirs(root)

    # Gather existing dirs and all agent files found across them
    existing_dirs = [d for d in candidate_dirs if d.exists() and d.is_dir()]
    if not existing_dirs:
        print("sync_agents: no agent directories found; nothing to do", file=sys.stderr)
        return 0

    union_files = {}
    for d in existing_dirs:
        for p in d.glob("*.agent.md"):
            try:
                data = p.read_bytes()
            except OSError:
                continue
            union_files[p.name] = data

    if not union_files:
        print(
            "sync_agents: no agent files found in existing agent roots", file=sys.stderr
        )
        return 0

    copied = 0
    updated = 0
    skipped = 0

    # Ensure every existing dir contains all union files
    for d in existing_dirs:
        d.mkdir(parents=True, exist_ok=True)
        for name, data in union_files.items():
            dst = d / name
            if dst.exists():
                try:
                    existing = dst.read_bytes()
                except OSError:
                    existing = None
                if existing == data:
                    skipped += 1
                    continue
                # update
                try:
                    dst.write_bytes(data)
                    updated += 1
                except OSError:
                    print(f"sync_agents: could not update {dst}", file=sys.stderr)
            else:
                try:
                    dst.write_bytes(data)
                    copied += 1
                except OSError:
                    print(f"sync_agents: could not copy to {dst}", file=sys.stderr)

    print(
        f"sync_agents: copied={copied} updated={updated} skipped={skipped} "
        f"roots={len(existing_dirs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(sync_agents())
