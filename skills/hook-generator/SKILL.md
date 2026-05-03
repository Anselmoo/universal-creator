---
name: hook-generator
description: >-
  Designs and generates Claude Code hook configurations for all 30+ lifecycle events
  including PreToolUse, PostToolUse, PermissionRequest, UserPromptSubmit, Stop,
  SessionStart, SubagentStop, PreCompact, PostCompact, FileChanged, ConfigChange,
  TeammateIdle, TaskCreated, TaskCompleted, and more. Use when the user asks to
  automate Claude Code behavior, enforce rules deterministically, block or approve
  tool calls, inject context after compaction, format code after edits, notify on
  idle, audit configuration changes, gate sub-agent execution, or add any lifecycle
  automation. Generates ready-to-paste JSON hook blocks, shell command scripts,
  prompt-based hook stubs, and agent-based hook stubs. DO NOT USE for general Claude
  API prompt engineering (use prompt-generator skill); for creating Claude agents
  or sub-agents (use agent-generator skill); for writing VS Code instructions (use
  instruction-generator skill).
license: "MIT"
---

# Hook Generator

Produces correct, safe, immediately usable Claude Code hook configurations.
Hooks give **deterministic** control over Claude Code; they run regardless of what
the LLM chooses. Use them only for rules that must always apply.

## Quick Decision: Which Hook Event?

| Goal | Event |
|------|-------|
| Block/approve a tool *before* it runs | `PreToolUse` |
| Validate or log after a tool runs | `PostToolUse` |
| Auto-approve specific permission prompts | `PermissionRequest` |
| Transform or reject user prompts | `UserPromptSubmit` |
| Verify all tasks complete before Claude stops | `Stop` |
| Inject context at session start or after compaction | `SessionStart` |
| Gate or observe sub-agent execution | `SubagentStop` / `SubagentStart` |
| Run logic right before context is compacted | `PreCompact` |
| Re-inject context after compaction | `PostCompact` |
| Track config file changes | `ConfigChange` |
| Reload env when `.env`/`.envrc` changes | `FileChanged` |
| Notify when Claude is idle/waiting | `TeammateIdle` |
| Observe task lifecycle milestones | `TaskCreated` / `TaskCompleted` |
| Handle batch tool completions | `PostToolBatch` |
| Audit failed tool executions | `PostToolUseFailure` |

Full event reference: [events.md](docs/events.md)

## Workflow

Follow these steps in order. Mark each ✓ when done.

### Step 1 — Clarify intent
- [ ] Identify the lifecycle moment (see Quick Decision table above).
- [ ] Identify the trigger scope: specific tool name, any tool, or a non-tool event.
- [ ] Decide: deterministic rule (→ `command` hook) or judgment call (→ `prompt` or `agent` hook)?

### Step 2 — Choose hook type

| Type | Use when | Timeout |
|------|----------|---------|
| `command` | Shell command is enough; fast and deterministic | 60 s default |
| `http` | Need to call an external webhook or REST API | 30 s default |
| `mcp_tool` | Need to invoke an MCP server tool | 60 s default |
| `prompt` | Need LLM judgment (yes/no decision) | 30 s default |
| `agent` | Need LLM + tool use (read files, run commands) | 60 s default |

### Step 3 — Write the matcher

Matchers filter which events fire your hook:

```
PreToolUse / PostToolUse      → tool name (e.g. "Bash", "Edit|Write", "mcp__.*")
SessionStart                  → source  (startup | resume | clear | compact)
PermissionRequest             → tool name
ConfigChange                  → source  (user_settings | project_settings | skills | …)
FileChanged                   → literal filenames (e.g. ".env|.envrc")
SubagentStart / SubagentStop  → agent type (general-purpose | Explore | Plan | custom)
StopFailure                   → error type (rate_limit | authentication_failed | billing_error)
InstructionsLoaded            → load reason (session_start | compact | path_glob_match)
```

