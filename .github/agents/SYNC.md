Syncing .github/agents to its consumers
=======================================

This repository keeps the canonical agent definitions under `.github/agents`
and mirrors them into two consumer locations via a local `pre-commit` hook
(`scripts/sync_agents.py`).

Mirrors
-------

1. **`agents/`** (repo root) — the conventional agents folder. Receives every
   file in `.github/agents/`, excluding this `SYNC.md` note.

2. **`skills/shared/agents/`** — receives the reusable trio plus the shared
   memory-guardrails snippet so the `universal-creator` CLI can ship them as
   part of the `shared` skill dependency. The exact file list is the
   `SHARED_TRIO` constant in `scripts/sync_agents.py`:

   - `validation-reviewer.agent.md`
   - `artifact-router.agent.md`
   - `prompt-strategist.agent.md`
   - `_memory-guardrails.md`

   The other three planning-suite agents (`universal-plan`,
   `universal-explore`, `primitive-selector`) are project-level orchestrators
   and stay in `agents/` only.

Usage
-----

- Install `pre-commit` once in your clone if you have not already:

```bash
pre-commit install
```

- The sync runs automatically on commit via the local hook defined in
  `.pre-commit-config.yaml`.
- Run it manually any time:

```bash
python scripts/sync_agents.py
```

Behavior
--------

- `.github/agents/` is the single source of truth. Never hand-edit files in
  `agents/` or `skills/shared/agents/` — your edits will be overwritten on the
  next commit.
- Stale files in `skills/shared/agents/` that are not listed in `SHARED_TRIO`
  are removed by the sync to keep the CLI ship surface deterministic.
- After this sync, `scripts/sync_skills.py` mirrors `skills/` →
  `.github/skills/`, so the trio transitively ends up in
  `.github/skills/shared/agents/` as well. That is intentional — do not edit
  there either.

Notes
-----

- There is no separate `.githooks/` setup; `pre-commit` owns the sync flow.
- If you need to refresh both mirrors without committing, run the manual sync
  command above and then `python scripts/sync_skills.py`.
