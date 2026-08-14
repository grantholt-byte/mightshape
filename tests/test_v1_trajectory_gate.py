from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evals.run_trajectory_benchmark import (
    DESIGN_THINKING_PROMPT_CONTROL,
    SCORE_DIMENSIONS,
    aggregate_results,
    build_judge_plan,
    build_pair_plan,
    candidate_quality,
    candidate_turn_prompt,
    canonical_tree_digest,
    load_trajectories,
    stable_digest,
    transcript_for_judge,
)
from scripts.verify_v1_trajectory_gate import (
    DEFAULT_POLICY,
    USAGE_FIELDS,
    V1TrajectoryGateError,
    load_policy,
    verify_v1_trajectory_run,
)


ROOT = Path(__file__).resolve().parents[1]


def _usage(multiplier: int = 1) -> dict[str, int]:
    return {
        "input_tokens": 10 * multiplier,
        "cached_input_tokens": 4 * multiplier,
        "uncached_input_tokens": 6 * multiplier,
        "output_tokens": 5 * multiplier,
        "reasoning_output_tokens": 1 * multiplier,
        "total_tokens": 15 * multiplier,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


class V1TrajectoryGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "gate-run"
        self.run.mkdir()
        self.commit = "a" * 40
        self.trajectories = load_trajectories()
        self.policy = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
        design = self.policy["design"]
        self.pairs = build_pair_plan(
            self.trajectories, design["repeats"], design["seed"]
        )
        self.judges = build_judge_plan(
            self.pairs, design["judge_repetitions"], design["seed"]
        )
        snapshot = self.run / "intervention-snapshot"
        shutil.copytree(ROOT / "skills/mightshape", snapshot)
        snapshot_digest = canonical_tree_digest(snapshot)
        corpus_payload = "\n".join(
            json.dumps(case, sort_keys=True, separators=(",", ":"))
            for case in self.trajectories
        )
        self.manifest = {
            "schema_version": "1.0.0",
            "run_id": self.run.name,
            "candidate_model": design["candidate_model"],
            "candidate_effort": design["candidate_effort"],
            "judge_model": design["judge_model"],
            "judge_effort": design["judge_effort"],
            "session_mode": design["session_mode"],
            "control_mode": design["control_mode"],
            "treatment_invocation": design["treatment_invocation"],
            "corpus_kind": "efficacy",
            "prompt_only_control_sha256": stable_digest(
                DESIGN_THINKING_PROMPT_CONTROL
            ),
            "case_ids": [case["id"] for case in self.trajectories],
            "repeats": design["repeats"],
            "judge_repetitions": design["judge_repetitions"],
            "seed": design["seed"],
            "bootstrap_samples": design["bootstrap_samples_minimum"],
            "tie_margin_points": design["tie_margin_points"],
            "minimum_important_uplift_points": design[
                "minimum_important_uplift_points"
            ],
            "planned_candidate_turn_calls": len(self.pairs) * 2 * 4,
            "planned_judge_calls": len(self.judges),
            "all_generations_complete_before_judging": True,
            "corpus_sha256": stable_digest(corpus_payload),
            "runner_sha256": "b" * 64,
            "judge_schema_sha256": "c" * 64,
            "intervention_snapshot": {
                **snapshot_digest,
                "frozen_before_first_model_call": True,
            },
            "reproducibility": {
                "design_council_version": "0.9.0-beta.test",
                "git": {
                    "commit": self.commit,
                    "dirty": False,
                    "status_available": True,
                },
            },
            "pair_plan": self.pairs,
            "judge_plan": self.judges,
        }
        self.generations: list[dict] = []
        by_id = {case["id"]: case for case in self.trajectories}
        for pair in self.pairs:
            case = by_id[pair["trajectory_id"]]
            for arm in ("treatment", "control"):
                turns = []
                for index, source_turn in enumerate(case["turns"]):
                    response = f"{arm} response {pair['pair_id']} turn {index + 1}"
                    delivered = candidate_turn_prompt(
                        source_turn["content"],
                        arm,
                        design["control_mode"],
                        turn_index=index,
                        treatment_invocation=design["treatment_invocation"],
                    )
                    turns.append(
                        {
                            "turn_number": index + 1,
                            "stage": source_turn["stage"],
                            "raw_user_turn_sha256": stable_digest(
                                source_turn["content"]
                            ),
                            "delivered_prompt_sha256": stable_digest(delivered),
                            "prompt_only_instruction_applied": arm == "control",
                            "treatment_invocation_applied": arm == "treatment"
                            and index == 0,
                            "assistant_response": response,
                            "assistant_word_count": len(response.split()),
                            "status": "OK",
                            "returncode": 0,
                            "timed_out": False,
                            "event_count": 3,
                            "usage": _usage(index + 1),
                        }
                    )
                aggregate_usage = {
                    field: sum(turn["usage"][field] for turn in turns)
                    for field in USAGE_FIELDS
                }
                self.generations.append(
                    {
                        "record_type": "generation",
                        "run_id": self.run.name,
                        "pair_id": pair["pair_id"],
                        "trajectory_id": pair["trajectory_id"],
                        "repeat": pair["repeat"],
                        "arm": arm,
                        "expected_raw_turn_sha256": pair["turn_sha256"],
                        "control_mode": design["control_mode"],
                        "treatment_invocation": design["treatment_invocation"],
                        "status": "OK",
                        "session_mode": "persisted",
                        "session_fidelity": "PERSISTED_CODEX_THREAD_VERIFIED_BY_ID",
                        "thread_id_sha256": hashlib.sha256(
                            f"{pair['pair_id']}/{arm}".encode()
                        ).hexdigest(),
                        "turns": turns,
                        "usage": aggregate_usage,
                        "wall_time_seconds": 1.0,
                    }
                )

        generation_lookup = {
            (row["pair_id"], row["arm"]): row for row in self.generations
        }
        self.judgments: list[dict] = []
        self.blinded: list[dict] = []
        for planned in self.judges:
            case = by_id[planned["trajectory_id"]]
            generation_a = generation_lookup[
                (planned["pair_id"], planned["label_a_arm"])
            ]
            generation_b = generation_lookup[
                (planned["pair_id"], planned["label_b_arm"])
            ]
            self.blinded.append(
                {
                    "comparison_id": planned["comparison_id"],
                    "trajectory_id": planned["trajectory_id"],
                    "candidate_a": transcript_for_judge(case, generation_a),
                    "candidate_b": transcript_for_judge(case, generation_b),
                }
            )
            a_treatment = planned["label_a_arm"] == "treatment"
            judgment = {
                "trajectory_id": planned["trajectory_id"],
                "comparison_id": planned["comparison_id"],
                "candidate_a": {
                    "scores": {
                        dimension: 5 if a_treatment else 3
                        for dimension in SCORE_DIMENSIONS
                    },
                    "strengths": [],
                    "weaknesses": [],
                },
                "candidate_b": {
                    "scores": {
                        dimension: 3 if a_treatment else 5
                        for dimension in SCORE_DIMENSIONS
                    },
                    "strengths": [],
                    "weaknesses": [],
                },
                "winner": "A" if a_treatment else "B",
                "confidence": 0.9,
                "rationale": "Treatment demonstrates stronger longitudinal adaptation.",
            }
            quality_a = candidate_quality(judgment["candidate_a"])
            quality_b = candidate_quality(judgment["candidate_b"])
            self.judgments.append(
                {
                    **planned,
                    "record_type": "judgment",
                    "run_id": self.run.name,
                    "status": "OK",
                    "error": None,
                    "judgment": judgment,
                    "candidate_a_quality": quality_a,
                    "candidate_b_quality": quality_b,
                    f"{planned['label_a_arm']}_quality": quality_a,
                    f"{planned['label_b_arm']}_quality": quality_b,
                    "mapped_winner": "TREATMENT",
                    "event_count": 3,
                    "usage": _usage(),
                    "wall_time_seconds": 1.0,
                }
            )
        self.summary = aggregate_results(
            trajectories=self.trajectories,
            pair_plan=self.pairs,
            judge_plan=self.judges,
            generations=self.generations,
            judgments=self.judgments,
            tie_margin=design["tie_margin_points"],
            minimum_important_uplift=design["minimum_important_uplift_points"],
            bootstrap_samples=design["bootstrap_samples_minimum"],
            seed=design["seed"],
            control_mode=design["control_mode"],
            treatment_invocation=design["treatment_invocation"],
        )
        self._write()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self) -> None:
        (self.run / "manifest.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        (self.run / "summary.json").write_text(
            json.dumps(self.summary), encoding="utf-8"
        )
        _write_jsonl(self.run / "generations.jsonl", self.generations)
        _write_jsonl(self.run / "judgments.jsonl", self.judgments)
        _write_jsonl(self.run / "blinded-pairs.jsonl", self.blinded)

    def _fake_git(self, commit: str, relative_path: str):
        if commit != self.commit:
            return None
        mapping = {
            self.policy["corpus"]["path"]: (
                ROOT / self.policy["corpus"]["path"]
            ).read_bytes(),
            "evals/run_trajectory_benchmark.py": b"runner",
            "evals/schema/trajectory-judge.schema.json": b"judge-schema",
            "VERSION": b"0.9.0-beta.test\n",
        }
        return mapping.get(relative_path)

    def _verify(self) -> dict:
        snapshot = self.manifest["intervention_snapshot"]
        with patch(
            "scripts.verify_v1_trajectory_gate._git_bytes",
            side_effect=self._fake_git,
        ), patch(
            "scripts.verify_v1_trajectory_gate._git_skill_tree_digest",
            return_value={
                "sha256": snapshot["sha256"],
                "file_count": snapshot["file_count"],
            },
        ):
            self.manifest["runner_sha256"] = hashlib.sha256(b"runner").hexdigest()
            self.manifest["judge_schema_sha256"] = hashlib.sha256(
                b"judge-schema"
            ).hexdigest()
            self._write()
            return verify_v1_trajectory_run(self.run)

    def test_exact_frozen_run_passes(self) -> None:
        report = self._verify()
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["checks_passed"], report["checks_total"])

    def test_policy_byte_change_is_rejected(self) -> None:
        changed = self.root / "changed-policy.json"
        value = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
        value["design"]["repeats"] = 1
        changed.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(
            V1TrajectoryGateError, "preregistered policy"
        ):
            load_policy(changed)

    def test_dirty_source_cannot_pass(self) -> None:
        self.manifest["reproducibility"]["git"]["dirty"] = True
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("source.clean_commit" in item for item in report["errors"]))

    def test_null_commit_cannot_pass(self) -> None:
        self.manifest["reproducibility"]["git"]["commit"] = None
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("source.clean_commit" in item for item in report["errors"]))

    def test_replay_session_cannot_pass(self) -> None:
        self.manifest["session_mode"] = "transcript-replay"
        self.generations[0]["session_mode"] = "transcript-replay"
        self.generations[0]["session_fidelity"] = "LABELED_TRANSCRIPT_REPLAY_FALLBACK"
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("manifest.session_mode" in item for item in report["errors"]))

    def test_small_design_cannot_pass(self) -> None:
        self.manifest["repeats"] = 1
        self.manifest["bootstrap_samples"] = 9999
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("manifest.repeats" in item for item in report["errors"]))
        self.assertTrue(any("manifest.bootstrap_samples" in item for item in report["errors"]))

    def test_missing_or_invalid_usage_cannot_pass(self) -> None:
        self.generations[0]["turns"][0].pop("usage")
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("records.generation_content" in item for item in report["errors"]))

    def test_forged_summary_cannot_pass(self) -> None:
        self.summary["effectiveness"]["quality_uplift_points"] = 999
        self.summary["effectiveness"]["verdict"] = (
            "MEANINGFUL_TREATMENT_BENEFIT_ESTABLISHED"
        )
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("summary.recomputed" in item for item in report["errors"]))

    def test_missing_record_cannot_pass(self) -> None:
        self.judgments.pop()
        report = self._verify()
        self.assertFalse(report["passed"])
        self.assertTrue(any("records.judgment_set" in item for item in report["errors"]))

    def test_cli_returns_one_for_gate_failure(self) -> None:
        self.manifest["reproducibility"]["git"]["dirty"] = True
        self._write()
        result = subprocess.run(
            [
                "python3",
                "scripts/verify_v1_trajectory_gate.py",
                str(self.run),
                "--allow-exported-bundle",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL:", result.stderr)


if __name__ == "__main__":
    unittest.main()
