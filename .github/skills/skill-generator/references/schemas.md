# JSON Schemas — skill-generator

This document defines the JSON schemas used by skill-generator's evaluation
and benchmark infrastructure. The schemas are shared across all skills in
universal-creator; this copy documents any skill-generator-specific extensions.

---

## evals.json

Defines test scenarios for a skill. Located at `evals/evals.json`.

```json
{
  "skill": "skill-generator",
  "version": "1.0",
  "scenarios": [
    {
      "id": "scenario-id",
      "description": "What this scenario tests",
      "query": "The user's task prompt",
      "expected_behavior": [
        "Observable outcome 1",
        "Observable outcome 2"
      ]
    }
  ]
}
```

**Fields:**
- `skill`: Name matching the skill's frontmatter `name` field
- `version`: Schema version string
- `scenarios[].id`: Unique kebab-case identifier
- `scenarios[].description`: Human-readable test description
- `scenarios[].query`: The prompt given to Claude when running this eval
- `scenarios[].expected_behavior`: List of verifiable outcome statements

---

## grading.json

Output written by `agents/grader.md` for each eval run.

```json
{
  "eval_id": "scenario-id",
  "expectations": [
    {
      "text": "Observable outcome statement",
      "passed": true,
      "evidence": "Specific text or file excerpt that supports the verdict"
    }
  ],
  "overall_notes": "Cross-cutting observations not captured by individual assertions"
}
```

**Field constraints:**
- `expectations[].text`: Must match the `expected_behavior` entry verbatim
- `expectations[].passed`: Boolean — `true` or `false` only
- `expectations[].evidence`: Non-empty string; "no evidence" counts as a FAIL

---

## benchmark.json

Aggregated benchmark results across one iteration. Produced by
`scripts/aggregate_benchmark.py`.

```json
{
  "skill_name": "skill-generator",
  "iteration": 1,
  "configurations": [
    {
      "name": "with_skill",
      "evals": [
        {
          "eval_id": "scenario-id",
          "pass_rate": 0.85,
          "total_tokens": 12000,
          "duration_ms": 15000
        }
      ],
      "aggregate": {
        "pass_rate_mean": 0.85,
        "pass_rate_stddev": 0.05,
        "tokens_mean": 12000,
        "duration_ms_mean": 15000
      }
    },
    {
      "name": "without_skill",
      "evals": [],
      "aggregate": {}
    }
  ],
  "delta": {
    "pass_rate": 0.20,
    "tokens": -500,
    "duration_ms": -2000
  }
}
```

---

## timing.json

Wall-clock timing data captured per run from subagent completion notifications.

```json
{
  "total_tokens": 12345,
  "duration_ms": 15000,
  "total_duration_seconds": 15.0
}
```

---

## history.json

Tracks skill improvement iterations. Written to the workspace root.

```json
{
  "started_at": "2026-05-03T10:00:00Z",
  "skill_name": "skill-generator",
  "current_best": "v1",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.60,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "expectation_pass_rate": 0.80,
      "grading_result": "won",
      "is_current_best": true
    }
  ]
}
```

---

## comparison.json

Output written by `agents/comparator.md` for blind A/B comparisons.

```json
{
  "winner": "A",
  "scores": {
    "A": {
      "scope_clarity": 4,
      "workflow_completeness": 5,
      "convention_depth": 4,
      "antipattern_coverage": 3,
      "script_quality": 4
    },
    "B": {
      "scope_clarity": 3,
      "workflow_completeness": 4,
      "convention_depth": 3,
      "antipattern_coverage": 2,
      "script_quality": 3
    }
  },
  "reason": "Explanation of deciding factors",
  "key_gaps": ["Gap 1 in losing candidate", "Gap 2"]
}
```

---

## SKILL.md frontmatter schema

Expected fields in every SKILL.md in universal-creator:

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `name` | string | yes | kebab-case, ≤64 chars |
| `description` | string | yes | ≥20 chars; should include trigger phrases and DO NOT USE clause |
| `license` | string | no | e.g. `"MIT"` |

Body required sections:

| Section heading | Hard required? |
|----------------|---------------|
| `## Workflow` | yes |
| `## Anti-patterns` | yes |
| `## Output format` | yes |
| `## Conventions` | advisory |
