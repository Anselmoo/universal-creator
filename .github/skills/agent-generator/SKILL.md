---
name: agent-generator
description: >-
  Designs and generates Claude agent definitions: custom sub-agents (.agent.md),
  bounded-role system prompts, tool-use policies, handoff criteria, and delegation
  boundaries. Use when the user wants to create a specialized Claude agent,
  define a multi-stage agentic workflow, set tool restrictions per agent role,
  design a sub-agent that returns a single result and terminates, scope an agent
  to a specific domain or task type, or prevent an agent from overstepping its
  role. Generates .agent.md files, system prompt stubs, tool-allow/deny matrices,
  and role boundaries. DO NOT USE for Claude Code lifecycle hooks (use hook-generator);
  for writing prompts for one-shot tasks (use prompt-generator); for writing
  always-on workspace instructions (use instruction-generator).
license: "MIT"
metadata:
  dependencies:
    - shared
---

# Agent Generator

Produces well-scoped, discoverable Claude agent definitions with explicit role
boundaries, tool policies, and termination criteria.

A good agent is **narrow**: it does one job well and knows when it is done.

## Quick Decision: Agent vs Prompt vs Sub-agent?

| Need | Best primitive |
|------|---------------|
| Single focused task, returns text | Prompt (`.prompt.md`) |
| Always-on workspace guidance | Instructions (`.instructions.md`) |
| Context isolation + single output | Sub-agent (`.agent.md`, spawned with `runSubagent`) |
| Multi-stage workflow, tool restrictions per stage | Custom agent chain |
| Domain-expert with persistent access to domain tools | Named custom agent |

## Workflow

Follow these steps in order. Mark each ✓ when done.

### Step 1 — Define role and mission

Complete this contract before writing any YAML or system prompt:

```
Role name:     <short, hyphenated, lowercase>
One-line mission: <what this agent does, in imperative>
Non-goals:     <what this agent must NOT do>
Caller:        <which agent/skill spawns this, or "user">
Output:        <exactly what is returned on success>
Terminates when: <explicit completion criteria>
```

### Step 2 — Assign tools

List only tools this agent needs. Anything not listed is implicitly unavailable.

| Tool | Include? | Reason |
|------|----------|--------|
| `file_search` | Yes | Read-only exploration |
| `read_file` / `grep_search` | Yes | Read-only analysis |
| `replace_string_in_file` / `create_file` | Only if writes needed | |
| `run_in_terminal` | Only if execution needed | Must be justified |
| `web_search` / `fetch_webpage` | Only if retrieval needed | |
| `vscode_*` | Only for VS Code-specific tasks | |

Default posture: **read-only unless writes are explicitly required**.

### Step 2.5 — Select Prompting Technique

Before writing the system prompt, spawn `skills/shared/technique-selector.md` as a subagent:
- `request`: the user's generation request (verbatim)
- `generator_type`: "agent"

Apply each item in the returned `structural_requirements` when writing the system prompt in Step 3:
- **zero-shot**: role + task + output format constraint only — nothing more
- **few-shot**: `<examples>` XML block with 3 input/output pairs in the system prompt body
- **cot**: "Think through this step by step" + numbered process steps + `<thinking>/<answer>` structure
- **prompt-chaining**: numbered stages with explicit named intermediate output placeholders
- **react**: Thought/Action/Observation loop + tool list + Finish[answer] termination signal

Embed the technique structurally — do not just name it.

### Step 3 — Write the system prompt

Keep the system prompt under 400 words. Structure:

```markdown
You are <role>. Your mission is <one-line mission>.

## Scope
<What you are responsible for>

## Out of scope
<What you must refuse or hand back>

## Output format
<Exact format of your final answer>

## Completion criteria
<When to call task_complete / return>
```

See [templates/agent-system-prompt.md](templates/agent-system-prompt.md) for a fill-in-the-blank version.

### Step 4 — Write the .agent.md frontmatter

```yaml
---
name: <role-name>          # lowercase, hyphens, ≤64 chars
description: >-
  <Third-person description. Start with what the agent does.
   Include "Use when…" trigger phrase with specific keywords.
   Max 1024 chars. No XML tags.>
tools:
  - <tool1>
  - <tool2>

# --- Optional fields ---
isolation: none            # none | container | vm  (sandbox level)
color: blue                # UI tile color
initialPrompt: >-
  <Pre-populated prompt shown to user when launching the agent>
memory:
  - user                   # user | project | local  (memory scopes to read)
background: false          # true = run headless, no interactive prompts
effort: normal             # low | normal | high | max
skills:
  - <skill-name>           # skills preloaded into this agent's context
hooks:                     # scoped hooks — only active when this agent runs
  - event: PreToolUse
    matcher: "Bash"
    handler:
      type: command
      command: echo "bash blocked in this agent"; exit 2
---
```

**Field guide:**

