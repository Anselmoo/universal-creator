from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from universal_creator.install import (
    install_entrypoint,
    install_skill,
    resolve_agent_target,
    resolve_target,
)
from universal_creator.manifest import (
    MANIFEST_RELATIVE_PATH,
    read_manifest,
)
from universal_creator.resources import list_bundled_agents


def _build_bundled_shared(root: Path) -> Path:
    """Build a representative fake bundled ``shared`` skill under ``root``.

    Returns the bundled-skills root (parent of ``shared/``).
    """
    bundled_root = root / "bundled-skills"
    shared = bundled_root / "shared"
    shared.mkdir(parents=True)
    (shared / "SKILL.md").write_text(
        "---\nname: shared\n---\nbundled v1\n", encoding="utf-8"
    )
    (shared / "techniques.json").write_text('{"version": "1"}\n', encoding="utf-8")
    (shared / "examples").mkdir()
    (shared / "examples" / "zero-shot.prompt.md").write_text(
        "bundled zero-shot example\n", encoding="utf-8"
    )
    (shared / "agents").mkdir()
    (shared / "agents" / "validation-reviewer.agent.md").write_text(
        "---\nname: validation-reviewer\n---\nbundled trio agent\n",
        encoding="utf-8",
    )
    (shared / "agents" / "_memory-guardrails.md").write_text(
        "bundled guardrails snippet\n", encoding="utf-8"
    )
    return bundled_root


def _install_shared(
    bundled_root: Path, cwd: Path, *, force_shared: bool = False
) -> int:
    """Drive ``install_skill('shared', 'claude', 'local')`` against a fake bundle."""
    with (
        patch(
            "universal_creator.install.list_bundled_skills",
            return_value=["shared"],
        ),
        patch(
            "universal_creator.install.get_bundled_skills_dir",
            return_value=bundled_root,
        ),
    ):
        return install_skill(
            "shared", "claude", "local", cwd, force_shared=force_shared
        )


class InstallTargetResolutionTests(unittest.TestCase):
    def test_resolve_target_copilot_local_uses_github_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = resolve_target("copilot", "local", cwd)
            self.assertEqual(target, (cwd / ".github" / "skills").resolve())

    def test_resolve_target_gemini_local_uses_agents_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = resolve_target("gemini", "local", cwd)
            self.assertEqual(target, (cwd / ".agents" / "skills").resolve())

    def test_resolve_target_codex_global_uses_agents_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with patch("universal_creator.install.Path.home", return_value=home):
                target = resolve_target("codex", "global")
            self.assertEqual(target, (home / ".agents" / "skills").resolve())

    def test_resolve_target_claude_local_still_uses_claude_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = resolve_target("claude", "local", cwd)
            self.assertEqual(target, (cwd / ".claude" / "skills").resolve())

    def test_resolve_agent_target_gemini_local_uses_agents_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            target = resolve_agent_target("gemini", "local", cwd)
            self.assertEqual(target, (cwd / ".agents" / "agents").resolve())

    def test_resolve_agent_target_codex_global_uses_agents_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with patch("universal_creator.install.Path.home", return_value=home):
                target = resolve_agent_target("codex", "global")
            self.assertEqual(target, (home / ".agents" / "agents").resolve())

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

    def test_install_entrypoint_overwrites_existing_destination_when_requested(
        self,
    ) -> None:
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
                result = install_entrypoint(
                    "hook-generator",
                    "copilot",
                    "local",
                    cwd,
                    overwrite=True,
                    backup=False,
                    interactive=False,
                )

            self.assertEqual(result, 0)
            self.assertFalse((dest / "old.txt").exists())
            self.assertEqual((dest / "SKILL.md").read_text(), "new skill")

    def test_list_bundled_agents_accepts_distribution_root_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "primitive-selector.agent.md").write_text(
                "---\nname: primitive-selector\n---\n"
            )
            (root / "README.txt").write_text("ignore me")

            with patch(
                "universal_creator.resources._candidate_agent_roots",
                return_value=[root],
            ):
                self.assertEqual(list_bundled_agents(), ["primitive-selector"])

    def test_repository_bundle_includes_planning_suite_agents(self) -> None:
        bundled = set(list_bundled_agents())
        self.assertTrue(
            {
                "primitive-selector",
                "universal-plan",
                "universal-explore",
                "artifact-router",
                "prompt-strategist",
                "validation-reviewer",
            }.issubset(bundled)
        )


