---
name: <role-name>
description: >-
  <Third-person. What this agent does and when to use it.
   Start with the agent's output or action, not "I" or "You".
   Include specific trigger keywords the user would say.
   Use "Use when…" pattern.
   Max 1024 chars. No XML tags. Lowercase + hyphens only in name.>
tools:
  - <tool1>
  - <tool2>
  # Remove all tools not explicitly required.
  # Default posture: read-only unless writes are justified.
---

# <Role Name>

<One-sentence context: what domain or system this agent operates in>

## Mission

<Imperative one-liner: "Analyze X and return Y." or "Search Z and summarize findings.">

## Scope

<Bullet list of what this agent is responsible for>

- …
- …

## Out of scope

<Anything this agent must refuse or hand back to the caller>

- …
- …

## Input

<What the caller must provide: format, required fields, optional fields>

## Output format

<Exact format of the final answer: JSON schema / markdown sections / plain text>

```
<example output skeleton>
```

## Completion criteria

<When this agent calls task_complete. Must be concrete and measurable.>
- [ ] …
- [ ] …

## Failure handling

<What to do if a sub-call fails, a file is missing, or the task is ambiguous>
- If …: …
- If …: …
