from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "skills" / "design-council" / "scripts"
SCHEMA_ROOT = ROOT / "skills" / "design-council" / "schemas"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from dc_core import schema_validation  # noqa: E402
from disclosure_guard import build_external_packet  # noqa: E402
from participant_sources import (  # noqa: E402
    BringYourOwnParticipantSource,
    ExchangeParticipantSource,
    SourceRequest,
    SyntheticParticipantSource,
)


def conflict_policy(mode: str = "STANDARD") -> dict:
    enabled = mode != "NONE"
    strict = mode == "STRICT"
    return {
        "mode": mode,
        "enabled": enabled,
        "excluded_companies": ["Example Rival"] if enabled else [],
        "excluded_industries": [],
        "excluded_roles": ["current vendor salesperson"] if enabled else [],
        "excluded_relationships": ["current employee"] if enabled else [],
        "strict_mode": strict,
        "legal_screening_claimed": False,
    }


def internal_study(*, exposure: str = "LEVEL_0_PROBLEM_ONLY", source: str = "BRING_YOUR_OWN") -> dict:
    source_request = SourceRequest(study_id="STUDY-001", target_count=5, invite_url=None)
    if source == "SYNTHETIC":
        source_config = SyntheticParticipantSource().prepare(source_request)
    elif source == "EXCHANGE":
        source_config = ExchangeParticipantSource().prepare(source_request)
    else:
        source_config = BringYourOwnParticipantSource().prepare(source_request)
    return {
        "id": "STUDY-001",
        "title": "Family coordination discovery",
        "research_goal": "Understand how families discover and resolve changing obligations.",
        "topics_to_cover": ["last schedule change", "discovery channels", "recovery"],
        "participant_source": source_config,
        "research_session": {
            "type": "QUALITATIVE_INTERVIEW",
            "duration_minutes": 10,
            "purpose": "Reconstruct recent coordination behavior.",
        },
        "project_exposure": {
            "level": exposure,
            "solution_blackout": exposure == "LEVEL_0_PROBLEM_ONLY",
            "concept_reveal_status": "NOT_PLANNED",
            "rationale": "Behavior can be reconstructed without disclosing the proposed product.",
            "confidentiality_controls_status": "NOT_APPLICABLE",
        },
        "conflict_policy": conflict_policy(),
        "internal_context": {
            "full_challenge": "Acme needs a new family coordination business.",
            "proposed_solution": "Project Nightingale is an AI family scheduler.",
            "company_context": "Acme strategy and customer list",
            "hypotheses": ["Discovery is harder than resolution."],
            "assumptions": ["Parents will centralize messages."],
            "strategic_rationale": "Launch before Example Rival at $29/month.",
        },
        "external_candidate": {
            "purpose": "Understand how families currently discover schedule changes.",
            "context": "We are studying coordination of changing extracurricular schedules.",
            "topics": ["the last change", "what happened next", "workarounds"],
            "duration_minutes": 10,
            "ai_interviewer_disclosure": "I am an AI interviewer helping a design team learn from your experience.",
            "stop_notice": "You may stop at any time.",
            "company_name": "Acme",
            "product_codename": "Project Nightingale",
            "pricing": "$29/month",
            "architecture": "private agent graph and source code",
            "internal_architecture": {"service_map": "confidential system"},
            "competitor_references": ["Example Rival"],
            "proposed_solution": "AI family scheduler",
            "email": "owner@acme.invalid",
            "Nightingale_internal_note": "not for participants",
        },
        "consent_boundary": {
            "project_owner_method_learning_opt_in": False,
            "participant_content_consent_required": True,
            "owner_opt_in_grants_participant_consent": False,
            "participant_consent_version": "consent-v1",
        },
        "sensitive_terms": ["Acme", "Nightingale"],
        "external_packet_ids": [],
        "created_at": "2026-08-12T12:00:00Z",
        "status": "READY_FOR_DISCLOSURE_REVIEW",
    }


class ParticipantSourceContractTests(unittest.TestCase):
    def test_synthetic_and_bring_your_own_work_without_exchange(self) -> None:
        request = SourceRequest(study_id="STUDY-004", target_count=3)
        synthetic = SyntheticParticipantSource().prepare(request)
        own = BringYourOwnParticipantSource().prepare(request)
        self.assertEqual(synthetic["status"], "READY")
        self.assertEqual(own["status"], "NEEDS_HOSTING")
        self.assertNotEqual(synthetic["next_action"], own["next_action"])
        self.assertTrue(schema_validation(synthetic, "participant-source.schema.json")["valid"])
        self.assertTrue(schema_validation(own, "participant-source.schema.json")["valid"])

    def test_bring_your_own_becomes_ready_only_with_real_url(self) -> None:
        request = SourceRequest(
            study_id="STUDY-004",
            target_count=3,
            invite_url="https://research.example.invalid/s/non-secret-fixture-token",
        )
        result = BringYourOwnParticipantSource().prepare(request)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["configuration"]["invite_url"], request.invite_url)

    def test_exchange_is_structured_and_side_effect_free(self) -> None:
        request = SourceRequest(study_id="STUDY-004", target_count=5)
        provider = ExchangeParticipantSource()
        status = provider.prepare(request)
        self.assertEqual(status["status"], "NOT_CONFIGURED")
        for operation in (
            provider.create_recruitment_request,
            provider.estimate_participant_pool,
            provider.match_participants,
            provider.invite_participants,
            provider.track_participation,
            provider.return_completed_sessions,
        ):
            result = operation(request)
            self.assertEqual(result["status"], "FUTURE_FEATURE")
            self.assertFalse(result["side_effect_performed"])


