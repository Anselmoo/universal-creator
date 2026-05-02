#!/usr/bin/env python
"""Run repository validation checks for every skill directory.

Called by pre-commit hook `validate-skills`. Exits non-zero if any skill fails.
"""

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
IGNORED_LINK_PREFIXES = ("http://", "https://", "mailto:", "file://")


def iter_skill_dirs() -> list[Path]:
    return sorted(
        skill_dir
        for skill_dir in SKILLS_ROOT.iterdir()
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
    )


def reset_scripts_modules() -> None:
    for key in [k for k in sys.modules if k.startswith("scripts")]:
        del sys.modules[key]


def load_skill_module(skill_dir: Path, module_name: str):
    module_path = skill_dir / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(
        f"{skill_dir.name}_{module_name}", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_skill_frontmatter(skill_dir: Path) -> list[str]:
    errors = []
    try:
        quick_validate_module = load_skill_module(skill_dir, "quick_validate")
        validate_skill = quick_validate_module.validate_skill
        ok, msg = validate_skill(str(skill_dir))
        if ok:
            print(f"  ✓ {skill_dir.name}: quick validation passed")
        else:
            errors.append(msg)
    except Exception as exc:
        errors.append(f"error running validate_skill: {exc}")
    finally:
        reset_scripts_modules()
    return errors


def validate_requirements(skill_dir: Path) -> list[str]:
    requirements_path = skill_dir / "requirements.txt"
    if not requirements_path.exists():
        return ["missing requirements.txt"]

    entries = {
        line.strip().lower()
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    if not any(entry.startswith("pyyaml") for entry in entries):
        return ["requirements.txt must declare pyyaml"]
    return []


def validate_skill_links(skill_dir: Path) -> list[str]:
    missing_links = []
    skill_md = skill_dir / "SKILL.md"
    content = skill_md.read_text()
    for raw_target in LOCAL_LINK_RE.findall(content):
        if raw_target.startswith("#") or raw_target.startswith(IGNORED_LINK_PREFIXES):
            continue
        target_path = raw_target.split("#", 1)[0]
        if not target_path:
            continue
        resolved_target = (skill_dir / target_path).resolve()
        if not resolved_target.exists():
            missing_links.append(f"missing linked file: {raw_target}")
    return missing_links


def validate_script_parity(skill_dirs: list[Path]) -> list[str]:
    """Check that every skill contains all canonical scripts with matching hashes.

    The canonical set is a fixed list of shared scripts that every skill must
    carry.  Skill-specific scripts (e.g. validate_agent_output.py in
    agent-generator, validate_hook_output.py in hook-generator) are intentionally
    NOT in this set and are never required in other skills — they are reported
    informally as extras.

    Skills may have *extra* scripts beyond the canonical set — those are
    reported informally but never treated as failures.  Only *missing*
    canonical scripts or *hash mismatches* on canonical scripts are errors.
    """
    # Fixed list of scripts that EVERY skill must carry (the parity contract).
    # Skill-specific scripts (generators, validators, etc.) must NOT be added here.
    CANONICAL_SCRIPT_NAMES = {
        "__init__.py",
        "aggregate_benchmark.py",
        "errors.py",
        "generate_report.py",
        "improve_description.py",
        "package_skill.py",
        "quick_validate.py",
        "run_eval.py",
        "run_loop.py",
        "utils.py",
    }

    failures = []
    per_skill_hashes = {}

    for skill_dir in skill_dirs:
        script_dir = skill_dir / "scripts"
        per_skill_hashes[skill_dir.name] = {
            script_path.name: hashlib.sha256(script_path.read_bytes()).hexdigest()
            for script_path in sorted(script_dir.glob("*.py"))
        }

    for skill_name, script_hashes in per_skill_hashes.items():
        skill_names = set(script_hashes.keys())
        missing = sorted(CANONICAL_SCRIPT_NAMES - skill_names)
        if missing:
            failures.append(
                f"script parity: {skill_name} missing canonical scripts {missing}"
            )
        extra = sorted(skill_names - CANONICAL_SCRIPT_NAMES)
        if extra:
            # Extra scripts are skill-specific — informational only, not a failure.
            print(f"  ℹ {skill_name}: skill-specific scripts {extra}")

    for script_name in sorted(CANONICAL_SCRIPT_NAMES):
        hashes = {
            skill_name: script_hashes[script_name]
            for skill_name, script_hashes in per_skill_hashes.items()
            if script_name in script_hashes
        }
        if len(set(hashes.values())) > 1:
            failures.append(f"script parity: hash mismatch for {script_name}")

    return failures


def run_skill_specific_validators(skill_dir: Path) -> list[str]:
    """Discover and run any validate_*.py scripts in a skill's scripts/ dir.

    Each validator is expected to exit 0 on success and non-zero on failure,
    printing its own diagnostic lines.  We capture stdout and surface it inline.
    """
    import subprocess

    failures = []
    scripts_dir = skill_dir / "scripts"
    validators = sorted(scripts_dir.glob("validate_*.py"))
    for validator in validators:
        # Pass examples/ as the search path so validators only scan the skill's
        # shipped examples, not the entire workspace.
        examples_dir = skill_dir / "examples"
        args = [sys.executable, str(validator)]
        if examples_dir.is_dir():
            args.append(str(examples_dir))
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  ✓ {skill_dir.name}/{validator.name}")
        else:
            failures.append(
                f"{skill_dir.name}/{validator.name} exited {result.returncode}"
            )
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    print(f"    {line}")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    print(f"    STDERR: {line}")
    return failures


def main() -> int:
    skill_dirs = iter_skill_dirs()
    if not skill_dirs:
        print(f"No skills found under {SKILLS_ROOT}")
        return 1

    failed: list[str] = []

    for skill_dir in skill_dirs:
        skill_errors = []
        skill_errors.extend(validate_skill_frontmatter(skill_dir))
        skill_errors.extend(validate_requirements(skill_dir))
        skill_errors.extend(validate_skill_links(skill_dir))
        skill_errors.extend(run_skill_specific_validators(skill_dir))

        if skill_errors:
            print(f"  ✗ {skill_dir.name}:")
            for error in skill_errors:
                print(f"    - {error}")
            failed.append(skill_dir.name)

    parity_failures = validate_script_parity(skill_dirs)
    if parity_failures:
        print("  ✗ script parity:")
        for failure in parity_failures:
            print(f"    - {failure}")
        failed.append("script-parity")
    else:
        print("  ✓ script parity")

    if failed:
        print(f"\n{len(failed)} validation group(s) failed: {', '.join(failed)}")
        return 1

    print(f"\nValidated {len(skill_dirs)} skill(s) successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
