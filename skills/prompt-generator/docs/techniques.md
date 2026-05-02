# Prompt Engineering Techniques Reference

## Rung 1 — Zero-shot

No examples. Rely on Claude's pre-trained knowledge of the task.

```
You are a <role>.

<Task description. Be specific about what you want.>

<Output format: "Return a JSON object with fields X, Y, Z." / "Answer in plain prose under 200 words." / etc.>
```

**When it works:** well-defined tasks with clear output formats, common domains.
**When it fails:** niche formats Claude hasn't seen; tasks requiring exact schema; ambiguous output expectations.

---

## Rung 2 — Few-shot

Provide 3–5 input/output examples inside `<example>` tags.

```xml
<examples>
<example>
<input>The sky at sunset</input>
<output>orange</output>
</example>
<example>
<input>Fresh mint leaves</input>
<output>green</output>
</example>
<example>
<input>Ocean water</input>
<output>blue</output>
</example>
</examples>

Now classify: <input>A ripe banana</input>
```

**Rules for examples:**
1. Use real task inputs, not toy inputs.
2. Cover edge cases — not multiple variations of the easy case.
3. Ordering matters for ambiguous tasks: put most instructive examples last.
4. 3 examples outperform 1; 5 rarely outperform 3 for classification; more may help for extraction.

---

## Rung 3 — Chain-of-thought (CoT)

Elicit intermediate reasoning before the final answer.

### Zero-shot CoT (simplest)
```
<task>

Think step by step before answering.
```

### Few-shot CoT (stronger)
```xml
<examples>
<example>
<input>If a train travels 60 mph for 2.5 hours, how far does it travel?</input>
<thinking>Speed × time = distance. 60 × 2.5 = 150.</thinking>
<output>150 miles</output>
</example>
</examples>

<input>If a cyclist rides 15 mph for 40 minutes, how far do they travel?</input>
```

### Structured CoT (controllable)
```
Use <thinking>…</thinking> for your reasoning and <answer>…</answer> for the final result.
Do not reveal <thinking> to the end user.
```

**Do NOT** prescribe the exact reasoning steps ("First check X, then check Y"). This usually degrades performance. Let Claude reason freely.

---

## Rung 4 — Prompt chaining

Decompose the task into sequential sub-prompts. Each output becomes the next input.

```
=== Prompt 1: Extract ===
From the document below, extract all statements of fact about revenue.
Return them as a JSON array of strings.

[document]

=== Prompt 2: Filter (takes Prompt 1 output) ===
From the revenue statements below, identify which ones are for Q4 2024.
Return matching statements only.

[Prompt 1 output]

=== Prompt 3: Synthesize (takes Prompt 2 output) ===
Based only on these Q4 2024 revenue statements, write a two-sentence executive summary.

[Prompt 2 output]
```

**Validation checkpoint:** inspect intermediate outputs before passing to the next stage.
**When to use:** tasks that naturally decompose; when intermediate outputs can be independently verified; when one failure shouldn't cascade.

---

## Rung 5 — ReAct (Reason + Act)

Interleave reasoning and tool use in Thought → Action → Observation cycles.

```
You have access to these tools: [tool_list]

Use the following format:
Thought: <what you need to find out and why>
Action: <tool_name>[<tool_input>]
Observation: <tool result will be inserted here>
…repeat as needed…
Thought: I now have enough information to answer.
Action: Finish[<final answer>]
```

**Rules:**
- Each `Thought` must explain *why* the next action is needed.
- `Finish[…]` terminates the loop.
- Never invent observations. Wait for the actual tool result.
- Limit loops — 10 cycles is usually the maximum before reformulating.

**When to use:** tasks requiring lookups, file reads, or state changes; when the task cannot be answered from the prompt alone.

---

## Context budget controls

| Risk | Prompt addition |
|------|----------------|
| Long context → drift | Repeat key constraints at the end: "Remember: output JSON only." |
| Tool results bloat context | "Quote the relevant passage before answering; do not reproduce entire documents." |
| Many-shot context overflow | Cap examples at 5; reference external files for extended examples |
| Compaction loses constraints | Re-inject via `SessionStart` hook (see hook-generator) |

