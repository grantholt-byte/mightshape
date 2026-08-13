from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_packages import build, write_checksums
from scripts.check_cross_platform_drift import check
from scripts.validate_packages import basic_claude_validate, is_semver


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "skills/design-council"
OPENAI = ROOT / "dist/openai/design-council"
CLAUDE = ROOT / "dist/claude/design-council"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CrossPlatformPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build(clean=True)

    def test_generated_packages_have_no_shared_core_drift(self) -> None:
        result = check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["human_model_count"], 10)

    def test_claude_adapter_preserves_canonical_skill_verbatim(self) -> None:
        canonical = (CANONICAL / "SKILL.md").read_text(encoding="utf-8").rstrip()
        openai = (OPENAI / "skills/design-council/SKILL.md").read_text(encoding="utf-8").rstrip()
        claude = (CLAUDE / "skills/design-council/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(openai, canonical)
        self.assertTrue(claude.startswith(canonical + "\n"))
        self.assertIn("Claude Code adapter", claude[len(canonical) :])

    def test_all_human_models_are_byte_identical(self) -> None:
        profiles = sorted(
            path
            for path in (CANONICAL / "references").glob("council-*.md")
            if path.name not in {"council-protocol.md", "council-roster.md"}
        )
        self.assertEqual(len(profiles), 10)
        for profile in profiles:
            relative = profile.relative_to(CANONICAL)
            with self.subTest(profile=profile.name):
                self.assertEqual(sha256(profile), sha256(OPENAI / "skills/design-council" / relative))
                self.assertEqual(sha256(profile), sha256(CLAUDE / "skills/design-council" / relative))

    def test_one_version_and_marketplace_identity(self) -> None:
        expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        manifests = [
            json.loads((OPENAI / ".codex-plugin/plugin.json").read_text(encoding="utf-8")),
            json.loads((CLAUDE / ".claude-plugin/plugin.json").read_text(encoding="utf-8")),
            json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")),
        ]
        self.assertTrue(all(item["version"] == expected for item in manifests))
        openai_marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(openai_marketplace["name"], "design-council")
        self.assertEqual(openai_marketplace["plugins"][0]["name"], "design-council")

    def test_openai_manifest_respects_runtime_prompt_limit(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        prompts = manifest.get("interface", {}).get("defaultPrompt", [])
        self.assertIsInstance(prompts, list)
        self.assertLessEqual(len(prompts), 3)

    def test_release_validator_accepts_semver_prereleases(self) -> None:
        for valid in ("1.0.0", "0.9.0-beta.1", "2.4.1-rc.3+build.9"):
            with self.subTest(valid=valid):
                self.assertTrue(is_semver(valid))
        for invalid in ("1.0", "v1.0.0", "01.0.0", "0.9.0-beta.01"):
            with self.subTest(invalid=invalid):
                self.assertFalse(is_semver(invalid))

    def test_state_schema_is_platform_neutral(self) -> None:
        text = (CANONICAL / "schemas/project-state.schema.json").read_text(encoding="utf-8").lower()
        for forbidden in ("openai", "codex", "anthropic", "claude"):
            self.assertNotIn(forbidden, text)

    def test_claude_package_contract_is_complete(self) -> None:
        self.assertEqual(basic_claude_validate(), [])
        self.assertTrue((CLAUDE / "agents/sealed-member.md").is_file())
        self.assertFalse((CLAUDE / "hooks").exists())

    def test_packages_ship_public_brand_assets_not_working_references(self) -> None:
        for package in (OPENAI, CLAUDE):
            with self.subTest(package=package):
                self.assertTrue((package / "assets/icon.png").is_file())
                self.assertTrue((package / "assets/logo.png").is_file())
                self.assertTrue((package / "assets/screenshots/01-design-journey.png").is_file())
                self.assertFalse((package / "assets/concepts").exists())

    def test_packages_exclude_local_duplicate_backups(self) -> None:
        for package in (OPENAI, CLAUDE):
            with self.subTest(package=package):
                duplicates = [path for path in package.rglob("*") if path.is_file() and " 2." in path.name]
                self.assertEqual(duplicates, [])

    def test_clean_build_preserves_user_duplicate_files_and_excludes_them_from_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_dist = Path(temporary) / "dist"
            temporary_dist.mkdir()
            duplicate = temporary_dist / "design-council-claude-0.9.0-beta.3 2.zip"
            duplicate.write_bytes(b"user-owned duplicate")
            unrelated = temporary_dist / "research-notes.txt"
            unrelated.write_text("preserve me", encoding="utf-8")
            with patch("scripts.build_packages.DIST", temporary_dist):
                build(clean=True)
                checksum = write_checksums().read_text(encoding="utf-8")
            self.assertEqual(duplicate.read_bytes(), b"user-owned duplicate")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "preserve me")
            self.assertNotIn(duplicate.name, checksum)

    def test_archives_are_deterministic(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        paths = [
            ROOT / f"dist/design-council-openai-{version}.zip",
            ROOT / f"dist/design-council-claude-{version}.zip",
        ]
        first = [sha256(path) for path in paths]
        build(clean=True)
        self.assertEqual(first, [sha256(path) for path in paths])
        sums = (ROOT / "dist/SHA256SUMS").read_text(encoding="utf-8")
        for path, digest in zip(paths, first):
            self.assertIn(f"{digest}  {path.name}", sums)

    def test_publication_documents_do_not_claim_publication(self) -> None:
        openai = (ROOT / "docs/marketplace-openai.md").read_text(encoding="utf-8")
        claude = (ROOT / "docs/marketplace-claude.md").read_text(encoding="utf-8")
        for document in (openai.lower(), claude.lower()):
            self.assertIn("no submission has", document)
            self.assertIn("been made", document)
        self.assertIn("no application", claude.lower())


if __name__ == "__main__":
    unittest.main()
