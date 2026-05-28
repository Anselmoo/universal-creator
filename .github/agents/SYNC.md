Syncing .github/agents -> agents
================================

This repository keeps canonical agent definitions under `.github/agents` and mirrors them into the repository root `agents/` directory through a local `pre-commit` hook.

Usage
-----

- Install `pre-commit` once in your clone if you have not already:

```bash
pre-commit install
```

- The sync runs automatically on commit via the local hook defined in `.pre-commit-config.yaml`.
- You can also run it manually at any time:

```bash
python scripts/sync_agents.py
```

Behavior
--------

- The local hook copies files from `.github/agents/` into `agents/` before each commit.
- The mirrored `agents/` directory intentionally excludes this `SYNC.md` note.

Notes
-----

- There is no separate `.githooks/` setup anymore; `pre-commit` owns the sync flow.
- If you need to refresh `agents/` without committing, run the manual sync command above.