---

## Hallucination reduction

```
Answer based only on the provided context. If the answer is not in the context, say "I don't know."
```
```
Do not invent names, dates, or figures. If uncertain, say "I'm not sure."
```
```
If a piece of information was not given to you in this conversation, do not include it.
```

---

## Advanced Technique 6 — Meta-prompting

Ask Claude to generate its own prompt for a task, then execute it.

```
You are a prompt engineer. Write a detailed system prompt for an AI assistant
that will <task description>. The prompt must specify:
- Role and persona
- Output format and constraints
- Edge case handling
- Failure modes to avoid

Then execute that prompt on this input: <input>
```

**When to use:** You know what you want but not how to phrase it; iterating on prompt quality; bootstrapping a new skill.
**Claude-specific note:** Claude can introspect on its own instruction quality. Append "Critique your prompt before executing it" for an extra refinement pass.
**When to escalate:** If the meta-prompt keeps producing similar-quality output → try APE (Technique 12) to systematically score candidates.

---

## Advanced Technique 7 — Self-consistency

Sample multiple independent reasoning paths, then select the most consistent (majority-vote) answer.

```
Answer the following question three times independently, using a different
reasoning approach each time. After all three answers, identify the answer
that appears most often and state it as your final answer.

Question: <question>

## Attempt 1
<Claude fills in>

## Attempt 2
<Claude fills in>

## Attempt 3
<Claude fills in>

## Final answer (most consistent)
<Claude fills in>
```

**When to use:** High-stakes single answers (math, logic, classification); tasks where reasoning path varies but the correct answer is unique.
**Claude-specific note:** Run multiple turns with temperature > 0 and collect answers programmatically; or instruct Claude to reason three ways in one turn.
**When to escalate:** If all three paths agree but are wrong → the error is systematic; try few-shot CoT with corrective examples instead.

---

## Advanced Technique 8 — Generate-knowledge

Prime the model with relevant facts before asking it to answer.

```
Step 1 — Generate knowledge:
List 5 key facts about <topic> that are relevant to answering <question>.
Be specific and factual. Number each fact.

Step 2 — Answer using those facts:
Using only the facts you listed above, answer: <question>
```

**When to use:** Factual questions where Claude may not surface the right background knowledge unprompted; science, history, policy domains.
**Claude-specific note:** Running both steps in one prompt works well. Add "If you are uncertain about a fact, mark it with ⚠️" to surface unreliable priors.
**When to escalate:** If Claude generates wrong facts → switch to RAG (Technique 10) to inject verified facts from external sources.

---

## Advanced Technique 9 — Tree-of-thoughts (ToT)

Enumerate multiple solution branches, evaluate each, and select or backtrack.

```
You are solving: <problem>

Generate 3 distinct high-level approaches (branches). For each branch:
1. Describe the approach in 1-2 sentences.
2. Score it on a 1–10 scale for: feasibility, effort, and risk.
3. Identify the biggest unknown or blocker.

After evaluating all branches, select the best one and explain why.
Then outline the first 3 concrete steps for the selected approach.
```

**When to use:** Strategic decisions; design problems; tasks with no single obvious solution path.
**Claude-specific note:** Limit to 3-4 branches to stay within context budget. For deep search, chain multiple ToT prompts (outer branch → inner sub-branches).
**When to escalate:** For combinatorial search problems, ToT in a single prompt may not explore deeply enough → use prompt chaining (Rung 4) with one prompt per branch depth.

---

## Advanced Technique 10 — RAG (Retrieval-Augmented Generation)

Retrieve relevant document chunks externally, then inject them as context before answering.

```
Answer the question below using ONLY the provided context passages.
If the answer is not found in the passages, say "Not found in the provided context."

<context>
[Passage 1]: {retrieved_chunk_1}
[Passage 2]: {retrieved_chunk_2}
[Passage 3]: {retrieved_chunk_3}
</context>

Question: <question>
```

