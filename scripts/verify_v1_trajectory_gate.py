#!/usr/bin/env python3
"""Fail-closed verifier for the preregistered Design Council V1 trajectory gate.

The verifier accepts only the exact neutral corpus and experimental design in
``evals/benchmark/v1-trajectory-gate-policy.json``. It reconstructs plans,
transcripts, usage totals, and the aggregate result from raw artifacts instead
of trusting the saved summary. A successful report is an engineering release
gate, not proof of real-world product outcomes.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.run_trajectory_benchmark import (  # noqa: E402
    ARMS,
    DESIGN_THINKING_PROMPT_CONTROL,
    JUDGE_SCHEMA,
    TURN_STAGES,
    aggregate_results,
    build_judge_plan,
    build_pair_plan,
    candidate_turn_prompt,
    canonical_tree_digest,
    load_trajectories,
    stable_digest,
    transcript_for_judge,
)


DEFAULT_POLICY = ROOT / "evals" / "benchmark" / "v1-trajectory-gate-policy.json"
V1_POLICY_SHA256 = "1a93e20029ce6123af94284ec8751a6921b420b05a723e08aed7964ffec6899c"
REQUIRED_ARTIFACTS = (
    "manifest.json",
    "generations.jsonl",
    "judgments.jsonl",
    "blinded-pairs.jsonl",
    "summary.json",
)
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class V1TrajectoryGateError(ValueError):
    """Raised when policy or evidence cannot be parsed safely."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise V1TrajectoryGateError(f"invalid JSON: {path}") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise V1TrajectoryGateError(f"invalid JSONL: {path}") from exc
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise V1TrajectoryGateError(
                f"invalid JSONL: {path}:{line_number}"
            ) from exc
        if not isinstance(value, dict):
            raise V1TrajectoryGateError(
                f"JSONL record is not an object: {path}:{line_number}"
            )
        records.append(value)
    return records


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _canonical_corpus_hash(trajectories: list[dict[str, Any]]) -> str:
    payload = "\n".join(
        json.dumps(case, sort_keys=True, separators=(",", ":"))
        for case in trajectories
    )
    return stable_digest(payload)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _same_number(value: Any, expected: float | int) -> bool:
    return _number(value) and float(value) == float(expected)


def _usage_error(value: Any, *, positive: bool = True) -> str | None:
    if not isinstance(value, dict):
        return "usage is not an object"
    for field in USAGE_FIELDS:
        token_count = value.get(field)
        if not isinstance(token_count, int) or isinstance(token_count, bool) or token_count < 0:
            return f"{field} must be a non-negative integer"
    if value["cached_input_tokens"] + value["uncached_input_tokens"] != value["input_tokens"]:
        return "cached plus uncached input does not equal input_tokens"
    if value["input_tokens"] + value["output_tokens"] != value["total_tokens"]:
        return "input plus output does not equal total_tokens"
    if value["reasoning_output_tokens"] > value["output_tokens"]:
        return "reasoning_output_tokens exceeds output_tokens"
    if positive and value["total_tokens"] <= 0:
        return "total_tokens must be positive"
    return None


def _sum_usage(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(int(row["usage"][field]) for row in rows)
        for field in USAGE_FIELDS
    }


