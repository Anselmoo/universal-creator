# Prompt Chaining Template

Use this template when the task decomposes into sequential stages and each intermediate output can be checked before the next stage runs.

## When to use

Use prompt chaining when:
- the task has naturally separable stages
- each stage produces a reusable intermediate artifact
- accuracy improves when later steps are constrained by earlier outputs

## Template

```markdown
### Prompt 1 — <stage name>
<Role or context>

<Task for stage 1>

Return output in this exact format:
<stage_1_output>
...
</stage_1_output>

### Prompt 2 — <stage name>
Using only the result inside `<stage_1_output>`, do the following:

<Task for stage 2>

Return output in this exact format:
<stage_2_output>
...
</stage_2_output>

### Prompt 3 — Final answer
Using only the validated outputs above:

<Final synthesis task>

Return:
<final_answer>
...
</final_answer>
```

## Design notes

- Give each stage one job.
- Make intermediate outputs explicit and easy to validate.
- Tell the next stage what prior output it is allowed to use.
- Avoid unnecessary stages; each extra step adds latency and coordination cost.

## Minimum checklist

- [ ] Each stage has a distinct purpose
- [ ] Intermediate outputs are structured
- [ ] Downstream stages are constrained to prior outputs
- [ ] Final stage does synthesis, not rework
