---
name: skill-generator
description: >-
  Designs and generates new skill directories for the universal-creator framework:
  SKILL.md definitions, workflow steps, domain conventions, generate_X_stub.py
  scaffold scripts, validate_X_output.py validators, agent definitions, templates,
  and evals. Use when the user wants to add a new skill to universal-creator,
  package a new artifact type as a reusable generator, create a skill from scratch
  following framework conventions, define a new skill for prompts/configs/documents
  or any domain-specific output, or extend the skill library with a new generator.
  Also use when someone says "make me a skill that generates X" or "I want a
  skill-creator style skill for Y" or "scaffold a new skill". DO NOT USE for
  creating Claude Code lifecycle hooks (use hook-generator); for writing workspace
  instruction files (use instruction-generator); for writing one-shot task prompts
  (use prompt-generator); for designing sub-agents with tool policies (use
  agent-generator).
license: "MIT"
dependencies:
  - shared
---

# Skill Generator

Produces a complete, immediately usable `skills/<name>/` directory that follows
universal-creator conventions — SKILL.md definition, domain scripts, agent stubs,
templates, and evals scaffolded and ready to fill in.

A good skill is **focused**: it handles one artifact type, defines clear conventions
for that artifact, and ships with enough scaffolding that future invocations are
consistent even when run by a different model on a different day.

## Quick Decision: Which generator skill?

| What you want to create | Right skill |
|-------------------------|------------|
| A new kind of artifact generator (new skill) | **skill-generator** ← you are here |
| A Claude Code lifecycle automation | hook-generator |
| A workspace / file-level always-on rule | instruction-generator |
| A reusable one-shot task prompt | prompt-generator |
| A bounded sub-agent with tool restrictions | agent-generator |

## Workflow

Follow these steps in order. Mark each ✓ when done.

### Step 1 — Capture intent

Answer these questions before writing anything:

```
Skill name (kebab-case):   <name>
Artifact type:             <what this skill generates, e.g. "SQL migration file">
One-line mission:          <imperative, e.g. "Generate SQL migration files from schema diffs">
Non-goals:                 <what this skill must NOT produce, at least two>
Primary output file(s):    <exact file names or patterns produced, e.g. "*.migration.sql">
Triggering context:        <user phrases that should activate this skill>
Competing skills to exclude: <list skills that could be confused with this one>
```

If the user says something like "turn this conversation into a skill", extract these
answers from the conversation history first (tools used, output patterns observed,
corrections made) rather than asking the user to repeat themselves.

### Step 1.5 — Select Prompting Technique

Spawn `skills/shared/technique-selector.md` as a subagent:
- `request`: the user's skill generation request (verbatim)
- `generator_type`: "skill"

Apply the returned `structural_requirements` when writing the SKILL.md body in Step 3:
- **zero-shot**: workflow steps are direct imperatives; output format is unambiguous without examples
- **few-shot**: `examples/` directory with 3 complete artifacts; workflow references them explicitly
- **cot**: workflow steps include reasoning checkpoints; conventions list explicit decision criteria
- **prompt-chaining**: SKILL.md defines numbered stages with named intermediate output artifacts
- **react**: workflow includes tool-invocation steps + conditional validation loops with recovery paths

Embed the technique structurally — do not just mention it.

### Step 2 — Design domain conventions

Before writing SKILL.md body content, decide what makes a *good* artifact of this type:

- What sections / fields / headings must always be present?
- What anti-patterns appear in bad outputs and why are they harmful?
- What does an excellent example look like vs. a mediocre one?

Write these down — they become the `## Conventions` and `## Anti-patterns` sections
of the skill, the grading rubric in `agents/grader.md`, and the validation checks
in `validate_<name>_output.py`.

### Step 3 — Scaffold and fill in

Scaffold the directory skeleton using the CLI:

```bash
universal-creator new-skill --name <name> --mode boilerplate
```

This creates the directory layout and drops in stub files. Then:

1. Replace the TODO stubs in `SKILL.md` with your Step 1 + Step 2 answers.
2. Set `description` to clearly name the artifact type and list trigger phrases.
3. Add a `## Conventions` section with domain-specific quality rules.
4. Add a `## Anti-patterns` section (at least three; explain *why* each is harmful).
5. Add `## Output format` specifying the exact file(s) produced.
6. Write `templates/<artifact-template>` as a fill-in-the-blank reference — something
   future invocations can lean on without reinventing the structure every time.

