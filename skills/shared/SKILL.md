---
name: shared
description: >-
  Shared resources for universal-creator generator skills: prompting technique
  registry (techniques.json) and the technique-selector subagent. Installed
  automatically when any dependent generator skill is installed.
  DO NOT USE directly — consumed by agent-generator, skill-generator, and hook-generator.
license: "MIT"
---

# Shared Resources

Shared prompting technique registry and technique-selector subagent used by all
universal-creator generator skills.

## Contents

- **`techniques.json`** — Registry of all 18 prompting techniques with structural
  signals, use case mappings, and example snippets.
- **`technique-selector.md`** — Subagent that classifies a generation request into
  one of 5 use case categories and returns the technique to embed plus concrete
  structural requirements.

## Usage

Generator skills (agent-generator, skill-generator, hook-generator) spawn
`technique-selector.md` as a subagent during their workflow to determine which
prompting technique to embed in the artifact they are producing.

The `techniques.json` registry is read by `technique-selector` at runtime —
it is the single source of truth for all technique definitions.