class DisclosureGuardTests(unittest.TestCase):
    def test_problem_only_packet_removes_solution_and_does_not_mutate_internal(self) -> None:
        study = internal_study()
        before = copy.deepcopy(study)
        result = build_external_packet(study)
        self.assertEqual(study, before)
        serialized = json.dumps(result, sort_keys=True)
        for secret in ("Acme", "Nightingale", "$29", "owner@acme", "AI family scheduler"):
            self.assertNotIn(secret, serialized)
        packet = result["external_study_packet"]
        self.assertTrue(packet["solution_blackout"])
        self.assertEqual(packet["project_exposure_level"], "LEVEL_0_PROBLEM_ONLY")
        self.assertIsNone(packet["participant_facing"]["prototype_reference"])
        self.assertEqual(packet["approval_status"], "REQUIRES_USER_DECISION")

    def test_guard_supports_all_recommendation_actions_and_assesses_ip(self) -> None:
        result = build_external_packet(internal_study())
        recommendations = {item["recommendation"] for item in result["review"]["findings"]}
        self.assertEqual(recommendations, {"REMOVE", "GENERALIZE", "RETAIN", "REQUIRES_USER_DECISION"})
        assessment = result["review"]["ip_exposure_assessment"]
        self.assertFalse(assessment["legal_guarantee"])
        self.assertIn(assessment["overall"], {"LOW", "MODERATE", "HIGH"})
        self.assertIn("does not guarantee", assessment["disclaimer"])

    def test_guard_outputs_validate_against_all_three_contracts(self) -> None:
        study = internal_study()
        self.assertTrue(schema_validation(study, "internal-study.schema.json")["valid"])
        result = build_external_packet(study)
        self.assertTrue(schema_validation(result["review"], "disclosure-review.schema.json")["valid"])
        self.assertTrue(schema_validation(result["external_study_packet"], "external-study-packet.schema.json")["valid"])
        self.assertTrue(schema_validation(result["review"]["ip_exposure_assessment"], "ip-exposure-assessment.schema.json")["valid"])

    def test_prototype_reference_is_retained_only_at_prototype_exposure(self) -> None:
        study = internal_study(exposure="LEVEL_2_PROTOTYPE_BLIND")
        study["project_exposure"]["solution_blackout"] = False
        study["project_exposure"]["concept_reveal_status"] = "ACTIVE"
        study["external_candidate"]["prototype_reference"] = "https://prototype.example.invalid/task"
        packet = build_external_packet(study)["external_study_packet"]
        self.assertEqual(packet["participant_facing"]["prototype_reference"], "https://prototype.example.invalid/task")