See [templates/skill-workflow.md](templates/skill-workflow.md) for a fill-in-the-blank
SKILL.md workflow section template.

### Step 4 — Write domain scripts

Every skill needs two domain-specific scripts in `scripts/`:

**`generate_<name>_stub.py`** — Scaffolds a minimal valid artifact from CLI arguments.

- Accept `--name`, `--description`, plus domain-specific options.
- Read the skill's template from `templates/`.
- Perform placeholder substitution (no Jinja2 required — simple string replace is fine).
- Write to stdout or `--out FILE`.
- Pattern: see `skills/agent-generator/scripts/generate_agent_stub.py`.

**`validate_<name>_output.py`** — Validates generated artifacts against domain conventions.

- Accept an optional path argument (default: CWD).
- Check frontmatter, required headings, field types, length limits.
- Exit 0 if all hard checks pass; exit 1 on any hard violation.
- Print `✓`, `△` (advisory), or `✗` lines per file.
- Pattern: see `skills/agent-generator/scripts/validate_agent_output.py`.

```bash
python skills/<name>/scripts/generate_<name>_stub.py \
  --name my-artifact --description "Does X"
python skills/<name>/scripts/validate_<name>_output.py examples/
```

### Step 5 — Fill in agents, evals, and examples

**`agents/grader.md`** — Grade outputs against the domain conventions from Step 2.
Write 5 named dimensions (e.g. Correctness, Completeness, Clarity, Usability,
Domain fit) and per-dimension pass/fail criteria with examples.

**`agents/fingerprint.md`** — Identify what makes an output from this skill
recognizably well-crafted. Focus on the traits that distinguish excellent outputs
from generic ones.

**`evals/evals.json`** — At least 3 test scenarios: one happy path, one edge case,
one near-miss (a request that *looks* like this skill but should use a different one).

**`examples/`** — At least one complete, real-quality example artifact.

### Step 6 — Verify quality checklist

Run the parity and validation checks before considering the skill done:

```bash
python3 scripts/run_validations.py
python skills/<name>/scripts/validate_<name>_output.py skills/<name>/examples/
```

- [ ] `name` is kebab-case and ≤64 characters.
- [ ] `description` covers: what it generates, trigger phrases, and DO NOT USE list.
- [ ] `## Workflow` section present with numbered/checkboxed steps.
- [ ] `## Conventions` section present with domain quality rules.
- [ ] `## Anti-patterns` section present with at least three entries.
- [ ] `## Output format` section present.
- [ ] `generate_<name>_stub.py` scaffolds a runnable stub without error.
- [ ] `validate_<name>_output.py` exits 0 on valid examples, 1 on bad ones.
- [ ] `evals/evals.json` has at least one happy-path and one near-miss scenario.
- [ ] `requirements.txt` declares `pyyaml>=6.0`.
- [ ] All local links in SKILL.md resolve to existing files.
- [ ] technique-selector was called before designing domain conventions.
- [ ] The selected technique's structural requirements are reflected in the workflow steps and conventions, not just mentioned.

## Conventions

A well-designed skill directory in universal-creator has these properties:

**Focused artifact type** — The skill generates one class of artifact. If a skill
generates both "SQL migrations" and "ER diagrams", split it into two skills.

**Self-contained conventions** — Domain quality rules live inside the skill, not in
a separate document. When someone invokes the skill months from now, all the guidance
they need is in SKILL.md.

**Runnable scripts** — `generate_X_stub.py` must run with just the declared
`requirements.txt` dependencies. No hidden imports, no repo-wide `sys.path` hacks.
The scripts self-bootstrap their path via `_SKILL_ROOT = Path(__file__).resolve().parent.parent`.

**Progressive disclosure** — Keep SKILL.md under 500 lines. If conventions are
extensive, link to `references/` rather than inlining everything.

**Eval coverage** — At least one near-miss eval (a request that belongs to a
neighboring skill) prevents the skill from over-triggering.

## Anti-patterns

**Copy-paste skill** — Duplicating an entire existing skill and renaming it without
adapting the workflow, scripts, or conventions. The result is a skill that gives
correct-looking but domain-wrong output because the grader and validator still check
for the old artifact type. Every script function that references the original artifact
name must be updated.

**Vague trigger description** — A description like "Generates files for various
purposes." gives Claude nothing to match against. The description is the primary
mechanism that determines when the skill fires; include concrete nouns, artifact names,
and at least one DO NOT USE clause for neighboring skills.

