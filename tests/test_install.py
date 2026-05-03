from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from universal_creator.install import resolve_target


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


if __name__ == "__main__":
    unittest.main()
