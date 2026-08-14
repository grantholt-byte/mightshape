from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from evals.run_contracts import load_cases
from evals.run_model_evals import (
    candidate_prompt,
    check_regex,
    combine_deterministic_checks,
    combine_deterministic_and_judge,
    inspect_state_effect,
    judge_prompt,
    make_skill_project,
    response_filename,
    run_codex,
    select_cases,
    validate_state_effect_cases,
    validate_result_shape,
    workspace_requirements,
    workspace_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "run_model_evals.py"
SKILL_SCRIPTS = REPO_ROOT / "skills" / "mightshape" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from sealed_round import freeze_round, prepare_round, stage_response  # noqa: E402
from project_state import initialize_project, record_visual_artifact  # noqa: E402
from render_visual import render_artifact, write_artifact  # noqa: E402


def sealed_response(round_id: str, member_id: str, position: str) -> dict:
    return {
        "round_id": round_id,
        "member_id": member_id,
        "position": position,
        "ideas": [{"idea": position, "territory": "SYSTEMIC"}],
        "concerns": ["The operational context is not yet observed."],
        "questions": ["What would actual behavior show?"],
        "unknowns": ["Local variation"],
        "surprise": "The current workaround may carry useful information.",
        "knowledge_boundary": "This is a design interpretation, not human evidence.",
        "confidence": 0.63,
    }


class ModelEvalRunnerTests(unittest.TestCase):
    def test_case_selection_is_deterministic(self) -> None:
        cases = load_cases()
        selected = select_cases(cases, "acceptance", None, 2)
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(case["family"] == "acceptance" for case in selected))

    def test_response_filename_is_stable(self) -> None:
        self.assertEqual(response_filename("routing.dark_mode"), "routing.dark_mode.md")

    def test_every_case_state_effect_is_explicitly_classified(self) -> None:
        cases = load_cases()
        self.assertEqual(validate_state_effect_cases(cases), [])
        dark_mode = next(item for item in cases if item["id"] == "routing.explicit_dark_mode")
        family = next(item for item in cases if item["id"] == "acceptance.family_scheduler")
        self.assertEqual(workspace_requirements(dark_mode), ())
        self.assertEqual(workspace_requirements(family), ("PROJECT_STATE",))

    def test_unclassified_state_effect_is_a_contract_error(self) -> None:
        case = {"id": "test.unknown", "expected": {"state_effect": "NEW_UNINSPECTED_EFFECT"}}
        errors = validate_state_effect_cases([case])
        self.assertEqual(len(errors), 1)
        self.assertIn("unclassified state_effect", errors[0])

    def test_acceptance_prompt_includes_declared_fixture_boundary(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "acceptance.family_scheduler")
        prompt = candidate_prompt(case)
        self.assertIn("EVALUATION SCENARIO BOUNDARY", prompt)
        self.assertIn("Run a representative journey", prompt)
        self.assertIn("CREATE_VERSIONED_DESIGN_JOURNEY", prompt)
        self.assertIn("PROJECT_STATE", prompt)
        self.assertIn("do not merely say", prompt)
        self.assertNotIn("required_sequence", prompt)

    def test_response_only_case_remains_read_only(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "routing.explicit_dark_mode")
        self.assertIn("Do not edit files", candidate_prompt(case))
        with tempfile.TemporaryDirectory() as temp_name:
            workdir = make_skill_project(Path(temp_name), allows_mutation=False)
            before = workspace_snapshot(workdir)
            clean = inspect_state_effect(case, workdir, before)
            self.assertEqual(clean["status"], "PASS")
            (workdir / "unauthorized.txt").write_text("changed", encoding="utf-8")
            changed = inspect_state_effect(case, workdir, before)
            self.assertEqual(changed["status"], "FAIL")

    def test_mutation_case_cannot_pass_by_narrating_state_creation(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "design_process.premature_build")
        with tempfile.TemporaryDirectory() as temp_name:
            workdir = make_skill_project(Path(temp_name), allows_mutation=True)
            before = workspace_snapshot(workdir)
            response_checks = check_regex(
                case,
                "The app is a proposed solution. First expose the coordination assumption.",
            )
            state_checks = inspect_state_effect(case, workdir, before)
            combined = combine_deterministic_checks(response_checks, state_checks)
        self.assertEqual(response_checks["status"], "PASS")
        self.assertEqual(state_checks["status"], "FAIL")
        self.assertEqual(combined["status"], "FAIL")

    def test_initialized_project_state_and_history_satisfy_initialize_effect(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "design_process.premature_build")
        with tempfile.TemporaryDirectory() as temp_name:
            workdir = make_skill_project(Path(temp_name), allows_mutation=True)
            before = workspace_snapshot(workdir)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_SCRIPTS / "dc.py"),
                    "init",
                    "--project-root",
                    str(workdir),
                    "--name",
                    "Model eval fixture",
                    "--prompt",
                    case["prompt"],
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)
            result = inspect_state_effect(case, workdir, before)
        self.assertEqual(result["status"], "PASS", result)

    def test_prepared_and_frozen_rounds_are_inspected_not_inferred_from_prose(self) -> None:
        packet = {
            "round_id": "CR-901",
            "task": "Generate independent interpretations",
            "challenge": "Reduce missed handoffs",
            "current_problem_frame": "Handoffs fail silently",
            "current_pov": None,
            "known_evidence": [],
            "assumptions": [],
            "unknowns": ["Where recovery begins"],
            "constraints": ["No production build"],
        }
        members = ["maya-chen", "rafael-alvarez"]
        prepared_case = next(
            item for item in load_cases() if item["id"] == "council_independence.common_packet_identity"
        )
        frozen_case = next(
            item for item in load_cases() if item["id"] == "council_independence.no_first_round_anchoring"
        )
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            prepared_workdir = make_skill_project(root, "prepared", allows_mutation=True)
            prepared_before = workspace_snapshot(prepared_workdir)
            prepared_round = prepared_workdir / ".design-council/council-rounds/CR-901"
            prepare_round(prepared_round, packet, members)
            prepared_result = inspect_state_effect(prepared_case, prepared_workdir, prepared_before)

            frozen_workdir = make_skill_project(root, "frozen", allows_mutation=True)
            frozen_before = workspace_snapshot(frozen_workdir)
            frozen_round = frozen_workdir / ".design-council/council-rounds/CR-901"
            prepare_round(frozen_round, packet, members)
            for member in members:
                stage_response(
                    frozen_round,
                    sealed_response(
                        "CR-901",
                        member,
                        "Preserve the recovery burden as an explicit design constraint.",
                    ),
                )
            freeze_round(frozen_round)
            frozen_result = inspect_state_effect(frozen_case, frozen_workdir, frozen_before)
        self.assertEqual(prepared_result["status"], "PASS", prepared_result)
        self.assertEqual(frozen_result["status"], "PASS", frozen_result)

    def test_visual_effect_requires_hashed_files_and_project_state_record(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "design_process.process_map_visual")
        source = {
            "schema_version": "1.0.0",
            "id": "VA-EVAL",
            "artifact_type": "PROCESS_MAP",
            "title": "One-step handoff",
            "summary": "The known handoff step is kept separate from the unknown branch.",
            "summary_provenance": "DESIGN_COUNCIL",
            "summary_record_ids": ["STEP-001"],
            "mode": "EMPATHIZE",
            "cycle": 1,
            "limitations": ["The missing-response path remains unknown."],
            "data": {
                "lanes": [{"id": "LANE-001", "label": "Participant"}],
                "steps": [
                    {
                        "id": "STEP-001",
                        "label": "Receives email",
                        "detail": "P-001 receives the handoff message.",
                        "lane_id": "LANE-001",
                        "provenance": "USER_PROVIDED",
                        "source_ids": ["P-001"],
                    }
                ],
                "transitions": [],
            },
        }
        with tempfile.TemporaryDirectory() as temp_name:
            workdir = make_skill_project(Path(temp_name), allows_mutation=True)
            before = workspace_snapshot(workdir)
            initialize_project(workdir, "Visual eval", case["prompt"])
            rendered = render_artifact(source)
            paths = write_artifact(
                rendered,
                workdir / ".design-council/artifacts/VA-EVAL",
            )
            record_visual_artifact(workdir, paths["manifest"])
            result = inspect_state_effect(case, workdir, before)
        self.assertEqual(result["status"], "PASS", result)

    def test_structured_judge_result_is_bound_to_case(self) -> None:
        valid = {
            "case_id": "routing.dark_mode",
            "status": "PASS",
            "criterion_results": [
                {"criterion": "does the work", "passed": True, "evidence": "observable"}
            ],
            "summary": "passed",
        }
        self.assertIsNone(validate_result_shape(valid, "routing.dark_mode"))
        self.assertIsNotNone(validate_result_shape(valid, "routing.other"))
        self.assertIsNotNone(validate_result_shape(valid, "routing.dark_mode", "NONE"))
        valid["criterion_results"].append(
            {"criterion": "state_effect: NONE", "passed": True, "evidence": "read-only"}
        )
        self.assertIsNone(validate_result_shape(valid, "routing.dark_mode", "NONE"))
        valid["criterion_results"][-1]["passed"] = False
        self.assertIn(
            "inconsistent",
            validate_result_shape(valid, "routing.dark_mode", "NONE") or "",
        )

    def test_semantic_judge_contract_includes_state_effect_and_workspace_observation(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "acceptance.family_scheduler")
        observation = {
            "case_id": case["id"],
            "status": "FAIL",
            "criterion_results": [],
            "summary": "missing state",
        }
        prompt = judge_prompt(case, "I created it.", observation)
        self.assertIn('"state_effect": "CREATE_VERSIONED_DESIGN_JOURNEY"', prompt)
        self.assertIn("DETERMINISTIC WORKSPACE OBSERVATION", prompt)
        self.assertIn("never infer a created artifact from prose", prompt)

    def test_regex_checker_reports_pass_and_fail(self) -> None:
        case = {
            "id": "test.regex",
            "automated": {
                "must_match": ["(?i)sealed"],
                "must_not_match": ["(?i)human interview"],
            },
        }
        self.assertEqual(check_regex(case, "A SEALED round." )["status"], "PASS")
        self.assertEqual(check_regex(case, "A human interview." )["status"], "FAIL")

    def test_model_judge_cannot_overwrite_failed_deterministic_gate(self) -> None:
        deterministic = {
            "case_id": "test.case",
            "status": "FAIL",
            "criterion_results": [
                {"criterion": "must_match: divergence", "passed": False, "evidence": "pattern absent"}
            ],
            "summary": "failed",
        }
        judged = {
            "case_id": "test.case",
            "status": "PASS",
            "criterion_results": [
                {"criterion": "semantic behavior", "passed": True, "evidence": "present"}
            ],
            "summary": "passed",
        }
        combined = combine_deterministic_and_judge(deterministic, judged)
        self.assertEqual(combined["status"], "FAIL")
        self.assertTrue(combined["criterion_results"][0]["criterion"].startswith("[deterministic]"))
        self.assertTrue(combined["criterion_results"][1]["criterion"].startswith("[judge]"))

    def test_combined_gate_passes_only_when_both_pass(self) -> None:
        result = {
            "case_id": "test.case",
            "status": "PASS",
            "criterion_results": [],
            "summary": "passed",
        }
        self.assertEqual(combine_deterministic_and_judge(result, result)["status"], "PASS")

    def test_judge_skip_cannot_hide_failed_deterministic_gate(self) -> None:
        deterministic = {
            "case_id": "test.case",
            "status": "FAIL",
            "criterion_results": [
                {"criterion": "required route", "passed": False, "evidence": "absent"}
            ],
            "summary": "failed",
        }
        skipped_judge = {
            "case_id": "test.case",
            "status": "SKIP",
            "criterion_results": [],
            "summary": "judge unavailable",
        }
        combined = combine_deterministic_and_judge(deterministic, skipped_judge)
        self.assertEqual(combined["status"], "FAIL")

    def test_default_invocation_skips_without_opt_in(self) -> None:
        environment = os.environ.copy()
        environment.pop("DC_RUN_MODEL_EVALS", None)
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--case", "routing.explicit_dark_mode"],
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("SKIP", completed.stdout)

    def test_dry_run_never_requires_model_opt_in(self) -> None:
        environment = os.environ.copy()
        environment.pop("DC_RUN_MODEL_EVALS", None)
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--case", "routing.meet_council", "--dry-run"],
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("$design-think", completed.stdout)
        self.assertIn("Meet the Council", completed.stdout)

    def test_saved_response_mode_is_offline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            (directory / "routing.explicit_dark_mode.md").write_text(
                "I will inspect issue.md and implement the toggle, then run tests.",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--case",
                    "routing.explicit_dark_mode",
                    "--responses-dir",
                    str(directory),
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertIn("PASS routing.explicit_dark_mode", completed.stdout)

    def test_saved_response_mode_does_not_overclaim_mutating_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            (directory / "design_process.premature_build.md").write_text(
                "This is a proposed solution. First test the coordination assumption.",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--case",
                    "design_process.premature_build",
                    "--responses-dir",
                    str(directory),
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertIn("SKIP design_process.premature_build", completed.stdout)
            self.assertIn("cannot inspect required workspace effect", completed.stdout)

    def test_run_codex_selects_explicit_sandbox_and_clean_context(self) -> None:
        observed: dict[str, object] = {}

        def fake_run(command, **kwargs):
            observed["command"] = command
            observed["env"] = kwargs["env"]
            return subprocess.CompletedProcess(command, 0, "ok")

        with tempfile.TemporaryDirectory() as temp_name, patch(
            "evals.run_model_evals.subprocess.run", side_effect=fake_run
        ):
            code, _ = run_codex(
                "codex",
                Path(temp_name),
                "prompt",
                Path(temp_name) / "last.md",
                "model",
                "medium",
                7,
                sandbox="workspace-write",
            )
        command = observed["command"]
        self.assertEqual(code, 0)
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertEqual(observed["env"]["PYTHONDONTWRITEBYTECODE"], "1")

    def test_model_timeout_is_reported_instead_of_crashing_runner(self) -> None:
        timeout = subprocess.TimeoutExpired(["codex", "exec"], 7, output=b"partial event\n")
        with tempfile.TemporaryDirectory() as temp_name, patch(
            "evals.run_model_evals.subprocess.run", side_effect=timeout
        ):
            code, output = run_codex(
                "codex",
                Path(temp_name),
                "prompt",
                Path(temp_name) / "last.md",
                "model",
                "medium",
                7,
            )
        self.assertEqual(code, 124)
        self.assertIn("timed out after 7s", output)
        self.assertIn("partial event", output)


if __name__ == "__main__":
    unittest.main()
