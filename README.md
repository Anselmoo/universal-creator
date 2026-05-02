# universal-creator

A collection of four **generator skills** for building Claude-native AI artifacts: hooks, agents, instructions, and prompts.

Each skill lives in `skills/<name>/` with a `SKILL.md` file that Claude loads automatically when the skill is triggered.

---

## Skills

### `hook-generator`
**Trigger:** "automate Claude Code behavior", "block a tool call", "add a hook", "enforce rules deterministically", "run a script after edit"

Designs and generates Claude Code hook configurations for all lifecycle events: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SessionStart`, `PostCompact`, and more.

→ [`skills/hook-generator/SKILL.md`](skills/hook-generator/SKILL.md)

---

### `agent-generator`
**Trigger:** "create a sub-agent", "design an agent role", "build a custom Claude agent", "tool restrictions per agent", "multi-stage agentic workflow"

Produces `.agent.md` files with bounded role definitions, explicit tool policies, system prompt stubs, and delegation rules.

→ [`skills/agent-generator/SKILL.md`](skills/agent-generator/SKILL.md)

---

### `instruction-generator`
**Trigger:** "write workspace instructions", "save coding preferences", "applyTo pattern", "add always-on rules", "create a copilot-instructions.md"

Generates `*.instructions.md`, `copilot-instructions.md`, and `AGENTS.md` files with correct glob patterns, verifiable rules, and scope guidance.

→ [`skills/instruction-generator/SKILL.md`](skills/instruction-generator/SKILL.md)

---

### `prompt-generator`
**Trigger:** "write a prompt", "create a system prompt", "few-shot examples", "chain of thought", "prompt chaining", "improve this prompt"

Designs prompts using 18 techniques from zero-shot through graph-prompting. Includes technique justification, eval scenarios, and worked `.prompt.md` examples for every technique.

→ [`skills/prompt-generator/SKILL.md`](skills/prompt-generator/SKILL.md)

---

## Repository layout

_Abridged, current structure (checked against the workspace tree):_

```
skills/
├── hook-generator/
│   ├── SKILL.md
│   ├── requirements.txt
│   ├── agents/
│   ├── assets/
│   ├── docs/events.md              ← full event reference
│   ├── docs/security.md
│   ├── eval-viewer/
│   ├── templates/
│   │   └── hook-block.json         ← copy-paste JSON structures
│   ├── examples/                   ← ready-to-use hook configs
│   ├── references/
│   ├── scripts/                    ← shared eval/packaging scripts + validate_hook_output.py + generate_hook_stub.py
│   └── evals/
│       ├── evals.json              ← 3 scenarios (happy, edge, repair)
│       ├── grading.json            ← per-assertion pass/fail criteria
│       ├── benchmark.json          ← with/without-skill quality delta
│       └── feedback.json           ← iteration notes and gaps
│
├── agent-generator/
│   ├── SKILL.md
│   ├── requirements.txt
│   ├── agents/
│   ├── assets/
│   ├── eval-viewer/
│   ├── templates/
│   │   └── agent-system-prompt.md  ← fill-in-the-blank template
│   ├── examples/                   ← sample .agent.md files
│   ├── references/
│   ├── scripts/                    ← shared eval/packaging scripts + validate_agent_output.py + generate_agent_stub.py
│   └── evals/
│       ├── evals.json
│       ├── grading.json
│       ├── benchmark.json
│       └── feedback.json
│
├── instruction-generator/
│   ├── SKILL.md
│   ├── requirements.txt
│   ├── agents/
│   ├── assets/
│   ├── eval-viewer/
│   ├── templates/
│   │   ├── instructions-concise.md
│   │   └── instructions-extended.md
│   ├── examples/                   ← sample .instructions.md files
│   ├── references/
│   ├── scripts/                    ← shared eval/packaging scripts + validate_instruction_output.py + generate_instruction_stub.py
│   └── evals/
│       ├── evals.json
│       ├── grading.json
│       ├── benchmark.json
│       └── feedback.json
│
└── prompt-generator/
    ├── SKILL.md
    ├── requirements.txt
    ├── agents/
    ├── assets/
    ├── docs/techniques.md          ← full 18-technique reference catalog
    ├── eval-viewer/
    ├── templates/
    │   ├── prompt-file.md          ← .prompt.md skeleton
    │   ├── chain.md
    │   └── react.md
    ├── examples/
    │   ├── few-shot-entity-extraction.prompt.md
    │   ├── zero-shot-document-summary.prompt.md
    │   └── techniques/             ← one worked .prompt.md per technique
    │       ├── zero-shot.prompt.md
    │       ├── few-shot.prompt.md
    │       ├── cot.prompt.md
    │       ├── prompt-chaining.prompt.md
    │       ├── react.prompt.md
    │       ├── meta-prompting.prompt.md
    │       ├── self-consistency.prompt.md
    │       ├── generate-knowledge.prompt.md
    │       ├── tree-of-thoughts.prompt.md
    │       ├── rag.prompt.md
    │       ├── art.prompt.md
    │       ├── ape.prompt.md
    │       ├── active-prompt.prompt.md
    │       ├── dsp.prompt.md
    │       ├── pal.prompt.md
    │       ├── reflexion.prompt.md
    │       ├── multimodal-cot.prompt.md
    │       └── graph-prompting.prompt.md
    ├── references/
    ├── scripts/                    ← shared eval/packaging scripts + validate_prompt_output.py + detect_over_prompting.py
    └── evals/
        ├── evals.json
        ├── grading.json
        ├── benchmark.json
        └── feedback.json

evals/
└── cross-skill-integration.json    ← multi-skill interplay scenario

src/
└── universal_creator/               ← CLI package (`universal-creator`)

.github/
└── workflows/
    └── cicd.yml                    ← CI/CD pipeline
```

## Cross-platform compatibility

These skills follow the [agentskills.io](https://agentskills.io) open standard: the same `SKILL.md` format works with both Claude Code and OpenAI Codex. Only the storage path differs.

| Feature | Claude Code | OpenAI Codex |
|---------|------------|--------------|
| Skill format | `SKILL.md` (Markdown) | `SKILL.md` (same format) |
| Skill storage path | `.claude/skills/<name>/` | `.agents/skills/<name>/` |
| Hook events | 30+ (see [events.md](skills/hook-generator/docs/events.md)) | 6 (`SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, `Stop`) |
| Hook handler types | `command`, `http`, `mcp_tool`, `prompt`, `agent` | `command` only |
| Hook config location | `settings.json` | `config.toml` + `[features] codex_hooks = true` |
| Sub-agent format | `.agent.md` (Markdown) | `.codex/agents/*.toml` (TOML) |
| Built-in sub-agents | user-defined | `default`, `worker`, `explorer` |
| Implicit skill invocation | configurable | disable with `allow_implicit_invocation: false` |

---

## Usage

These skills are designed for use with Copilot Chat or Claude's skill-loading system. When you describe a task matching a skill's trigger keywords, Claude loads the relevant `SKILL.md` and follows its workflow.

### Run from PyPI with `uvx`

You can run `universal-creator` directly from PyPI without creating a local virtualenv:

```bash
uvx universal-creator --help
uvx universal-creator menu
```

Pinning a version is also supported:

```bash
uvx universal-creator==0.1.0 --help
```

You can also load them manually:
```
@workspace /skills/hook-generator/SKILL.md
```
or reference a specific template:
```
@workspace /skills/prompt-generator/templates/prompt-file.md
```
