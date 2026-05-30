# Hook Generator — Events Reference

## Hook lifecycle events and their capabilities

Events are grouped by when they fire in the Claude Code lifecycle. "Can block?" means the hook's output can halt or redirect Claude's behavior.

### Session-level

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `SessionStart` | Session begins, resumes, or context is cleared | No | source (startup \| resume \| clear \| compact) |
| `Setup` | CLI `--setup` flag triggered | No | flag name |
| `InstructionsLoaded` | An instructions file is loaded into context | No | load reason (session_start \| compact \| path_glob_match \| nested_traversal) |
| `SessionEnd` | Session ends | No | reason (clear \| resume \| logout \| other) |

### Turn-level

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `UserPromptSubmit` | User submits a message | `additionalContext` only (no block) | — |
| `UserPromptExpansion` | A skill or slash-command is expanded | No | command name |
| `Elicitation` | An MCP server issues an elicitation request | No | MCP server name |
| `ElicitationResult` | Elicitation result is returned | No | MCP server name |
| `TeammateIdle` | Claude is idle, waiting for teammate input | No | — |

### Agentic loop (tool execution)

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `PreToolUse` | Before a tool runs | **Yes** (`permissionDecision`) | tool name |
| `PostToolUse` | After a tool succeeds | **Yes** (`decision: "block"`) | tool name |
| `PostToolBatch` | After a batch of parallel tool calls completes | No | — |
| `PostToolUseFailure` | After a tool fails with an error | No | tool name |
| `PermissionRequest` | Claude requests permission to use a tool | **Yes** (`hookSpecificOutput.decision`) | tool name |
| `PermissionDenied` | A permission request is denied | No | tool name |

### Stop / completion

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `Stop` | Claude is about to emit its final response | **Yes** (`decision: "block"`) | — |
| `StopFailure` | Claude stop attempt errored | No | error type (rate_limit \| authentication_failed \| billing_error \| server_error) |
| `TaskCreated` | A task is added to Claude's task list | No | — |
| `TaskCompleted` | A task is marked complete | No | — |

### Sub-agent / async

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `SubagentStart` | A sub-agent is spawned | No | agent type (general-purpose \| Explore \| Plan \| custom) |
| `SubagentStop` | A sub-agent finishes | **Yes** (`decision: "block"`) | agent type |

### Compaction

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `PreCompact` | Before context compaction runs | No | trigger type |
| `PostCompact` | After compaction completes | No | trigger type |

### Filesystem / config

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `FileChanged` | A watched file changes on disk | No | filename (literal, e.g. `.env\|.envrc`) |
| `ConfigChange` | A Claude config file changes externally | **Yes** (exit 2) | config source (user_settings \| project_settings \| local_settings \| skills) |
| `CwdChanged` | Working directory changes | No | — |
| `WorktreeCreate` | A git worktree is created | No | — |
| `WorktreeRemove` | A git worktree is removed | No | — |

### Notifications

| Event | Fires when | Can block? | Matcher field |
|-------|-----------|-----------|---------------|
| `Notification` | Claude sends a notification to the user | No | notification type (permission_prompt \| idle_prompt \| auth_success) |

## Decision schema summary

### PreToolUse
```json
{
  "permissionDecision": {
    "behavior": "allow" | "deny" | "ask",
    "message": "<optional reason shown to Claude or user>"
  }
}
```

### PostToolUse / Stop / SubagentStop
```json
{ "decision": "block", "reason": "<fed back to Claude as next instruction>" }
```
Exit code 2 = equivalent to `{"decision": "block"}`.

### UserPromptSubmit
```json
{ "additionalContext": "<injected into Claude's context; cannot block>" }
```

### PermissionRequest
```json
{
  "hookSpecificOutput": {
    "decision": {
      "behavior": "allow" | "deny" | "ask",
      "message": "<optional>"
    }
  }
}
```

### prompt / agent hooks (all supporting events)
```json
{ "ok": true }
{ "ok": false, "reason": "<Claude uses this as its next instruction>" }
```

## Matcher patterns by event

```
PreToolUse / PostToolUse  → "Bash"  "Edit|Write"  "mcp__server__tool"  ""
SessionStart              → "startup"  "resume"  "clear"  "compact"
SessionEnd                → "clear"  "resume"  "logout"  "prompt_input_exit"  "other"
ConfigChange              → "user_settings"  "project_settings"  "local_settings"  "skills"
FileChanged               → ".env|.envrc"  (literal filenames)
SubagentStart/Stop        → "general-purpose"  "Explore"  "Plan"  "<custom-name>"
StopFailure               → "rate_limit"  "authentication_failed"  "billing_error"  "server_error"
Notification              → "permission_prompt"  "idle_prompt"  "auth_success"
InstructionsLoaded        → "session_start"  "nested_traversal"  "path_glob_match"  "compact"
```

## Settings file locations

| Scope | File |
|-------|------|
| User (global) | `~/.claude/settings.json` |
| Project | `.claude/settings.json` |
| Local (not committed) | `.claude/settings.local.json` |
| Policy (managed) | `.claude/policy.json` |

**Precedence:** `policy.json` > `settings.json` (project) > `settings.local.json` > `~/.claude/settings.json`

Policy settings always override hook approvals.

## Security checklist

- Never hardcode secrets in hook commands — use env vars (`$MY_TOKEN`)
- Never auto-approve broad `PreToolUse Bash` matchers without `if` narrowing
- Validate that scripts referenced by hooks are executable and auditable
- Keep hook scripts in `.claude/hooks/` and commit them alongside settings
- Review hooks when onboarding to a new project — they execute with your user permissions

---

## OpenAI Codex hooks — comparison

OpenAI Codex supports hooks via a **command handler only** (no http/mcp_tool/prompt/agent types). Hooks must be enabled with `[features] codex_hooks = true` in `config.toml`. Hook scripts live in `.codex/hooks/` or are declared inline.

| Codex Event | Claude Code Equivalent | Notes |
|-------------|----------------------|-------|
| `SessionStart` | `SessionStart` | Same semantics; Codex sources: `startup`, `resume` |
| `PreToolUse` | `PreToolUse` | Same blocking semantics; Codex uses exit code for allow/deny |
| `PermissionRequest` | `PermissionRequest` | Same; Codex prompts user via terminal only |
| `PostToolUse` | `PostToolUse` | Same; Codex exit 2 = block |
| `UserPromptSubmit` | `UserPromptSubmit` | Codex cannot inject `additionalContext` — output ignored |
| `Stop` | `Stop` | Same blocking semantics |

**Key Codex differences:**
- 6 events total (vs 30+ in Claude Code)
- Command handler only — no `http`, `mcp_tool`, `prompt`, or `agent` hook types
- Hooks stored in `.codex/hooks/` (vs `.claude/hooks/`)
- Config: `config.toml` with `[features] codex_hooks = true` (vs `settings.json`)
- No scoped hooks in agent/skill frontmatter
