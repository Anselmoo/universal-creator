# Shared memory guardrails

Common conventions for any agent that reads from or writes to the memory
system (`#tool:vscode/memory`, `#tool:serena/*_memory`).

Each agent links here from its own `## Memory guardrails` section and adds
**one** line naming its specific write policy (e.g. "read-only",
"`#tool:vscode/memory` + `#tool:serena/write_memory` only"). The rules below
apply universally and need not be restated per agent.

## Conflict signal

When retrieved memories contain contradictory context relevant to the agent's
scoped task, surface the conflict in the agent's structured output —
under `**Risks or blockers**`, `**Eval scenarios**`, `**Decisions**`, or the
agent's equivalent section — rather than silently resolving it. Conflict
resolution belongs to `universal-plan`'s stroke-mode procedure, not to
downstream subagents.

## Session-scope deletes only

Only `/memories/session/*` entries may be deleted by any subagent. The
`/memories/repo/*` namespace and the global user memory are read-only unless
the user explicitly authorizes a write in the invocation. `universal-plan`'s
stroke-mode procedure is the single exception and is documented in
[`universal-plan.agent.md`](./universal-plan.agent.md).

## Prefer compaction over deletion

When a memory entry is outdated, partially correct, or overlapping with a
newer entry, use `#tool:serena/edit_memory` to compact or rewrite it. Reach
for `#tool:serena/delete_memory` only when:

- the referenced item no longer exists in the workspace, or
- compaction cannot resolve a direct contradiction with a newer entry that
  shares the same key.

## Resume token: `/memories/session/plan.md`

The canonical resume token for the planning suite is
`/memories/session/plan.md`. Subagents must not move, rename, or rewrite this
file; only `universal-plan` owns its lifecycle. Subagents that need to record
findings write to a separate session entry (e.g.
`/memories/session/<topic-slug>.md`) and reference it from their structured
output so `universal-plan` can synthesize.
