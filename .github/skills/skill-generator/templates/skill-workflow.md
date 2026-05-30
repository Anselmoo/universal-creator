---
name: {{SKILL_NAME}}
description: >-
  {{SKILL_DESCRIPTION}}
  Use when the user wants to generate {{ARTIFACT_TYPE}} files or scaffold
  {{ARTIFACT_TYPE}} structures. DO NOT USE for [competing skill 1]
  (use [skill-name]); for [competing skill 2] (use [skill-name]).
license: "MIT"
---

# {{SKILL_TITLE}}

TODO: One sentence explaining what this skill produces and why it exists.

## Quick Decision

| Goal | Use instead |
|------|------------|
| [Adjacent need 1] | [skill-name] |
| [Adjacent need 2] | [skill-name] |

## Workflow

Follow these steps in order. Mark each ✓ when done.

### Step 1 — Clarify intent

Answer these questions before writing anything:

- **What is the target artifact?** (file name, extension, structure)
- **What inputs does the user have?** (schema, spec, existing file, free text)
- **What conventions apply?** (naming, required fields, style rules)

### Step 2 — Design the artifact structure

Define the required sections or fields for a well-formed {{ARTIFACT_TYPE}}:

```
Field/Section 1:  <description>
Field/Section 2:  <description>
Field/Section N:  <description>
```

### Step 3 — Scaffold with the generator script

```bash
python skills/{{SKILL_NAME}}/scripts/generate_{{SKILL_NAME}}_stub.py \
  --name <name> --description "<one-line description>" [--out FILE]
```

The stub creates a minimal valid {{ARTIFACT_TYPE}} ready to edit.

### Step 4 — Fill in domain content

1. Replace TODO stubs with real content.
2. Apply conventions from the ## Conventions section below.
3. Check against ## Anti-patterns before delivering.

### Step 5 — Validate

```bash
python skills/{{SKILL_NAME}}/scripts/validate_{{SKILL_NAME}}_output.py <path>
```

Fix any hard errors before delivering the output.

## Conventions

TODO: List the quality rules for a well-formed {{ARTIFACT_TYPE}}.

- **Convention 1** — Explanation of what is required and why.
- **Convention 2** — Explanation of what is required and why.
- **Convention N** — Explanation of what is required and why.

## Anti-patterns

TODO: List failure modes and explain why each is harmful.

**Anti-pattern 1** — Description. This is harmful because...

**Anti-pattern 2** — Description. This is harmful because...

**Anti-pattern 3** — Description. This is harmful because...

## Output format

Deliver a complete `{{ARTIFACT_TYPE}}` file (or directory) containing:

```
<name>.<ext>           # primary artifact
<name>.validation.txt  # optional: validation output
```

Examples: [examples/](examples/)
Generator script: [scripts/generate_{{SKILL_NAME}}_stub.py](scripts/generate_{{SKILL_NAME}}_stub.py)
Validator script: [scripts/validate_{{SKILL_NAME}}_output.py](scripts/validate_{{SKILL_NAME}}_output.py)
