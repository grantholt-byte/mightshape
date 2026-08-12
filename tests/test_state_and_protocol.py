"""Executable tests for versioned state and sealed Council independence."""

from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "design-council" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dc_core import DesignCouncilError, load_json  # noqa: E402
from project_state import (  # noqa: E402
    add_assumption,
    add_evidence,
    commit_project,
    initialize_project,
    load_project,
    record_council_memory,
    record_gate_override,
    set_mode,
    validate_state,
)
from sealed_round import (  # noqa: E402
    anonymize_round,
    freeze_round,
    prepare_round,
    stage_response,
    validate_response,
)
from session_summary import summarize_state  # noqa: E402


def response(round_id: str, member_id: str, position: str) -> dict:
    return {
        "round_id": round_id,
        "member_id": member_id,
        "position": position,
        "ideas": [{"idea": f"A bounded experiment for {position.lower()}", "territory": "BEHAVIORAL"}],
        "concerns": ["The current claim may outrun its evidence."],
        "questions": ["What behavior would distinguish the competing explanations?"],
        "unknowns": ["Local variation is unknown."],
        "surprise": "The coordination burden may sit elsewhere.",
        "knowledge_boundary": "This is intuition; I would want to observe the workflow.",
        "confidence": 0.63,
    }


class ProjectStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = initialize_project(
            self.root,
            "Family coordination",
            "Build an AI family scheduler",
            "AI family scheduler",
            "DC-TESTSTATE",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_history_is_append_only_and_revisioned(self) -> None:
        self.assertTrue(validate_state(self.state)["valid"])
        self.assertTrue((self.root / ".design-council/history/rev-000001.json").exists())
        with self.assertRaises(DesignCouncilError):
            initialize_project(self.root, "Overwrite", "No")

        updated = add_assumption(self.root, "Families will delegate conflict resolution", "HIGH", "HIGH")
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(load_json(self.root / ".design-council/history/rev-000001.json")["revision"], 1)
        self.assertEqual(load_json(self.root / ".design-council/history/rev-000002.json")["assumptions"][0]["id"], "A-001")

        stale = dict(self.state)
        with self.assertRaisesRegex(DesignCouncilError, "stale write"):
            commit_project(self.root, stale, "STALE", {})

    def test_evidence_firewall_and_human_traceability(self) -> None:
        with self.assertRaisesRegex(DesignCouncilError, "evidence_strength 0"):
            add_evidence(self.root, "The user says demand is high", "USER_PROVIDED", 0.95, 4)
        with self.assertRaisesRegex(DesignCouncilError, "evidence_strength 0"):
            add_evidence(self.root, "Synthetic families agree", "SYNTHETIC_USER", 0.98, 1)
        with self.assertRaisesRegex(DesignCouncilError, "requires participant_id"):
            add_evidence(self.root, "A participant hesitated", "HUMAN_INTERVIEW", 0.7, 4, ["T-001"], study_id="STUDY-001")
        with self.assertRaisesRegex(DesignCouncilError, "requires study_id"):
            add_evidence(self.root, "A participant hesitated", "HUMAN_INTERVIEW", 0.7, 4, ["T-001"], participant_id="P-001")
        with self.assertRaisesRegex(DesignCouncilError, "consent_allows_quote"):
            add_evidence(
                self.root,
                "A participant hesitated",
                "HUMAN_INTERVIEW",
                0.7,
                4,
                ["T-001#M-004"],
                study_id="STUDY-001",
                participant_id="P-001",
                excerpt="I check three messages first.",
            )

        result = add_evidence(
            self.root,
            "P-001 checked messages before opening a calendar",
            "HUMAN_INTERVIEW",
            0.76,
            4,
            ["T-001#M-004"],
            scope="One participant in this study",
            study_id="STUDY-001",
            participant_id="P-001",
            excerpt="I check three messages first.",
            consent_allows_quote=True,
        )
        item = result["evidence"][0]
        self.assertEqual(item["provenance"], "HUMAN_INTERVIEW")
        self.assertEqual(item["participant_id"], "P-001")
        self.assertEqual(item["study_id"], "STUDY-001")
        self.assertEqual(item["evidence_strength"], 4)
        self.assertNotEqual(item["confidence"], item["evidence_strength"])

    def test_backward_learning_memory_and_override_debt(self) -> None:
        state = add_assumption(self.root, "Parents want automatic decisions", "HIGH", "HIGH")
        self.assertEqual(state["assumptions"][0]["status"], "OPEN_HIGH_RISK")
        set_mode(self.root, "PROTOTYPE", "Create the smallest useful learning artifact")
        rewound = set_mode(self.root, "DEFINE", "P-004 contradicted the scheduling frame", ["E-004"])
        self.assertEqual(rewound["journey"]["cycle"], 2)
        self.assertEqual(rewound["journey"]["transitions"][-1]["direction"], "BACKWARD_LEARNING")

        with self.assertRaisesRegex(DesignCouncilError, "changed_because"):
            record_council_memory(self.root, "priya-rao", "changes_of_mind", "Automation may preserve control")
        remembered = record_council_memory(
            self.root,
            "priya-rao",
            "changes_of_mind",
            "I opposed automatic decisions in Cycle 1, but approval-first automation may preserve control.",
            0.81,
            ["E-004"],
            ["P-004", "EXP-002"],
        )
        entry = remembered["council_memory"]["priya-rao"]["changes_of_mind"][0]
        self.assertEqual(entry["cycle"], 2)
        self.assertEqual(entry["changed_because"], ["P-004", "EXP-002"])

        overridden = record_gate_override(self.root, "User chose a reversible coded experiment")
        self.assertTrue(overridden["build_gate"]["override"]["active"])
        self.assertEqual(len(overridden["design_debt"]), 1)
        self.assertEqual(len(overridden["evidence_debt"]), 1)
        summary = summarize_state(overridden)
        self.assertIn("DEFINE", summary)
        self.assertIn("Build Gate", summary)


class SealedRoundTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.round_dir = Path(self.temp.name) / "CR-101"
        self.packet = {
            "round_id": "CR-101",
            "task": "Generate competing interpretations before convergence",
            "challenge": "Families miss changing commitments",
            "current_problem_frame": "Coordination failures create avoidable conflict",
            "current_pov": None,
            "known_evidence": [{"id": "E-001", "provenance": "USER_PROVIDED", "claim": "A founder has seen missed commitments"}],
            "assumptions": [{"id": "A-001", "statement": "Scheduling is the primary pain"}],
            "unknowns": ["Where commitments first arrive"],
            "constraints": ["Two-hour reversible prototype"],
        }
        self.members = ["maya-chen", "rafael-alvarez"]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_prepare_uses_equal_packet_and_excludes_social_history(self) -> None:
        manifest = prepare_round(self.round_dir, self.packet, self.members)
        self.assertEqual(manifest["status"], "PREPARED")
        prompt_packets = []
        for member in self.members:
            path = self.round_dir / "prompts" / f"{member}.json"
            prompt = load_json(path)
            prompt_packets.append(prompt["common_packet"])
            self.assertNotIn("Council relationships", prompt["identity_model"])
            self.assertFalse(path.stat().st_mode & stat.S_IWUSR)
        self.assertEqual(prompt_packets[0], prompt_packets[1])

    def test_freeze_then_anonymize_preserves_independence(self) -> None:
        prepare_round(self.round_dir, self.packet, self.members)
        stage_response(self.round_dir, response("CR-101", "maya-chen", "Map the invisible recovery burden before automating."))
        with self.assertRaisesRegex(DesignCouncilError, "incomplete set"):
            freeze_round(self.round_dir)
        stage_response(self.round_dir, response("CR-101", "rafael-alvarez", "rafael would remove scheduling and make changes physically legible."))
        frozen = freeze_round(self.round_dir)
        self.assertEqual(frozen["status"], "FROZEN")
        self.assertTrue(frozen["response_set_hash"])

        anonymous = anonymize_round(self.round_dir)
        self.assertTrue(anonymous["authorship_removed"])
        rendered = json.dumps(anonymous).lower()
        self.assertNotIn("maya", rendered)
        self.assertNotIn("rafael", rendered)
        self.assertNotIn("human reality", rendered)
        self.assertEqual(len(anonymous["kernels"]), 2)
        self.assertTrue(all(kernel["source_response_hash"] for kernel in anonymous["kernels"]))

        frozen_path = self.round_dir / "frozen/responses.json"
        self.assertFalse(frozen_path.stat().st_mode & stat.S_IWUSR)
        self.assertEqual(anonymize_round(self.round_dir), anonymous)

    def test_sibling_reference_is_rejected_before_freeze(self) -> None:
        for spelling in ("Rafael", "rafael", "ALVAREZ"):
            with self.subTest(spelling=spelling):
                bad = response("CR-101", "maya-chen", f"{spelling} has the better idea.")
                result = validate_response(bad, "CR-101", "maya-chen", ["rafael-alvarez"])
                self.assertFalse(result["valid"])
                self.assertIn("rafael-alvarez", result["referenced_siblings"])


if __name__ == "__main__":
    unittest.main()