**Scoped hooks**: Hooks can also be declared in a skill's or agent's YAML frontmatter under a `hooks` field. Scoped hooks only activate when that skill/agent is in context — use them for tool policies specific to an agent role.

Use `""` (empty string) to match all occurrences of an event.

`if` field: adds argument-level filtering beyond the tool name.
```json
"if": "tool_input.command contains 'rm -rf'"
```
Always use `if` to narrow broad matchers — never auto-approve all Bash commands.

### Step 4 — Define outputs

**For `PreToolUse` (blocking):**
```json
{ "permissionDecision": { "behavior": "allow" } }
{ "permissionDecision": { "behavior": "deny",  "message": "Reason shown to user" } }
{ "permissionDecision": { "behavior": "ask",   "message": "Prompt Claude shows" } }
```

**For `PostToolUse`, `Stop`, `SubagentStop` (non-blocking):**
```json
{ "decision": "block", "reason": "Why Claude should reconsider" }
```
Exit code 0 = success, exit code 2 = block (same as `{"decision":"block"}`).

**For `UserPromptSubmit` (context injection only):**
Use `additionalContext` — **cannot block** this event.
```json
{ "additionalContext": "Project rule: always use Bun, not npm." }
```

**For `prompt`/`agent` hooks — yes/no interface:**
```json
{ "ok": true }
{ "ok": false, "reason": "Explanation fed back to Claude as next instruction" }
```

### Step 5 — Assemble the JSON block

See [templates/hook-block.json](templates/hook-block.json) for copy-paste structures.

To scaffold a minimal valid hook block from the command line:
```bash
python skills/hook-generator/scripts/generate_hook_stub.py \
  --event PostToolUse --type command --intent "run prettier on the edited file"
```
This fills the template for you and outputs a ready-to-paste JSON block.

### Step 6 — Validate the output

After generating a hook block, run the validator to confirm the event name,
`type` field, and output schema are all correct:
```bash
python skills/hook-generator/scripts/validate_hook_output.py <path-to-output>
# or via poe:
poe validate-hook <path-to-output>
```
Exit 0 = valid; non-zero = schema violations printed per block.

### Step 7 — Verify safety checklist

- [ ] Does the hook contain hardcoded secrets or tokens? → Remove; use env vars.
- [ ] Does the hook auto-approve broad patterns (e.g. all Bash)? → Narrow with `if` or `matcher`.
- [ ] Is the script executable and returning valid JSON on stdout? → Test with `echo '{}' | ./hook.sh`.
- [ ] Is the hook in project scope (`.claude/settings.json`) or user scope (`~/.claude/settings.json`)? → Confirm intent.
- [ ] Does an async hook need its side-effects to complete before Claude continues? → Use `"async": false` (only `PostToolUse` supports async).

## Anti-patterns

- **Auto-approving all Bash**: Always use `if` to narrow; never write `"matcher": ""` + allow on `PreToolUse Bash`.
- **Blocking UserPromptSubmit**: The event does not support `decision`. Use `additionalContext` only.
- **Overloading a single hook**: Each concern should be a separate hook entry.
- **Wrong scope**: User-scope hooks (`~/.claude/settings.json`) run on every project. Use project-scope (`.claude/settings.json`) for project-specific rules.
- **Missing SubagentStop on agentic tasks**: If using sub-agents, add a `SubagentStop` hook to verify sub-agent output before Claude continues.
- **Time-sensitive matchers**: Avoid matching on content that changes frequently; prefer tool-name + if combination.
- **Storing secrets in command strings**: Any secret in a JSON file is readable. Use environment variable references.

## Output format

Always deliver hooks as a **complete, pasteable JSON settings fragment** plus any companion scripts.
Reference [examples/](examples/) for common ready-to-use patterns.

Full event schemas, async support, MCP tool hooks: [docs/events.md](docs/events.md)
Security guidance: [docs/security.md](docs/security.md)
