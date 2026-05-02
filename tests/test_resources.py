from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from universal_creator import resources


class ResourcesResolutionTests(unittest.TestCase):
    def test_get_bundled_skills_dir_from_wheel_style_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agent-generator").mkdir()
            (root / "agent-generator" / "SKILL.md").write_text("# Agent\n")
            (root / "hook-generator").mkdir()
            (root / "hook-generator" / "SKILL.md").write_text("# Hook\n")
            (root / "random-dir").mkdir()

            with patch.object(resources, "_candidate_skill_roots", return_value=[root]):
                resolved = resources.get_bundled_skills_dir()
                self.assertEqual(resolved, root)
                self.assertEqual(
                    resources.list_bundled_skills(),
                    ["agent-generator", "hook-generator"],
                )

    def test_get_bundled_skills_dir_from_editable_skills_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            (skills_root / "instruction-generator").mkdir(parents=True)
            (skills_root / "instruction-generator" / "SKILL.md").write_text(
                "# Instruction\n"
            )

            with patch.object(
                resources, "_candidate_skill_roots", return_value=[skills_root]
            ):
                resolved = resources.get_bundled_skills_dir()
                self.assertEqual(resolved, skills_root)
                self.assertEqual(
                    resources.list_bundled_skills(), ["instruction-generator"]
                )

    def test_get_bundled_skills_dir_exits_when_no_valid_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            invalid_root = Path(tmp)
            (invalid_root / "agent-generator").mkdir()

            with patch.object(
                resources, "_candidate_skill_roots", return_value=[invalid_root]
            ):
                with self.assertRaises(SystemExit) as exc:
                    resources.get_bundled_skills_dir()
                self.assertEqual(exc.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