**When to use:** Factual Q&A over large corpora (docs, codebases, knowledge bases); any task where Claude's training data may be stale or incomplete.
**Claude-specific note:** Use `<context>` XML tags to isolate retrieved text from the question. Instruct Claude to cite passage numbers: "Cite which passage(s) support your answer."
**When to escalate:** If retrieval quality is poor (wrong chunks returned) → the fix is in the retrieval pipeline, not the prompt. If chunks are too long and compress poorly → summarize each chunk before injecting.

---

## Advanced Technique 11 — ART (Auto-Reasoning & Tool-use)

Combine a frozen LLM with a dynamic tool library: Claude picks the right tool for each sub-task from a provided catalog.

```
You have access to the following tools. For each sub-task, select the most
appropriate tool and call it. Do not use a tool if the sub-task can be
answered from context alone.

Available tools:
- search(query: str) → list of web results
- calculator(expression: str) → numeric result
- code_exec(code: str, language: str) → stdout/stderr
- lookup(entity: str, field: str) → structured fact

Task: <complex multi-step task>

Work through the task step by step. For each step, state:
Tool used: <tool name or "none">
Reason: <why this tool is needed>
Result: <tool output>
```

**When to use:** Tasks requiring heterogeneous operations (search + calculation + code); agentic workflows with a known tool library.
**Claude-specific note:** Explicitly listing all tools reduces hallucinated tool names. Add `"If you are unsure which tool to use, describe what you need and ask."` for safety.
**When to escalate:** If tool selection logic is complex → move to ReAct (Rung 5) which handles dynamic observation-reaction loops.

---

## Advanced Technique 12 — APE (Auto Prompt Engineer)

Automatically generate and score multiple prompt candidates to find the best one.

```
Task description: <what you want the final prompt to accomplish>
Evaluation criterion: <how to score output quality — e.g., "shorter is better", "must include X">

Generate 5 distinct system prompt candidates for this task. Each candidate
should take a different approach (different tone, structure, or instruction style).

After generating all 5, evaluate each against the criterion and assign a score 0–10.
Output: the highest-scoring prompt in full, followed by your reasoning.
```

**When to use:** When you need a reusable prompt and aren't sure which framing works best; prompt quality optimization before deployment.
**Claude-specific note:** Run APE in a separate session before the production session. Feed the winner into the production prompt without the APE scaffolding.
**When to escalate:** For large-scale prompt optimization across many test cases → automated APE with an eval harness (e.g., skill-creator eval loop) is more reliable than single-turn APE.

---

## Advanced Technique 13 — Active-prompt

Annotate examples where the model is most uncertain, then add those as few-shot examples to reduce error.

```
Step 1 — Identify uncertainty:
For each input below, answer the question AND provide a confidence score (0–100%).
Flag any answer with confidence below 70%.

Inputs: [list of candidate inputs]

Step 2 — Human annotates flagged inputs (external step)

Step 3 — Add annotated inputs as examples:
<examples>
<example><input>[flagged input]</input><output>[correct answer]</output></example>
</examples>

Now answer: <new input>
```

**When to use:** Fine-tuning few-shot example selection; when you have many candidate examples and want to pick the most informative ones rather than randomly sampling.
**Claude-specific note:** The uncertainty elicitation step (confidence scores) works in a single Claude turn. Human review of flagged items is the only external step.
**When to escalate:** If low-confidence cases are a majority → the task may be too ambiguous for few-shot; reframe the task or add richer context.

---

## Advanced Technique 14 — DSP (Demonstrate-Search-Predict)

Multi-hop reasoning: retrieve evidence, demonstrate with examples, then predict.

```
You are answering a multi-hop question. Follow these three steps:

Step 1 — Search: identify what sub-questions need to be answered first.
List each sub-question.

Step 2 — Demonstrate: for each sub-question, find or state the relevant fact.
Cite your source if available.

Step 3 — Predict: using only the facts from Step 2, answer the original question.

Original question: <complex multi-hop question>
```

**When to use:** Questions requiring chaining of multiple facts (e.g., "Who was the CEO of X when Y happened, and what did they say about Z?"); knowledge graph traversal.
**Claude-specific note:** Works best when Claude has the facts in context (RAG retrieval per sub-question). Without retrieval, Claude may hallucinate intermediate facts.
**When to escalate:** More than 3 hops → chain multiple DSP prompts, passing sub-answers forward rather than fitting everything in one turn.

