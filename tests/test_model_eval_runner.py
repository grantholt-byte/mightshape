from __future__ import annotations

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
    combine_deterministic_and_judge,
    response_filename,
    run_codex,
    select_cases,
    validate_result_shape,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "run_model_evals.py"


class ModelEvalRunnerTests(unittest.TestCase):
    def test_case_selection_is_deterministic(self) -> None:
        cases = load_cases()
        selected = select_cases(cases, "acceptance", None, 2)
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(case["family"] == "acceptance" for case in selected))

    def test_response_filename_is_stable(self) -> None:
        self.assertEqual(response_filename("routing.dark_mode"), "routing.dark_mode.md")

    def test_acceptance_prompt_includes_declared_fixture_boundary(self) -> None:
        case = next(item for item in load_cases() if item["id"] == "acceptance.family_scheduler")
        prompt = candidate_prompt(case)
        self.assertIn("EVALUATION SCENARIO BOUNDARY", prompt)
        self.assertIn("Run a representative journey", prompt)
        self.assertNotIn("required_sequence", prompt)

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
