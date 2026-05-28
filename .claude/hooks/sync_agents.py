#!/usr/bin/env python3
"""Mirror `.github/agents` into `agents` for local agent discovery parity."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sync_agents() -> int:
    root = _repo_root()
    src_dir = root / ".github" / "agents"
    dst_dir = root / "agents"

    if not src_dir.is_dir():
        print(f"sync_agents: source directory missing: {src_dir}", file=sys.stderr)
        return 1

    dst_dir.mkdir(parents=True, exist_ok=True)

    src_files = sorted(src_dir.glob("*.agent.md"))
    src_names = {p.name for p in src_files}

    copied = 0
    unchanged = 0

    for src in src_files:
        dst = dst_dir / src.name
        if dst.exists() and src.read_bytes() == dst.read_bytes():
            unchanged += 1
            continue
        shutil.copy2(src, dst)
        copied += 1

    removed = 0
    for dst in sorted(dst_dir.glob("*.agent.md")):
        if dst.name not in src_names:
            dst.unlink()
            removed += 1

    print(
        f"sync_agents: copied={copied} unchanged={unchanged} removed={removed} "
        f"source={src_dir} target={dst_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(sync_agents())
