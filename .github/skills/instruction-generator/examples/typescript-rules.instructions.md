---
applyTo: "**/*.ts"
---

# TypeScript Coding Rules

Applies to all TypeScript files in this workspace.

## Rules

- Use strict TypeScript (`"strict": true`). Never use `any`; use `unknown` and narrow explicitly.
- Use `const` over `let`. Use `let` only when reassignment is required.
- Use `?.` and `??` over manual null/undefined checks.
- Export named exports only; avoid default exports.
- Keep functions under 40 lines. Extract helpers if a function grows beyond this.
- Wrap async operations in try/catch. Surface errors to the caller — never swallow them silently.
- Use `z.parse` (Zod) or equivalent for all external data at system boundaries.

## Do not

- Do not use `@ts-ignore` or `@ts-expect-error` without a JSDoc comment explaining why.
- Do not import from `..` more than two levels deep — restructure if needed.
- Do not use `console.log` in production code — use the project logger.