def _git_bytes(commit: str, relative_path: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative_path}"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _git_skill_tree_digest(commit: str) -> dict[str, Any] | None:
    prefix = "skills/design-council/"
    try:
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit, "--", prefix.rstrip("/")],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if listing.returncode != 0:
        return None
    paths = sorted(path for path in listing.stdout.splitlines() if path.startswith(prefix))
    included: list[tuple[str, bytes]] = []
    for path in paths:
        relative = path[len(prefix) :]
        parts = Path(relative).parts
        if (
            any(part in {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"} for part in parts)
            or Path(relative).name == ".DS_Store"
            or Path(relative).suffix in {".pyc", ".pyo"}
            or fnmatch.fnmatch(Path(relative).name, "* 2.*")
        ):
            continue
        content = _git_bytes(commit, path)
        if content is None:
            return None
        included.append((Path(relative).as_posix(), content))
    if not included:
        return None
    digest = hashlib.sha256()
    for relative, content in included:
        path_bytes = relative.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return {"sha256": digest.hexdigest(), "file_count": len(included)}


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    try:
        policy_bytes = path.read_bytes()
    except OSError as exc:
        raise V1TrajectoryGateError(f"cannot read V1 gate policy: {path}") from exc
    if hashlib.sha256(policy_bytes).hexdigest() != V1_POLICY_SHA256:
        raise V1TrajectoryGateError(
            "V1 gate policy bytes differ from the preregistered policy"
        )
    policy = _read_json(path)
    required = {"schema_version", "policy_id", "corpus", "design", "decision"}
    if not isinstance(policy, dict) or set(policy) != required:
        raise V1TrajectoryGateError("V1 gate policy has unexpected top-level fields")
    if policy.get("schema_version") != "1.0.0":
        raise V1TrajectoryGateError("unsupported V1 gate policy version")
    corpus = policy.get("corpus")
    design = policy.get("design")
    decision = policy.get("decision")
    if not all(isinstance(section, dict) for section in (corpus, design, decision)):
        raise V1TrajectoryGateError("V1 gate policy sections must be objects")
    corpus_required = {"path", "canonical_sha256", "case_ids", "turn_stages"}
    design_required = {
        "session_mode",
        "control_mode",
        "treatment_invocation",
        "repeats",
        "judge_repetitions",
        "seed",
        "bootstrap_samples_minimum",
        "tie_margin_points",
        "minimum_important_uplift_points",
        "candidate_model",
        "candidate_effort",
        "judge_model",
        "judge_effort",
        "prompt_only_control_sha256",
    }
    decision_required = {
        "required_verdict",
        "require_more_wins_than_losses",
        "require_clean_non_null_git_commit",
        "require_live_persisted_sessions",
        "require_exact_plans_and_records",
        "require_valid_usage",
    }
    if set(corpus) != corpus_required or set(design) != design_required or set(decision) != decision_required:
        raise V1TrajectoryGateError("V1 gate policy is missing or adds policy fields")
    if not isinstance(corpus["case_ids"], list) or len(corpus["case_ids"]) != 5:
        raise V1TrajectoryGateError("V1 gate policy must name exactly five neutral cases")
    if corpus["turn_stages"] != list(TURN_STAGES):
        raise V1TrajectoryGateError("V1 gate policy turn stages differ from the runner")
    if not HEX_SHA256.fullmatch(str(corpus["canonical_sha256"])):
        raise V1TrajectoryGateError("V1 corpus digest is invalid")
    if any(decision[field] is not True for field in decision_required if field != "required_verdict"):
        raise V1TrajectoryGateError("V1 gate policy cannot disable a required safeguard")
    if decision["required_verdict"] != "MEANINGFUL_TREATMENT_BENEFIT_ESTABLISHED":
        raise V1TrajectoryGateError("V1 gate policy requires an unsafe verdict")
    return policy


def verify_v1_trajectory_run(
    run_dir: Path,
    *,
    policy_path: Path = DEFAULT_POLICY,
    require_snapshot: bool = True,
) -> dict[str, Any]:
    """Return a complete pass/fail report; any unverified invariant fails."""

    run_dir = run_dir.resolve()
    policy = load_policy(policy_path)
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            errors.append(f"{name}: {detail}")

    if not run_dir.is_dir():
        raise V1TrajectoryGateError(f"run directory does not exist: {run_dir}")
    missing = [name for name in REQUIRED_ARTIFACTS if not (run_dir / name).is_file()]
    if missing:
        raise V1TrajectoryGateError(f"run is missing required artifact(s): {', '.join(missing)}")

    manifest = _read_json(run_dir / "manifest.json")
    summary = _read_json(run_dir / "summary.json")
    generations = _read_jsonl(run_dir / "generations.jsonl")
    judgments = _read_jsonl(run_dir / "judgments.jsonl")
    blinded_pairs = _read_jsonl(run_dir / "blinded-pairs.jsonl")
    if not isinstance(manifest, dict) or not isinstance(summary, dict):
        raise V1TrajectoryGateError("manifest and summary must be objects")

    corpus_policy = policy["corpus"]
    design = policy["design"]
    decision = policy["decision"]
    corpus_path = (ROOT / corpus_policy["path"]).resolve()
    try:
        corpus_path.relative_to(ROOT)
    except ValueError as exc:
        raise V1TrajectoryGateError("policy corpus path escapes repository") from exc
    trajectories = load_trajectories(corpus_path)
    corpus_ids = [case["id"] for case in trajectories]
    corpus_hash = _canonical_corpus_hash(trajectories)
    check("policy.corpus_ids", corpus_ids == corpus_policy["case_ids"], "canonical corpus IDs must match policy order")
    check("policy.corpus_hash", corpus_hash == corpus_policy["canonical_sha256"], "canonical neutral corpus digest must match policy")
    check("policy.control_prompt_hash", stable_digest(DESIGN_THINKING_PROMPT_CONTROL) == design["prompt_only_control_sha256"], "frozen control prompt digest must match policy")

    exact_manifest_fields = {
        "corpus_kind": "efficacy",
        "case_ids": corpus_ids,
        "session_mode": design["session_mode"],
        "control_mode": design["control_mode"],
        "treatment_invocation": design["treatment_invocation"],
        "repeats": design["repeats"],
        "judge_repetitions": design["judge_repetitions"],
        "seed": design["seed"],
        "tie_margin_points": design["tie_margin_points"],
        "minimum_important_uplift_points": design["minimum_important_uplift_points"],
        "candidate_model": design["candidate_model"],
        "candidate_effort": design["candidate_effort"],
        "judge_model": design["judge_model"],
        "judge_effort": design["judge_effort"],
        "prompt_only_control_sha256": design["prompt_only_control_sha256"],
        "corpus_sha256": corpus_hash,
        "all_generations_complete_before_judging": True,
    }
    for field, expected in exact_manifest_fields.items():
        actual = manifest.get(field)
        matches = (
            _same_number(actual, expected)
            if isinstance(expected, float)
            else type(actual) is type(expected) and actual == expected
        )
        check(f"manifest.{field}", matches, f"expected {expected!r}, observed {actual!r}")
    run_id = manifest.get("run_id")
    check(
        "manifest.run_id",
        isinstance(run_id, str)
        and RUN_ID_PATTERN.fullmatch(run_id) is not None
        and run_dir.name == run_id,
        "run ID must be valid and equal the run-directory name",
    )
    bootstrap_samples = manifest.get("bootstrap_samples")
    check(
        "manifest.bootstrap_samples",
        isinstance(bootstrap_samples, int)
        and not isinstance(bootstrap_samples, bool)
        and bootstrap_samples >= design["bootstrap_samples_minimum"],
        f"must be an integer >= {design['bootstrap_samples_minimum']}; observed {bootstrap_samples!r}",
    )

    expected_pair_plan = build_pair_plan(trajectories, design["repeats"], design["seed"])
    expected_judge_plan = build_judge_plan(
        expected_pair_plan, design["judge_repetitions"], design["seed"]
    )
    check("manifest.pair_plan", manifest.get("pair_plan") == expected_pair_plan, "pair plan must equal the canonical counterbalanced plan")
    check("manifest.judge_plan", manifest.get("judge_plan") == expected_judge_plan, "judge plan must equal the canonical blinded plan")
    expected_candidate_calls = len(expected_pair_plan) * len(ARMS) * len(TURN_STAGES)
    check("manifest.planned_candidate_turn_calls", manifest.get("planned_candidate_turn_calls") == expected_candidate_calls, f"expected {expected_candidate_calls}")
    check("manifest.planned_judge_calls", manifest.get("planned_judge_calls") == len(expected_judge_plan), f"expected {len(expected_judge_plan)}")

    reproducibility = manifest.get("reproducibility")
    git = reproducibility.get("git") if isinstance(reproducibility, dict) else None
    commit = git.get("commit") if isinstance(git, dict) else None
    git_ok = (
        isinstance(commit, str)
        and HEX_GIT_COMMIT.fullmatch(commit) is not None
        and git.get("dirty") is False
        and git.get("status_available") is True
    )
    check("source.clean_commit", git_ok, "run must record a clean, available, non-null full Git commit")
    committed_corpus = _git_bytes(commit, corpus_policy["path"]) if isinstance(commit, str) else None
    committed_runner = _git_bytes(commit, "evals/run_trajectory_benchmark.py") if isinstance(commit, str) else None
    committed_schema = _git_bytes(commit, str(JUDGE_SCHEMA.relative_to(ROOT))) if isinstance(commit, str) else None
    committed_version = _git_bytes(commit, "VERSION") if isinstance(commit, str) else None
    check("source.commit_exists", committed_corpus is not None, "recorded commit and corpus must exist locally")
    if committed_corpus is not None:
        try:
            committed_lines = [json.loads(line) for line in committed_corpus.decode("utf-8").splitlines() if line.strip()]
        except (UnicodeDecodeError, json.JSONDecodeError):
            committed_hash = None
        else:
            committed_hash = _canonical_corpus_hash(committed_lines)
        check("source.committed_corpus", committed_hash == corpus_hash, "recorded commit must contain the frozen neutral corpus")
    check(
        "source.committed_runner",
        committed_runner is not None
        and hashlib.sha256(committed_runner).hexdigest() == manifest.get("runner_sha256"),
        "runner digest must resolve from recorded commit",
    )
    check(
        "source.committed_judge_schema",
        committed_schema is not None
        and hashlib.sha256(committed_schema).hexdigest() == manifest.get("judge_schema_sha256"),
        "judge schema digest must resolve from recorded commit",
    )
    recorded_version = reproducibility.get("design_council_version") if isinstance(reproducibility, dict) else None
    check(
        "source.committed_version",
        committed_version is not None
        and committed_version.decode("utf-8", errors="replace").strip() == recorded_version,
        "recorded Design Council version must match VERSION at the commit",
    )

    snapshot_manifest = manifest.get("intervention_snapshot")
    snapshot_expected = (
        {key: snapshot_manifest.get(key) for key in ("sha256", "file_count")}
        if isinstance(snapshot_manifest, dict)
        else None
    )
    check(
        "source.snapshot_declared_frozen",
        isinstance(snapshot_manifest, dict)
        and snapshot_manifest.get("frozen_before_first_model_call") is True
        and isinstance(snapshot_manifest.get("file_count"), int)
        and snapshot_manifest.get("file_count", 0) > 0
        and isinstance(snapshot_manifest.get("sha256"), str)
        and HEX_SHA256.fullmatch(snapshot_manifest["sha256"]) is not None,
        "intervention snapshot must have a valid digest and be frozen before calls",
    )
    committed_skill = _git_skill_tree_digest(commit) if isinstance(commit, str) else None
    check("source.committed_skill_snapshot", committed_skill == snapshot_expected, "snapshot digest must equal the Design Council skill at the clean commit")
    snapshot_path = run_dir / "intervention-snapshot"
    if require_snapshot:
        actual_snapshot = canonical_tree_digest(snapshot_path) if snapshot_path.is_dir() else None
        check("source.raw_snapshot_present", actual_snapshot == snapshot_expected, "raw gate verification requires the frozen intervention snapshot")

    generation_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_generation_keys: list[tuple[str, str]] = []
    for row in generations:
        key = (row.get("pair_id"), row.get("arm"))
        if key in generation_by_key:
            duplicate_generation_keys.append(key)
        elif all(isinstance(item, str) for item in key):
            generation_by_key[key] = row
    expected_generation_keys = {
        (pair["pair_id"], arm) for pair in expected_pair_plan for arm in ARMS
    }
    check(
        "records.generation_set",
        len(generations) == len(expected_generation_keys)
        and not duplicate_generation_keys
        and set(generation_by_key) == expected_generation_keys,
        "generation records must exactly match every planned pair and arm",
    )
    trajectory_by_id = {case["id"]: case for case in trajectories}
    generation_content_ok = True
    generation_errors: list[str] = []
    for pair in expected_pair_plan:
        trajectory = trajectory_by_id[pair["trajectory_id"]]
        for arm in ARMS:
            row = generation_by_key.get((pair["pair_id"], arm))
            if row is None:
                generation_content_ok = False
                continue
            expected_metadata = {
                "record_type": "generation",
                "run_id": manifest.get("run_id"),
                "trajectory_id": pair["trajectory_id"],
                "repeat": pair["repeat"],
                "arm": arm,
                "expected_raw_turn_sha256": pair["turn_sha256"],
                "control_mode": design["control_mode"],
                "treatment_invocation": design["treatment_invocation"],
                "session_mode": "persisted",
                "session_fidelity": "PERSISTED_CODEX_THREAD_VERIFIED_BY_ID",
                "status": "OK",
            }
            for field, expected in expected_metadata.items():
                if type(row.get(field)) is not type(expected) or row.get(field) != expected:
                    generation_errors.append(f"{pair['pair_id']}/{arm}: {field}")
            thread_hash = row.get("thread_id_sha256")
            if not isinstance(thread_hash, str) or HEX_SHA256.fullmatch(thread_hash) is None:
                generation_errors.append(f"{pair['pair_id']}/{arm}: thread_id_sha256")
            turns = row.get("turns")
            if not isinstance(turns, list) or len(turns) != len(TURN_STAGES):
                generation_errors.append(f"{pair['pair_id']}/{arm}: four turns")
                generation_content_ok = False
                continue
            for index, (turn, source_turn) in enumerate(zip(turns, trajectory["turns"])):
                delivered = candidate_turn_prompt(
                    source_turn["content"],
                    arm,
                    design["control_mode"],
                    turn_index=index,
                    treatment_invocation=design["treatment_invocation"],
                )
                expected_turn = {
                    "turn_number": index + 1,
                    "stage": source_turn["stage"],
                    "raw_user_turn_sha256": stable_digest(source_turn["content"]),
                    "delivered_prompt_sha256": stable_digest(delivered),
                    "prompt_only_instruction_applied": arm == "control",
                    "treatment_invocation_applied": arm == "treatment" and index == 0,
                    "status": "OK",
                    "returncode": 0,
                    "timed_out": False,
                }
                for field, expected in expected_turn.items():
                    if type(turn.get(field)) is not type(expected) or turn.get(field) != expected:
                        generation_errors.append(f"{pair['pair_id']}/{arm}/turn{index + 1}: {field}")
                response = turn.get("assistant_response")
                if not isinstance(response, str) or not response.strip():
                    generation_errors.append(f"{pair['pair_id']}/{arm}/turn{index + 1}: assistant_response")
                expected_word_count = len(response.split()) if isinstance(response, str) else None
                if turn.get("assistant_word_count") != expected_word_count:
                    generation_errors.append(f"{pair['pair_id']}/{arm}/turn{index + 1}: assistant_word_count")
                usage_error = _usage_error(turn.get("usage"))
                if usage_error:
                    generation_errors.append(f"{pair['pair_id']}/{arm}/turn{index + 1}: {usage_error}")
                if not isinstance(turn.get("event_count"), int) or turn.get("event_count", 0) < 1:
                    generation_errors.append(f"{pair['pair_id']}/{arm}/turn{index + 1}: event_count")
            aggregate_usage_error = _usage_error(row.get("usage"))
            if aggregate_usage_error:
                generation_errors.append(f"{pair['pair_id']}/{arm}: {aggregate_usage_error}")
            elif all(_usage_error(turn.get("usage")) is None for turn in turns):
                if row["usage"] != _sum_usage(turns):
                    generation_errors.append(f"{pair['pair_id']}/{arm}: aggregate usage mismatch")
            if not _number(row.get("wall_time_seconds")) or row.get("wall_time_seconds", 0) <= 0:
                generation_errors.append(f"{pair['pair_id']}/{arm}: wall_time_seconds")
    generation_content_ok = generation_content_ok and not generation_errors
    check("records.generation_content", generation_content_ok, "; ".join(generation_errors[:8]) or "all generation records validated")

    judgment_ids = [row.get("comparison_id") for row in judgments]
    expected_comparison_ids = [row["comparison_id"] for row in expected_judge_plan]
    judgment_set_ok = (
        len(judgments) == len(expected_judge_plan)
        and all(isinstance(value, str) for value in judgment_ids)
        and set(judgment_ids) == set(expected_comparison_ids)
        and len(set(judgment_ids)) == len(judgment_ids)
    )
    check("records.judgment_set", judgment_set_ok, "judgment records must exactly match the blind plan")
    judgment_content_errors: list[str] = []
    for row in judgments:
        if row.get("record_type") != "judgment" or row.get("run_id") != manifest.get("run_id") or row.get("status") != "OK" or row.get("error") is not None:
            judgment_content_errors.append(f"{row.get('comparison_id')}: metadata/status")
        usage_error = _usage_error(row.get("usage"))
        if usage_error:
            judgment_content_errors.append(f"{row.get('comparison_id')}: {usage_error}")
        if not _number(row.get("wall_time_seconds")) or row.get("wall_time_seconds", 0) <= 0:
            judgment_content_errors.append(f"{row.get('comparison_id')}: wall_time_seconds")
    check("records.judgment_content", not judgment_content_errors, "; ".join(judgment_content_errors[:8]) or "all judgment records validated")

    blinded_by_id: dict[str, dict[str, Any]] = {}
    duplicate_blinded: list[str] = []
    for row in blinded_pairs:
        comparison_id = row.get("comparison_id")
        if not isinstance(comparison_id, str) or comparison_id in blinded_by_id:
            duplicate_blinded.append(str(comparison_id))
        else:
            blinded_by_id[comparison_id] = row
    blinded_errors: list[str] = []
    for planned in expected_judge_plan:
        row = blinded_by_id.get(planned["comparison_id"])
        if row is None:
            blinded_errors.append(f"{planned['comparison_id']}: missing")
            continue
        trajectory = trajectory_by_id[planned["trajectory_id"]]
        generation_a = generation_by_key.get((planned["pair_id"], planned["label_a_arm"]))
        generation_b = generation_by_key.get((planned["pair_id"], planned["label_b_arm"]))
        if generation_a is None or generation_b is None:
            blinded_errors.append(f"{planned['comparison_id']}: missing generation")
            continue
        try:
            expected_blinded = {
                "comparison_id": planned["comparison_id"],
                "trajectory_id": planned["trajectory_id"],
                "candidate_a": transcript_for_judge(trajectory, generation_a),
                "candidate_b": transcript_for_judge(trajectory, generation_b),
            }
        except (KeyError, TypeError):
            blinded_errors.append(f"{planned['comparison_id']}: malformed generation")
            continue
        if row != expected_blinded:
            blinded_errors.append(f"{planned['comparison_id']}: transcript mismatch")
    check(
        "records.blinded_pairs",
        len(blinded_pairs) == len(expected_judge_plan)
        and not duplicate_blinded
        and set(blinded_by_id) == set(expected_comparison_ids)
        and not blinded_errors,
        "; ".join((duplicate_blinded + blinded_errors)[:8]) or "all blinded transcripts reconstructed",
    )

    try:
        recomputed = aggregate_results(
            trajectories=trajectories,
            pair_plan=expected_pair_plan,
            judge_plan=expected_judge_plan,
            generations=generations,
            judgments=judgments,
            tie_margin=design["tie_margin_points"],
            minimum_important_uplift=design["minimum_important_uplift_points"],
            bootstrap_samples=(
                bootstrap_samples
                if isinstance(bootstrap_samples, int)
                and not isinstance(bootstrap_samples, bool)
                and bootstrap_samples > 0
                else design["bootstrap_samples_minimum"]
            ),
            seed=design["seed"],
            control_mode=design["control_mode"],
            treatment_invocation=design["treatment_invocation"],
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        recomputed = {"completion": {}, "effectiveness": {}}
        check("summary.recomputed", False, f"raw records cannot be aggregated: {type(exc).__name__}")
    else:
        check("summary.recomputed", summary == recomputed, "saved summary must exactly equal the result recomputed from raw records")
    completion = recomputed.get("completion", {})
    check(
        "summary.complete",
        completion.get("realized_design_complete") is True
        and completion.get("generation_plan_complete") is True
        and completion.get("judgment_plan_complete") is True,
        "all generation and judgment plans must be complete",
    )
    effect = recomputed.get("effectiveness", {})
    check("decision.verdict", effect.get("verdict") == decision["required_verdict"], f"expected {decision['required_verdict']}, observed {effect.get('verdict')!r}")
    check("decision.wins", isinstance(effect.get("wins"), int) and isinstance(effect.get("losses"), int) and effect["wins"] > effect["losses"], "trajectory wins must exceed losses")
    interval = effect.get("case_bootstrap_ci")
    check(
        "decision.interval",
        isinstance(interval, dict)
        and _number(interval.get("lower"))
        and interval["lower"] >= design["minimum_important_uplift_points"]
        and isinstance(interval.get("samples"), int)
        and interval["samples"] >= design["bootstrap_samples_minimum"],
        "case-bootstrap lower bound and sample count must clear policy",
    )

    policy_sha256 = V1_POLICY_SHA256
    return {
        "schema_version": "1.0.0",
        "policy_id": policy["policy_id"],
        "policy_sha256": policy_sha256,
        "run_id": manifest.get("run_id"),
        "source_commit": commit,
        "passed": not errors,
        "checks_passed": sum(item["passed"] for item in checks),
        "checks_total": len(checks),
        "errors": errors,
        "checks": checks,
        "claim_boundary": "Engineering V1 release gate only; not evidence of real-world product outcomes.",
    }


def require_v1_trajectory_gate(
    run_dir: Path,
    *,
    policy_path: Path = DEFAULT_POLICY,
    require_snapshot: bool = True,
) -> dict[str, Any]:
    report = verify_v1_trajectory_run(
        run_dir, policy_path=policy_path, require_snapshot=require_snapshot
    )
    if not report["passed"]:
        raise V1TrajectoryGateError(
            "V1 trajectory gate failed: " + " | ".join(report["errors"])
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--allow-exported-bundle",
        action="store_true",
        help="do not require the raw intervention snapshot (never use for first release-gate verification)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = verify_v1_trajectory_run(
            args.run_dir,
            policy_path=args.policy,
            require_snapshot=not args.allow_exported_bundle,
        )
    except V1TrajectoryGateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["passed"]:
        print(
            f"PASS: {report['policy_id']} ({report['checks_passed']}/{report['checks_total']} checks); "
            f"run={report['run_id']} commit={report['source_commit']}"
        )
    else:
        print(
            f"FAIL: {report['policy_id']} ({report['checks_passed']}/{report['checks_total']} checks)",
            file=sys.stderr,
        )
        for error in report["errors"]:
            print(f"- {error}", file=sys.stderr)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