class ExchangeSchemaBoundaryTests(unittest.TestCase):
    def test_conflict_policy_preserves_exclusions_without_legal_claim(self) -> None:
        policy = conflict_policy("STRICT")
        result = schema_validation(policy, "conflict-policy.schema.json")
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(policy["legal_screening_claimed"])

    def test_researcher_visible_profile_rejects_private_identity(self) -> None:
        profile = {
            "participant_id": "P-001",
            "private_profile": {
                "identity_reference": "private://identity/1",
                "contact_reference": None,
                "verification_evidence_references": [],
            },
            "matching_profile": {"experience_signals": []},
            "researcher_visible_profile": {
                "participant_id": "P-001",
                "experience_summary": "Coordinates three children's activities weekly.",
                "professional_role": None,
                "environment": "multi-caregiver household",
                "experience_signals": ["manages_multiple_childrens_activities"],
                "verification_status": "SELF_REPORTED",
                "limitations": ["No identity verification was performed."],
                "full_name": "Must Not Leak",
            },
            "verification": {
                "status": "SELF_REPORTED",
                "verified_at": None,
                "verification_reference": None,
                "verified_by_provider": None,
            },
        }
        result = schema_validation(profile, "participant-profile.schema.json")
        self.assertFalse(result["valid"])
        profile["researcher_visible_profile"].pop("full_name")
        self.assertTrue(schema_validation(profile, "participant-profile.schema.json")["valid"])

    def test_owner_opt_in_cannot_grant_participant_consent(self) -> None:
        study = internal_study()
        study["consent_boundary"]["project_owner_method_learning_opt_in"] = True
        study["consent_boundary"]["owner_opt_in_grants_participant_consent"] = True
        result = schema_validation(study, "internal-study.schema.json")
        self.assertFalse(result["valid"])

    def test_future_recruitment_request_preserves_fit_and_conflict_without_matching(self) -> None:
        signal = {
            "id": "XS-001",
            "signal": "works_in_hospital_operations",
            "basis": "WORKFLOW_EXPOSURE",
            "frequency": "DAILY",
            "recency": "CURRENT",
            "years_experience": 7,
            "self_reported": True,
            "methodological_relevance": "Has recent experience with the target handoff workflow.",
        }
        request = {
            "id": "EXR-001",
            "study_id": "STUDY-001",
            "provider": "EXCHANGE",
            "status": "FUTURE_FEATURE",
            "session_type": "QUALITATIVE_INTERVIEW",
            "target_count": 5,
            "experience_signals": [signal],
            "conflict_policy": conflict_policy("STRICT"),
            "project_exposure_level": "LEVEL_0_PROBLEM_ONLY",
            "credit_estimate": None,
            "created_at": "2026-08-12T12:00:00Z",
            "message": "No recruitment or matching occurs in V1.",
        }
        self.assertTrue(schema_validation(signal, "experience-signal.schema.json")["valid"])
        self.assertTrue(schema_validation(request, "exchange-recruitment-request.schema.json")["valid"])
        request["matched_participants"] = ["P-001"]
        self.assertFalse(schema_validation(request, "exchange-recruitment-request.schema.json")["valid"])

    def test_verification_requires_real_reference_and_timestamp(self) -> None:
        claimed = {
            "status": "PROFESSIONALLY_VERIFIED",
            "verified_at": None,
            "verification_reference": None,
            "verified_by_provider": None,
        }
        self.assertFalse(schema_validation(claimed, "participant-verification-status.schema.json")["valid"])
        self_reported = {
            "status": "SELF_REPORTED",
            "verified_at": None,
            "verification_reference": None,
            "verified_by_provider": None,
        }
        self.assertTrue(schema_validation(self_reported, "participant-verification-status.schema.json")["valid"])

    def test_learning_signal_structurally_rejects_raw_content(self) -> None:
        signal = {
            "schema_version": "1.0.0",
            "contribution_opt_in": True,
            "participant_content_included": False,
            "challenge_archetypes": ["AI_PRODUCT"],
            "methods_used": ["empathy-interview"],
            "stage_transitions": ["EMPATHIZE->DEFINE"],
            "problem_frame_changed": True,
            "assumptions_tested": 2,
            "assumptions_falsified": 1,
            "prototype_types": ["concierge"],
            "minority_report_influenced_direction": True,
            "synthetic_human_reality_check_result": "TRANSFORMED",
            "build_gate_outcome": "TEST_FIRST",
            "transcript": "raw participant words must never fit this schema",
        }
        self.assertFalse(schema_validation(signal, "learning-signal.schema.json")["valid"])
        signal.pop("transcript")
        self.assertTrue(schema_validation(signal, "learning-signal.schema.json")["valid"])

    def test_optional_demand_signal_cannot_carry_project_content(self) -> None:
        event = {
            "event": "participant_recruitment_requested",
            "occurred_at": "2026-08-12T12:00:00Z",
            "collection_opt_in": True,
            "contains_project_content": False,
        }
        self.assertTrue(schema_validation(event, "demand-signal-event.schema.json")["valid"])
        event["project_prompt"] = "confidential idea"
        self.assertFalse(schema_validation(event, "demand-signal-event.schema.json")["valid"])

    def test_exchange_credit_contract_is_inert_in_v1(self) -> None:
        ledger = {
            "ledger_version": "1.0.0",
            "feature_status": "FUTURE_FEATURE",
            "currency": "EXCHANGE_CREDITS",
            "account_id": None,
            "balance": None,
            "entries": [],
            "pricing_model": None,
        }
        self.assertTrue(schema_validation(ledger, "exchange-credit-ledger.schema.json")["valid"])
        ledger["entries"].append({
            "id": "XCL-001",
            "transaction_type": "SPEND",
            "amount": 1,
            "study_id": "STUDY-001",
            "participant_id": "P-001",
            "created_at": "2026-08-12T12:00:00Z",
        })
        self.assertTrue(schema_validation(ledger, "exchange-credit-ledger.schema.json")["valid"])
        self.assertEqual(ExchangeParticipantSource().prepare(SourceRequest("STUDY-001"))["status"], "NOT_CONFIGURED")

    def test_all_exchange_schemas_are_valid_json_schema(self) -> None:
        import jsonschema

        names = {
            "project-exposure.schema.json",
            "research-session-type.schema.json",
            "conflict-policy.schema.json",
            "participant-source.schema.json",
            "experience-signal.schema.json",
            "participant-verification-status.schema.json",
            "participant-profile.schema.json",
            "ip-exposure-assessment.schema.json",
            "disclosure-review.schema.json",
            "external-study-packet.schema.json",
            "internal-study.schema.json",
            "exchange-recruitment-request.schema.json",
            "exchange-credit-ledger.schema.json",
            "learning-signal.schema.json",
            "demand-signal-event.schema.json",
        }
        for name in names:
            with self.subTest(schema=name):
                schema = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
                jsonschema.validators.validator_for(schema).check_schema(schema)


if __name__ == "__main__":
    unittest.main()
