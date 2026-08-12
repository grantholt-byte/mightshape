from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evals.run_contracts import load_cases
from evals.run_model_evals import candidate_prompt, check_regex, response_filename, select_cases, validate_result_shape


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
        self.assertIn("$design-council", completed.stdout)
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


if __name__ == "__main__":
    unittest.main()
