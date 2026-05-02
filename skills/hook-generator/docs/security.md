# Hook Security Guide

Use this reference when generating or reviewing Claude Code hooks that execute commands, call HTTP endpoints, or invoke agent/prompt logic.

## Core safety rules

- Never hardcode secrets, API keys, tokens, or passwords in hook JSON or companion scripts.
- Prefer environment variables for credentials and document the variable names explicitly.
- Keep matchers narrow. Avoid broad approvals like allowing every `Bash` invocation.
- Use the `if` field to restrict high-risk tools by arguments, paths, or command fragments.
- Prefer project-scoped hooks for repository rules; use user-scoped hooks only for truly global policies.

## Command hook safety

- Quote shell variables defensively.
- Treat any interpolated user-controlled value as untrusted input.
- Avoid `eval`, command substitution of untrusted text, and permissive globbing.
- Return valid JSON on stdout for machine-readable decisions.
- Fail closed: if validation cannot complete, deny or ask instead of silently allowing.

## Approval design

Use `allow` only when the matcher and conditions are specific enough that accidental overreach is unlikely.

Prefer these defaults:
- `ask` for potentially destructive actions
- `deny` for clearly prohibited patterns
- `allow` only for low-risk, precisely constrained cases

## Secrets and logging

- Do not echo secrets into terminal output, logs, or JSON messages.
- Redact tokens and credentials before returning errors.
- Keep audit logs high-signal: record event, matcher, and decision reason, not sensitive payloads.

## Companion script checklist

Before shipping a hook with a script:

- [ ] Script is executable when needed
- [ ] Script returns valid JSON for supported hook types
- [ ] Script handles malformed input safely
- [ ] Script has bounded runtime and clear failure behavior
- [ ] Script does not depend on undeclared local state

## Scope decisions

| Scope | Use when | Risk |
|-------|----------|------|
| Project | Rule is repository-specific | Lower blast radius |
| User | Rule should follow the user everywhere | Higher blast radius |
| Agent/Skill frontmatter | Rule should apply only in a specific guided workflow | Most precise |

## Practical anti-patterns

- Auto-approving all shell commands
- Embedding bearer tokens directly in hook JSON
- Relying on `UserPromptSubmit` to block content when that event only supports `additionalContext`
- Using one giant hook for unrelated concerns instead of separate focused entries

## Validation tip

Test the companion script with representative sample input and confirm that:

1. the output is valid JSON
2. the decision shape matches the hook event requirements
3. failure cases are explicit and safe
