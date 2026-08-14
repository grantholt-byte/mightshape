"""Structural tests for the portable team-channel workshop boundary."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "mightshape" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dc_core import schema_validation  # noqa: E402


def portable_session() -> dict:
    return {
        "schema_version": "1.0.0",
        "id": "TW-01234567-89AB-CDEF-0123-456789ABCDEF",
        "exercise": "BRAINWRITING",
        "starting_point": "CONCEPT",
        "challenge": "How might a team preserve context across handoffs?",
        "visibility": "SEALED",
        "status": "COLLECTING",
        "facilitator_level": "NOVICE_ASSISTED",
        "initiator_participant_id": "TP-001",
        "controller_participant_ids": ["TP-001"],
        "participants": [
            {
                "id": "TP-001",
                "role": "INITIATOR",
                "status": "ACTIVE",
                "joined_at": "2026-08-14T12:00:00Z",
            },
            {
                "id": "TP-002",
                "role": "CONTRIBUTOR",
                "status": "ACTIVE",
                "joined_at": "2026-08-14T12:01:00Z",
            },
        ],
        "prompts": [
            {
                "id": "UP-001",
                "purpose": "Protect independent thought before discussion.",
                "mindset": "Diverge without ranking.",
                "prompt": "Write one concise possibility.",
                "status": "OPEN",
                "opened_at": "2026-08-14T12:00:00Z",
                "closed_at": None,
            }
        ],
        "contributions": [
            {
                "id": "UC-001",
                "participant_id": "TP-002",
                "kind": "IDEA",
                "content": "Make the unresolved question travel with the work.",
                "provenance": "USER_PROVIDED",
                "status": "ACTIVE",
                "submitted_at": "2026-08-14T12:02:00Z",
                "revealed_at": None,
            }
        ],
        "artifacts": [],
        "contribution_set_frozen_at": None,
        "step_version": 2,
        "created_at": "2026-08-14T12:00:00Z",
        "updated_at": "2026-08-14T12:02:00Z",
        "retention_expires_at": "2026-09-13T12:00:00Z",
        "history": [
            {
                "version": 1,
                "at": "2026-08-14T12:00:00Z",
                "action": "WORKSHOP_STARTED",
                "actor_participant_id": "TP-001",
                "details": {"visibility": "SEALED"},
            },
            {
                "version": 2,
                "at": "2026-08-14T12:02:00Z",
                "action": "CONTRIBUTION_ADDED",
                "actor_participant_id": "TP-002",
                "details": {"contribution_id": "UC-001"},
            },
        ],
    }


def private_binding() -> dict:
    return {
        "schema_version": "1.0.0",
        "session_id": "TW-01234567-89AB-CDEF-0123-456789ABCDEF",
        "binding_version": 1,
        "platform": "SLACK",
        "workspace_ref": "T123",
        "channel_ref": "C123",
        "conversation_ref": "171234.000",
        "root_message_ref": "171234.000",
        "participant_refs": {"b" * 64: "TP-001", "c" * 64: "TP-002"},
        "processed_event_digests": ["d" * 64],
        "outbound_deliveries": [],
        "created_at": "2026-08-14T12:00:00Z",
        "updated_at": "2026-08-14T12:02:00Z",
    }


class TeamWorkshopContractTests(unittest.TestCase):
    def test_portable_session_and_private_binding_validate_separately(self) -> None:
        portable = portable_session()
        binding = private_binding()
        self.assertTrue(schema_validation(portable, "team-workshop-session.schema.json")["valid"])
        self.assertTrue(schema_validation(binding, "team-channel-binding.schema.json")["valid"])
        text = str(portable)
        self.assertNotIn(binding["workspace_ref"], text)
        self.assertNotIn(binding["channel_ref"], text)

    def test_channel_contribution_cannot_masquerade_as_human_research(self) -> None:
        value = copy.deepcopy(portable_session())
        value["contributions"][0]["provenance"] = "HUMAN_INTERVIEW"
        result = schema_validation(value, "team-workshop-session.schema.json")
        self.assertFalse(result["valid"])

    def test_raw_platform_identifiers_are_rejected_from_portable_root(self) -> None:
        value = portable_session()
        value["workspace_ref"] = "T123"
        result = schema_validation(value, "team-workshop-session.schema.json")
        self.assertFalse(result["valid"])

    def test_portable_session_rejects_more_than_one_hundred_contributions(self) -> None:
        value = portable_session()
        prototype = value["contributions"][0]
        value["contributions"] = []
        for index in range(1, 102):
            contribution = copy.deepcopy(prototype)
            contribution["id"] = f"UC-{index:03d}"
            contribution["content"] = f"Bounded source record {index}"
            value["contributions"].append(contribution)
        result = schema_validation(value, "team-workshop-session.schema.json")
        self.assertFalse(result["valid"])
        self.assertTrue(any("at most 100" in error.lower() for error in result["errors"]), result["errors"])


if __name__ == "__main__":
    unittest.main()
