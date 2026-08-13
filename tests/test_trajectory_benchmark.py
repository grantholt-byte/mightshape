from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evals.run_trajectory_benchmark import (
    DESIGN_THINKING_PROMPT_CONTROL,
    SCORE_DIMENSIONS,
    TrajectoryBenchmarkError,
    _stderr_category,
    aggregate_results,
    build_judge_plan,
    build_pair_plan,
    candidate_turn_prompt,
    extract_thread_id,
    initial_command,
    isolated_environment,
    load_trajectories,
    prepare_codex_home,
    prepare_workspace,
    replay_prompt,
    render_summary,
    resume_command,
    run_candidate_trajectory,
    stable_digest,
    validate_judgment,
)
from evals.run_ab_benchmark import (
    DESIGN_THINKING_PROMPT_CONTROL as ONESHOT_DESIGN_THINKING_PROMPT_CONTROL,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "run_trajectory_benchmark.py"
SCHEMA = REPO_ROOT / "evals" / "schema" / "trajectory-judge.schema.json"


def _complete_records(
    pair_plan: list[dict], judge_plan: list[dict]
) -> tuple[list[dict], list[dict]]:
    generations: list[dict] = []
    for pair in pair_plan:
        for arm, tokens, wall_time in (
            ("treatment", 3000, 30),
            ("control", 1000, 10),
        ):
            generations.append(
                {
                    "pair_id": pair["pair_id"],
                    "trajectory_id": pair["trajectory_id"],
                    "repeat": pair["repeat"],
                    "arm": arm,
                    "status": "OK",
                    "usage": {"total_tokens": tokens},
                    "wall_time_seconds": wall_time,
                }
            )

    judgments: list[dict] = []
    for planned in judge_plan:
        candidate_a_treatment = planned["label_a_arm"] == "treatment"
        candidate_a_score = 5 if candidate_a_treatment else 4
        candidate_b_score = 4 if candidate_a_treatment else 5
        candidate_a_quality = candidate_a_score * 20
        candidate_b_quality = candidate_b_score * 20
        judgments.append(
            {
                **planned,
                "status": "OK",
                "candidate_a_quality": candidate_a_quality,
                "candidate_b_quality": candidate_b_quality,
                "treatment_quality": 100,
                "control_quality": 80,
                "mapped_winner": "TREATMENT",
                "judgment": {
                    "trajectory_id": planned["trajectory_id"],
                    "comparison_id": planned["comparison_id"],
                    "candidate_a": {
                        "scores": {
                            dimension: candidate_a_score for dimension in SCORE_DIMENSIONS
                        },
                        "strengths": [],
                        "weaknesses": [],
                    },
                    "candidate_b": {
                        "scores": {
                            dimension: candidate_b_score for dimension in SCORE_DIMENSIONS
                        },
                        "strengths": [],
                        "weaknesses": [],
                    },
                    "winner": "A" if candidate_a_treatment else "B",
                    "confidence": 0.8,
                    "rationale": "The treatment trajectory adapts better.",
                },
            }
        )
    return generations, judgments


class TrajectoryBenchmarkTests(unittest.TestCase):
    def test_corpus_has_strict_four_turn_evidence_trajectories(self) -> None:
        trajectories = load_trajectories()
        self.assertGreaterEqual(len(trajectories), 3)
        expected_stages = [
            "solution_first_request",
            "user_constraint_or_contribution",
            "contradictory_evidence",
            "revised_frame_and_next_test",
        ]
        for trajectory in trajectories:
            self.assertEqual([turn["stage"] for turn in trajectory["turns"]], expected_stages)
            self.assertIn("USER_PROVIDED", trajectory["turns"][2]["content"])
            self.assertIn("not", trajectory["turns"][2]["content"].lower())

    def test_loader_rejects_wrong_turn_order(self) -> None:
        case = load_trajectories()[0]
        case = json.loads(json.dumps(case))
        case["turns"][1]["stage"] = "contradictory_evidence"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.jsonl"
            path.write_text(json.dumps(case) + "\n", encoding="utf-8")
            with self.assertRaises(TrajectoryBenchmarkError):
                load_trajectories(path)

    def test_pair_plan_is_deterministic_counterbalanced_and_turn_identical(self) -> None:
        cases = load_trajectories()[:2]
        first = build_pair_plan(cases, repeats=2, seed=6)
        second = build_pair_plan(cases, repeats=2, seed=6)
        self.assertEqual(first, second)
        for case in cases:
            rows = [row for row in first if row["trajectory_id"] == case["id"]]
            self.assertEqual(
                {tuple(row["arm_order"]) for row in rows},
                {("treatment", "control"), ("control", "treatment")},
            )
            self.assertEqual(rows[0]["turn_sha256"], rows[1]["turn_sha256"])
            self.assertEqual(len(rows[0]["turn_sha256"]), 4)

    def test_judge_plan_blinds_and_swaps_candidate_labels(self) -> None:
        pairs = build_pair_plan(load_trajectories()[:1], repeats=1, seed=9)
        judges = build_judge_plan(pairs, repetitions=2, seed=9)
        self.assertEqual({row["label_a_arm"] for row in judges}, {"treatment", "control"})
        self.assertTrue(all(row["label_a_arm"] != row["label_b_arm"] for row in judges))

    def test_persisted_commands_never_use_ephemeral_or_last(self) -> None:
        initial = initial_command(
            codex="codex",
            workdir=Path("/opaque/workspace"),
            response_path=Path("/opaque/response"),
            model="candidate-model",
            effort="medium",
            prompt="first turn",
        )
        resumed = resume_command(
            codex="codex",
            thread_id="12345678-1234-1234-1234-123456789abc",
            response_path=Path("/opaque/response-2"),
            model="candidate-model",
            effort="medium",
            prompt="second turn",
        )
        self.assertNotIn("--ephemeral", initial)
        self.assertNotIn("--ephemeral", resumed)
        self.assertNotIn("--last", resumed)
        self.assertEqual(resumed[:3], ["codex", "exec", "resume"])
        self.assertIn("12345678-1234-1234-1234-123456789abc", resumed)
        self.assertIn('sandbox_mode="read-only"', resumed)

    def test_thread_id_extraction_requires_uuid_from_started_event(self) -> None:
        identifier = "12345678-1234-1234-1234-123456789abc"
        self.assertEqual(
            extract_thread_id([{"type": "thread.started", "thread_id": identifier}]),
            identifier,
        )
        self.assertIsNone(extract_thread_id([{"type": "thread.started", "thread_id": "latest"}]))
        self.assertIsNone(extract_thread_id([{"type": "turn.completed"}]))

    def test_real_session_runner_resumes_explicit_verified_thread(self) -> None:
        trajectory = load_trajectories()[0]
        identifier = "12345678-1234-1234-1234-123456789abc"
        observed_commands: list[list[str]] = []

        def fake_call(**kwargs):
            command = list(kwargs["command"])
            observed_commands.append(command)
            turn = len(observed_commands)
            return {
                "status": "OK",
                "returncode": 0,
                "timed_out": False,
                "wall_time_seconds": 0.1,
                "usage": {
                    "input_tokens": 10,
                    "cached_input_tokens": 0,
                    "uncached_input_tokens": 10,
                    "output_tokens": 5,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 15,
                },
                "response": f"assistant turn {turn}",
                "thread_id": identifier,
                "event_count": 3,
                "activity": {"completed_items": 1, "tool_calls": 0, "agent_messages": 1},
                "warnings": [],
                "stderr_category": None,
            }

        with tempfile.TemporaryDirectory() as temporary, patch(
            "evals.run_trajectory_benchmark.run_codex_call", side_effect=fake_call
        ):
            root = Path(temporary)
            response_root = root / "responses"
            response_root.mkdir()
            result = run_candidate_trajectory(
                codex="codex",
                workdir=root,
                codex_home=root / "codex-home",
                fake_home=root / "home",
                trajectory=trajectory,
                model="candidate",
                effort="medium",
                timeout_seconds=5,
                session_mode="persisted",
                response_root=response_root,
                arm="treatment",
                control_mode="design-thinking-prompt",
            )
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["session_fidelity"], "PERSISTED_CODEX_THREAD_VERIFIED_BY_ID")
        self.assertEqual(len(observed_commands), 4)
        self.assertEqual(observed_commands[0][:2], ["codex", "exec"])
        for command in observed_commands[1:]:
            self.assertEqual(command[:3], ["codex", "exec", "resume"])
            self.assertIn(identifier, command)
            self.assertNotIn("--last", command)
        self.assertEqual(
            [row["raw_user_turn_sha256"] for row in result["turns"]],
            build_pair_plan([trajectory], 1, 1)[0]["turn_sha256"],
        )
        self.assertTrue(all(not row["prompt_only_instruction_applied"] for row in result["turns"]))

    def test_frozen_prompt_control_is_exact_and_applied_to_every_control_turn_only(self) -> None:
        self.assertEqual(DESIGN_THINKING_PROMPT_CONTROL, ONESHOT_DESIGN_THINKING_PROMPT_CONTROL)
        trajectory = load_trajectories()[0]
        identifier = "12345678-1234-1234-1234-123456789abc"
        delivered: list[str] = []

        def fake_call(**kwargs):
            command = list(kwargs["command"])
            delivered.append(command[-1])
            return {
                "status": "OK",
                "returncode": 0,
                "timed_out": False,
                "wall_time_seconds": 0.1,
                "usage": {
                    "input_tokens": 10,
                    "cached_input_tokens": 0,
                    "uncached_input_tokens": 10,
                    "output_tokens": 5,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 15,
                },
                "response": "assistant response",
                "thread_id": identifier,
                "event_count": 3,
                "activity": {"completed_items": 1, "tool_calls": 0, "agent_messages": 1},
                "warnings": [],
                "stderr_category": None,
            }

        with tempfile.TemporaryDirectory() as temporary, patch(
            "evals.run_trajectory_benchmark.run_codex_call", side_effect=fake_call
        ):
            root = Path(temporary)
            responses = root / "responses"
            responses.mkdir()
            result = run_candidate_trajectory(
                codex="codex",
                workdir=root,
                codex_home=root / "codex-home",
                fake_home=root / "home",
                trajectory=trajectory,
                model="candidate",
                effort="medium",
                timeout_seconds=5,
                session_mode="persisted",
                response_root=responses,
                arm="control",
                control_mode="design-thinking-prompt",
            )
        self.assertEqual(len(delivered), 4)
        for raw_turn, delivered_prompt, turn_record in zip(
            trajectory["turns"], delivered, result["turns"]
        ):
            self.assertIn(raw_turn["content"], delivered_prompt)
            self.assertIn(DESIGN_THINKING_PROMPT_CONTROL, delivered_prompt)
            self.assertTrue(turn_record["prompt_only_instruction_applied"])
            self.assertEqual(
                turn_record["raw_user_turn_sha256"], stable_digest(raw_turn["content"])
            )
            self.assertEqual(
                turn_record["delivered_prompt_sha256"], stable_digest(delivered_prompt)
            )
        for raw_turn in trajectory["turns"]:
            treatment = candidate_turn_prompt(
                raw_turn["content"], "treatment", "design-thinking-prompt"
            )
            self.assertEqual(treatment, raw_turn["content"])
            self.assertNotIn(DESIGN_THINKING_PROMPT_CONTROL, treatment)

    def test_transcript_replay_is_explicitly_labeled_and_contains_history(self) -> None:
        case = load_trajectories()[0]
        prompt = replay_prompt(case["turns"], ["first response"], 1)
        self.assertIn("TRANSCRIPT-REPLAY FALLBACK", prompt)
        self.assertIn("lower fidelity", prompt)
        self.assertIn("first response", prompt)
        self.assertIn(case["turns"][1]["content"], prompt)

    def test_isolation_copies_auth_only_and_hides_real_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "auth.json").write_text('{"token":"test-only"}', encoding="utf-8")
            (source / "config.toml").write_text("danger=true", encoding="utf-8")
            destination = prepare_codex_home(root / "fresh", source)
            environment = isolated_environment(
                destination,
                root / "fake-home",
                {"PATH": "/bin", "OPENAI_API_KEY": "must-not-leak", "SECRET": "no"},
            )
            self.assertTrue((destination / "auth.json").is_file())
            self.assertFalse((destination / "config.toml").exists())
            self.assertNotIn("OPENAI_API_KEY", environment)
            self.assertNotIn("SECRET", environment)
            self.assertEqual(environment["HOME"], str(root / "fake-home"))
            self.assertEqual(environment["CODEX_HOME"], str(destination))

    def test_only_treatment_workspace_contains_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            treatment = prepare_workspace(root / "a", "treatment")
            control = prepare_workspace(root / "b", "control")
            self.assertTrue((treatment / ".agents/skills/design-council/SKILL.md").is_file())
            self.assertFalse((control / ".agents/skills").exists())

    def test_judgment_schema_and_runtime_validator_cover_longitudinal_dimensions(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = schema["$defs"]["candidate"]["properties"]["scores"]["required"]
        self.assertEqual(set(required), set(SCORE_DIMENSIONS))
        value = {
            "trajectory_id": "case",
            "comparison_id": "comparison",
            "candidate_a": {
                "scores": {dimension: 5 for dimension in SCORE_DIMENSIONS},
                "strengths": ["adapts"],
                "weaknesses": [],
            },
            "candidate_b": {
                "scores": {dimension: 3 for dimension in SCORE_DIMENSIONS},
                "strengths": [],
                "weaknesses": ["anchors"],
            },
            "winner": "A",
            "confidence": 0.8,
            "rationale": "A adapts better.",
        }
        self.assertIsNone(validate_judgment(value, "case", "comparison"))
        value["candidate_a"]["scores"]["frame_adaptation"] = 6
        self.assertIsNotNone(validate_judgment(value, "case", "comparison"))

    def test_effectiveness_verdict_is_quality_based_not_token_gated(self) -> None:
        trajectories = load_trajectories()[:2]
        plan = build_pair_plan(trajectories, repeats=1, seed=4)
        judge_plan = build_judge_plan(plan, repetitions=1, seed=4)
        generations, judgments = _complete_records(plan, judge_plan)
        summary = aggregate_results(
            trajectories=trajectories,
            pair_plan=plan,
            judge_plan=judge_plan,
            generations=generations,
            judgments=judgments,
            tie_margin=2,
            minimum_important_uplift=3,
            bootstrap_samples=100,
            seed=4,
            control_mode="design-thinking-prompt",
        )
        self.assertEqual(
            summary["effectiveness"]["verdict"],
            "MEANINGFUL_TREATMENT_BENEFIT_ESTABLISHED",
        )
        self.assertEqual(summary["effectiveness"]["control_mode"], "design-thinking-prompt")
        self.assertIn("frozen Design Thinking prompt", summary["effectiveness"]["primary_estimand"])
        self.assertTrue(summary["completion"]["realized_design_complete"])
        self.assertEqual(summary["resource_diagnostics"]["treatment_control_token_ratio"], 3)
        self.assertIn("not a quality gate", summary["resource_diagnostics"]["interpretation"])
        self.assertTrue(summary["completion"]["judgment_plan_complete"])

    def test_judgment_plan_requires_every_exact_comparison_and_repetition(self) -> None:
        trajectories = load_trajectories()[:2]
        pair_plan = build_pair_plan(trajectories, repeats=1, seed=4)
        judge_plan = build_judge_plan(pair_plan, repetitions=2, seed=4)
        generations, complete_judgments = _complete_records(pair_plan, judge_plan)

        variants: dict[str, list[dict]] = {
            "missing_repetition": [
                record for record in complete_judgments if record["judge_repeat"] == 1
            ],
            "duplicate_comparison": json.loads(json.dumps(complete_judgments)),
            "unexpected_comparison": json.loads(json.dumps(complete_judgments)),
            "mismatched_repetition": json.loads(json.dumps(complete_judgments)),
            "mismatched_repetition_type": json.loads(json.dumps(complete_judgments)),
        }
        variants["duplicate_comparison"][-1] = json.loads(
            json.dumps(variants["duplicate_comparison"][0])
        )
        variants["unexpected_comparison"][-1]["comparison_id"] = "unplanned.r99.j99"
        variants["mismatched_repetition"][-1]["judge_repeat"] = 99
        variants["mismatched_repetition_type"][-1]["judge_repeat"] = float(
            variants["mismatched_repetition_type"][-1]["judge_repeat"]
        )

        summaries: dict[str, dict] = {}
        for name, judgments in variants.items():
            with self.subTest(name=name):
                summary = aggregate_results(
                    trajectories=trajectories,
                    pair_plan=pair_plan,
                    judge_plan=judge_plan,
                    generations=generations,
                    judgments=judgments,
                    tie_margin=2,
                    minimum_important_uplift=3,
                    bootstrap_samples=100,
                    seed=4,
                    control_mode="design-thinking-prompt",
                )
                summaries[name] = summary
                self.assertEqual(summary["effectiveness"]["verdict"], "INCOMPLETE")
                self.assertFalse(summary["completion"]["realized_design_complete"])
                self.assertFalse(summary["completion"]["judgment_plan_complete"])

        self.assertEqual(
            len(summaries["missing_repetition"]["completion"]["missing_comparison_ids"]),
            len(pair_plan),
        )
        self.assertTrue(
            summaries["duplicate_comparison"]["completion"][
                "duplicate_recorded_comparison_ids"
            ]
        )
        self.assertEqual(
            summaries["unexpected_comparison"]["completion"]["unexpected_comparison_ids"],
            ["unplanned.r99.j99"],
        )
        self.assertEqual(
            summaries["mismatched_repetition"]["completion"]["mismatched_comparisons"][
                0
            ]["fields"],
            ["judge_repeat"],
        )
        self.assertEqual(
            summaries["mismatched_repetition_type"]["completion"][
                "mismatched_comparisons"
            ][0]["fields"],
            ["judge_repeat"],
        )

    def test_generation_plan_requires_every_exact_pair_arm_and_metadata(self) -> None:
        trajectories = load_trajectories()[:2]
        pair_plan = build_pair_plan(trajectories, repeats=1, seed=4)
        judge_plan = build_judge_plan(pair_plan, repetitions=2, seed=4)
        complete_generations, judgments = _complete_records(pair_plan, judge_plan)

        variants: dict[str, list[dict]] = {
            "missing_generation": json.loads(json.dumps(complete_generations[:-1])),
            "duplicate_generation": json.loads(json.dumps(complete_generations)),
            "unexpected_generation": json.loads(json.dumps(complete_generations)),
            "mismatched_metadata": json.loads(json.dumps(complete_generations)),
            "mismatched_metadata_type": json.loads(json.dumps(complete_generations)),
        }
        variants["duplicate_generation"][-1] = json.loads(
            json.dumps(variants["duplicate_generation"][0])
        )
        unexpected = json.loads(json.dumps(complete_generations[0]))
        unexpected.update(
            {
                "pair_id": "unplanned.r99",
                "trajectory_id": "unplanned",
                "repeat": 99,
                "usage": {"total_tokens": 999_999},
            }
        )
        variants["unexpected_generation"].append(unexpected)
        variants["mismatched_metadata"][-1]["repeat"] = 99
        variants["mismatched_metadata_type"][-1]["repeat"] = float(
            variants["mismatched_metadata_type"][-1]["repeat"]
        )

        summaries: dict[str, dict] = {}
        for name, generations in variants.items():
            with self.subTest(name=name):
                summary = aggregate_results(
                    trajectories=trajectories,
                    pair_plan=pair_plan,
                    judge_plan=judge_plan,
                    generations=generations,
                    judgments=judgments,
                    tie_margin=2,
                    minimum_important_uplift=3,
                    bootstrap_samples=100,
                    seed=4,
                    control_mode="design-thinking-prompt",
                )
                summaries[name] = summary
                self.assertEqual(summary["effectiveness"]["verdict"], "INCOMPLETE")
                self.assertFalse(summary["completion"]["realized_design_complete"])
                self.assertFalse(summary["completion"]["generation_plan_complete"])
                self.assertTrue(summary["completion"]["judgment_plan_complete"])

        self.assertEqual(
            len(summaries["missing_generation"]["completion"]["missing_generation_keys"]),
            1,
        )
        self.assertTrue(
            summaries["duplicate_generation"]["completion"][
                "duplicate_recorded_generation_keys"
            ]
        )
        self.assertEqual(
            summaries["unexpected_generation"]["completion"]["unexpected_generation_keys"],
            [{"pair_id": "unplanned.r99", "arm": "treatment"}],
        )
        self.assertEqual(
            summaries["mismatched_metadata"]["completion"]["mismatched_generations"][0][
                "fields"
            ],
            ["repeat"],
        )
        self.assertEqual(
            summaries["mismatched_metadata_type"]["completion"][
                "mismatched_generations"
            ][0]["fields"],
            ["repeat"],
        )
        self.assertEqual(
            summaries["unexpected_generation"]["resource_diagnostics"][
                "treatment_control_token_ratio"
            ],
            3,
        )

    def test_saved_judgment_payloads_and_derived_values_must_be_authentic(self) -> None:
        trajectories = load_trajectories()[:2]
        pair_plan = build_pair_plan(trajectories, repeats=1, seed=4)
        judge_plan = build_judge_plan(pair_plan, repetitions=2, seed=4)
        generations, complete_judgments = _complete_records(pair_plan, judge_plan)

        variants = {
            name: json.loads(json.dumps(complete_judgments))
            for name in (
                "missing_payload",
                "invalid_payload",
                "forged_derived_value",
                "missing_derived_value",
            )
        }
        variants["missing_payload"][-1]["judgment"] = None
        variants["missing_payload"][-1]["treatment_quality"] = 999
        variants["invalid_payload"][-1]["judgment"]["candidate_a"]["scores"][
            SCORE_DIMENSIONS[0]
        ] = 6
        variants["forged_derived_value"][-1]["treatment_quality"] = 999
        variants["forged_derived_value"][-1]["mapped_winner"] = "CONTROL"
        variants["missing_derived_value"][-1].pop("candidate_a_quality")

        summaries: dict[str, dict] = {}
        for name, judgments in variants.items():
            with self.subTest(name=name):
                summary = aggregate_results(
                    trajectories=trajectories,
                    pair_plan=pair_plan,
                    judge_plan=judge_plan,
                    generations=generations,
                    judgments=judgments,
                    tie_margin=2,
                    minimum_important_uplift=3,
                    bootstrap_samples=100,
                    seed=4,
                    control_mode="design-thinking-prompt",
                )
                summaries[name] = summary
                self.assertEqual(summary["effectiveness"]["verdict"], "INCOMPLETE")
                self.assertFalse(summary["completion"]["realized_design_complete"])
                self.assertFalse(summary["completion"]["judgment_plan_complete"])
                self.assertEqual(summary["effectiveness"]["treatment_quality"], 100)
                self.assertEqual(summary["effectiveness"]["control_quality"], 80)

        for name in ("missing_payload", "invalid_payload"):
            self.assertTrue(
                summaries[name]["completion"]["invalid_judgment_payloads"]
            )
        self.assertIn(
            "treatment_quality",
            summaries["forged_derived_value"]["completion"][
                "invalid_judgment_derived_fields"
            ][0]["fields"],
        )
        self.assertIn(
            "mapped_winner",
            summaries["forged_derived_value"]["completion"][
                "invalid_judgment_derived_fields"
            ][0]["fields"],
        )
        self.assertIn(
            "candidate_a_quality",
            summaries["missing_derived_value"]["completion"][
                "invalid_judgment_derived_fields"
            ][0]["fields"],
        )

    def test_incomplete_run_summary_is_none_safe_and_does_not_claim_completion(self) -> None:
        trajectories = load_trajectories()[:2]
        pair_plan = build_pair_plan(trajectories, repeats=1, seed=4)
        judge_plan = build_judge_plan(pair_plan, repetitions=2, seed=4)
        generations = [
            {
                "pair_id": pair["pair_id"],
                "trajectory_id": pair["trajectory_id"],
                "repeat": pair["repeat"],
                "arm": arm,
                "status": "ERROR",
                "usage": {},
                "wall_time_seconds": 0.1,
            }
            for pair in pair_plan
            for arm in ("treatment", "control")
        ]
        summary = aggregate_results(
            trajectories=trajectories,
            pair_plan=pair_plan,
            judge_plan=judge_plan,
            generations=generations,
            judgments=[],
            tie_margin=2,
            minimum_important_uplift=3,
            bootstrap_samples=100,
            seed=4,
            control_mode="design-thinking-prompt",
        )
        report = render_summary(
            summary,
            {
                "run_id": "quota-failure",
                "session_mode": "persisted",
                "control_mode": "design-thinking-prompt",
                "prompt_only_control_sha256": "a" * 64,
                "candidate_model": "candidate",
                "candidate_effort": "medium",
                "judge_model": "judge",
                "judge_effort": "medium",
                "corpus_sha256": "b" * 64,
                "intervention_snapshot": {"sha256": "c" * 64},
            },
        )
        self.assertEqual(summary["effectiveness"]["verdict"], "INCOMPLETE")
        self.assertIn("unavailable treatment vs unavailable control", report)
        self.assertIn("Run incomplete", report)
        self.assertIn("planned candidate trajectories", report)
        self.assertIn("planned blind judgments", report)
        self.assertNotIn("All planned candidate trajectories", report)

    def test_quota_and_rate_limits_receive_content_free_categories(self) -> None:
        self.assertEqual(_stderr_category("Execution quota reached"), "QUOTA_DIAGNOSTIC")
        self.assertEqual(_stderr_category("HTTP 429: too many requests"), "RATE_LIMIT_DIAGNOSTIC")

    def test_cli_is_opt_in_and_dry_run_makes_no_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = dict(os.environ)
            environment.pop("DC_RUN_TRAJECTORY_BENCHMARK", None)
            skipped = subprocess.run(
                [sys.executable, str(RUNNER), "--limit", "1", "--results-dir", temporary],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(skipped.returncode, 0)
            self.assertIn("opt-in", skipped.stdout)
            self.assertEqual(list(Path(temporary).iterdir()), [])
            dry = subprocess.run(
                [sys.executable, str(RUNNER), "--dry-run", "--limit", "1", "--results-dir", temporary],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(dry.returncode, 0)
            self.assertIn("8 candidate turns", dry.stdout)
            self.assertIn("contradictory_evidence", dry.stdout)
            self.assertIn("control_mode=design-thinking-prompt", dry.stdout)
            self.assertIn(stable_digest(DESIGN_THINKING_PROMPT_CONTROL), dry.stdout)
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
