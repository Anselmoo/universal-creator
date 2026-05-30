---
applyTo: "**/*.{jsx,tsx}"
---

# React Component Conventions

## Structure

- Use named function declarations for components, not arrow function variables.
- One component per file. File name must match the exported component name.
- Place `interface Props` or `type Props` immediately before the component function.

## Props

- Define all props explicitly — no object spread `{...props}` passed to DOM elements.
- Mark optional props with `?` in the type definition.
- Do not use `any` or `unknown` for prop types.

## Hooks

- Call hooks only at the top level of a component — never inside conditions or loops.
- Name custom hooks with the `use` prefix.
- Extract repeated hook logic into a custom hook when used in two or more components.

## State and effects

- Use `useState` and `useReducer` over global state for component-local data.
- Every `useEffect` must declare an exhaustive dependency array — no omissions.
- Avoid `useEffect` for data fetching; use React Query, SWR, or equivalent.

## Accessibility

- All interactive elements require an accessible label: `aria-label` or visible text.
- Use semantic HTML elements (`<button>`, `<nav>`, `<main>`) rather than `<div>` with click handlers.
