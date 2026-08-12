from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from pathlib import Path

from evals.run_contracts import EVAL_ROOT, load_cases, validate_corpus


class EvalCorpusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_cases()

    def test_corpus_is_valid(self) -> None:
        result = validate_corpus()
        self.assertTrue(result["valid"], "\n".join(result["errors"]))
        self.assertGreaterEqual(result["case_count"], 87)

    def test_ids_are_unique_and_family_prefixed(self) -> None:
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.cases:
            self.assertTrue(case["id"].startswith(case["family"] + "."), case["id"])

    def test_all_invocation_routes_are_exercised(self) -> None:
        invocations = Counter(case["invocation"] for case in self.cases)
        self.assertGreater(invocations["explicit"], 0)
        self.assertGreater(invocations["implicit"], 0)
        self.assertGreaterEqual(invocations["avoid"], 3)

    def test_adversarial_cases_are_material_fraction(self) -> None:
        adversarial = sum(case["adversarial"] for case in self.cases)
        self.assertGreaterEqual(adversarial / len(self.cases), 0.35)

    def test_automated_patterns_compile(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                for key in ("must_match", "must_not_match"):
                    for pattern in case["automated"][key]:
                        re.compile(pattern)

    def test_acceptance_cases_reference_existing_fixtures(self) -> None:
        for case in self.cases:
            if case["family"] != "acceptance":
                continue
            setup = case.get("setup", {})
            for field in ("fixture", "contract"):
                relative = setup.get(field)
                if relative is None:
                    continue
                with self.subTest(case=case["id"], field=field):
                    self.assertTrue((EVAL_ROOT / relative).is_file())

    def test_fixture_contracts_have_learning_sequence_and_failures(self) -> None:
        for path in sorted((EVAL_ROOT / "fixtures").glob("*.contract.json")):
            with self.subTest(path=path.name):
                contract = json.loads(path.read_text(encoding="utf-8"))
                self.assertGreaterEqual(len(contract["required_sequence"]), 7)
                self.assertGreaterEqual(len(contract["quality_failures"]), 4)

    def test_corpus_has_no_empty_semantic_contracts(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                expected = case["expected"]
                self.assertTrue(expected["must_demonstrate"])
                self.assertTrue(case["invariants"])
                self.assertTrue(case["tags"])
                self.assertIsInstance(expected.get("must_avoid", []), list)


if __name__ == "__main__":
    unittest.main()
