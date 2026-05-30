"""Tests for ``universal_creator.sync.sync_scripts``.

Covers the canonical-script parity flow: identical-file short-circuit,
overwrite=False skip behaviour, overwrite=True replacement, and
preservation of skill-specific scripts that are not in the parity list.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from universal_creator import sync as sync_module


def _make_skills_layout(
    root: Path,
    canonical_scripts: dict[str, str],
    other_skills: dict[str, dict[str, str]],
) -> Path:
    """Build a skills/ tree with a canonical skill plus consumer skills.

    Returns the skills root directory.
    """
    skills_root = root / "skills"
    canonical_dir = skills_root / "agent-generator" / "scripts"
    canonical_dir.mkdir(parents=True)
    for name, content in canonical_scripts.items():
        (canonical_dir / name).write_text(content, encoding="utf-8")
    for skill_name, scripts in other_skills.items():
        target = skills_root / skill_name / "scripts"
        target.mkdir(parents=True)
        for name, content in scripts.items():
            (target / name).write_text(content, encoding="utf-8")
    return skills_root


class SyncScriptsTests(unittest.TestCase):
    def test_skips_identical_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = _make_skills_layout(
                root,
                canonical_scripts={"utils.py": "shared utils"},
                other_skills={"skill-generator": {"utils.py": "shared utils"}},
            )

            with patch.object(sync_module, "_SKILLS_DIR", skills_root):
                rc = sync_module.sync_scripts()

            self.assertEqual(rc, 0)
            self.assertEqual(
                (skills_root / "skill-generator" / "scripts" / "utils.py").read_text(),
                "shared utils",
            )

    def test_overwrite_false_leaves_divergent_files_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = _make_skills_layout(
                root,
                canonical_scripts={"utils.py": "v2"},
                other_skills={"skill-generator": {"utils.py": "v1-local-edit"}},
            )

            with patch.object(sync_module, "_SKILLS_DIR", skills_root):
                rc = sync_module.sync_scripts(overwrite=False)

            self.assertEqual(rc, 0)
            self.assertEqual(
                (skills_root / "skill-generator" / "scripts" / "utils.py").read_text(),
                "v1-local-edit",
            )

    def test_overwrite_true_replaces_divergent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = _make_skills_layout(
                root,
                canonical_scripts={"utils.py": "v2"},
                other_skills={"skill-generator": {"utils.py": "v1-local-edit"}},
            )

            with patch.object(sync_module, "_SKILLS_DIR", skills_root):
                rc = sync_module.sync_scripts(overwrite=True)

            self.assertEqual(rc, 0)
            self.assertEqual(
                (skills_root / "skill-generator" / "scripts" / "utils.py").read_text(),
                "v2",
            )

    def test_skill_specific_scripts_survive_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = _make_skills_layout(
                root,
                canonical_scripts={"utils.py": "shared"},
                other_skills={
                    "skill-generator": {
                        "utils.py": "shared",
                        # Not in the parity list — must be left alone.
                        "validate_skill_output.py": "skill-specific logic",
                    }
                },
            )

            with patch.object(sync_module, "_SKILLS_DIR", skills_root):
                rc = sync_module.sync_scripts(overwrite=True)

            self.assertEqual(rc, 0)
            survivor = (
                skills_root / "skill-generator" / "scripts" / "validate_skill_output.py"
            )
            self.assertTrue(survivor.is_file())
            self.assertEqual(survivor.read_text(), "skill-specific logic")

    def test_returns_error_when_canonical_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            skills_root.mkdir()

            with patch.object(sync_module, "_SKILLS_DIR", skills_root):
                rc = sync_module.sync_scripts(canonical="does-not-exist")

            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
