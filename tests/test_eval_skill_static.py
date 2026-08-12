from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "design-council" / "SKILL.md"


class SkillBehavioralContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SKILL.exists():
            raise unittest.SkipTest("Design Council skill is still being assembled")
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_skill_names_core_evidence_provenance(self) -> None:
        for marker in (
            "OBSERVED_HUMAN_BEHAVIOR",
            "HUMAN_INTERVIEW",
            "AUTHORITATIVE_RESEARCH",
            "SYNTHETIC_USER",
            "SYNTHETIC_PRACTITIONER",
            "SYNTHETIC_EXPERT",
            "DESIGN_COUNCIL",
            "ASSUMPTION",
            "UNKNOWN",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_skill_names_independence_sequence(self) -> None:
        indices = [
            self.text.index("sealed responses"),
            self.text.index("freeze"),
            self.text.index("anonymous cross-pollination"),
            self.text.index("forced mutation"),
            self.text.index("convergent challenge"),
            self.text.index("MINORITY REPORT"),
            self.text.index("facilitator synthesis"),
        ]
        self.assertEqual(indices, sorted(indices))
        self.assertIn("SEALED RECEIPT", self.text)
        self.assertIn("completed before sharing", self.text)
        self.assertIn("evaluation appendix with all ten", self.text)
        self.assertIn("uniform one-line table", self.text)
        self.assertIn("names and role labels removed", self.text)
        self.assertIn("ROUND B / ANONYMOUS CROSS-POLLINATION", self.text)
        self.assertIn("ROUND C / FORCED MUTATION", self.text)
        self.assertIn("ROUND D / CONVERGENT CHALLENGE", self.text)
        self.assertIn("Do not replace these artifacts with a sentence", self.text)

    def test_skill_forbids_unlabeled_evidence_and_requires_competing_povs(self) -> None:
        self.assertIn("Do not use an unlabeled `Evidence` heading", self.text)
        self.assertIn("at least two genuinely competing", self.text)

    def test_synthetic_participants_are_distinct_from_council_members(self) -> None:
        self.assertIn("opaque study ID", self.text)
        self.assertIn("never reuse a Council name", self.text)
        self.assertIn("compact Human Model card", self.text)
        self.assertIn("restrained heading `◇ INQUIRY LAB`", self.text)
        self.assertIn("future update rule", self.text)
        self.assertIn("supersede the provisional frame", self.text)

    def test_skill_keeps_build_gate_advisory(self) -> None:
        self.assertIn("Build Gate advisory", self.text)
        self.assertIn("build it anyway", self.text.lower())

    def test_skill_uses_progressive_disclosure(self) -> None:
        self.assertIn("Load exactly one current-mode file", self.text)
        self.assertLess(len(self.text.splitlines()), 500)


if __name__ == "__main__":
    unittest.main()
