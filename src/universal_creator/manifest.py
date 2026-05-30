"""Per-file SHA256 manifest for the ``shared`` skill install.

The ``shared`` skill is installed transitively by every generator skill, which
means a naive overwrite-on-reinstall (the historical behaviour) silently
clobbers any local edits a user has made to ``technique-selector.md``,
``techniques.json``, an example, or one of the fanned-out trio agents.

The manifest lets us detect those local edits and preserve them. The lock file
lives at ``<host_root>/.universal-creator/shared.lock`` where ``host_root`` is
the parent of both the host's ``skills/`` and ``agents/`` directories. Keys
are POSIX relative paths from that root, e.g.:

    skills/shared/examples/zero-shot.prompt.md
    skills/shared/agents/validation-reviewer.agent.md
    agents/validation-reviewer.agent.md   # the fanned-out deploy copy

Values are SHA256 hex digests of the file content at install time.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

MANIFEST_VERSION = 1
MANIFEST_RELATIVE_PATH = Path(".universal-creator") / "shared.lock"

Action = Literal[
    "fresh",
    "idempotent",
    "safe_upgrade",
    "user_modified",
    "user_deleted",
]


def sha256_of_file(path: Path) -> str:
    """Return the SHA256 hex digest of ``path``."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def compute_tree_manifest(root: Path) -> dict[str, str]:
    """Walk ``root`` and return ``{posix-relative-path: sha256}`` for every file."""
    if not root.is_dir():
        return {}
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rel] = sha256_of_file(path)
    return out


def read_manifest(lock_path: Path) -> dict[str, str] | None:
    """Read the ``files`` mapping from a shared.lock, or ``None`` if absent.

    Returns the inner ``files`` dict so callers can look up by manifest key
    without unwrapping the envelope every time. Returns ``None`` if the lock
    file is missing, unreadable, or malformed — callers should treat that as
    "no prior install on record".
    """
    if not lock_path.is_file():
        return None
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        files = payload.get("files")
        if isinstance(files, dict):
            return {str(k): str(v) for k, v in files.items()}
    except (json.JSONDecodeError, OSError):
        return None
    return None


def write_manifest(
    lock_path: Path, files: dict[str, str], source_sha: str = ""
) -> None:
    """Write the manifest envelope to ``lock_path``, creating parents as needed."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": MANIFEST_VERSION,
        "shared_source_sha": source_sha,
        "files": dict(sorted(files.items())),
    }
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def decide_action(
    bundled_hash: str,
    manifest_hash: str | None,
    disk_hash: str | None,
) -> Action:
    """Pick the reconciliation action for one file.

    - ``fresh``         — file is not yet on disk and not yet tracked.
    - ``idempotent``    — disk matches bundled and manifest; nothing to do.
    - ``safe_upgrade``  — bundled changed but the on-disk copy still matches
                          the prior manifest, so we can overwrite cleanly.
    - ``user_modified`` — disk diverges from manifest; the user edited it and
                          we must preserve it.
    - ``user_deleted``  — file is tracked in the manifest but missing on disk;
                          restore from bundle.
    """
    if disk_hash is None and manifest_hash is None:
        return "fresh"
    if disk_hash is None:
        return "user_deleted"
    if manifest_hash is None:
        # File exists on disk but isn't tracked. If it happens to match the
        # bundled hash we can adopt it silently; otherwise treat it as a user
        # edit so we don't blow it away.
        return "idempotent" if disk_hash == bundled_hash else "user_modified"
    if disk_hash == manifest_hash == bundled_hash:
        return "idempotent"
    if disk_hash == manifest_hash and bundled_hash != manifest_hash:
        return "safe_upgrade"
    if disk_hash != manifest_hash:
        return "user_modified"
    return "idempotent"
