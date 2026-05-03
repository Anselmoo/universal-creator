---
name: prompt-generator
description: >-
  Designs and generates effective prompts for Claude and other LLMs using all 18
  prompting techniques: zero-shot, few-shot, chain-of-thought, prompt chaining,
  ReAct, meta-prompting, self-consistency, generate-knowledge, tree-of-thoughts,
  RAG, ART, APE, active-prompt, DSP, PAL, reflexion, multimodal-CoT, and
  graph-prompting (full catalog: docs/techniques.md; examples: examples/).
  Use when the user wants to write a Claude system prompt, create a .prompt.md file,
  improve an existing prompt, choose between prompting techniques, structure
  multi-step reasoning, or apply context-budget-aware prompt engineering.
  Generates ready-to-use prompt files with technique justification and eval scenarios.
  DO NOT USE for Claude Code lifecycle hooks (use hook-generator); for creating
  agent role definitions (use agent-generator); for workspace instructions (use
  instruction-generator).
license: "MIT"
---

# Prompt Generator

Produces clear, effective prompts matched to the right technique for the task.

## Technique Escalation Ladder

Start at the lowest rung that works. Move up only when lower rungs fail evaluation.

```
1. Zero-shot  →  2. Few-shot  →  3. CoT  →  4. Chaining  →  5. ReAct
```

| Rung | Technique | Use when |
|------|-----------|----------|
| 1 | **Zero-shot** | Task is clear; Claude knows the domain; no output format constraint |
| 2 | **Few-shot** | Format is critical; task is niche; Claude misreads zero-shot |
| 3 | **Chain-of-thought** | Multi-step reasoning; arithmetic; logic; ambiguous decision boundaries |
| 4 | **Prompt chaining** | Task decomposes naturally; intermediate outputs can be validated |
| 5 | **ReAct** | External lookups/tools needed; state changes during task execution |

Full technique catalog (18 entries): [docs/techniques.md](docs/techniques.md)
Worked examples for every technique: [examples/](examples/)

## Workflow

Follow these steps in order. Mark each ✓ when done.

### Step 1 — Define success criteria first

Before writing a single word of prompt, answer:
- **What does a perfect output look like?** (format, length, structure, tone)
- **What does a failing output look like?** (wrong format, hallucination, missed step)
- **How will you evaluate it?** (rubric, regex check, human review)

Prompts without success criteria cannot be improved systematically.

### Step 2 — Choose the technique (use the ladder)

**Zero-shot baseline (Rung 1):**
```
<role>

<task description>

<output format constraint>
```
Start here. Evaluate. Only escalate if this fails.

**Few-shot (Rung 2):** Add 3–5 concrete examples. Wrap in `<examples>` tags.
```xml
<examples>
<example>
<input>…</input>
<output>…</output>
</example>
</examples>
```
Examples must be:
- Relevant: mirror the real use case
- Diverse: cover edge cases, not variations of the same case
- Structured: clear input/output demarcation

**Chain-of-thought (Rung 3):** Elicit step-by-step reasoning before the final answer.
```
Think through this step by step before giving your final answer.

Use <thinking>…</thinking> for reasoning and <answer>…</answer> for the result.
```
Do not prescribe each reasoning step — "think step by step" outperforms hand-written plans.

**Prompt chaining (Rung 4):** Break the task into sequential prompts where each output feeds the next.
```
Prompt 1: Extract relevant quotes from the document.
          → Output: <quotes>…</quotes>

Prompt 2: Using only the quotes above, answer the question.
          → Output: final answer
```
Use chaining when intermediate outputs can be independently validated. See [templates/chain.md](templates/chain.md).

**ReAct (Rung 5):** Interleave Thought → Action → Observation loops.
```
Thought: What do I need to find out?
Action: <tool call>
Observation: <result>
Thought: What does this tell me?
…
Action: Finish[<final answer>]
```
Use ReAct only when the task genuinely requires external tool use. See [templates/react.md](templates/react.md).

### Step 3 — Manage context budget

| Risk | Mitigation |
|------|-----------|
| Long context → model ignores early instructions | Put critical rules at the start AND end |
| Tool results bloat context | Instruct Claude to extract/quote before summarizing |
| Many shots exceed token budget | Cap at 5 examples; use reference file for more |
| Compaction may lose context | Re-inject key constraints via `SessionStart` hook |

Verbosity control prompts (add to system prompt when needed):
```
Provide concise, focused responses. Skip non-essential context; keep examples minimal.
```
```
This task involves multi-step reasoning. Think carefully before responding.
```

### Step 4 — Write the .prompt.md file (for Copilot prompts)

```markdown
---
name: <prompt-name>
description: >-
  <Third-person. What this prompt does and when to use it. Include trigger keywords.>
---

<System/role context>

<Task instruction>

<Output format>
```

See [templates/prompt-file.md](templates/prompt-file.md).

### Step 5 — Verify quality checklist

- [ ] Success criteria are defined before the prompt is finalized.
- [ ] Technique rung is the lowest that achieves success criteria.
- [ ] Examples (if any) are relevant, diverse, and wrapped in `<example>` tags.
- [ ] Output format is explicit (structure, length, type).
- [ ] No time-sensitive information (no version-date constraints in the prompt body).
- [ ] Role / persona (if given) is consistent throughout.
- [ ] Prompt has been tested against at least one happy-path and one edge case.
- [ ] No over-prompting (ALWAYS / NEVER / CRITICAL density ≤ 1 per 100 words).

Run the validators to catch structural issues and over-prompting automatically:
```bash
# Validate frontmatter and eval sections
python skills/prompt-generator/scripts/validate_prompt_output.py <path>
# or: poe validate-prompts <path>

# Check for over-prompting (emphasis word density analysis)
python skills/prompt-generator/scripts/detect_over_prompting.py <file.prompt.md>
```

## Anti-patterns

- **Skipping the ladder**: jumping to ReAct for tasks that need zero-shot. Use the minimal technique.
- **Prescribing reasoning steps**: "First do A, then B, then C" performs worse than "think step by step" for most tasks.
- **Vague output format**: "give a good summary" → instead specify length, structure, tone, and any required sections.
- **Over-prompting**: repeated CRITICAL/ALWAYS instructions cause overtriggering. Use normal phrasing.
- **Exemplar monoculture**: all examples from the same case pattern teach unintended shortcuts.
- **Hallucination-friendly phrasing**: "What do you know about X?" → use "Based only on the provided context, …".

## Output format

Deliver:
1. The prompt file (`.prompt.md` or raw text block)
2. Technique justification (one sentence: why this rung)
3. One happy-path and one edge-case eval scenario

See [examples/](examples/) for domain-specific prompt patterns.
Technique reference: [docs/techniques.md](docs/techniques.md)
