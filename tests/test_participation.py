"""Behavior and state tests for optional participatory MightShape exercises."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "mightshape" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dc_core import DesignCouncilError, schema_validation  # noqa: E402
from project_state import (  # noqa: E402
    add_participation_contribution,
    initialize_project,
    open_participation_prompt,
    participation_action,
    record_participation_guidance,
    set_facilitator_level,
    set_participation_mode,
    start_participation,
    validate_state,
)


class ParticipationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        initialize_project(self.root, "Participation test", "Help us explore a workflow", project_id="DC-PARTICIPATE")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _start_turn_by_turn(self, **kwargs):
        state = start_participation(
            self.root,
            "FACILITATED_TURN_BY_TURN",
            kwargs.pop("activity", "AFFINITY_CLUSTERING"),
            kwargs.pop("facilitator_level", "NOVICE_ASSISTED"),
            kwargs.pop("round_id", None),
            kwargs.pop("sealed_phase", "NONE"),
        )
        self.assertFalse(kwargs)
        return state["participation_sessions"][-1]["id"]

    def _novice_prompt(self, session_id: str, prompt: str = "Where would you place E-04?"):
        return open_participation_prompt(
            self.root,
            session_id,
            prompt,
            "Make the emerging pattern inspectable without forcing agreement.",
            "We are grouping provisionally, so outliers are useful.",
            "For example, a missed call may sit between discovery and recovery.",
        )

    def test_participation_is_optional_and_observe_mode_cannot_coerce_input(self) -> None:
        state = start_participation(self.root, "OBSERVE", "BRAINSTORMING")
        session = state["participation_sessions"][0]
        self.assertEqual(session["mode"], "OBSERVE")
        self.assertEqual(session["facilitator_level"], "NOVICE_ASSISTED")
        with self.assertRaisesRegex(DesignCouncilError, "OBSERVE mode cannot open"):
            open_participation_prompt(self.root, session["id"], "Give me an idea")
        with self.assertRaisesRegex(DesignCouncilError, "does not accept contributions"):
            add_participation_contribution(self.root, session["id"], "IDEA", "A shared signal")

    def test_novice_onboarding_and_exactly_one_open_prompt(self) -> None:
        session_id = self._start_turn_by_turn()
        with self.assertRaisesRegex(DesignCouncilError, "purpose, mindset, and concrete example"):
            open_participation_prompt(self.root, session_id, "Where would you place E-04?")
        state = self._novice_prompt(session_id)
        session = state["participation_sessions"][0]
        prompt = session["prompts"][0]
        self.assertTrue(prompt["purpose"])
        self.assertTrue(prompt["mindset"])
        self.assertTrue(prompt["example"])
        self.assertEqual(prompt["guidance_level"], "NOVICE_ASSISTED")
        with self.assertRaisesRegex(DesignCouncilError, "current prompt"):
            open_participation_prompt(self.root, session_id, "Name the cluster")

    def test_user_contribution_answers_prompt_and_updates_only_a_meaningful_delta(self) -> None:
        session_id = self._start_turn_by_turn()
        self._novice_prompt(session_id)
        state = add_participation_contribution(
            self.root,
            session_id,
            "SORT_MOVE",
            "Move E-04 into Recovery",
            "Moved E-04 to Recovery",
        )
        session = state["participation_sessions"][0]
        item = session["contributions"][0]
        self.assertEqual(item["id"], "UC-001")
        self.assertEqual(item["provenance"], "USER_PROVIDED")
        self.assertEqual(item["board_revision"], 1)
        self.assertEqual(session["prompts"][0]["status"], "ANSWERED")
        self.assertEqual(session["prompts"][0]["answered_by"], "UC-001")
        self.assertEqual(item["prompt_id"], session["prompts"][0]["id"])
        self.assertEqual(len(session["board_changes"]), 1)

        # A contribution can be captured without claiming that the board moved.
        open_participation_prompt(self.root, session_id, "Which note still feels unresolved?")
        state = add_participation_contribution(self.root, session_id, "NOTE", "I am unsure about E-09")
        session = state["participation_sessions"][0]
        self.assertEqual(session["board_revision"], 1)
        self.assertEqual(len(session["board_changes"]), 1)

    def test_guidance_is_progressive_and_does_not_create_user_contributions(self) -> None:
        session_id = self._start_turn_by_turn()
        self._novice_prompt(session_id)
        state = record_participation_guidance(
            self.root,
            session_id,
            "DEFINE",
            "A boundary card plausibly belongs in more than one group; we keep that ambiguity visible.",
            "boundary card",
        )
        session = state["participation_sessions"][0]
        self.assertEqual(session["guidance_checkpoints"][0]["id"], "UG-001")
        self.assertEqual(session["guidance_checkpoints"][0]["prompt_id"], session["prompts"][0]["id"])
        self.assertEqual(session["contributions"], [])
        self.assertEqual(session["prompts"][0]["status"], "OPEN")
        state = record_participation_guidance(
            self.root,
            session_id,
            "SLOWER",
            "I will use smaller decisions and less jargon.",
            adaptation_reason="The user asked for a more deliberate pace.",
            adaptation_source="USER_REQUEST",
        )
        self.assertEqual(state["participation_sessions"][0]["guidance_state"]["pace"], "SLOWER")
        adaptation = state["participation_sessions"][0]["adaptations"][0]
        self.assertEqual(adaptation["reason"], "The user asked for a more deliberate pace.")
        self.assertEqual(adaptation["source"], "USER_REQUEST")
        self.assertEqual(adaptation["prompt_id"], session["prompts"][0]["id"])

    def test_fluent_user_can_switch_to_light_touch(self) -> None:
        session_id = self._start_turn_by_turn(facilitator_level="GUIDED")
        state = set_facilitator_level(
            self.root,
            session_id,
            "LIGHT_TOUCH",
            "The user demonstrated fluency with assumption mapping.",
            "FACILITATOR_INFERENCE",
        )
        session = state["participation_sessions"][0]
        self.assertEqual(session["facilitator_level"], "LIGHT_TOUCH")
        self.assertEqual(session["adaptations"][0]["source"], "FACILITATOR_INFERENCE")
        state = open_participation_prompt(self.root, session_id, "Which assumption has the weakest evidence?")
        self.assertIsNone(state["participation_sessions"][0]["prompts"][0]["example"])

    def test_skip_pause_resume_hand_back_and_superseding_undo_preserve_history(self) -> None:
        session_id = self._start_turn_by_turn()
        self._novice_prompt(session_id)
        participation_action(self.root, session_id, "SKIP")
        open_participation_prompt(self.root, session_id, "Name one cluster")
        state = add_participation_contribution(
            self.root,
            session_id,
            "CLUSTER_RENAME",
            "Call it Alerts",
            "Named the cluster Alerts",
        )
        contribution_id = state["participation_sessions"][0]["contributions"][0]["id"]
        state = participation_action(
            self.root,
            session_id,
            "UNDO",
            contribution_id,
            "Call it Signal overload",
        )
        session = state["participation_sessions"][0]
        old, replacement = session["contributions"]
        self.assertEqual(old["status"], "SUPERSEDED")
        self.assertEqual(old["superseded_by"], replacement["id"])
        self.assertEqual(replacement["supersedes"], old["id"])
        participation_action(self.root, session_id, "PAUSE")
        participation_action(self.root, session_id, "RESUME")
        state = participation_action(self.root, session_id, "HAND_BACK")
        self.assertEqual(state["participation_sessions"][0]["status"], "HANDED_BACK")
        self.assertTrue(validate_state(state)["valid"])

    def test_sealed_round_input_is_equal_pre_round_or_held_during_round_a(self) -> None:
        pre_id = self._start_turn_by_turn(round_id="CR-100", sealed_phase="PRE_ROUND")
        self._novice_prompt(pre_id)
        state = add_participation_contribution(self.root, pre_id, "IDEA", "Make ownership visible")
        contribution = state["participation_sessions"][0]["contributions"][0]
        self.assertEqual(contribution["sealed_disposition"], "COMMON_PACKET_NEXT_ROUND")
        self.assertTrue(state["participation_sessions"][0]["sealed_coordination"]["applies_equally"])
        participation_action(self.root, pre_id, "COMPLETE")

        open_id = self._start_turn_by_turn(round_id="CR-101", sealed_phase="ROUND_A_OPEN")
        self._novice_prompt(open_id)
        with self.assertRaisesRegex(DesignCouncilError, "held until post-freeze"):
            add_participation_contribution(
                self.root,
                open_id,
                "IDEA",
                "Send it only to the last member",
                sealed_disposition="NONE",
            )
        state = add_participation_contribution(self.root, open_id, "IDEA", "Hold this idea")
        self.assertEqual(
            state["participation_sessions"][-1]["contributions"][0]["sealed_disposition"],
            "HOLD_UNTIL_POST_FREEZE",
        )

    def test_mode_can_switch_without_erasing_session(self) -> None:
        state = start_participation(self.root, "OBSERVE", "POV_HMW")
        session_id = state["participation_sessions"][0]["id"]
        state = set_participation_mode(self.root, session_id, "COLLABORATE")
        self.assertEqual(state["participation_sessions"][0]["mode"], "COLLABORATE")
        self.assertEqual(state["participation_sessions"][0]["actions"][-1]["action"], "MODE_CHANGED")

    def test_turn_by_turn_contributions_require_one_open_prompt_but_collaboration_does_not(self) -> None:
        session_id = self._start_turn_by_turn()
        with self.assertRaisesRegex(DesignCouncilError, "exactly one open participation prompt"):
            add_participation_contribution(self.root, session_id, "NOTE", "An unprompted answer")
        self._novice_prompt(session_id)
        add_participation_contribution(self.root, session_id, "NOTE", "A prompted answer")
        with self.assertRaisesRegex(DesignCouncilError, "exactly one open participation prompt"):
            add_participation_contribution(self.root, session_id, "NOTE", "A second answer")
        participation_action(self.root, session_id, "COMPLETE")

        state = start_participation(self.root, "COLLABORATE", "BRAINSTORMING", "GUIDED")
        collaborate_id = state["participation_sessions"][-1]["id"]
        state = add_participation_contribution(self.root, collaborate_id, "IDEA", "A volunteered idea")
        self.assertIsNone(state["participation_sessions"][-1]["contributions"][0]["prompt_id"])

    def test_guidance_requires_and_retains_the_open_prompt_id(self) -> None:
        session_id = self._start_turn_by_turn()
        with self.assertRaisesRegex(DesignCouncilError, "requires exactly one open participation prompt"):
            record_participation_guidance(self.root, session_id, "WHY", "To expose a useful pattern.")
        state = self._novice_prompt(session_id)
        prompt_id = state["participation_sessions"][0]["prompts"][0]["id"]
        state = record_participation_guidance(self.root, session_id, "WHY", "To expose a useful pattern.")
        self.assertEqual(state["participation_sessions"][0]["guidance_checkpoints"][0]["prompt_id"], prompt_id)
        add_participation_contribution(self.root, session_id, "SORT_MOVE", "Place E-04 with recovery")
        with self.assertRaisesRegex(DesignCouncilError, "requires exactly one open participation prompt"):
            record_participation_guidance(self.root, session_id, "EXAMPLE", "A distant example.")

    def test_slower_requires_scaffolding_and_records_adaptive_level_change(self) -> None:
        session_id = self._start_turn_by_turn(facilitator_level="LIGHT_TOUCH")
        open_participation_prompt(self.root, session_id, "Which card should move first?")
        state = record_participation_guidance(
            self.root,
            session_id,
            "SLOWER",
            "I will narrow each decision and explain its immediate purpose.",
            adaptation_reason="The user asked for smaller steps.",
            adaptation_source="USER_REQUEST",
        )
        pace_adaptation = state["participation_sessions"][0]["adaptations"][0]
        self.assertEqual((pace_adaptation["from"], pace_adaptation["to"]), ("STANDARD", "SLOWER"))
        participation_action(self.root, session_id, "SKIP")
        with self.assertRaisesRegex(DesignCouncilError, "not LIGHT_TOUCH"):
            open_participation_prompt(self.root, session_id, "Which card should move next?")
        state = set_facilitator_level(
            self.root,
            session_id,
            "GUIDED",
            "The slower pace needs lightweight scaffolding.",
            "FACILITATOR_INFERENCE",
        )
        level_adaptation = state["participation_sessions"][0]["adaptations"][1]
        self.assertEqual(level_adaptation["dimension"], "FACILITATOR_LEVEL")
        self.assertEqual(level_adaptation["source"], "FACILITATOR_INFERENCE")
        with self.assertRaisesRegex(DesignCouncilError, "not LIGHT_TOUCH"):
            set_facilitator_level(self.root, session_id, "LIGHT_TOUCH", "Keep it terse")
        with self.assertRaisesRegex(DesignCouncilError, "purpose and mindset scaffolding"):
            open_participation_prompt(self.root, session_id, "Which card should move next?")
        state = open_participation_prompt(
            self.root,
            session_id,
            "Which card should move next?",
            "Choose one small board change.",
            "Treat the move as provisional.",
        )
        prompt = state["participation_sessions"][0]["prompts"][-1]
        self.assertEqual(prompt["pace"], "SLOWER")
        self.assertIsNone(prompt["example"])

    def test_faster_omits_repeat_scaffolding_but_not_novice_onboarding(self) -> None:
        session_id = self._start_turn_by_turn()
        state = self._novice_prompt(session_id)
        first = state["participation_sessions"][0]["prompts"][0]
        self.assertTrue(all(first[field] for field in ("purpose", "mindset", "example")))
        record_participation_guidance(
            self.root,
            session_id,
            "FASTER",
            "I will keep later prompts terse.",
            adaptation_reason="The user wants fewer repeated explanations.",
        )
        add_participation_contribution(self.root, session_id, "SORT_MOVE", "Place E-04 with recovery")
        state = open_participation_prompt(self.root, session_id, "Which card should move next?")
        second = state["participation_sessions"][0]["prompts"][1]
        self.assertEqual(second["pace"], "FASTER")
        self.assertIsNone(second["purpose"])
        self.assertIsNone(second["mindset"])

    def test_obviously_compound_prompts_are_rejected_conservatively(self) -> None:
        session_id = self._start_turn_by_turn(facilitator_level="GUIDED")
        compound_prompts = (
            "Which card should move, and why?",
            "Which card should move? What should we call the cluster?",
            "Choose a card; then name the cluster.",
            "Do both:\n1. Move a card\n2. Name the cluster",
        )
        for prompt in compound_prompts:
            with self.subTest(prompt=prompt):
                with self.assertRaisesRegex(DesignCouncilError, "obviously compound"):
                    open_participation_prompt(self.root, session_id, prompt)
        state = open_participation_prompt(self.root, session_id, "Compare E-03 and E-04.")
        self.assertEqual(state["participation_sessions"][0]["prompts"][0]["status"], "OPEN")

    def test_participation_schema_and_project_state_validate(self) -> None:
        session_id = self._start_turn_by_turn()
        state = self._novice_prompt(session_id)
        session = state["participation_sessions"][0]
        self.assertTrue(schema_validation(session, "participation-session.schema.json")["valid"])
        self.assertTrue(validate_state(state)["valid"])


class ParticipationStaticContractTests(unittest.TestCase):
    def test_skill_and_reference_encode_adaptive_noncoercive_facilitation(self) -> None:
        skill = (ROOT / "skills/mightshape/SKILL.md").read_text(encoding="utf-8")
        reference = (ROOT / "skills/mightshape/references/participatory-workshops.md").read_text(encoding="utf-8")
        for marker in (
            "OBSERVE",
            "COLLABORATE",
            "FACILITATED_TURN_BY_TURN",
            "NOVICE_ASSISTED",
            "GUIDED",
            "LIGHT_TOUCH",
            "exactly one bounded prompt",
            "USER_PROVIDED",
            "held unchanged until after the set is frozen",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        self.assertIn("never force participation", reference.lower())
        self.assertIn("PARTICIPATION (optional) · Watch · Collaborate · One prompt at a time", skill)
        self.assertIn("immediately continue in `OBSERVE`", skill)
        self.assertIn("without grading", reference)
        self.assertIn("Never fabricate the user's improved answer", reference)
        self.assertIn("Honor the activity the user requested", reference)
        self.assertIn("Do not silently replace brainstorming", skill)
        self.assertIn("avoid anchoring", skill)
        self.assertIn("never seed a protected independent brainstorm", reference)
        self.assertIn("why are we doing this?", reference)
        self.assertIn("show an example", reference)
        self.assertIn("define that", reference)


if __name__ == "__main__":
    unittest.main()