**Missing anti-patterns section** — A skill that does not list its own anti-patterns
produces outputs that exhibit those anti-patterns. The grader has nothing to check
against, so bad outputs pass undetected. List at least three.

**God skill** — A skill that claims to generate "any kind of document". Scope to a
single artifact class. Breadth is the enemy of reliable conventions.

**Untested validator** — A `validate_X_output.py` that has never been run on a
known-bad example. Write at least one test with a deliberately missing required
field and confirm the validator catches it before shipping.

**Missing DO NOT USE clauses** — Without explicit exclusions in the description,
the skill may trigger when a neighboring skill (agent-generator, hook-generator,
etc.) is the right choice. Always name the competing skills.

## Technique Embedding Guide

When technique-selector returns a result, embed the technique structurally — not just by mentioning it.

| Technique | What "embedded" means for a SKILL.md |
|-----------|--------------------------------------|
| zero-shot | Workflow steps are direct imperatives with unambiguous output format — no examples required. |
| few-shot | `examples/` has 3+ complete artifacts; workflow references them explicitly; grader evaluates example quality. |
| cot | Steps include reasoning checkpoints ("Before proceeding, verify…"); conventions list explicit decision criteria; grader checks reasoning depth. |
| prompt-chaining | SKILL.md defines numbered stages with named intermediate output artifacts; each stage independently verifiable before passing forward. |
| react | Workflow includes tool-invocation steps; validation loops with conditional retry paths; each validation step is conditional on the previous output. |

## Output format

Deliver a complete skill directory suitable for the target host. Preferred host-local locations are:

- Claude (repo-local): `.claude/skills/<name>/` or global `~/.claude/skills/<name>/`
- GitHub Copilot (repo-local): `.github/skills/<name>/` or global `~/.copilot/skills/<name>/`
- Gemini / Codex (repo-local): `.agents/skills/<name>/` or global `~/.agents/skills/<name>/`

Repository-level instruction artifacts may instead belong under `.github/` (e.g., `.github/<instructions...>`). If the consumer requires the legacy workspace layout, explicitly write to `./skills/<name>/` or `./skill/` only when the user or host requests it.

Example on-disk tree (use host-appropriate parent dir instead of `skills/` when installing):

```
<host-specific-parent>/<name>/   # e.g. .claude/skills/my-skill or .github/skills/my-skill or .agents/skills/my-skill
├── SKILL.md                              # frontmatter + workflow body
├── requirements.txt                      # pyyaml>=6.0 + any domain deps
├── agents/
│   ├── analyzer.md                       # request analysis agent
│   ├── comparator.md                     # A/B comparison agent
│   ├── fingerprint.md                    # output quality signature agent
│   └── grader.md                         # output grading agent
├── assets/
│   └── eval_review.html                  # evaluation viewer (copied from framework)
├── evals/
│   ├── benchmark.json                    # empty {} stub
│   ├── evals.json                        # ≥3 scenarios
│   ├── feedback.json                     # empty {} stub
│   └── grading.json                      # empty {} stub
├── eval-viewer/
│   ├── generate_review.py               # (copied from framework)
│   └── viewer.html                       # (copied from framework)
├── examples/                             # ≥1 real quality example
├── references/
│   └── schemas.md                        # JSON schemas used by this skill
├── scripts/
│   ├── __init__.py                        # canonical (parity-checked)
│   ├── aggregate_benchmark.py             # canonical (parity-checked)
│   ├── errors.py                          # canonical (parity-checked)
│   ├── generate_report.py                 # canonical (parity-checked)
│   ├── generate_<name>_stub.py            # skill-specific: scaffolds artifact
│   ├── improve_description.py             # canonical (parity-checked)
│   ├── package_skill.py                   # canonical (parity-checked)
│   ├── quick_validate.py                  # canonical (parity-checked)
│   ├── run_eval.py                        # canonical (parity-checked)
│   ├── run_loop.py                        # canonical (parity-checked)
│   ├── utils.py                           # canonical (parity-checked)
│   └── validate_<name>_output.py          # skill-specific: validates artifacts
└── templates/
    └── skill-workflow.md                  # fill-in-the-blank SKILL.md sections
```

See [references/schemas.md](references/schemas.md) for the JSON schemas used in
`evals/`, `agents/`, and benchmark output.

Script templates: [templates/skill-workflow.md](templates/skill-workflow.md)
