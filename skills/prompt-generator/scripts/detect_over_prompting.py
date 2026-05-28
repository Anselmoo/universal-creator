#!/usr/bin/env python
"""Detect over-prompting patterns in a *.prompt.md file.

Counts ALL-CAPS emphasis words (ALWAYS, NEVER, CRITICAL, MUST, IMPORTANT,
REMEMBER, FORBIDDEN, WARNING, NOTE) per 100 words and classifies the result:

  - density ≤ 1 / 100 words → clean
    - density 1-3 / 100 words → borderline
  - density > 3 / 100 words → over-prompted

Also flags specific anti-pattern phrases that are rarely needed in well-written
prompts (e.g. "YOU MUST", "DO NOT EVER", "ABSOLUTELY").

Exit 0 if clean or borderline; exit 1 if over-prompted (useful in CI or as
a quality gate).

Usage:
    python detect_over_prompting.py <prompt_file>
    python -m skills.prompt-generator.scripts.detect_over_prompting <prompt_file>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Emphasis words that are meaningful to count
_EMPHASIS_WORDS = {
    "ALWAYS",
    "NEVER",
    "CRITICAL",
    "MUST",
    "IMPORTANT",
    "REMEMBER",
    "FORBIDDEN",
    "WARNING",
    "MANDATORY",
    "ABSOLUTELY",
    "ENSURE",
    "REQUIRED",
    "DO NOT",
    "YOU MUST",
    "MAKE SURE",
}

# Single-word match (handles words that appear in ALL CAPS in prose)
_ALLCAPS_WORD_RE = re.compile(r"\b([A-Z]{2,})\b")

# Multi-word phrase patterns
_PHRASE_RE = re.compile(
    r"\b(DO NOT|YOU MUST|MAKE SURE|DO NOT EVER|NEVER EVER|ALWAYS ALWAYS|"
    r"CRITICAL[LY]*|MANDATORY|ABSOLUTELY)\b"
)

# Strip frontmatter before analysis
_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

# Ignore lines that are code blocks (between ``` fences) — those may have caps for valid reasons
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

# Common legitimate ALL-CAPS words that aren't over-prompting
_ALLOWLIST = {
    "URL",
    "API",
    "JSON",
    "YAML",
    "HTML",
    "CSS",
    "SQL",
    "CLI",
    "SDK",
    "GPT",
    "LLM",
    "AI",
    "ID",
    "UI",
    "UX",
    "TBD",
    "TODO",
    "FAQ",
    "HTTP",
    "HTTPS",
    "REST",
    "JWT",
    "UUID",
    "EOF",
    "NULL",
    "TRUE",
    "FALSE",
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
}


def _strip_code_blocks(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text)


def analyze(path: Path) -> dict:
    """Analyze a prompt file and return a result dict."""
    text = path.read_text(encoding="utf-8")

    # Remove frontmatter
    text = _FRONTMATTER_RE.sub("", text, count=1)

    # Remove code blocks (legitimate ALL-CAPS in code are fine)
    clean_text = _strip_code_blocks(text)

    words = clean_text.split()
    word_count = len(words)
    if word_count == 0:
        return {
            "path": str(path),
            "word_count": 0,
            "emphasis_count": 0,
            "density_per_100": 0.0,
            "classification": "clean",
            "flagged_lines": [],
        }

    # Count emphasis hits
    flagged_lines: list[dict] = []
    emphasis_count = 0

    for lineno, line in enumerate(clean_text.splitlines(), start=1):
        line_hits: list[str] = []

        # Check multi-word phrases first
        for m in _PHRASE_RE.finditer(line):
            line_hits.append(m.group(0))
            emphasis_count += 1

        # Then single ALL-CAPS words (not in allowlist, not already counted as phrase)
        for m in _ALLCAPS_WORD_RE.finditer(line):
            word = m.group(1)
            if word not in _ALLOWLIST and word not in _EMPHASIS_WORDS:
                # Only count if the word looks like emphasis (not an acronym of known type)
                # Heuristic: 4+ chars and all caps is suspicious in prose context
                if len(word) >= 4:
                    line_hits.append(word)
                    emphasis_count += 1
            elif word in _EMPHASIS_WORDS:
                line_hits.append(word)
                emphasis_count += 1

        if line_hits:
            flagged_lines.append(
                {"line": lineno, "text": line.strip(), "hits": list(set(line_hits))}
            )

    density = (emphasis_count / word_count) * 100
    if density <= 1.0:
        classification = "clean"
    elif density <= 3.0:
        classification = "borderline"
    else:
        classification = "over-prompted"

    return {
        "path": str(path),
        "word_count": word_count,
        "emphasis_count": emphasis_count,
        "density_per_100": round(density, 2),
        "classification": classification,
        "flagged_lines": flagged_lines,
    }


def _print_report(result: dict) -> None:
    icon = {"clean": "✓", "borderline": "△", "over-prompted": "✗"}[
        result["classification"]
    ]
    print(f"  {icon} {result['path']}")
    print(
        f"    {result['emphasis_count']} emphasis hits / "
        f"{result['word_count']} words "
        f"= {result['density_per_100']:.1f} / 100 → {result['classification']}"
    )
    if result["flagged_lines"]:
        print("    Flagged lines:")
        for fl in result["flagged_lines"][:10]:  # cap at 10 to avoid noise
            hits_str = ", ".join(fl["hits"])
            print(f"      line {fl['line']}: [{hits_str}] {fl['text'][:100]}")


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <prompt_file_or_dir>", file=sys.stderr)
        return 1

    target = Path(sys.argv[1])
    if target.is_dir():
        files = sorted(target.rglob("*.prompt.md"))
    elif target.is_file():
        files = [target]
    else:
        print(f"ERROR: not a file or directory: {target}", file=sys.stderr)
        return 1

    if not files:
        print(f"No *.prompt.md files found under {target}")
        return 0

    exit_code = 0
    for path in files:
        result = analyze(path)
        _print_report(result)
        if result["classification"] == "over-prompted":
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
