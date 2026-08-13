from __future__ import annotations

import hashlib
import io
import json
import math
import unittest
from contextlib import redirect_stdout

from evals import run_council_recognition as recognition


SAFE_RESPONSE = (
    "The first risk is treating a visible dashboard as the same thing as a reliable handoff. "
    "Right now, several different failures are bundled together: noticing, interpreting, deciding, "
    "and confirming ownership. The anecdotes tell us the bundle exists, but not which transition "
    "creates the most consequential loss. Protect the option to learn before automating. Reconstruct "
    "three recent changes from trigger through recovery, including who noticed, who waited, and where "
    "the next action became ambiguous. Then rehearse one manual notification-and-acknowledgment loop. "
    "If that changes behavior, the team has located a mechanism worth testing; if not, the dashboard "
    "would only make uncertainty prettier."
)


class CouncilRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = recognition.load_profiles()
        cls.challenge = recognition.load_challenge()

    def test_loads_all_ten_canonical_profiles_with_source_hashes(self) -> None:
        self.assertEqual([profile.name for profile in self.profiles], list(recognition.IDENTITIES))
        for profile in self.profiles:
            self.assertTrue(profile.path.is_file())
            self.assertEqual(profile.source_sha256, hashlib.sha256(profile.path.read_bytes()).hexdigest())
            self.assertEqual(profile.sealed_sha256, recognition.sha256_text(profile.sealed_text))
            self.assertEqual(profile.judge_sha256, recognition.sha256_text(profile.judge_text))

    def test_candidate_prompt_has_one_profile_and_no_sibling_names(self) -> None:
        common_packets: set[str] = set()
        for profile in self.profiles:
            prompt = recognition.candidate_prompt(profile, self.challenge)
            self.assertIn(profile.source_text.splitlines()[0], prompt)
            for other in self.profiles:
                if other.name == profile.name:
                    continue
                self.assertNotIn(other.name, prompt)
                self.assertNotIn(other.source_text, prompt)
            common_packets.add(
                prompt.split("COMMON PACKET (identical for all ten sealed calls):\n", 1)[1].split(
                    "\n\nONE CANONICAL HUMAN MODEL", 1
                )[0]
            )
        self.assertEqual(len(common_packets), 1)

    def test_sealed_projection_removes_relationship_and_project_memory_sections(self) -> None:
        for profile in self.profiles:
            lowered = profile.sealed_text.lower()
            self.assertNotIn("## council relationships", lowered)
            self.assertNotIn("## project-memory behavior", lowered)
            self.assertNotIn("## council relationships and project memory", lowered)

    def test_blind_judge_prompt_withholds_identity_role_biography_and_source_mapping(self) -> None:
        artifacts = [
            {"artifact_id": f"A-01-{index:02d}", "response": SAFE_RESPONSE}
            for index in range(1, 11)
        ]
        cards = [
            {"profile_id": f"P-01-{index:02d}", "behavioral_reference": profile.judge_text}
            for index, profile in enumerate(self.profiles, 1)
        ]
        prompt = recognition.judge_prompt(self.challenge, artifacts, cards)
        for profile in self.profiles:
            self.assertNotIn(profile.name, prompt)
        self.assertIsNone(recognition.ROLE_LEAK_RE.search(prompt))
        self.assertIsNone(recognition.PLACE_LEAK_RE.search(prompt))
        self.assertIsNone(recognition.AGE_LEAK_RE.search(prompt))
        self.assertNotRegex(prompt, r"source_by_artifact|identity_by_profile_id")
        for sample in (
            "what happens when this goes wrong",
            "crudest thing we can build today",
            "which part of this actually needs intelligence",
            "delete the app",
        ):
            self.assertNotIn(sample, prompt.lower())

    def test_leakage_screen_detects_direct_identifiers_roles_and_biography(self) -> None:
        cases = {
            "Maya Chen thinks this is fragile.": "council_identifier",
            "As a behavioral scientist, this concerns me.": "explicit_role",
            "Back in Minneapolis, the workaround was common.": "place_or_origin",
            "I grew up watching this exact tension.": "biography_statement",
            "At 47 years old, I read it differently.": "age",
            "What happens when this goes wrong at 5:30?": "signature_question",
        }
        for text, expected_type in cases.items():
            with self.subTest(text=text):
                types = {item["type"] for item in recognition.leakage_findings(text, self.profiles)}
                self.assertIn(expected_type, types)

    def test_leakage_screen_detects_signature_sample_and_long_copy(self) -> None:
        sample = "The reminder is doing its job on paper. I want to know what happens next."
        types = {item["type"] for item in recognition.leakage_findings(sample, self.profiles)}
        self.assertIn("signature_sample_phrase", types)
        long_copy = (
            "The reminder is doing its job on paper I want to know what happens when three reminders arrive."
        )
        types = {item["type"] for item in recognition.leakage_findings(long_copy, self.profiles)}
        self.assertIn("copied_profile_phrase", types)

    def test_leakage_screen_allows_reasoning_fingerprint_without_identity_shortcut(self) -> None:
        self.assertEqual(recognition.leakage_findings(SAFE_RESPONSE, self.profiles), [])
        parsed = recognition.parse_candidate_response(json.dumps({"response": SAFE_RESPONSE}), self.profiles)
        self.assertGreaterEqual(parsed["word_count"], 70)
        self.assertLessEqual(parsed["word_count"], 180)

    def test_parse_candidate_rejects_extra_shape_and_leak(self) -> None:
        with self.assertRaises(recognition.RecognitionError):
            recognition.parse_candidate_response(
                json.dumps({"response": SAFE_RESPONSE, "identity": "withheld"}), self.profiles
            )
        leaked = SAFE_RESPONSE + " Maya Chen."
        with self.assertRaisesRegex(recognition.RecognitionError, "leakage screen"):
            recognition.parse_candidate_response(json.dumps({"response": leaked}), self.profiles)

    def _judgment(self, assigned_profiles: list[str]) -> dict[str, object]:
        return {
            "assignments": [
                {
                    "artifact_id": f"A-01-{index:02d}",
                    "assigned_profile_id": profile_id,
                    "confidence": 0.7,
                    "observable_cues": ["attention and decision style"],
                }
                for index, profile_id in enumerate(assigned_profiles, 1)
            ],
            "overall_notes": "The cards overlap, so assignments are forced comparisons.",
        }

    def test_judgment_is_a_complete_one_to_one_assignment(self) -> None:
        profile_ids = [f"P-01-{index:02d}" for index in range(1, 11)]
        raw = json.dumps(self._judgment(profile_ids))
        parsed = recognition.parse_judgment(
            raw,
            [f"A-01-{index:02d}" for index in range(1, 11)],
            profile_ids,
        )
        self.assertEqual(len(parsed["assignments"]), 10)
        duplicate = profile_ids[:-1] + [profile_ids[0]]
        with self.assertRaisesRegex(recognition.RecognitionError, "duplicate profile-card"):
            recognition.parse_judgment(
                json.dumps(self._judgment(duplicate)),
                [f"A-01-{index:02d}" for index in range(1, 11)],
                profile_ids,
            )

    def test_score_builds_name_level_confusion_matrix_after_blind_assignment(self) -> None:
        artifacts = [f"A-01-{index:02d}" for index in range(1, 11)]
        profile_ids = [f"P-01-{index:02d}" for index in range(1, 11)]
        source = dict(zip(artifacts, recognition.IDENTITIES))
        identity_by_profile = dict(zip(profile_ids, recognition.IDENTITIES))
        assigned = profile_ids.copy()
        assigned[0], assigned[1] = assigned[1], assigned[0]
        judgment = self._judgment(assigned)
        score = recognition.score_assignments(source, identity_by_profile, judgment)
        self.assertEqual(score["correct"], 8)
        self.assertEqual(score["total"], 10)
        self.assertEqual(score["confusion_matrix"]["Maya Chen"]["Leo Martinez"], 1)
        self.assertEqual(score["confusion_matrix"]["Leo Martinez"]["Maya Chen"], 1)
        self.assertEqual(score["confusion_matrix"]["Priya Rao"]["Priya Rao"], 1)

    def test_derangement_distribution_is_exact_permutation_chance_model(self) -> None:
        counts = recognition.fixed_point_counts(10)
        self.assertEqual(sum(counts), math.factorial(10))
        self.assertEqual(counts[9], 0)
        expected_fixed_points = sum(index * count for index, count in enumerate(counts)) / math.factorial(10)
        self.assertAlmostEqual(expected_fixed_points, 1.0)
        self.assertEqual(recognition.derangements(0), 1)
        self.assertEqual(recognition.derangements(4), 9)

    def test_chance_tail_probability_handles_single_and_repeated_panels(self) -> None:
        self.assertEqual(recognition.chance_tail_probability(0, 1), 1.0)
        self.assertAlmostEqual(recognition.chance_tail_probability(10, 1), 1 / math.factorial(10))
        self.assertEqual(recognition.chance_tail_probability(0, 2), 1.0)
        self.assertGreater(
            recognition.chance_tail_probability(5, 2),
            recognition.chance_tail_probability(10, 2),
        )

    def test_incomplete_design_suppresses_accuracy_and_confusion_claims(self) -> None:
        score = {
            "correct": 10,
            "total": 10,
            "confusion_matrix": recognition.empty_confusion_matrix(),
        }
        summary = recognition.build_summary([score], planned_repeats=2, run_error="second panel failed")
        self.assertEqual(summary["status"], "INCOMPLETE")
        self.assertIsNone(summary["accuracy"])
        self.assertIsNone(summary["correct_assignments"])
        self.assertIsNone(summary["confusion_matrix"])

    def test_complete_summary_includes_narrow_claim_and_chance_baseline(self) -> None:
        matrix = recognition.empty_confusion_matrix()
        for identity in recognition.IDENTITIES:
            matrix[identity][identity] = 1
        summary = recognition.build_summary(
            [{"correct": 10, "total": 10, "confusion_matrix": matrix}],
            planned_repeats=1,
            run_error=None,
        )
        self.assertEqual(summary["status"], "COMPLETE")
        self.assertEqual(summary["accuracy"], 1.0)
        self.assertEqual(summary["chance_baseline"]["expected_accuracy"], 0.1)
        self.assertIn("not human ground truth", summary["study_scope"])

    def test_dry_run_records_prompt_models_and_source_hashes_without_calls(self) -> None:
        args = recognition.build_parser().parse_args(["--dry-run", "--repeats", "2"])
        payload = recognition.dry_run_payload(self.profiles, self.challenge, args)
        self.assertEqual(payload["model_calls_made"], 0)
        self.assertEqual(payload["planned_model_calls"], 22)
        self.assertEqual(payload["candidate_model"], "gpt-5.6-sol")
        self.assertEqual(payload["judge_model"], "gpt-5.6-terra")
        self.assertEqual(len(payload["candidate_prompts"]), 10)
        self.assertRegex(payload["generator_instruction_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(payload["judge_instruction_sha256"], r"^[0-9a-f]{64}$")
        for item in payload["candidate_prompts"]:
            self.assertRegex(item["canonical_profile_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(item["prompt_sha256"], r"^[0-9a-f]{64}$")

    def test_git_state_is_explicit_even_when_worktree_is_dirty(self) -> None:
        state = recognition.git_state()
        self.assertEqual(set(state), {"commit", "dirty", "status_available"})
        self.assertIsInstance(state["status_available"], bool)
        if state["commit"] is not None:
            self.assertRegex(state["commit"], r"^[0-9a-f]{40}$")

    def test_output_schemas_parse_and_match_runtime_contract(self) -> None:
        response_schema = json.loads(recognition.RESPONSE_SCHEMA.read_text(encoding="utf-8"))
        judge_schema = json.loads(recognition.JUDGE_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(response_schema["required"], ["response"])
        assignment = judge_schema["properties"]["assignments"]["items"]
        self.assertIn("assigned_profile_id", assignment["required"])
        self.assertNotIn("assigned_identity", assignment["properties"])
        self.assertEqual(judge_schema["properties"]["assignments"]["minItems"], 10)
        self.assertEqual(judge_schema["properties"]["assignments"]["maxItems"], 10)

    def test_main_is_offline_by_default_and_dry_run_succeeds(self) -> None:
        old = recognition.os.environ.pop("DC_RUN_COUNCIL_RECOGNITION", None)
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(recognition.main([]), 0)
                self.assertEqual(recognition.main(["--dry-run"]), 0)
            self.assertIn("SKIP: Council recognition is opt-in", output.getvalue())
            self.assertIn('"model_calls_made": 0', output.getvalue())
        finally:
            if old is not None:
                recognition.os.environ["DC_RUN_COUNCIL_RECOGNITION"] = old


if __name__ == "__main__":
    unittest.main()
