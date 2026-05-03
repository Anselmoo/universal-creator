---
name: instruction-generator
description: >-
  Creates and refines workspace and file-level instruction files: copilot-instructions.md,
  AGENTS.md, and *.instructions.md. Use when the user wants to save coding preferences,
  enforce team conventions, apply rules to specific file patterns, configure always-on
  agent behavior, document style guides for Claude to follow automatically, or scope
  instructions to a particular language, framework, or workflow area. Generates
  ready-to-use instruction markdown with correct applyTo patterns, concise rule sets,
  and optional extended variants for fragile workflows. DO NOT USE for
  one-shot prompts (use prompt-generator); for custom agent role definitions
  (use agent-generator); for Claude Code lifecycle hooks (use hook-generator).
license: "MIT"
---

# Instruction Generator

Produces clear, scoped, non-contradictory instruction files that Claude loads
and follows automatically.

Instructions are **always-on**: they apply whenever Claude processes matching
files or contexts. Keep them concise. Every word in an instruction file costs
context tokens on every invocation.

## Quick Decision: Which instruction file?

| Need | File | Location |
|------|------|----------|
| Applies to the whole workspace / all files | `copilot-instructions.md` or `AGENTS.md` | `.github/` or root |
| Applies to specific file types or folders | `<name>.instructions.md` | `.github/instructions/` |
| Applies to user (cross-workspace) | `<name>.instructions.md` | `{{VSCODE_USER_PROMPTS_FOLDER}}/` |

`applyTo` patterns:
- `"**"` — matches all files
- `"**/*.ts"` — TypeScript files
- `"src/**"` — everything under `src/`
- `"**/*.{ts,tsx}"` — multiple extensions
- Leave `applyTo` absent for on-demand instructions (not auto-applied)

## Workflow

Follow these steps in order. Mark each ✓ when done.

### Step 1 — Clarify scope

Answer before writing:
- **Who is this for?** All team members (workspace) or just this user (user-level)?
- **What files trigger it?** Language, framework, folder, or all files?
- **What behavior changes?** Style, safety rules, prohibited patterns, or workflow steps?

### Step 2 — Choose depth

| Variant | Use when | Target length |
|---------|----------|---------------|
| Concise rules | Simple preferences (naming, style, imports) | ≤ 20 lines |
| Extended rules | Fragile workflows, multi-step processes, error-prone areas | 20–60 lines |
| Reference-based | Large rule sets; use progressive disclosure | SKILL body → `details.md` |

If the instruction body would exceed 60 lines, split it:
- SKILL body: overview + key rules
- Separate `*.md` file: extended rules, examples, edge cases

### Step 3 — Write the instruction

```markdown
---
applyTo: "<glob>"
description: "<optional: use for on-demand instructions>"
---

# <Short title>

<Context sentence: what this file covers and why>

## Rules

- <Rule 1: imperative, specific, verifiable>
- <Rule 2: imperative, specific, verifiable>
- <Rule n>

## Do not

- <Prohibited action 1>
- <Prohibited action 2>
```

See [templates/instructions-concise.md](templates/instructions-concise.md) and
[templates/instructions-extended.md](templates/instructions-extended.md).

To scaffold a stub from the command line:
```bash
python skills/instruction-generator/scripts/generate_instruction_stub.py \
  --apply-to "**/*.ts" --title "TypeScript rules" [--variant concise|extended]
```

### Step 4 — Rewrite vague rules

Run each rule through this test: "Can Claude determine pass/fail without judgment?"

| Vague (reject) | Specific (accept) |
|----------------|-------------------|
| "Write good code" | "Prefer pure functions; avoid side effects in utility modules" |
| "Be concise" | "Keep function bodies under 40 lines; extract helpers if exceeded" |
| "Handle errors properly" | "Wrap async calls in try/catch; surface errors to the caller — never swallow" |
| "Use modern syntax" | "Use ES2022+; prefer `?.` and `??` over manual null checks" |

### Step 5 — Check for contradictions

- [ ] Does any rule contradict another in this file?
- [ ] Does any rule contradict existing instructions in `.github/copilot-instructions.md`?
- [ ] Are `applyTo` patterns precise enough? (Overly broad patterns → high context cost)

### Step 6 — Validate quality checklist

- [ ] Every rule is imperative and verifiable (no "should", "try to", "consider").
- [ ] `applyTo` pattern is correct glob syntax — validated against target file paths.
- [ ] No time-sensitive information (no version numbers with expiry dates, no API phases).
- [ ] Consistent terminology throughout (same term for same concept).
- [ ] Instructions don't duplicate VS Code / Copilot defaults.
- [ ] File length is appropriate for the chosen depth variant.

Run the validator to catch soft rules and frontmatter issues automatically:
```bash
python skills/instruction-generator/scripts/validate_instruction_output.py <path>
# or via poe:
poe validate-instructions <path>
```

## Anti-patterns

- **Omnibus instructions**: one file covering too many unrelated concerns. Split by domain.
- **Soft rules**: "prefer" without a fallback condition. Use "unless X, then Y" when needed.
- **Stale specifics**: "until August 2025 use the old API" — becomes wrong immediately.
- **Missing `applyTo`**: without a glob, the file is on-demand only; teams expecting auto-apply will be confused.
- **Duplicating documentation**: instructions should tell Claude *what* to do, not *explain* the library.

## Output format

Deliver the full instruction file (frontmatter + body) and note:
- Recommended file path
- Recommended scope (workspace vs user)
- Any follow-up rule files if progressive disclosure was used

See [examples/](examples/) for language-specific and workflow-specific patterns.
Concise template: [templates/instructions-concise.md](templates/instructions-concise.md)
Extended template: [templates/instructions-extended.md](templates/instructions-extended.md)
