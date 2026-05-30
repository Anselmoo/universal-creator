"""Unit tests for the per-file SHA256 manifest helpers in
``universal_creator.manifest``.

These tests cover the pure functions only — read/write/diff. The orchestrated
install behaviour that drives them is exercised in ``tests/test_install.py``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from universal_creator.manifest import (
    MANIFEST_RELATIVE_PATH,
    MANIFEST_VERSION,
    compute_tree_manifest,
    decide_action,
    read_manifest,
    sha256_of_file,
    write_manifest,
)


class ManifestRelativePathTests(unittest.TestCase):
    def test_lock_lives_under_universal_creator_dir(self) -> None:
        self.assertEqual(
            MANIFEST_RELATIVE_PATH, Path(".universal-creator") / "shared.lock"
        )


class FileHashTests(unittest.TestCase):
    def test_sha256_of_file_matches_known_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hello.txt"
            path.write_bytes(b"hello world")
            self.assertEqual(
                sha256_of_file(path),
                # Pre-computed sha256 of "hello world".
                "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
            )


class ComputeTreeManifestTests(unittest.TestCase):
    def test_walks_nested_files_with_posix_relative_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("alpha")
            sub = root / "sub" / "deep"
            sub.mkdir(parents=True)
            (sub / "b.txt").write_text("beta")

            manifest = compute_tree_manifest(root)

            self.assertEqual(set(manifest), {"a.txt", "sub/deep/b.txt"})
            self.assertEqual(manifest["sub/deep/b.txt"], sha256_of_file(sub / "b.txt"))

    def test_returns_empty_for_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope"
            self.assertEqual(compute_tree_manifest(missing), {})


class ManifestRoundTripTests(unittest.TestCase):
    def test_write_then_read_returns_files_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / ".universal-creator" / "shared.lock"
            files = {"a.txt": "deadbeef", "sub/b.txt": "cafef00d"}
            write_manifest(lock, files, source_sha="abc123")

            loaded = read_manifest(lock)
            self.assertEqual(loaded, files)

            # Envelope shape is preserved.
            payload = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], MANIFEST_VERSION)
            self.assertEqual(payload["shared_source_sha"], "abc123")

    def test_read_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(read_manifest(Path(tmp) / "absent.lock"))

    def test_read_returns_none_on_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "shared.lock"
            lock.write_text("{not valid json", encoding="utf-8")
            self.assertIsNone(read_manifest(lock))


class DecideActionTests(unittest.TestCase):
    def test_fresh_when_no_manifest_and_no_disk(self) -> None:
        self.assertEqual(decide_action("a", None, None), "fresh")

    def test_user_deleted_when_manifest_but_no_disk(self) -> None:
        self.assertEqual(decide_action("a", "b", None), "user_deleted")

    def test_idempotent_when_all_three_match(self) -> None:
        self.assertEqual(decide_action("a", "a", "a"), "idempotent")

    def test_safe_upgrade_when_bundle_changed_disk_matches_manifest(self) -> None:
        self.assertEqual(decide_action("new", "old", "old"), "safe_upgrade")

    def test_user_modified_when_disk_differs_from_manifest(self) -> None:
        self.assertEqual(decide_action("a", "a", "edited"), "user_modified")
        self.assertEqual(decide_action("a", "old", "edited"), "user_modified")

    def test_untracked_disk_matching_bundle_is_idempotent(self) -> None:
        # File appeared on disk without ever being tracked, but happens to
        # match the bundled hash — adopt it silently.
        self.assertEqual(decide_action("a", None, "a"), "idempotent")

    def test_untracked_disk_diverging_from_bundle_is_user_modified(self) -> None:
        # File appeared on disk without being tracked and does NOT match the
        # bundle — preserve it as a user edit.
        self.assertEqual(decide_action("a", None, "b"), "user_modified")


if __name__ == "__main__":
    unittest.main()
