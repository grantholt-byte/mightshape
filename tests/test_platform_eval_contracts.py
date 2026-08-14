from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from evals.run_contracts import load_cases
from evals.run_platform_contracts import PLATFORMS, _load_manifest, map_prompt, validate
from scripts.build_packages import build


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlatformEvalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build(clean=True)

    def test_both_platforms_map_the_complete_shared_corpus(self) -> None:
        result = validate()
        self.assertTrue(result["valid"], result["errors"])
        self.assertGreaterEqual(result["shared_case_count"], 90)
        self.assertEqual([item["platform"] for item in result["platforms"]], list(PLATFORMS))
        self.assertTrue(
            all(item["case_count"] == result["shared_case_count"] for item in result["platforms"])
        )

    def test_explicit_cases_receive_only_the_platform_invocation(self) -> None:
        cases = load_cases()
        explicit = next(case for case in cases if case["invocation"] == "explicit")
        implicit = next(case for case in cases if case["invocation"] == "implicit")
        avoid = next(case for case in cases if case["invocation"] == "avoid")
        for platform in PLATFORMS:
            manifest = _load_manifest(platform)
            with self.subTest(platform=platform):
                self.assertTrue(map_prompt(explicit, manifest).startswith(manifest["explicit_invocation"]))
                self.assertEqual(map_prompt(implicit, manifest), implicit["prompt"])
                self.assertEqual(map_prompt(avoid, manifest), avoid["prompt"])

    def test_platform_manifests_reference_shared_cases_instead_of_copying_them(self) -> None:
        for platform in PLATFORMS:
            manifest_path = ROOT / "evals" / platform / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            with self.subTest(platform=platform):
                self.assertEqual(manifest["shared_case_map"]["source"], "evals/cases")
                self.assertFalse((manifest_path.parent / "cases").exists())
                self.assertFalse((manifest_path.parent / "fixtures").exists())

    def test_single_platform_build_preserves_other_platform_artifact(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        claude_archive = ROOT / f"dist/mightshape-claude-{version}.zip"
        before = sha256(claude_archive)
        result = build(platform="openai")
        self.assertEqual(result["platforms"], ["openai"])
        self.assertTrue(claude_archive.is_file())
        self.assertEqual(before, sha256(claude_archive))

    def test_makefile_exposes_requested_release_targets(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        targets = {
            line.split(":", 1)[0]
            for line in makefile.splitlines()
            if line and not line.startswith(("\t", ".")) and ":" in line
        }
        expected = {
            "build-openai",
            "build-claude",
            "validate-openai",
            "validate-claude",
            "check-cross-platform-drift",
            "release-check",
        }
        self.assertTrue(expected.issubset(targets), expected.difference(targets))

    def test_release_gate_requires_platform_and_interview_app_checks(self) -> None:
        script = (ROOT / "scripts/release_check.py").read_text(encoding="utf-8")
        for marker in (
            '"--require-claude"',
            '"test:full"',
            '"lint"',
            '"typecheck"',
            '"build"',
            '"audit", "--omit=dev"',
            '"evals/run_platform_contracts.py"',
            '"scripts/check_runtime_branding.py"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)


if __name__ == "__main__":
    unittest.main()
