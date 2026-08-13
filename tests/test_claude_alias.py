"""Tests for the optional exact `/design-think` Claude Code alias."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.install_claude_alias import (
    SOURCE,
    AliasInstallError,
    install_alias,
    target_skill_dir,
    uninstall_alias,
)


class ClaudeAliasTests(unittest.TestCase):
    def test_alias_is_explicit_only_and_delegates_to_plugin(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("name: design-think", text)
        self.assertIn("disable-model-invocation: true", text)
        self.assertIn("- Skill(design-council:design-think)\n", text)
        self.assertIn("- Skill(design-council:design-think *)\n", text)
        self.assertIn("design-council:design-think", text)
        self.assertIn("$ARGUMENTS", text)
        self.assertNotIn("Think wider. Frame better", text)

    def test_project_target_is_platform_standard_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = target_skill_dir(scope="project", project_root=root)
        self.assertEqual(target, root.resolve() / ".claude" / "skills" / "design-think")

    def test_project_scope_requires_a_root(self) -> None:
        with self.assertRaisesRegex(AliasInstallError, "project-root"):
            target_skill_dir(scope="project")

    def test_install_is_atomic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target_dir = Path(temporary) / "design-think"
            first = install_alias(target_dir=target_dir)
            second = install_alias(target_dir=target_dir)
            installed = (target_dir / "SKILL.md").read_bytes()

        self.assertEqual(first["status"], "INSTALLED")
        self.assertEqual(second["status"], "UNCHANGED")
        self.assertEqual(installed, SOURCE.read_bytes())

    def test_conflict_fails_closed_unless_force_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target_dir = Path(temporary) / "design-think"
            target_dir.mkdir(parents=True)
            target = target_dir / "SKILL.md"
            target.write_text("user-owned alias\n", encoding="utf-8")

            with self.assertRaisesRegex(AliasInstallError, "refusing to overwrite"):
                install_alias(target_dir=target_dir)
            self.assertEqual(target.read_text(encoding="utf-8"), "user-owned alias\n")

            result = install_alias(target_dir=target_dir, force=True)
            self.assertEqual(result["status"], "INSTALLED")
            self.assertEqual(target.read_bytes(), SOURCE.read_bytes())

    def test_uninstall_is_idempotent_and_removes_only_shipped_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target_dir = Path(temporary) / "design-think"
            not_installed = uninstall_alias(target_dir=target_dir)
            install_alias(target_dir=target_dir)
            removed = uninstall_alias(target_dir=target_dir)
            removed_again = uninstall_alias(target_dir=target_dir)

        self.assertEqual(not_installed["status"], "NOT_INSTALLED")
        self.assertEqual(removed["status"], "REMOVED")
        self.assertEqual(removed_again["status"], "NOT_INSTALLED")

    def test_uninstall_refuses_modified_alias_and_preserves_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target_dir = Path(temporary) / "design-think"
            install_alias(target_dir=target_dir)
            target = target_dir / "SKILL.md"
            sibling = target_dir / "notes.md"
            sibling.write_text("keep me\n", encoding="utf-8")
            target.write_text("user-modified alias\n", encoding="utf-8")

            with self.assertRaisesRegex(AliasInstallError, "modified or foreign"):
                uninstall_alias(target_dir=target_dir)

            self.assertEqual(target.read_text(encoding="utf-8"), "user-modified alias\n")
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep me\n")

    def test_uninstall_leaves_nonempty_skill_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target_dir = Path(temporary) / "design-think"
            install_alias(target_dir=target_dir)
            sibling = target_dir / "notes.md"
            sibling.write_text("keep me\n", encoding="utf-8")
            result = uninstall_alias(target_dir=target_dir)

            self.assertEqual(result["status"], "REMOVED")
            self.assertTrue(target_dir.is_dir())
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep me\n")


if __name__ == "__main__":
    unittest.main()
