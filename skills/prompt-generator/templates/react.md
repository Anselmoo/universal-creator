# ReAct Template

Use this template when the model must reason about what to do next, call tools or external resources, observe results, and continue iteratively.

## When to use

Use ReAct when:
- the task requires external lookup or tool use
- the environment changes during execution
- the model needs to decide between multiple investigative steps

## Template

```markdown
You are <role>.

Goal: <task goal>

Use the following loop until the task is complete:

Thought: describe what you need to learn or verify next.
Action: specify the tool call or external action.
Observation: record the result of that action.

Repeat only while more information is required.

When the task is complete, return:
Final Answer: <concise final response>
```

## Guardrails

- Keep thoughts short and decision-focused.
- Use tools only when they materially improve the answer.
- Do not fabricate observations.
- Stop the loop once enough evidence exists to answer well.

## Minimum checklist

- [ ] Thought/Action/Observation loop is explicit
- [ ] Tool use is justified by the task
- [ ] Final answer format is defined
- [ ] The prompt makes it clear when to stop
