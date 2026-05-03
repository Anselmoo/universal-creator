from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from universal_creator.install import install_skill, resolve_target


class InstallTargetResolutionTests(unittest.TestCase):
    def test_resolve_target_copilot_local_uses_github_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = resolve_target("copilot", "local", cwd)
            self.assertEqual(target, (cwd / ".github" / "skills").resolve())

    def test_resolve_target_claude_local_still_uses_claude_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = resolve_target("claude", "local", cwd)
            self.assertEqual(target, (cwd / ".claude" / "skills").resolve())

    def test_install_skill_returns_error_when_destination_exists_without_overwrite(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled = root / "bundled-skills"
            src = bundled / "hook-generator"
            src.mkdir(parents=True)
            (src / "SKILL.md").write_text("---\nname: hook-generator\n---\n")

            cwd = root / "workspace"
            dest = cwd / ".github" / "skills" / "hook-generator"
            dest.mkdir(parents=True)
            (dest / "old.txt").write_text("old")

            with (
                patch(
                    "universal_creator.install.list_bundled_skills",
                    return_value=["hook-generator"],
                ),
                patch(
                    "universal_creator.install.get_bundled_skills_dir",
                    return_value=bundled,
                ),
            ):
                result = install_skill("hook-generator", "copilot", "local", cwd)

            self.assertEqual(result, 1)
            self.assertTrue((dest / "old.txt").exists())

    def test_install_skill_overwrites_existing_destination_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled = root / "bundled-skills"
            src = bundled / "hook-generator"
            src.mkdir(parents=True)
            (src / "SKILL.md").write_text("new skill")

            cwd = root / "workspace"
            dest = cwd / ".github" / "skills" / "hook-generator"
            dest.mkdir(parents=True)
            (dest / "old.txt").write_text("old")

            with (
                patch(
                    "universal_creator.install.list_bundled_skills",
                    return_value=["hook-generator"],
                ),
                patch(
                    "universal_creator.install.get_bundled_skills_dir",
                    return_value=bundled,
                ),
            ):
                result = install_skill(
                    "hook-generator",
                    "copilot",
                    "local",
                    cwd,
                    overwrite=True,
                )

            self.assertEqual(result, 0)
            self.assertFalse((dest / "old.txt").exists())
            self.assertEqual((dest / "SKILL.md").read_text(), "new skill")


if __name__ == "__main__":
    unittest.main()
