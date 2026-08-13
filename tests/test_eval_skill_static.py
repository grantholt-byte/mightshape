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
        self.assertIn("at least three mechanism-distinct", self.text)
        self.assertIn("three to five intervention models", self.text)
        self.assertIn("incumbent or no-new-product path", self.text)
        self.assertIn("do not crown one as the provisional problem", self.text)

    def test_outcome_quality_precedes_token_efficiency(self) -> None:
        self.assertIn("Optimize for decision quality and learning value first", self.text)
        self.assertIn("Token use is a secondary diagnostic", self.text)
        self.assertIn("Remove repetition and decorative ceremony", self.text)

    def test_output_only_work_does_not_append_participation_ceremony(self) -> None:
        self.assertIn("stay silently in `OBSERVE`", self.text)
        self.assertIn("without appending this invitation", self.text)
        self.assertIn("lead with the useful result", self.text)

    def test_prototype_signals_are_coherent_and_support_iteration(self) -> None:
        self.assertIn("Keep live alternative frames visible", self.text)
        self.assertIn("conditional pivot", self.text)
        self.assertIn("every signal denominator consistent", self.text)
        self.assertIn("label them proposed heuristics", self.text)
        self.assertIn("establish the incumbent response without teaching the concept", self.text)
        self.assertIn("counterbalanced sequential exposure", self.text)
        self.assertIn("minimum mechanism needed", self.text)
        self.assertIn("Keep live alternative frames visible through experiment choice", self.text)
        self.assertIn("under matched triggers", self.text)
        self.assertIn("run a proportionality pass", self.text)
        self.assertIn("does not increase discrimination, realism, safety, or decision value", self.text)
        self.assertIn("a count of events is not a count of cases or participants", self.text)
        self.assertIn("narrative qualifier is not an `n/N`", self.text)
        self.assertIn("explicitly supersede incompatible earlier scope", self.text)
        self.assertIn("distinguish one accountable owner from permitted contributors", self.text)
        self.assertIn("false duplicate detection", self.text)
        self.assertIn("prior claim → STRENGTHENED | WEAKENED | FALSIFIED | RETAINED", self.text)

    def test_authoritative_grounding_stays_scoped_to_its_evidence(self) -> None:
        self.assertIn("Generic guidance constrains safe inquiry", self.text)
        self.assertIn("not evidence of the local failure mechanism", self.text)
        self.assertIn("isolated research pass", self.text)
        self.assertIn("compact cited claim ledger", self.text)

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
        self.assertIn("Choose one primary route, not a stack", self.text)
        self.assertIn("named method uses the matching method file instead of a stage file", self.text)
        self.assertLess(len(self.text.splitlines()), 500)

    def test_skill_exposes_inspectable_work_without_hidden_reasoning(self) -> None:
        for marker in ("`VISIBLE`", "`WORKSHOP`", "`COMPACT`", "WHAT CHANGED"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)
        self.assertIn("Never stream member content", self.text)
        self.assertIn("hidden chain-of-thought", self.text)
        self.assertIn("private subagent reasoning", self.text)

    def test_skill_routes_spatial_methods_to_portable_visual_artifacts(self) -> None:
        self.assertIn("[visual-workbench.md](references/visual-workbench.md)", self.text)
        self.assertIn("render_visual.py", self.text)
        self.assertIn("HTML, SVG, and Markdown fallback paths", self.text)
        self.assertIn("Browser is optional", self.text)
        self.assertIn("otherwise print each card once", self.text)
        self.assertIn("separate `VERIFY` area", self.text)
        self.assertIn("name one concrete next learning move", self.text)

    def test_quick_work_does_not_require_an_extra_reference_load(self) -> None:
        self.assertIn("one-turn Quick Look or compact Intake uses this file alone", self.text)
        self.assertIn("only to create or inspect a durable spatial artifact", self.text)
        self.assertIn("read-only conversational preview", self.text)
        self.assertIn("one-turn read-only affinity or process-map preview uses this inline contract alone", self.text)
        self.assertIn("do not load another reference", self.text)

    def test_bounded_technical_spikes_route_directly(self) -> None:
        self.assertIn("bounded, low-consequence technical validation spike directly", self.text)
        self.assertIn(
            "smallest fixture corpus that covers named formats and boundary cases",
            self.text,
        )
        self.assertIn("enough variation or repetitions for the selected metric", self.text)
        self.assertIn("do not force a full Prototype Card", self.text)

    def test_starting_point_orientation_is_nonblocking_and_nonlinear(self) -> None:
        self.assertIn("starting point", self.text)
        self.assertIn("Where are you today", self.text)
        self.assertIn("Starting point never forces earlier modes", self.text)
        self.assertIn("Infer the user's current", self.text)

    def test_skill_allocates_output_to_distinct_mechanisms_and_grounding(self) -> None:
        for marker in (
            "ground the decision-changing domain and safety boundaries",
            "broad domain model from local facts",
            "`EXPECTED`, `ADJACENT`, `BEHAVIORAL`, `SYSTEMIC`, and `RADICAL`",
            "Compress feature variants",
            "defer ranking or portfolio selection unless asked",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_expert_facilitator_is_progressively_loaded(self) -> None:
        self.assertIn("[facilitator-practice.md](references/facilitator-practice.md)", self.text)
        self.assertIn("Diagnose the learning bottleneck", self.text)
        facilitator = (REPO_ROOT / "skills/design-council/references/facilitator-practice.md").read_text(encoding="utf-8")
        for marker in ("Intervention ladder", "psychological safety", "When ideas stall", "Debrief every substantive exercise"):
            with self.subTest(marker=marker):
                self.assertIn(marker, facilitator)


if __name__ == "__main__":
    unittest.main()