---

## Advanced Technique 15 — PAL (Program-Aided Language models)

Generate runnable code to solve the problem, execute it, and use the result as the answer.

```
Solve the following problem by writing a Python program.
Do not calculate the answer in your head — write code that calculates it.
Return ONLY the Python code. Do not include explanations or prose.

Problem: <mathematical or algorithmic problem>
```

Then execute the code and substitute the result back into the final answer.

**When to use:** Arithmetic word problems; combinatorics; any task where symbolic calculation is more reliable than language-model arithmetic.
**Claude-specific note:** Claude can generate the code and reason about the output in the same turn. Wrap in a code execution tool for production use. Add `# If an error occurs, print a helpful message` to make debugging easier.
**When to escalate:** If the problem requires external data → combine PAL with RAG (retrieve data → pass to generated code → execute).

---

## Advanced Technique 16 — Reflexion

Self-critique loop: generate an answer, evaluate it against explicit criteria, revise, and repeat.

```
## Round 1 — Draft
<task description>

Draft your answer below:

## Round 2 — Critique
Review your draft against these criteria:
- [ ] Criterion 1: <e.g., "All claims are supported by evidence">
- [ ] Criterion 2: <e.g., "Word count is under 300">
- [ ] Criterion 3: <e.g., "No passive voice">

For each criterion, mark pass ✓ or fail ✗ and explain why.

## Round 3 — Revision
Rewrite the answer to fix every failed criterion. Do not introduce new failures.
```

**When to use:** Writing tasks (essays, emails, reports); code review; any output that benefits from a structured second pass.
**Claude-specific note:** Cap at 2-3 rounds — additional rounds rarely improve quality and compress context. If all criteria pass after Round 2, stop.
**When to escalate:** If the same criterion keeps failing across rounds → the issue is likely ambiguous criteria, not the content. Rewrite the criterion to be more concrete.

---

## Advanced Technique 17 — Multimodal-CoT

Chain-of-thought reasoning that integrates both image/diagram analysis and text in the same reasoning chain.

```
Look at the image and answer the question using chain-of-thought reasoning.

Image: [attached image or diagram]

Question: <question about the image>

Reasoning format:
Step 1 — Describe what you see in the image (be specific about labels, values, shapes).
Step 2 — Identify which visual elements are relevant to the question.
Step 3 — Reason step by step using those elements.
Step 4 — State your final answer.
```

**When to use:** Science diagrams, charts, flowcharts, architectural diagrams, math problems with figures.
**Claude-specific note:** Claude Sonnet and Opus handle multimodal CoT well. Instruct Claude to describe the image before reasoning — this surfaces any misinterpretations early.
**When to escalate:** If the image is too complex or low-resolution for Claude to describe accurately → pre-process the image (OCR, annotation, cropping) before prompting.

---

## Advanced Technique 18 — Graph-prompting

Inject a knowledge graph as structured triples (subject–relation–object) to ground reasoning in explicit relationships.

```
Use the following knowledge graph facts to answer the question.
Each fact is in the format: [Subject] --[Relation]--> [Object]

Knowledge graph:
[Alice] --works_at--> [Acme Corp]
[Bob] --manages--> [Alice]
[Acme Corp] --located_in--> [Berlin]
[Bob] --reports_to--> [Carol]

Question: <question that requires traversing the graph>

Reasoning:
1. Identify which nodes and edges are relevant to the question.
2. Trace the path through the graph.
3. State the answer with the supporting path.
```

**When to use:** Entity relationship queries; organizational charts; dependency graphs; any task where explicit relationship structure improves grounding.
**Claude-specific note:** Plain-text triple format (as above) works reliably. For large graphs (>50 triples), include only the subgraph relevant to the query — inject the full graph only if context budget allows.
**When to escalate:** If the graph is too large to fit in context → use RAG to retrieve relevant triples first, then inject the retrieved subgraph.
