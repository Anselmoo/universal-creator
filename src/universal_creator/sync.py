"""Script parity sync: copy canonical scripts from one skill to all others.

Default canonical source: skills/agent-generator/scripts/

Only the scripts listed in _PARITY_SCRIPTS are synced.  Any scripts outside
that list (e.g. skill-specific validators like validate_hook_output.py or
generation helpers like generate_hook_stub.py) are intentionally left alone —
they live only in their respective skill and are never overwritten by sync.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SKILLS_DIR = _REPO_ROOT / "skills"
_PARITY_SCRIPTS = [
    "__init__.py",
    "aggregate_benchmark.py",
    "errors.py",
    "generate_report.py",
    "improve_description.py",
    "package_skill.py",
    "quick_validate.py",
    "run_eval.py",
    "run_loop.py",
    "utils.py",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_scripts(
    canonical: str = "agent-generator",
    overwrite: bool = True,
) -> int:
    """Copy parity-tracked scripts from canonical skill to all other skills.

    Returns 0 on success, 1 if canonical skill not found.
    """
    canonical_dir = _SKILLS_DIR / canonical / "scripts"
    if not canonical_dir.is_dir():
        print(
            f"ERROR: canonical scripts dir not found: {canonical_dir}", file=sys.stderr
        )
        return 1

    skill_dirs = [
        d for d in sorted(_SKILLS_DIR.iterdir()) if d.is_dir() and d.name != canonical
    ]

    if not skill_dirs:
        print("No other skill directories found.")
        return 0

    changed = 0
    skipped = 0

    for skill_dir in skill_dirs:
        dest_scripts = skill_dir / "scripts"
        if not dest_scripts.is_dir():
            print(
                f"  WARNING: {skill_dir.name}/scripts/ does not exist — skipping",
                file=sys.stderr,
            )
            continue

        for script_name in _PARITY_SCRIPTS:
            src = canonical_dir / script_name
            if not src.exists():
                continue
            dest = dest_scripts / script_name
            if dest.exists() and _sha256(src) == _sha256(dest):
                skipped += 1
                continue
            if dest.exists() and not overwrite:
                print(
                    f"  SKIP (overwrite=False): {skill_dir.name}/scripts/{script_name}"
                )
                skipped += 1
                continue
            shutil.copy2(src, dest)
            print(f"  synced {skill_dir.name}/scripts/{script_name}")
            changed += 1

    print(f"\nSync complete: {changed} updated, {skipped} already up-to-date")
    return 0
