---
name: shared
description: >-
  Shared resources for universal-creator generator skills: prompting technique
  registry (techniques.json), the technique-selector subagent, the 18 worked
  prompt-technique examples (examples/), and the reusable agent trio
  (agents/) — validation-reviewer, artifact-router, prompt-strategist —
  plus the shared memory-guardrails snippet. Installed automatically when any
  dependent generator skill is installed.
  DO NOT USE directly — consumed by agent-generator, skill-generator,
  hook-generator, and prompt-generator.
license: "MIT"
---

# Shared Resources

Shared assets used by every universal-creator generator skill. This directory
is dependency-only: it ships when any generator skill that declares
`dependencies: [shared]` is installed.

## Contents

- **`techniques.json`** — Registry of all 18 prompting techniques with
  structural signals, use case mappings, and example snippets.
- **`technique-selector.md`** — Subagent that classifies a generation request
  into one of 5 use case categories and returns the technique to embed plus
  concrete structural requirements.
- **`examples/`** — 18 worked `.prompt.md` files, one per technique (zero-shot,
  few-shot, cot, react, reflexion, rag, self-consistency, generate-knowledge,
  tree-of-thoughts, ape, active-prompt, dsp, pal, multimodal-cot,
  graph-prompting, meta-prompting, prompt-chaining, art). Read at runtime by
  any generator that needs to apply or reference a technique example.
- **`agents/`** — Reusable agent definitions: `validation-reviewer.agent.md`,
  `artifact-router.agent.md`, `prompt-strategist.agent.md`, and the shared
  `_memory-guardrails.md` snippet they all link to. These are sync-fanned in
  from the canonical `.github/agents/` source by `scripts/sync_agents.py`;
  do not hand-edit.
- **`scripts/`** — Canonical helper scripts (`package_skill.py`,
  `quick_validate.py`, `run_eval.py`, `run_loop.py`, `utils.py`, etc.) used
  by every generator skill's `scripts/` directory; kept in parity via
  `universal-creator sync`.

## Usage

Generator skills (agent-generator, skill-generator, hook-generator,
prompt-generator) spawn `technique-selector.md` as a subagent during their
workflow to determine which prompting technique to embed. Agents and examples
are referenced by relative path from the consumer skill (e.g.
`../shared/examples/cot.prompt.md`, `../shared/agents/validation-reviewer.agent.md`).

The `techniques.json` registry is read by `technique-selector` at runtime —
it is the single source of truth for all technique definitions.

## Edit protection

The CLI installer (`universal-creator install ...`) writes a per-file SHA256
manifest at `<scope>/.universal-creator/shared.lock` on first install. On
reinstall, files whose on-disk hash diverges from the manifest are preserved
and skipped with a warning. Pass `--force-shared` to override the protection
and reset the directory to bundled content.
