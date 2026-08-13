"""Focused tests for the static progressive-disclosure context profiler."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from profile_context import (  # noqa: E402
    BASE_SKILL,
    PROFILE_BY_ID,
    PROFILES,
    LoadSpec,
    ProfileError,
    ProfileSpec,
    build_report,
    heuristic_token_estimate,
    profile_loads,
    render_text,
)


class ContextProfilerTests(unittest.TestCase):
    def test_builtin_profiles_match_progressive_disclosure_contract(self) -> None:
        paths = {
            identifier: [load.path for load in PROFILE_BY_ID[identifier].loads]
            for identifier in PROFILE_BY_ID
        }
        base = BASE_SKILL.path
        self.assertEqual(
            tuple(PROFILE_BY_ID),
            (
                "quick-look",
                "participatory-first-prompt",
                "expert-facilitated-workshop",
                "inquiry-lab",
                "sealed-panel",
                "visual-affinity",
            ),
        )
        self.assertEqual(paths["quick-look"], [base])
        self.assertEqual(
            paths["participatory-first-prompt"],
            [base, "skills/design-council/references/participatory-workshops.md"],
        )
        self.assertEqual(
            paths["expert-facilitated-workshop"],
            [
                base,
                "skills/design-council/references/participatory-workshops.md",
                "skills/design-council/references/facilitator-practice.md",
            ],
        )
        self.assertEqual(
            paths["inquiry-lab"],
            [base, "skills/design-council/references/inquiry-lab.md"],
        )
        self.assertEqual(paths["sealed-panel"][0:2], [base, "skills/design-council/references/council-protocol.md"])
        self.assertEqual(len(paths["sealed-panel"]), 7)
        self.assertTrue(
            all(
                path.startswith("skills/design-council/references/council-")
                for path in paths["sealed-panel"][1:]
            )
        )
        self.assertEqual(
            paths["visual-affinity"],
            [base, "skills/design-council/references/visual-workbench.md"],
        )

    def test_counts_and_redundancies_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "first.md").write_bytes(b"Alpha beta\n")
            (root / "copy.md").write_bytes(b"Alpha beta\n")
            profile = ProfileSpec(
                "fixture",
                "Fixture",
                "Duplicate fixture",
                (
                    LoadSpec("first.md", "first"),
                    LoadSpec("first.md", "same path again"),
                    LoadSpec("copy.md", "different path, identical bytes"),
                ),
            )

            first = profile_loads(root, profile)
            second = profile_loads(root, profile)

        self.assertEqual(first, second)
        self.assertEqual(first["totals"]["gross"], {"bytes": 33, "words": 6, "heuristic_token_estimate": 9})
        self.assertEqual(first["totals"]["unique_content"], {"bytes": 11, "words": 2, "heuristic_token_estimate": 3})
        self.assertEqual(first["totals"]["redundant"], {"bytes": 22, "words": 4, "heuristic_token_estimate": 6})
        self.assertEqual(first["totals"]["distinct_paths"], 2)
        self.assertEqual(first["totals"]["unique_content_blobs"], 1)
        self.assertEqual(first["totals"]["redundant_load_events"], 2)
        self.assertEqual(
            [item["kind"] for item in first["redundancies"]],
            ["repeated_path", "identical_content"],
        )

    def test_builtin_report_is_stable_and_has_no_route_stacking(self) -> None:
        first = build_report(ROOT, PROFILES)
        second = build_report(ROOT, PROFILES)
        self.assertEqual(first, second)
        self.assertEqual(len(first["profiles"]), 6)
        for profile in first["profiles"]:
            with self.subTest(profile=profile["id"]):
                self.assertGreater(profile["totals"]["unique_content"]["bytes"], 0)
                self.assertEqual(profile["totals"]["redundant_load_events"], 0)
                self.assertEqual(profile["totals"]["gross"], profile["totals"]["unique_content"])
                self.assertEqual(
                    profile["totals"]["gross"]["heuristic_token_estimate"],
                    heuristic_token_estimate(profile["totals"]["gross"]["bytes"]),
                )

    def test_text_output_labels_the_heuristic_and_duplicates(self) -> None:
        report = build_report(ROOT, (PROFILE_BY_ID["quick-look"],))
        text = render_text(report)
        self.assertIn("STATIC CONTEXT-LOAD PROFILE (no model calls)", text)
        self.assertIn("HEURISTIC token estimate", text)
        self.assertIn("not exact model-input or billing-token counts", text)
        self.assertIn("Duplicate/redundant loads: none", text)
        self.assertNotIn("exact token", text.lower())

    def test_json_cli_is_parseable_and_carries_limitations(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "profile_context.py"),
                "--profile",
                "quick-look",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual([item["id"] for item in payload["profiles"]], ["quick-look"])
        self.assertIn("No model or tokenizer is called", payload["measurement"]["limitations"])
        self.assertIn("rough comparative", payload["measurement"]["heuristic_token_estimate"])

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProfileError, "negative"):
            heuristic_token_estimate(-1)
        missing = ProfileSpec(
            "missing",
            "Missing",
            "Missing resource",
            (LoadSpec("missing.md", "fixture"),),
        )
        with self.assertRaisesRegex(ProfileError, "not a file"):
            profile_loads(ROOT, missing)


if __name__ == "__main__":
    unittest.main()
