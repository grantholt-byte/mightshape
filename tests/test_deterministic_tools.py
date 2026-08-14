"""Unit and adversarial tests for MightShape's deterministic helpers."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "mightshape" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from allocate_council import allocate_council  # noqa: E402
from check_evidence import audit_evidence  # noqa: E402
from cluster_ideas import cluster_ideas  # noqa: E402
from compare_participants import compare_participants  # noqa: E402
from create_persona import create_persona  # noqa: E402
from create_study import create_study, study_warnings  # noqa: E402
from dc_core import DesignCouncilError, schema_validation  # noqa: E402
from detect_leading_questions import coach_input, coach_question  # noqa: E402
from project_state import new_project_state  # noqa: E402
from score_build_gate import assess_build_gate  # noqa: E402
from score_pov import score_pov  # noqa: E402
from select_methods import select_methods  # noqa: E402
from synthesize_inquiry import synthesize_inquiry  # noqa: E402
from validate_reality_packet import validate_reality_packet  # noqa: E402


NOW = "2026-08-12T12:00:00Z"


def evidence(identifier: str, provenance: str, strength: int = 0, **extra: object) -> dict:
    return {
        "id": identifier,
        "claim": extra.pop("claim", "A scoped claim"),
        "provenance": provenance,
        "confidence": extra.pop("confidence", 0.8),
        "evidence_strength": strength,
        "status": "active",
        "source_refs": extra.pop("source_refs", []),
        "scope": extra.pop("scope", "this source only"),
        "study_id": extra.pop("study_id", None),
        "participant_id": extra.pop("participant_id", None),
        "excerpt": extra.pop("excerpt", None),
        "consent_allows_quote": extra.pop("consent_allows_quote", None),
        "created_at": NOW,
        "relations": [],
        **extra,
    }


def researched_packet() -> dict:
    sources = [
        {"id": "SRC-001", "title": "Official workflow guide", "publisher": "Authority A", "url": "https://example.org/a", "published": None, "accessed": "2026-08-12", "authority_type": "official"},
        {"id": "SRC-002", "title": "Professional standard", "publisher": "Authority B", "url": "https://example.org/b", "published": None, "accessed": "2026-08-12", "authority_type": "professional_authority"},
        {"id": "SRC-003", "title": "Primary field study", "publisher": "Journal C", "url": "https://example.org/c", "published": None, "accessed": "2026-08-12", "authority_type": "peer_reviewed"},
    ]
    details = {
        "responsibilities": ["Coordinate competing care tasks"],
        "working_environment": ["Interrupt-driven shared workspace"],
        "workflows": ["Receive handoff then triage work", "Document changes and escalate exceptions"],
        "decision_rights": ["Prioritize assigned work within local policy"],
        "terminology": ["handoff", "escalation"],
        "tools_and_systems": ["shared record", "secure communication"],
        "dependencies": ["upstream handoff quality"],
        "organizational_relationships": ["works across clinical and operational roles"],
        "incentives": ["safe and timely care"],
        "constraints": ["interruptions and incomplete information"],
        "regulations": ["local and national requirements vary by setting"],
        "performance_pressures": ["time pressure with safety consequences"],
        "failure_modes": ["important change is missed during transition"],
        "workarounds": ["personal reminder notes that vary locally"],
        "common_variations": ["division of work varies by hospital"],
        "cultural_context": ["escalation norms depend on local team culture"],
        "unresolved_questions": ["Which workflow applies at the target site?"],
        "local_variation": ["Staffing, tools, and authority vary by site"],
    }
    facts = [
        {"claim": "Work includes coordinating multiple concurrent responsibilities.", "source_ids": ["SRC-001"]},
        {"claim": "Workflow relies on handoffs.", "source_ids": ["SRC-001", "SRC-002"]},
        {"claim": "Interruptions affect information flow.", "source_ids": ["SRC-003"]},
        {"claim": "Local workflow and tools vary.", "source_ids": ["SRC-001", "SRC-003"]},
        {"claim": "Escalation is part of exception handling.", "source_ids": ["SRC-002"]},
    ]
    return {
        "id": "RP-001",
        "grounding_level": "RESEARCHED",
        "role": "Emergency department nurse",
        "scope_and_locale": "General U.S. context; not a specific hospital",
        **details,
        "supported_facts": facts,
        "research_supported_inferences": [{"claim": "Fragmented handoffs may create reconciliation burden.", "based_on": ["SRC-001", "SRC-003"]}],
        "sources": sources,
        "created_at": NOW,
    }


def human_model() -> dict:
    string_fields = lambda names: {name: [f"Grounded {name.replace('_', ' ')}"] for name in names}
    return {
        "human_model_version": "1.0",
        "identity": {"name": "Nora Bell", "age": 37, "home_region": "Midwestern United States", "occupation": "Emergency department nurse", "previous_occupations": ["Nursing assistant"], "education": ["Bachelor of Science in Nursing"]},
        "life_story": {
            "childhood_context": "Raised in a family that shared care work.", "adolescence": "Learned to stay calm during messy group projects.",
            "education_path": "Worked through nursing school.", "career_path": "Moved from inpatient care to emergency nursing.",
            "family_and_relationships": "Lives with a partner and stays close to a sibling.", "caregiving_context": "Helps an older relative coordinate appointments.",
            "formative_events": ["A confusing early handoff shaped her practice"], "major_successes": ["Helped improve a unit routine"],
            "major_failures": ["Once overprepared a process nobody adopted"], "turning_points": ["Learned to ask what people actually do"],
        },
        "present_life": {"household": "Two-adult household", **string_fields(["routines", "responsibilities", "hobbies", "communities", "interests", "current_pressures", "aspirations"]), "financial_orientation": "Cautious but willing to spend for durability"},
        "professional_model": string_fields(["expertise", "workflows", "vocabulary", "tools", "accumulated_pattern_recognition", "incentives", "constraints", "frustrations", "professional_values"]),
        "worldview": {key: f"A situated view of {key}; neither categorical nor universal." for key in ["people", "institutions", "technology", "authority", "expertise", "markets", "creativity", "risk", "fairness", "progress", "uncertainty"]},
        "values": string_fields(["primary", "secondary", "values_in_tension"]),
        "cognition": {"first_notices": ["where information goes missing"], "attention_bias": ["handoff burden"], "reasoning_style": "Reconstructs sequences before judging", "analogy_style": "Uses household coordination sparingly", "decision_style": "Acts quickly on reversible decisions", "ambiguity_tolerance": "Moderate", "novelty_seeking": "Moderate", "skepticism": "High toward broad claims", "risk_tolerance": "Context dependent", "social_orientation": "Collaborative", "systems_orientation": "Strong"},
        "emotional_model": {**string_fields(["energizers", "irritants", "anxieties", "pride", "sensitivities"]), "humor": "Dry observations about workflow absurdity"},
        "communication": {"vocabulary": ["handoff", "exception"], "sentence_style": "Concrete and sequential", "disagreement_style": "Names the practical gap", "persuasion_style": "Uses a recent example", "question_style": "Asks what happened next", "humor_style": "Dry", "typical_verbosity": "Moderate"},
        "contradictions": [{"belief": "Work should be standardized", "behavior": "Keeps a private reminder ritual", "source_of_tension": "Local reliability gaps"}],
        "blind_spots": ["May overweight high-pressure episodes"],
        "knowledge_boundaries": string_fields(["strong", "moderate", "personal_experience", "weak", "outside_expertise"]),
        "relationships_with_council": [],
        "design_behavior": {key: f"A bounded approach to {key}." for key in ["divergence", "convergence", "prototyping", "testing", "evidence", "conflict"]},
        "persistent_project_memory": {key: [] for key in ["positions", "changes_of_mind", "ideas_supported", "ideas_opposed", "unresolved_questions", "surprises", "important_evidence"]},
        "current_state": {"confidence": {}, "concerns": [], "intellectual_tensions": [], "active_interests": []},
    }


class RoutingAndCouncilTests(unittest.TestCase):
    def test_ai_panel_spans_cognitive_groups(self) -> None:
        result = allocate_council({"operating_level": "PANEL", "archetypes": ["AI_PRODUCT"], "challenge": "AI scheduler", "task": "sealed ideation"})
        self.assertEqual(len(result["selected"]), 5)
        self.assertTrue(result["diversity_check"]["passes"])
        self.assertEqual({item["member_id"] for item in result["selected"]}, {"mei-tanaka", "maya-chen", "priya-rao", "jack-sullivan", "rafael-alvarez"})
        self.assertTrue(result["sealed_round_required"])

    def test_facilitator_only_avoids_unnecessary_council(self) -> None:
        result = allocate_council({"operating_level": "FACILITATOR_ONLY", "challenge": "Explicit code edit"})
        self.assertEqual(result["selected"], [])
        self.assertFalse(result["sealed_round_required"])

    def test_method_router_targets_uncertainty_and_timebox(self) -> None:
        result = select_methods({"current_mode": "EMPATHIZE", "challenge_archetype": "WORKFLOW", "evidence_level": "LOW", "time_available": 120, "uncertainty_type": "behavior", "council_requested": False})
        self.assertGreaterEqual(len(result["recommended"]), 1)
        self.assertTrue(all(item["source_family"] for item in result["recommended"]))
        self.assertIn("advisory", result)
        self.assertNotIn("systems-mapping", json.dumps(result))


class DesignProcessToolTests(unittest.TestCase):
    def test_pov_detects_solution_contamination(self) -> None:
        bad = score_pov({"user": "users", "need": "an AI calendar app", "insight": "People are busy", "evidence_ids": []})
        self.assertTrue(bad["solution_contamination"]["detected"])
        self.assertEqual(bad["interpretation"], "REFRAME")
        good = score_pov({"user": "parents who receive commitments through unrelated channels", "need": "confidence that obligations will not silently collide", "insight": "Coordination is continuous reconciliation because commitments arrive outside a single planning moment", "evidence_ids": ["E-001", "E-002", "E-003"]})
        self.assertFalse(good["solution_contamination"]["detected"])
        self.assertGreater(good["total"], bad["total"])

    def test_clustering_preserves_outliers_and_territory_gaps(self) -> None:
        result = cluster_ideas([
            {"id": "IDEA-001", "statement": "Forward every schedule message into one inbox", "territory": "EXPECTED"},
            {"id": "IDEA-002", "statement": "A shared inbox receives every schedule message", "territory": "ADJACENT"},
            {"id": "IDEA-003", "statement": "A neighborhood bell signals changes physically", "territory": "RADICAL"},
        ], threshold=0.2)
        self.assertEqual(result["input_count"], 3)
        self.assertGreaterEqual(result["outlier_count"], 1)
        self.assertEqual(result["warning"], "IDEATION_TERRITORY_GAP")

    def test_build_gate_is_risk_aware_and_advisory(self) -> None:
        state = new_project_state("Career AI", "Build AI that chooses careers", "AI career chooser", "DC-GATE")
        state["classification"].update({"consequence_of_error": "HIGH", "reversibility": "LOW"})
        state["assumptions"] = [{"id": "A-001", "status": "OPEN_HIGH_RISK"}]
        result = assess_build_gate(state)
        self.assertIn(result["status"], {"TEST_FIRST", "REFRAME_FIRST"})
        self.assertTrue(result["advisory"])
        self.assertTrue(result["override_available"])


class InquiryToolTests(unittest.TestCase):
    def test_interview_coach_is_story_first_and_nonblocking(self) -> None:
        result = coach_question("Wouldn't our AI assistant make this much easier?", solution_blackout=True)
        self.assertIn("LEADING", result["flags"])
        self.assertIn("SOLUTION_BLACKOUT_BREACH", result["flags"])
        self.assertIn("last time", result["suggested_alternative"].lower())
        self.assertFalse(result["blocking"])
        hypothetical = coach_question("Would you use an AI assistant for this?", solution_blackout=True)
        self.assertIn("HYPOTHETICAL_PREFERENCE", hypothetical["flags"])
        compound = coach_input(["What happened and how did you feel and what did you do?"])
        self.assertIn("COMPOUND", compound["results"][0]["flags"])

    def test_study_requires_ai_disclosure_and_minimizes_pii(self) -> None:
        with self.assertRaisesRegex(DesignCouncilError, "explicitly say"):
            create_study({"title": "Study", "research_goal": "Understand handoffs", "topics_to_cover": ["last handoff"], "consent": {"ai_disclosure": "A friendly interviewer"}})
        study = create_study({"title": "Handoff study", "research_goal": "Understand last handoffs", "topics_to_cover": ["last event"], "data_collected": ["anonymous participant ID", "text transcript"]})
        self.assertTrue(study["solution_blackout"])
        self.assertFalse(study["privacy_configuration"]["collect_names"])
        self.assertTrue(study["consent"]["may_stop"])
        self.assertEqual(study_warnings(study), [])

    def test_reality_packet_and_deep_persona(self) -> None:
        packet = researched_packet()
        validation = validate_reality_packet(packet, consequential=True)
        self.assertTrue(validation["valid_for_persona"], validation["errors"])
        persona = create_persona({
            "id": "SP-001",
            "participant_type": "SYNTHETIC_PRACTITIONER",
            "reality_packet": packet,
            "variation_dimensions": {"interruption_density": "high", "workflow_ownership": "shared"},
            "human_model": human_model(),
            "constructed_continuity": ["Keeps a repaired kitchen timer at home"],
            "limitations": ["Does not represent all nurses"],
        })
        self.assertEqual(persona["provenance"], "SYNTHETIC_PRACTITIONER")
        self.assertEqual(len(persona["epistemic_layers"]["DOMAIN_GROUNDING"]), 5)
        self.assertIn("Constructed continuity is fictional", " ".join(persona["limitations"]))
        with self.assertRaisesRegex(DesignCouncilError, "limitations must be an array"):
            create_persona({"participant_type": "SYNTHETIC_PRACTITIONER", "reality_packet": packet, "variation_dimensions": {"a": 1, "b": 2}, "human_model": human_model(), "limitations": "none"})

    def test_synthetic_convergence_warning_and_independence(self) -> None:
        transcripts = [
            {"participant_id": "SP-001", "provenance": "SYNTHETIC_USER", "response": "I check the school portal then message my partner before changing the calendar."},
            {"participant_id": "SP-002", "provenance": "SYNTHETIC_USER", "response": "I check the school portal then message my partner before changing the calendar."},
            {"participant_id": "SP-003", "provenance": "SYNTHETIC_USER", "response": "I check the school portal then message my partner before changing the calendar."},
        ]
        result = compare_participants({"transcripts": transcripts, "personas": [{"variation_dimensions": {"planning": "dense", "ownership": "shared"}}] * 3})
        self.assertEqual(result["warning"], "SYNTHETIC_CONVERGENCE_WARNING")
        self.assertIn("model convergence", result["possible_causes"])
        self.assertIn("not evidence", result["interpretation"])

    def test_evidence_audit_keeps_confidence_separate(self) -> None:
        records = [
            evidence("E-001", "SYNTHETIC_USER", 0, claim="A synthetic parent anticipates change-discovery friction", confidence=0.99),
            evidence("E-002", "USER_PROVIDED", 0, claim="The founder reports demand", confidence=0.97),
            evidence("E-003", "HUMAN_INTERVIEW", 4, claim="P-001 checked messages before a calendar", source_refs=["T-001#M-004"], study_id="STUDY-001", participant_id="P-001"),
        ]
        result = audit_evidence(records)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["direct_human_participant_count"], 1)
        promoted = copy.deepcopy(records[1])
        promoted["evidence_strength"] = 4
        bad = audit_evidence([promoted])
        self.assertFalse(bad["valid"])
        self.assertEqual(bad["errors"][0]["code"], "UNSUPPORTED_PROMOTION")

    def test_synthesis_keeps_layers_and_reality_check(self) -> None:
        findings = [
            {"id": "F-001", "statement": "Synthetic households anticipate frequent changes as the main burden", "finding_type": "insight_candidate", "provenance": "SYNTHETIC_USER", "source_refs": ["STUDY-SYN-001"], "scope": "synthetic study", "confidence": 0.7, "evidence_strength": 0, "contradicts": ["F-002"], "created_at": NOW},
            {"id": "F-002", "statement": "P-001 struggled most to discover a change", "finding_type": "contradiction", "provenance": "HUMAN_INTERVIEW", "source_refs": ["T-001#M-004"], "scope": "one participant", "confidence": 0.8, "evidence_strength": 4, "contradicts": ["F-001"], "created_at": NOW},
        ]
        result = synthesize_inquiry({"findings": findings})
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(len(result["layers"]["synthetic_signals"]), 1)
        self.assertEqual(len(result["layers"]["human_supported"]), 1)
        self.assertEqual(len(result["reality_check_candidates"]), 1)
        self.assertEqual(result["next_move"], "Run a Reality Check")


class SchemaTests(unittest.TestCase):
    def test_all_schemas_are_valid_draft_2020_12(self) -> None:
        try:
            import jsonschema
        except ImportError:  # pragma: no cover - requirements-dev installs it
            self.skipTest("jsonschema unavailable")
        for path in sorted((ROOT / "skills/mightshape/schemas").glob("*.json")):
            with self.subTest(schema=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                jsonschema.validators.validator_for(schema).check_schema(schema)

    def test_human_model_schema_resolves_local_reference(self) -> None:
        result = schema_validation(human_model(), "human-model.schema.json")
        self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
