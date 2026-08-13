"""Regression tests for dependency-free runtime schema enforcement."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "design-council" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dc_core import DesignCouncilError, _check_schema_contract, schema_validation  # noqa: E402
from project_state import new_project_state  # noqa: E402


class StdlibSchemaValidationTests(unittest.TestCase):
    def valid_evidence(self) -> dict:
        return {
            "id": "E-001",
            "claim": "The supplied note identifies a possible workflow burden.",
            "provenance": "USER_PROVIDED",
            "confidence": 0.6,
            "evidence_strength": 0,
            "status": "active",
            "source_refs": [],
            "scope": None,
            "study_id": None,
            "participant_id": None,
            "excerpt": None,
            "consent_allows_quote": None,
            "created_at": "2026-08-13T12:00:00Z",
            "relations": [],
        }

    def test_malformed_evidence_is_rejected_without_optional_dependencies(self) -> None:
        malformed = self.valid_evidence()
        malformed.update(
            {
                "id": "not-an-evidence-id",
                "claim": [],
                "confidence": 99,
                "status": "invented",
                "source_refs": "not-an-array",
                "created_at": "not-a-date",
                "unreviewed_private_data": True,
            }
        )
        result = schema_validation(malformed, "evidence.schema.json")
        self.assertFalse(result["valid"])
        self.assertEqual(result["validator"], "design-council-stdlib-2020-12-subset")
        combined = "\n".join(result["errors"])
        for marker in (
            "id:",
            "claim:",
            "confidence:",
            "status:",
            "source_refs:",
            "created_at:",
            "unreviewed_private_data",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, combined)

    def test_orientation_fields_are_optional_as_a_pair_and_enforced_when_present(self) -> None:
        state = new_project_state("Orientation", "Help me decide where to begin")
        self.assertTrue(schema_validation(state, "project-state.schema.json")["valid"])

        legacy = copy.deepcopy(state)
        for key in ("starting_point", "starting_point_basis", "current_decision"):
            legacy["journey"].pop(key)
        self.assertTrue(schema_validation(legacy, "project-state.schema.json")["valid"])

        missing_basis = copy.deepcopy(legacy)
        missing_basis["journey"]["starting_point"] = "LIVE"
        result = schema_validation(missing_basis, "project-state.schema.json")
        self.assertFalse(result["valid"])
        self.assertIn("starting_point_basis", "\n".join(result["errors"]))

        missing_point = copy.deepcopy(legacy)
        missing_point["journey"]["starting_point_basis"] = "INFERRED"
        result = schema_validation(missing_point, "project-state.schema.json")
        self.assertFalse(result["valid"])
        self.assertIn("starting_point", "\n".join(result["errors"]))

    def test_external_refs_conditionals_and_additional_properties_remain_enforced(self) -> None:
        verified = {
            "status": "VERIFIED",
            "verified_at": None,
            "verification_reference": None,
            "verified_by_provider": None,
        }
        result = schema_validation(verified, "participant-verification-status.schema.json")
        self.assertFalse(result["valid"])
        self.assertIn("verified_at", "\n".join(result["errors"]))

        source = {
            "provider": "SYNTHETIC",
            "provider_version": "1.0.0",
            "status": "READY",
            "study_id": "STUDY-001",
            "configuration": {
                "target_count": 1,
                "grounding_level": "RESEARCHED",
                "invite_url": None,
                "exchange_connector": None,
            },
            "capabilities": ["GENERATE"],
            "next_action": "Create independently grounded participants.",
        }
        self.assertTrue(schema_validation(source, "participant-source.schema.json")["valid"])
        source["configuration"]["target_count"] = 0
        self.assertFalse(schema_validation(source, "participant-source.schema.json")["valid"])

    def test_integer_validation_handles_arbitrarily_large_json_integers(self) -> None:
        # Python integers are unbounded. Validation must not coerce them to a
        # finite float and crash, even when they exceed IEEE-754 range.
        state = new_project_state("Large revision", "Keep validating without float coercion")
        state["revision"] = 10**1000
        self.assertTrue(schema_validation(state, "project-state.schema.json")["valid"])

    def test_unsupported_schema_keyword_fails_closed(self) -> None:
        with self.assertRaisesRegex(DesignCouncilError, "unsupported keyword"):
            _check_schema_contract({"type": "string", "mysteryConstraint": True})


if __name__ == "__main__":
    unittest.main()