| Field | Type | When to use |
|-------|------|-------------|
| `isolation` | enum | `container` for code execution agents; `vm` for untrusted input |
| `color` | string | Any CSS color name or hex; helps distinguish agents in the UI |
| `initialPrompt` | string | Pre-seed the conversation; useful for onboarding flows |
| `memory` | list | `user` = reads `~/.claude/memories`; `project` = `.claude/memories` |
| `background` | bool | `true` for fully automated agents that must not prompt the user |
| `effort` | enum | `max` for complex research; `low` for quick, cheap tasks |
| `skills` | list | Preloads named skills so they are always available to this agent |
| `hooks` | list | Scoped hooks — identical schema to `settings.json` hooks |

### Step 5 — Define handoff/delegation rules

If this agent delegates to sub-agents, document:
- Which agents it can spawn (names + reason)
- What it passes as input
- What it expects back (schema or format)
- What happens if a sub-agent fails

### Step 6 — Verify quality checklist

- [ ] Mission is one sentence and imperative.
- [ ] Non-goals are explicit and unambiguous.
- [ ] Tool list is minimal — no tool listed without justification.
- [ ] System prompt is under 400 words.
- [ ] Description is written in third person and includes trigger keywords.
- [ ] Description does NOT start with "I" or "You".
- [ ] Termination criteria are concrete (not "when done").
- [ ] Handoff output format is specified if the agent delegates.
- [ ] technique-selector was called before writing the system prompt.
- [ ] The selected technique's structural requirements are embedded (not just named) in the system prompt body.

### Step 7 — Scaffold and validate the file

To scaffold a minimal valid agent file from the command line, run:

```bash
python skills/agent-generator/scripts/generate_agent_stub.py \
  --name "doc-writer" \
  --description "Writes technical docs from source code. Use when..." \
  --tools "read_file,semantic_search" \
  --scope bounded
```

The `--scope bounded` flag (default) adds an `## Out of scope` placeholder and keeps
the tool list restricted to what you declared.  Use `--scope open` to omit the
`## Out of scope` section when the agent needs unrestricted access.

After generating or editing an agent file, validate frontmatter and body structure:

```bash
python skills/agent-generator/scripts/validate_agent_output.py <path>
# or via poe:
poe validate-agents <path>
```

The validator checks:
- `name` is kebab-case and ≤60 characters
- `description` is present and ≤200 characters (prints an advisory if >70 chars, since Copilot mode labels truncate around 70)
- `tools` is a non-empty list
- Body has at least one `##` heading, a scope-defining heading (`## Scope / ## Role / ## Mission / ## System / ## Task`), and `## Output format`
- Prints an advisory if `## Completion criteria` is missing

## Anti-patterns

- **God agent**: one agent doing everything. Split by domain or stage.
- **Implicit tool access**: listing no tools and relying on defaults. Always be explicit.
- **Vague termination**: "when the task is complete". Add measurable criteria.
- **Missing non-goals**: without explicit exclusions, agents scope-creep. List at least two.
- **First-person description**: `description` is injected into system context; inconsistent POV causes discovery failures.

## Technique Embedding Guide

When technique-selector returns a result, embed the technique structurally — not just as a mention.

| Technique | What "embedded" means for an agent system prompt |
|-----------|--------------------------------------------------|
| zero-shot | Explicit role + precise task + output format constraint. Nothing else. |
| few-shot | System prompt body contains `<examples>` XML with 3 `<example>` children (each `<input>` + `<output>`). |
| cot | Process section uses numbered steps; output format requires `<thinking>` before conclusion; "think step by step" is in the instructions. |
| prompt-chaining | Agent outputs a named artifact feeding a documented downstream stage; handoff schema is in the Output format section. |
| react | Instructions contain the Thought/Action/Observation loop; tools listed with signatures; Finish[answer] terminates. |

## Output format

Deliver a complete `.agent.md` file (frontmatter + body) plus:
- A filled system prompt following the Step 3 template
- A tool matrix table
- Any delegation rules (if applicable)

See [examples/](examples/) for domain-specific agent patterns.
Role template: [templates/agent-system-prompt.md](templates/agent-system-prompt.md)

---

## OpenAI Codex subagents — comparison

OpenAI Codex uses TOML files (not Markdown) for agent definitions. Stored under `.codex/agents/`.

| Feature | Claude Code `.agent.md` | OpenAI Codex `.toml` |
|---------|------------------------|----------------------|
| Format | Markdown + YAML frontmatter | TOML |
| Storage | `.claude/agents/` | `.codex/agents/` |
| Built-in agents | Explore, Plan, general-purpose | default, worker, explorer |
| Max parallel agents | Configurable | `max_threads = 6` (default) |
| Max nesting depth | Configurable | `max_depth = 1` (default) |
| Tool restrictions | `tools:` list in frontmatter | `[tools]` table in TOML |
| Scoped hooks | Yes (frontmatter `hooks:`) | No |
| Memory scopes | `user \| project \| local` | Not natively supported |
| Batch spawning | Via `runSubagent` calls | `spawn_agents_on_csv` (experimental) |