class SharedManifestInstallTests(unittest.TestCase):
    """End-to-end coverage of the manifest-aware ``shared`` install path."""

    def test_first_install_writes_manifest_and_fans_out_trio_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            rc = _install_shared(bundled_root, workspace)

            self.assertEqual(rc, 0)
            shared_dest = workspace / ".claude" / "skills" / "shared"
            self.assertTrue((shared_dest / "SKILL.md").is_file())
            self.assertTrue(
                (shared_dest / "examples" / "zero-shot.prompt.md").is_file()
            )
            # Trio agent fanned out to the host's agents/ dir.
            trio = workspace / ".claude" / "agents" / "validation-reviewer.agent.md"
            self.assertTrue(trio.is_file())
            # Lockfile written at <host_root>/.universal-creator/shared.lock.
            lock = workspace / ".claude" / MANIFEST_RELATIVE_PATH
            self.assertTrue(lock.is_file())
            files = read_manifest(lock) or {}
            self.assertIn("skills/shared/SKILL.md", files)
            self.assertIn("skills/shared/examples/zero-shot.prompt.md", files)
            self.assertIn("agents/validation-reviewer.agent.md", files)

    def test_reinstall_is_idempotent_when_nothing_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            lock = workspace / ".claude" / MANIFEST_RELATIVE_PATH
            first = read_manifest(lock)
            first_mtime = lock.stat().st_mtime_ns

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            second = read_manifest(lock)
            self.assertEqual(first, second)
            # Re-running writes the manifest again (intentional, keeps content
            # canonicalised); the file mtime may advance but content is stable.
            self.assertEqual(read_manifest(lock), first)
            _ = first_mtime  # touch to silence "unused" complaints if any

    def test_reinstall_preserves_user_edited_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            edited = (
                workspace
                / ".claude"
                / "skills"
                / "shared"
                / "examples"
                / "zero-shot.prompt.md"
            )
            edited.write_text("user customisation\n", encoding="utf-8")

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            self.assertEqual(edited.read_text(), "user customisation\n")

    def test_reinstall_upgrades_unmodified_file_when_bundle_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            # Bundle ships a new version of techniques.json.
            (bundled_root / "shared" / "techniques.json").write_text(
                '{"version": "2"}\n', encoding="utf-8"
            )

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            deployed = workspace / ".claude" / "skills" / "shared" / "techniques.json"
            self.assertEqual(deployed.read_text(), '{"version": "2"}\n')

    def test_force_shared_clobbers_user_edits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            edited = (
                workspace
                / ".claude"
                / "skills"
                / "shared"
                / "examples"
                / "zero-shot.prompt.md"
            )
            edited.write_text("user customisation\n", encoding="utf-8")

            self.assertEqual(
                _install_shared(bundled_root, workspace, force_shared=True), 0
            )
            self.assertEqual(edited.read_text(), "bundled zero-shot example\n")

    def test_missing_manifest_refuses_to_take_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            # Pre-populate the destination so the installer sees existing
            # files but no lockfile.
            preexisting = workspace / ".claude" / "skills" / "shared" / "rogue.txt"
            preexisting.parent.mkdir(parents=True)
            preexisting.write_text("not ours\n", encoding="utf-8")

            rc = _install_shared(bundled_root, workspace)
            self.assertEqual(rc, 1)
            self.assertTrue(preexisting.is_file())
            self.assertEqual(preexisting.read_text(), "not ours\n")

    def test_force_shared_overrides_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            preexisting = workspace / ".claude" / "skills" / "shared" / "rogue.txt"
            preexisting.parent.mkdir(parents=True)
            preexisting.write_text("not ours\n", encoding="utf-8")

            self.assertEqual(
                _install_shared(bundled_root, workspace, force_shared=True), 0
            )
            # Force install wipes the directory clean.
            self.assertFalse(preexisting.is_file())
            self.assertTrue(
                (workspace / ".claude" / "skills" / "shared" / "SKILL.md").is_file()
            )

    def test_reinstall_restores_user_deleted_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundled_root = _build_bundled_shared(root)
            workspace = root / "workspace"

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            doomed = (
                workspace
                / ".claude"
                / "skills"
                / "shared"
                / "examples"
                / "zero-shot.prompt.md"
            )
            doomed.unlink()

            self.assertEqual(_install_shared(bundled_root, workspace), 0)
            self.assertTrue(doomed.is_file())
            self.assertEqual(doomed.read_text(), "bundled zero-shot example\n")
