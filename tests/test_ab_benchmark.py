from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from evals.run_ab_benchmark import (
    BenchmarkError,
    DIAGNOSTIC_ARM,
    SCORE_DIMENSIONS,
    activity_from_events,
    aggregate_results,
    allocate_opaque_cell,
    build_generation_execution_plan,
    build_judge_plan,
    build_pair_plan,
    candidate_prompt,
    canonical_tree_digest,
    collect_reproducibility,
    copy_canonical_tree,
    find_user_skill_files,
    isolated_environment,
    load_cases,
    load_outcome_constructs,
    paired_bootstrap_ci,
    parse_jsonl_events,
    prepare_workspace,
    render_summary,
    run_bounded_ordered,
    usage_from_events,
    validate_judgment,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "run_ab_benchmark.py"


class ABBenchmarkTests(unittest.TestCase):
    @staticmethod
    def _scores_near(quality: float) -> dict[str, int]:
        total = max(0, min(35, round(quality * len(SCORE_DIMENSIONS) / 20)))
        quotient, remainder = divmod(total, len(SCORE_DIMENSIONS))
        return {
            dimension: quotient + (1 if index < remainder else 0)
            for index, dimension in enumerate(SCORE_DIMENSIONS)
        }

    def _judgment_for_plan(
        self,
        planned: dict,
        treatment_quality: float,
        control_quality: float,
    ) -> dict:
        scores_by_arm = {
            "treatment": self._scores_near(treatment_quality),
            "control": self._scores_near(control_quality),
        }
        a_arm = planned["label_a_arm"]
        b_arm = planned["label_b_arm"]
        a_quality = round(
            sum(scores_by_arm[a_arm].values()) / len(SCORE_DIMENSIONS) * 20, 6
        )
        b_quality = round(
            sum(scores_by_arm[b_arm].values()) / len(SCORE_DIMENSIONS) * 20, 6
        )
        if a_quality == b_quality:
            winner = "TIE"
            mapped_winner = "TIE"
        elif a_quality > b_quality:
            winner = "A"
            mapped_winner = a_arm.upper()
        else:
            winner = "B"
            mapped_winner = b_arm.upper()
        return {
            "record_type": "judgment",
            **planned,
            "status": "OK",
            "judgment": {
                "case_id": planned["case_id"],
                "comparison_id": planned["comparison_id"],
                "candidate_a": {
                    "scores": scores_by_arm[a_arm],
                    "strengths": [],
                    "weaknesses": [],
                },
                "candidate_b": {
                    "scores": scores_by_arm[b_arm],
                    "strengths": [],
                    "weaknesses": [],
                },
                "winner": winner,
                "confidence": 0.8,
                "rationale": "Candidates were compared against the frozen rubric.",
            },
            "candidate_a_quality": a_quality,
            "candidate_b_quality": b_quality,
            "treatment_quality": a_quality if a_arm == "treatment" else b_quality,
            "control_quality": a_quality if a_arm == "control" else b_quality,
            "mapped_winner": mapped_winner,
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "uncached_input_tokens": 100,
                "output_tokens": 10,
                "reasoning_output_tokens": 2,
                "total_tokens": 110,
            },
            "wall_time_seconds": 1,
        }

    def _positive_complete_fixture(
        self,
        *,
        treatment_quality: float = 80,
        control_quality: float = 60,
        treatment_tokens: int = 140,
        control_tokens: int = 100,
    ) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
        cases = load_cases()[:12]
        plan = build_pair_plan(cases, repeats=2, seed=21)
        judge_plan = build_judge_plan(plan, repetitions=2, seed=21)
        generations: list[dict] = []
        judgments: list[dict] = []
        for pair in plan:
            for arm, tokens in (("treatment", treatment_tokens), ("control", control_tokens)):
                generations.append(
                    {
                        "record_type": "generation",
                        "case_id": pair["case_id"],
                        "pair_id": pair["pair_id"],
                        "repeat": pair["repeat"],
                        "arm": arm,
                        "raw_prompt_sha256": pair["raw_prompt_sha256"],
                        "included_in_primary_uplift": True,
                        "status": "OK",
                        "usage": {
                            "input_tokens": tokens - 20,
                            "cached_input_tokens": 0,
                            "uncached_input_tokens": tokens - 20,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 5,
                            "total_tokens": tokens,
                        },
                        "wall_time_seconds": 1,
                        "response_word_count": 80,
                        "activity": {
                            "completed_items": 2,
                            "tool_calls": 1 if arm == "treatment" else 0,
                            "command_executions": 1 if arm == "treatment" else 0,
                            "agent_messages": 1,
                        },
                    }
                )
        for planned in judge_plan:
            judgments.append(
                self._judgment_for_plan(planned, treatment_quality, control_quality)
            )
        return cases, plan, generations, judgments

    def _aggregate_complete(
        self,
        cases: list[dict],
        plan: list[dict],
        generations: list[dict],
        judgments: list[dict],
    ) -> dict:
        return aggregate_results(
            cases=cases,
            pair_plan=plan,
            generations=generations,
            judgments=judgments,
            bootstrap_samples=500,
            seed=21,
            tie_margin=2,
            repeats=2,
            judge_repetitions=2,
            candidate_model="candidate",
            judge_model="independent-judge",
            word_cap=900,
            outcome_constructs=load_outcome_constructs(cases),
        )

    def test_neutral_corpus_has_breadth_and_straightforward_case(self) -> None:
        cases = load_cases()
        self.assertGreaterEqual(len(cases), 12)
        self.assertIn("dark_mode", {case["id"] for case in cases})
        body = json.dumps(cases).lower()
        self.assertNotIn("must demonstrate", body)
        self.assertNotIn("expected answer", body)

    def test_outcome_construct_registry_covers_intended_product_value(self) -> None:
        cases = load_cases()
        constructs = load_outcome_constructs(cases)
        self.assertEqual(set(constructs), {
            "right_problem_framing",
            "structured_divergence_and_synthesis",
            "evidence_discipline",
            "learning_and_iteration",
            "appropriate_scope",
        })
        self.assertIn("family_scheduler", constructs["right_problem_framing"]["case_ids"])
        self.assertIn("contradictory_evidence", constructs["learning_and_iteration"]["case_ids"])
        self.assertEqual(
            set(constructs["appropriate_scope"]["case_ids"]),
            {"dark_mode", "parser_spike"},
        )

    def test_committed_beta3_evidence_separates_effectiveness_from_resources(self) -> None:
        evidence = json.loads(
            (REPO_ROOT / "evals" / "evidence" / "ab-benchmark-beta3.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            evidence["reporting_hierarchy"]["primary_effectiveness_verdict"],
            "MEANINGFUL_BENEFIT_ESTABLISHED",
        )
        self.assertEqual(
            evidence["reporting_hierarchy"]["resource_descriptor"],
            "ABOVE_CONFIGURED_BUDGET",
        )
        self.assertNotIn("preregistered_value_verdict", evidence["incremental_value"])
        self.assertIn("post-hoc", evidence["post_hoc_outcome_profile"]["note"].lower())

    def test_identical_primary_prompt_and_explicit_diagnostic(self) -> None:
        raw = "Help me decide what to do."
        treatment = candidate_prompt(raw, word_cap=700)
        control = candidate_prompt(raw, word_cap=700)
        diagnostic = candidate_prompt(raw, word_cap=700, explicit=True)
        self.assertEqual(treatment, control)
        self.assertEqual(treatment.count(raw), 1)
        self.assertNotIn("$design-think", treatment)
        self.assertIn("$design-think", diagnostic)
        self.assertIn("within 700 words", treatment)

    def test_frozen_prompt_only_control_is_explicit_and_not_in_primary_prompt(self) -> None:
        raw = "Help me decide what to do."
        treatment = candidate_prompt(raw)
        prompt_control = candidate_prompt(raw, control_mode="design-thinking-prompt")
        self.assertNotIn("PROMPT-ONLY METHOD INSTRUCTION", treatment)
        self.assertIn("PROMPT-ONLY METHOD INSTRUCTION", prompt_control)
        self.assertIn("underlying human problem", prompt_control)

    def test_pair_plan_is_deterministic_and_counterbalanced(self) -> None:
        cases = load_cases()[:4]
        first = build_pair_plan(cases, repeats=2, seed=17)
        second = build_pair_plan(cases, repeats=2, seed=17)
        self.assertEqual(first, second)
        for case in cases:
            rows = [row for row in first if row["case_id"] == case["id"]]
            self.assertEqual({tuple(row["arm_order"]) for row in rows}, {
                ("treatment", "control"),
                ("control", "treatment"),
            })

    def test_judge_plan_swaps_labels_with_two_repetitions(self) -> None:
        pairs = build_pair_plan(load_cases()[:3], repeats=1, seed=9)
        plan = build_judge_plan(pairs, repetitions=2, seed=9)
        for pair in pairs:
            rows = [row for row in plan if row["pair_id"] == pair["pair_id"]]
            self.assertEqual({row["label_a_arm"] for row in rows}, {"treatment", "control"})
            self.assertTrue(all(row["label_a_arm"] != row["label_b_arm"] for row in rows))

    def test_generation_execution_plan_keeps_pair_arms_serial_and_sequences_stable(self) -> None:
        pairs = build_pair_plan(load_cases()[:4], repeats=2, seed=17)
        first = build_generation_execution_plan(pairs, explicit_diagnostic=True)
        second = build_generation_execution_plan(pairs, explicit_diagnostic=True)
        self.assertEqual(first, second)
        self.assertEqual([batch["pair_id"] for batch in first], [pair["pair_id"] for pair in pairs])
        calls = [call for batch in first for call in batch["calls"]]
        self.assertEqual(
            [call["generation_sequence"] for call in calls],
            list(range(1, len(calls) + 1)),
        )
        for pair, batch in zip(pairs, first):
            self.assertEqual(
                [call["arm"] for call in batch["calls"]],
                pair["arm_order"] + [DIAGNOSTIC_ARM],
            )
            self.assertEqual(
                [call["included_in_primary_uplift"] for call in batch["calls"]],
                [True, True, False],
            )

    def test_bounded_pair_concurrency_returns_deterministic_plan_order(self) -> None:
        pairs = build_pair_plan(load_cases()[:3], repeats=1, seed=8)
        batches = build_generation_execution_plan(pairs)
        lock = threading.Lock()
        first_two_started = threading.Barrier(2)
        active = 0
        maximum_active = 0
        observed_arms: dict[str, list[str]] = {}
        completion_order: list[str] = []

        def worker(batch: dict) -> dict:
            nonlocal active, maximum_active
            with lock:
                active += 1
                maximum_active = max(maximum_active, active)
            if batch["pair_index"] < 2:
                first_two_started.wait(timeout=2)
            if batch["pair_index"] == 0:
                time.sleep(0.03)
            arms: list[str] = []
            for call in batch["calls"]:
                arms.append(call["arm"])
            with lock:
                observed_arms[batch["pair_id"]] = arms
                active -= 1
            return {
                "pair_id": batch["pair_id"],
                "sequences": [call["generation_sequence"] for call in batch["calls"]],
            }

        def progress(completed: int, total: int, batch: dict, _result: dict) -> None:
            self.assertLessEqual(completed, total)
            completion_order.append(batch["pair_id"])

        results = run_bounded_ordered(batches, worker, workers=2, progress=progress)
        self.assertEqual(maximum_active, 2)
        self.assertEqual(len(completion_order), len(batches))
        self.assertEqual([result["pair_id"] for result in results], [batch["pair_id"] for batch in batches])
        self.assertEqual(
            [sequence for result in results for sequence in result["sequences"]],
            list(range(1, len(batches) * 2 + 1)),
        )
        for pair, batch in zip(pairs, batches):
            self.assertEqual(observed_arms[batch["pair_id"]], pair["arm_order"])

    def test_bounded_execution_rejects_nonpositive_workers(self) -> None:
        with self.assertRaisesRegex(BenchmarkError, "--workers must be positive"):
            run_bounded_ordered([1], lambda value: value, workers=0)

    def test_workspaces_differ_only_by_local_skill_intervention(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            treatment = prepare_workspace(root / "one", "treatment")
            control = prepare_workspace(root / "two", "control")
            explicit = prepare_workspace(root / "three", DIAGNOSTIC_ARM)
            self.assertTrue((treatment / ".agents/skills/mightshape/SKILL.md").is_file())
            self.assertFalse((control / ".agents/skills").exists())
            self.assertTrue((explicit / ".agents/skills/mightshape/SKILL.md").is_file())
            self.assertEqual(
                (treatment / "AGENTS.md").read_text(),
                (control / "AGENTS.md").read_text(),
            )

    def test_candidate_cells_are_opaque_and_do_not_leak_arm_in_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            treatment_cell = allocate_opaque_cell(root)
            control_cell = allocate_opaque_cell(root)
            treatment = prepare_workspace(treatment_cell, "treatment")
            control = prepare_workspace(control_cell, "control")
            self.assertNotEqual(treatment_cell, control_cell)
            for workdir in (treatment, control):
                relative = workdir.relative_to(root).as_posix().lower()
                self.assertNotIn("treatment", relative)
                self.assertNotIn("control", relative)
                self.assertRegex(relative, r"^candidate-cells/cell-[0-9a-f]{24}/workspace$")

    def test_canonical_skill_hash_excludes_caches_and_duplicate_two_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / "SKILL.md").write_text("canonical\n", encoding="utf-8")
            (root / "references").mkdir()
            (root / "references" / "policy.md").write_text("policy\n", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "cache.pyc").write_bytes(b"one")
            (root / "SKILL 2.md").write_text("duplicate one\n", encoding="utf-8")
            first = canonical_tree_digest(root)
            self.assertEqual(first["file_count"], 2)
            (root / "__pycache__" / "cache.pyc").write_bytes(b"two")
            (root / "SKILL 2.md").write_text("duplicate two\n", encoding="utf-8")
            self.assertEqual(first, canonical_tree_digest(root))
            (root / "SKILL.md").write_text("changed\n", encoding="utf-8")
            self.assertNotEqual(first["sha256"], canonical_tree_digest(root)["sha256"])

    def test_frozen_intervention_snapshot_is_independent_of_later_source_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("frozen\n", encoding="utf-8")
            (source / "SKILL 2.md").write_text("ignored\n", encoding="utf-8")
            snapshot = root / "snapshot"
            frozen_digest = copy_canonical_tree(source, snapshot)
            self.assertEqual(frozen_digest, canonical_tree_digest(snapshot))
            self.assertFalse((snapshot / "SKILL 2.md").exists())

            (source / "SKILL.md").write_text("mutated after freeze\n", encoding="utf-8")
            self.assertNotEqual(canonical_tree_digest(source), frozen_digest)
            treatment = prepare_workspace(root / "cell", "treatment", snapshot)
            self.assertEqual(
                (treatment / ".agents/skills/mightshape/SKILL.md").read_text(encoding="utf-8"),
                "frozen\n",
            )

    def test_reproducibility_manifest_captures_source_and_runtime_hashes(self) -> None:
        details = collect_reproducibility(sys.executable)
        self.assertEqual(details["design_council_version"], (REPO_ROOT / "VERSION").read_text().strip())
        self.assertRegex(details["skill_tree"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(details["runner_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(details["judge_schema_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(details["codex_version"].startswith("Python "))
        self.assertIn("dirty", details["git"])
        self.assertTrue(details["python"]["version"])
        self.assertTrue(details["platform"])

    def test_isolated_environment_drops_unrelated_credentials(self) -> None:
        environment = isolated_environment(
            Path("/tmp/benchmark-codex-home"),
            {
                "PATH": "/bin",
                "LANG": "en_US.UTF-8",
                "OPENAI_API_KEY": "must-not-pass",
                "GITHUB_TOKEN": "must-not-pass",
                "MCP_SERVICE_SECRET": "must-not-pass",
            },
        )
        self.assertEqual(environment["PATH"], "/bin")
        self.assertEqual(environment["CODEX_HOME"], "/tmp/benchmark-codex-home")
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("GITHUB_TOKEN", environment)
        self.assertNotIn("MCP_SERVICE_SECRET", environment)

    def test_user_skill_preflight_detects_contamination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            home = Path(temp_name)
            skill = home / ".agents" / "skills" / "other" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: other\n---\n", encoding="utf-8")
            self.assertEqual(find_user_skill_files(home), [skill])

    def test_jsonl_usage_parser_keeps_reasoning_as_output_breakdown(self) -> None:
        text = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "t"}),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 120,
                            "cached_input_tokens": 80,
                            "output_tokens": 30,
                            "reasoning_output_tokens": 10,
                        },
                    }
                ),
            ]
        )
        events, errors = parse_jsonl_events(text)
        usage, warnings = usage_from_events(events)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(usage["uncached_input_tokens"], 40)
        self.assertEqual(usage["total_tokens"], 150)

    def test_jsonl_usage_parser_rejects_missing_required_totals(self) -> None:
        usage, warnings = usage_from_events(
            [{"type": "turn.completed", "usage": {"cached_input_tokens": 10, "output_tokens": 5}}]
        )
        self.assertIsNone(usage)
        self.assertIn("required input_tokens", " ".join(warnings))

    def test_jsonl_usage_parser_rejects_impossible_cached_total(self) -> None:
        usage, warnings = usage_from_events(
            [
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 10,
                        "cached_input_tokens": 11,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 2,
                    },
                }
            ]
        )
        self.assertIsNone(usage)
        self.assertIn("exceeds input_tokens", " ".join(warnings))

    def test_activity_parser_counts_completed_tool_rounds_without_duplicates(self) -> None:
        events = [
            {"type": "item.started", "item": {"id": "i1", "type": "command_execution"}},
            {"type": "item.completed", "item": {"id": "i1", "type": "command_execution"}},
            {"type": "item.completed", "item": {"id": "i1", "type": "command_execution"}},
            {"type": "item.completed", "item": {"id": "i2", "type": "agent_message"}},
        ]
        self.assertEqual(
            activity_from_events(events),
            {"completed_items": 2, "tool_calls": 1, "command_executions": 1, "agent_messages": 1},
        )

    def test_judgment_validation_binds_case_and_dimensions(self) -> None:
        scores = {
            "problem_understanding": 4,
            "methodological_rigor": 4,
            "breadth_and_nonobviousness": 4,
            "evidence_calibration": 4,
            "actionability": 4,
            "task_fit_and_clarity": 4,
            "communication_efficiency": 4,
        }
        value = {
            "case_id": "case",
            "comparison_id": "case.r01.j01",
            "candidate_a": {"scores": scores, "strengths": [], "weaknesses": []},
            "candidate_b": {"scores": scores, "strengths": [], "weaknesses": []},
            "winner": "TIE",
            "confidence": 0.5,
            "rationale": "Equivalent.",
        }
        self.assertIsNone(validate_judgment(value, "case", "case.r01.j01"))
        self.assertIsNotNone(validate_judgment(value, "other", "case.r01.j01"))
        value["confidence"] = True
        self.assertIn("confidence", validate_judgment(value, "case", "case.r01.j01"))
        value["confidence"] = 0.5
        value["rationale"] = ""
        self.assertIn("rationale", validate_judgment(value, "case", "case.r01.j01"))

    def test_bootstrap_is_deterministic(self) -> None:
        first = paired_bootstrap_ci([10, 5, -1, 7], samples=1000, seed=3)
        second = paired_bootstrap_ci([10, 5, -1, 7], samples=1000, seed=3)
        self.assertEqual(first, second)
        self.assertLess(first["lower"], first["upper"])

    def test_aggregate_warns_small_sample_and_crossing_zero(self) -> None:
        cases = load_cases()[:2]
        plan = build_pair_plan(cases, repeats=1, seed=4)
        judge_plan = build_judge_plan(plan, repetitions=1, seed=4)
        generations = []
        for pair in plan:
            for arm in ("treatment", "control"):
                input_tokens = 160 if arm == "treatment" else 100
                generations.append(
                    {
                        "record_type": "generation",
                        "case_id": pair["case_id"],
                        "pair_id": pair["pair_id"],
                        "repeat": pair["repeat"],
                        "arm": arm,
                        "raw_prompt_sha256": pair["raw_prompt_sha256"],
                        "included_in_primary_uplift": True,
                        "status": "OK",
                        "usage": {
                            "input_tokens": input_tokens,
                            "cached_input_tokens": 20,
                            "uncached_input_tokens": input_tokens - 20,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 5,
                            "total_tokens": input_tokens + 20,
                        },
                        "wall_time_seconds": 1 if arm == "control" else 2,
                        "response_word_count": 50,
                        "activity": {
                            "completed_items": 1,
                            "tool_calls": 0,
                            "command_executions": 0,
                            "agent_messages": 1,
                        },
                    }
                )
        judgments = [
            self._judgment_for_plan(planned, 60 if index == 0 else 40, 50)
            for index, planned in enumerate(judge_plan)
        ]
        summary = aggregate_results(
            cases=cases,
            pair_plan=plan,
            generations=generations,
            judgments=judgments,
            bootstrap_samples=1000,
            seed=4,
            tie_margin=2,
            repeats=1,
            judge_repetitions=1,
            candidate_model="same",
            judge_model="same",
            word_cap=900,
        )
        self.assertEqual(summary["conclusion"], "INCONCLUSIVE")
        self.assertEqual(summary["explicit_invocation_diagnostic"]["included_in_primary_uplift"], False)
        self.assertEqual(summary["quality"]["case_win_tie_loss"], {
            "wins": 1,
            "ties": 0,
            "losses": 1,
            "tie_margin_points": 2,
        })
        self.assertEqual(summary["quality"]["blind_preference_votes"], {
            "treatment": 1,
            "control": 1,
            "tie": 0,
        })
        warning_text = " ".join(summary["warnings"])
        self.assertIn("exploratory", warning_text)
        self.assertIn("crosses zero", warning_text)
        self.assertIn("heuristic", warning_text)
        self.assertEqual(summary["primary_effectiveness_assessment"]["verdict"], "INCONCLUSIVE")

    def test_complete_realized_design_can_support_separate_quality_and_value_verdicts(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "TREATMENT_BETTER")
        self.assertEqual(
            summary["primary_effectiveness_assessment"]["verdict"],
            "MEANINGFUL_BENEFIT_ESTABLISHED",
        )
        self.assertEqual(summary["resource_efficiency_assessment"]["verdict"], "WITHIN_CONFIGURED_BUDGET")
        self.assertTrue(summary["realized_design"]["minimum_design_met"])
        self.assertEqual(summary["complete_pairs"], summary["planned_pairs"])
        incremental = summary["incremental_value"]
        self.assertEqual(incremental["primary_metric"]["name"], "marginal_quality_yield")
        self.assertEqual(incremental["primary_metric"]["value"], 500.0)
        self.assertEqual(incremental["resource_premium"]["incremental_generation_tokens"], 40.0)
        self.assertEqual(incremental["diagnostics"]["incremental_tokens_per_quality_point"], 2.0)
        self.assertEqual(
            incremental["diagnostics"]["quality_cost_quadrant"],
            "QUALITY_GAIN_FOR_TOKEN_PREMIUM",
        )
        self.assertEqual(len(summary["outcome_construct_profile"]["constructs"]), 5)
        self.assertEqual(len(summary["outcome_dimension_profile"]["dimensions"]), 7)

    def test_missing_judgment_forces_direction_and_value_inconclusive(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        judgments.pop()
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")
        self.assertEqual(summary["primary_effectiveness_assessment"]["verdict"], "INCONCLUSIVE")
        self.assertFalse(summary["realized_design"]["requested_judgments_realized"])
        self.assertEqual(summary["complete_pairs"], summary["planned_pairs"] - 1)

    def test_failed_generation_forces_direction_inconclusive_even_with_scores(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        generations[0]["status"] = "ERROR"
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")
        self.assertFalse(summary["realized_design"]["all_planned_pairs_usable"])

    def test_generation_records_must_match_the_exact_plan_and_schema(self) -> None:
        cases, plan, complete_generations, judgments = self._positive_complete_fixture()
        variants = {
            name: json.loads(json.dumps(complete_generations))
            for name in (
                "duplicate",
                "unexpected",
                "mismatched_metadata",
                "invalid_payload",
            )
        }
        variants["duplicate"][-1] = json.loads(json.dumps(variants["duplicate"][0]))
        unexpected = json.loads(json.dumps(complete_generations[0]))
        unexpected.update({"pair_id": "unplanned.r99", "case_id": "unplanned"})
        variants["unexpected"].append(unexpected)
        variants["mismatched_metadata"][-1]["repeat"] = 99
        variants["invalid_payload"][-1]["response_word_count"] = -1

        summaries = {}
        for name, generations in variants.items():
            with self.subTest(name=name):
                summary = self._aggregate_complete(cases, plan, generations, judgments)
                summaries[name] = summary
                integrity = summary["realized_design"]["generation_integrity"]
                self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")
                self.assertFalse(summary["realized_design"]["release_quality_complete"])
                self.assertFalse(integrity["generation_plan_complete"])

        self.assertTrue(
            summaries["duplicate"]["realized_design"]["generation_integrity"][
                "duplicate_recorded_generation_keys"
            ]
        )
        self.assertEqual(
            summaries["unexpected"]["realized_design"]["generation_integrity"][
                "unexpected_generation_keys"
            ],
            [{"pair_id": "unplanned.r99", "arm": "treatment"}],
        )
        self.assertEqual(
            summaries["mismatched_metadata"]["realized_design"]["generation_integrity"][
                "mismatched_generations"
            ][0]["fields"],
            ["repeat"],
        )
        self.assertTrue(
            summaries["invalid_payload"]["realized_design"]["generation_integrity"][
                "invalid_generation_payloads"
            ]
        )

    def test_missing_or_inconsistent_generation_usage_fails_closed(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        generations[0]["usage"].pop("total_tokens")
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        integrity = summary["realized_design"]["generation_integrity"]
        self.assertFalse(integrity["generation_usage_complete"])
        self.assertFalse(summary["realized_design"]["release_quality_complete"])
        self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")
        self.assertEqual(
            summary["generation_cost"]["resource_profile_by_arm"]["treatment"][
                "successful_resource_complete_calls"
            ],
            len(plan) - 1,
        )

    def test_judgments_must_match_exact_blind_plan_and_valid_payload(self) -> None:
        cases, plan, generations, complete_judgments = self._positive_complete_fixture()
        variants = {
            name: json.loads(json.dumps(complete_judgments))
            for name in ("duplicate", "unexpected", "mismatched_label", "invalid_payload")
        }
        variants["duplicate"][-1] = json.loads(json.dumps(variants["duplicate"][0]))
        variants["unexpected"][-1]["comparison_id"] = "unplanned.r99.j99"
        variants["mismatched_label"][-1]["label_a_arm"] = (
            "control"
            if variants["mismatched_label"][-1]["label_a_arm"] == "treatment"
            else "treatment"
        )
        variants["invalid_payload"][-1]["judgment"]["candidate_a"]["scores"][
            SCORE_DIMENSIONS[0]
        ] = 6

        summaries = {}
        for name, judgments in variants.items():
            with self.subTest(name=name):
                summary = self._aggregate_complete(cases, plan, generations, judgments)
                summaries[name] = summary
                integrity = summary["realized_design"]["judgment_integrity"]
                self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")
                self.assertFalse(summary["realized_design"]["release_quality_complete"])
                self.assertFalse(integrity["judgment_plan_complete"])

        self.assertTrue(
            summaries["duplicate"]["realized_design"]["judgment_integrity"][
                "duplicate_recorded_comparison_ids"
            ]
        )
        self.assertEqual(
            summaries["unexpected"]["realized_design"]["judgment_integrity"][
                "unexpected_comparison_ids"
            ],
            ["unplanned.r99.j99"],
        )
        self.assertIn(
            "label_a_arm",
            summaries["mismatched_label"]["realized_design"]["judgment_integrity"][
                "mismatched_comparisons"
            ][0]["fields"],
        )
        self.assertTrue(
            summaries["invalid_payload"]["realized_design"]["judgment_integrity"][
                "invalid_judgment_payloads"
            ]
        )

    def test_quality_and_winner_are_recomputed_from_payload_not_cached_fields(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        judgments[0]["candidate_a_quality"] = 0
        judgments[0]["treatment_quality"] = 0
        judgments[0]["control_quality"] = 100
        judgments[0]["mapped_winner"] = "CONTROL"
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        integrity = summary["realized_design"]["judgment_integrity"]
        self.assertEqual(summary["quality"]["treatment_mean"], 80)
        self.assertEqual(summary["quality"]["control_mean"], 60)
        self.assertEqual(summary["quality"]["blind_preference_votes"]["treatment"], len(judgments))
        self.assertTrue(integrity["derived_values_recomputed"])
        self.assertTrue(integrity["mismatched_cached_judgment_fields"])
        self.assertFalse(integrity["judgment_plan_complete"])
        self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")

    def test_redundant_cached_judgment_fields_are_not_required(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        for judgment in judgments:
            for field in (
                "candidate_a_quality",
                "candidate_b_quality",
                "treatment_quality",
                "control_quality",
                "mapped_winner",
            ):
                judgment.pop(field)
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertTrue(summary["realized_design"]["release_quality_complete"])
        self.assertEqual(summary["quality"]["treatment_mean"], 80)
        self.assertEqual(summary["quality"]["control_mean"], 60)

    def test_missing_judge_usage_fails_closed_without_losing_payload_diagnostic(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        judgments[0]["usage"] = None
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        integrity = summary["realized_design"]["judgment_integrity"]
        self.assertFalse(integrity["judgment_usage_complete"])
        self.assertFalse(summary["realized_design"]["release_quality_complete"])
        self.assertEqual(summary["quality"]["treatment_mean"], 80)
        self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")

    def test_resource_profile_reports_absolute_token_words_and_activity_deltas(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        cost = summary["generation_cost"]
        self.assertEqual(cost["absolute_mean_token_delta"], 40)
        self.assertEqual(
            cost["absolute_treatment_minus_control"]["mean_usage_per_call"],
            {
                "input_tokens": 40,
                "cached_input_tokens": 0,
                "uncached_input_tokens": 40,
                "output_tokens": 0,
                "reasoning_output_tokens": 0,
                "total_tokens": 40,
            },
        )
        self.assertEqual(
            cost["absolute_treatment_minus_control"]["mean_response_words_per_call"],
            0,
        )
        self.assertEqual(
            cost["absolute_treatment_minus_control"]["mean_activity_per_call"]["tool_calls"],
            1,
        )
        self.assertEqual(
            cost["resource_profile_by_arm"]["treatment"]["mean_usage_per_call"]["total_tokens"],
            140,
        )

    def test_missing_requested_repeat_forces_direction_inconclusive(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        removed_pair = plan.pop()
        generations[:] = [record for record in generations if record["pair_id"] != removed_pair["pair_id"]]
        judgments[:] = [record for record in judgments if record["pair_id"] != removed_pair["pair_id"]]
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "INCONCLUSIVE")
        self.assertFalse(summary["realized_design"]["plan_shape_complete"])
        self.assertFalse(summary["realized_design"]["requested_repeats_realized"])

    def test_token_budget_cannot_veto_meaningful_outcome_benefit(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture(
            treatment_tokens=180,
            control_tokens=100,
        )
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "TREATMENT_BETTER")
        self.assertEqual(
            summary["primary_effectiveness_assessment"]["verdict"],
            "MEANINGFUL_BENEFIT_ESTABLISHED",
        )
        self.assertEqual(summary["resource_efficiency_assessment"]["verdict"], "ABOVE_CONFIGURED_BUDGET")

    def test_statistical_quality_gain_below_importance_threshold_is_not_called_meaningful(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture(
            treatment_quality=62,
            control_quality=60,
        )
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "TREATMENT_BETTER")
        self.assertEqual(
            summary["primary_effectiveness_assessment"]["verdict"],
            "BENEFIT_BELOW_IMPORTANCE_THRESHOLD",
        )

    def test_lower_tokens_are_reported_separately_from_effectiveness(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture(
            treatment_quality=62,
            control_quality=60,
            treatment_tokens=80,
            control_tokens=100,
        )
        summary = self._aggregate_complete(cases, plan, generations, judgments)
        self.assertEqual(summary["quality_direction"], "TREATMENT_BETTER")
        self.assertEqual(
            summary["primary_effectiveness_assessment"]["verdict"],
            "BENEFIT_BELOW_IMPORTANCE_THRESHOLD",
        )
        self.assertEqual(summary["resource_efficiency_assessment"]["verdict"], "NO_TOKEN_PREMIUM")

    def test_markdown_report_separates_quality_value_and_reproducibility(self) -> None:
        cases, plan, generations, judgments = self._positive_complete_fixture()
        reproducibility = {
            "design_council_version": "0.9.0-beta.3",
            "skill_tree": {"sha256": "a" * 64, "file_count": 42},
            "runner_sha256": "b" * 64,
            "judge_schema_sha256": "c" * 64,
            "git": {"commit": "d" * 40, "dirty": False},
            "codex_version": "codex-test",
            "python": {"implementation": "CPython", "version": "3.test"},
            "platform": "test-platform",
        }
        summary = aggregate_results(
            cases=cases,
            pair_plan=plan,
            generations=generations,
            judgments=judgments,
            bootstrap_samples=500,
            seed=21,
            tie_margin=2,
            repeats=2,
            judge_repetitions=2,
            candidate_model="candidate",
            judge_model="independent-judge",
            word_cap=900,
            reproducibility=reproducibility,
        )
        report = render_summary(
            summary,
            {
                "run_id": "test-run",
                "candidate_model": "candidate",
                "candidate_effort": "medium",
                "judge_model": "independent-judge",
                "judge_effort": "medium",
                "seed": 21,
                "case_count": 12,
                "repeats": 2,
                "judge_repetitions": 2,
                "corpus_sha256": "e" * 64,
            },
        )
        self.assertIn("Quality direction", report)
        self.assertIn("Primary outcome effectiveness", report)
        self.assertIn("Token-budget descriptor", report)
        self.assertIn("Canonical skill tree SHA-256", report)
        self.assertIn("Treatment invocation", report)
        self.assertIn("does not determine outcome effectiveness", report)
        self.assertIn("Generation-cost anatomy", report)
        self.assertIn("Absolute Δ (T−C)", report)
        self.assertIn("Exact release-quality record/usage integrity", report)
        self.assertIn("Completed tool calls", report)
        self.assertIn("command executions", report)
        self.assertIn("Incremental value purchased", report)
        self.assertIn("quality points per 1k additional tokens", report)
        self.assertIn("User-value construct profile", report)
        self.assertIn("Blind judge dimension profile", report)

    def test_default_cli_skips_without_opt_in(self) -> None:
        environment = os.environ.copy()
        environment.pop("DC_RUN_AB_BENCHMARK", None)
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--limit", "1"],
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("SKIP", completed.stdout)

    def test_dry_run_is_offline_and_reports_isolation_flags(self) -> None:
        environment = os.environ.copy()
        environment.pop("DC_RUN_AB_BENCHMARK", None)
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--case",
                "dark_mode",
                "--explicit-diagnostic",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("explicit_diagnostic=True", completed.stdout)
        self.assertIn("workers=1", completed.stdout)
        self.assertIn("minimum_important_uplift=3.0", completed.stdout)
        self.assertIn("max_token_ratio=1.5", completed.stdout)
        self.assertIn("$design-think", completed.stdout)

    def test_claude_dry_run_uses_native_invocation_without_auth(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--case",
                "family_scheduler",
                "--candidate-runtime",
                "claude",
                "--explicit-diagnostic",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("runtime=claude", completed.stdout)
        self.assertIn("/mightshape:design-think", completed.stdout)

    def test_primary_treatment_can_be_explicitly_invoked(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--case",
                "family_scheduler",
                "--control-mode",
                "design-thinking-prompt",
                "--treatment-invocation",
                "explicit",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("treatment_invocation=explicit", completed.stdout)
        treatment_section = completed.stdout.split("[treatment candidate input]", 1)[1].split(
            "[prompt-only control candidate input]", 1
        )[0]
        self.assertIn("$design-think", treatment_section)
        self.assertNotIn("PROMPT-ONLY METHOD INSTRUCTION", treatment_section)


if __name__ == "__main__":
    unittest.main()
