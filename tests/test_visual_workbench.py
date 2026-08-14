"""Tests for accessible, evidence-safe visual workshop rendering."""

from __future__ import annotations

import json
import hashlib
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "mightshape" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dc_core import DesignCouncilError, schema_validation  # noqa: E402
from render_visual import (  # noqa: E402
    open_artifact,
    render_artifact,
    validate_artifact,
    write_artifact,
)


def affinity_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "id": "VA-001",
        "artifact_type": "AFFINITY_MAP",
        "title": "Family coordination evidence wall",
        "summary": "Notes cluster around discovery, authority, and recovery.",
        "summary_provenance": "DESIGN_COUNCIL",
        "summary_record_ids": ["N-001", "N-002", "N-003", "N-004"],
        "mode": "DEFINE",
        "cycle": 1,
        "limitations": ["P-001 contributes two of the four notes."],
        "data": {
            "clusters": [
                {
                    "id": "CLUSTER-001",
                    "label": "Changes are discovered late",
                    "description": "Incoming commitments arrive through unrelated channels.",
                    "interpretation_provenance": "DESIGN_COUNCIL",
                    "record_ids": ["N-001", "N-002"],
                    "notes": [
                        {
                            "id": "N-001",
                            "text": "P-001 checked a school message before opening the calendar.",
                            "provenance": "HUMAN_INTERVIEW",
                            "source_ids": ["T-001#M-004"],
                        },
                        {
                            "id": "N-002",
                            "text": "Information capture may be the pivotal failure.",
                            "provenance": "RESEARCH_SUPPORTED_INFERENCE",
                            "source_ids": ["E-011", "E-014"],
                        },
                    ],
                },
                {
                    "id": "CLUSTER-002",
                    "label": "Decision ownership is ambiguous",
                    "interpretation_provenance": "DESIGN_COUNCIL",
                    "record_ids": ["N-003"],
                    "notes": [
                        {
                            "id": "N-003",
                            "text": "Automatic rescheduling will be welcomed.",
                            "provenance": "ASSUMPTION",
                            "source_ids": [],
                        }
                    ],
                },
            ],
            "outliers": [
                {
                    "id": "N-004",
                    "text": "One household wants conflicts surfaced but no scheduling recommendation.",
                    "provenance": "HUMAN_INTERVIEW",
                    "source_ids": ["T-002#M-008"],
                }
            ],
        },
    }


def process_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "id": "VA-002",
        "artifact_type": "PROCESS_MAP",
        "title": "Schedule-change discovery process",
        "summary": "A change crosses parent and school-system lanes before calendar reconciliation.",
        "summary_provenance": "DESIGN_COUNCIL",
        "summary_record_ids": ["STEP-001", "STEP-002", "STEP-003", "FLOW-001", "FLOW-002"],
        "mode": "EMPATHIZE",
        "cycle": 1,
        "limitations": ["The exception branch is based on one interview."],
        "data": {
            "lanes": [
                {"id": "LANE-PARENT", "label": "Parent"},
                {"id": "LANE-SCHOOL", "label": "School system"},
            ],
            "steps": [
                {
                    "id": "STEP-001",
                    "label": "Activity time changes",
                    "detail": "Staff update the school portal.",
                    "lane_id": "LANE-SCHOOL",
                    "provenance": "AUTHORITATIVE_RESEARCH",
                    "source_ids": ["SRC-001"],
                },
                {
                    "id": "STEP-002",
                    "label": "Parent discovers message",
                    "detail": "The message is found during an unrelated check.",
                    "lane_id": "LANE-PARENT",
                    "provenance": "HUMAN_INTERVIEW",
                    "source_ids": ["T-001#M-004"],
                },
                {
                    "id": "STEP-003",
                    "label": "Calendar is reconciled",
                    "detail": "Authority for changing shared commitments is unclear.",
                    "lane_id": "LANE-PARENT",
                    "provenance": "ASSUMPTION",
                    "source_ids": [],
                },
            ],
            "transitions": [
                {
                    "id": "FLOW-001",
                    "from_step_id": "STEP-001",
                    "to_step_id": "STEP-002",
                    "label": "notification",
                    "provenance": "HUMAN_INTERVIEW",
                    "source_ids": ["T-001#M-004"],
                },
                {
                    "id": "FLOW-002",
                    "from_step_id": "STEP-002",
                    "to_step_id": "STEP-003",
                    "label": "manual update or exception",
                    "provenance": "ASSUMPTION",
                    "source_ids": [],
                },
            ],
        },
    }


class VisualWorkbenchTests(unittest.TestCase):
    def test_affinity_map_preserves_outlier_and_provenance_in_every_format(self) -> None:
        result = render_artifact(affinity_artifact())
        self.assertEqual(result["record_count"], 4)
        self.assertEqual(result["provenance_counts"]["HUMAN_INTERVIEW"], 2)
        for output in (result["svg"], result["html"]):
            with self.subTest(format=output[:20]):
                self.assertIn("N-004", output)
                self.assertIn("outliers", output.lower())
                self.assertIn("Human interview", output)
                self.assertIn("T-002#M-008", output)
        self.assertIn(r"N\-004", result["markdown"])
        self.assertIn("outliers", result["markdown"].lower())
        self.assertIn("Human interview", result["markdown"])
        self.assertIn(r"T\-002\#M\-008", result["markdown"])
        self.assertIn('role="img"', result["svg"])
        self.assertIn('class="sticky-note"', result["svg"])
        self.assertIn('class="dog-ear"', result["svg"])
        self.assertIn('class="tape"', result["svg"])
        self.assertIn('class="cluster-zone"', result["svg"])
        self.assertIn("Facilitator interpretation", result["svg"])
        self.assertIn("Complete text view", result["html"])
        self.assertIn("Content-Security-Policy", result["html"])
        self.assertNotIn('href="http', result["html"].lower())
        self.assertNotIn('src="http', result["html"].lower())
        self.assertNotIn("<script", result["html"].lower())

    def test_process_map_shows_lanes_branches_sources_and_text_fallback(self) -> None:
        result = render_artifact(process_artifact())
        self.assertIn("Parent", result["svg"])
        self.assertIn("School system", result["svg"])
        self.assertIn('data-transition="FLOW-001"', result["svg"])
        self.assertIn("<polygon", result["svg"])
        self.assertIn("manual update or exception", result["svg"])
        self.assertIn("FLOW-001", result["svg"])
        self.assertIn("T-001#M-004", result["svg"])
        self.assertIn(r"STEP\-001 → STEP\-002", result["markdown"])
        self.assertIn("AUTHORITATIVE_RESEARCH", result["markdown"])
        self.assertIn("<table>", result["html"])
        self.assertIn('class="process-card"', result["svg"])
        self.assertIn('class="flow-path"', result["svg"])
        self.assertIn('class="process-lane"', result["svg"])

    def test_affinity_cluster_description_is_not_lost_in_any_format(self) -> None:
        result = render_artifact(affinity_artifact())
        self.assertIn("Incoming commitments arrive through", result["svg"])
        self.assertIn("unrelated channels.", result["svg"])
        self.assertIn("Incoming commitments arrive through unrelated channels.", result["html"])
        self.assertIn(r"Incoming commitments arrive through unrelated channels\.", result["markdown"])

    def test_renderer_escapes_untrusted_content_in_html_and_svg(self) -> None:
        artifact = affinity_artifact()
        artifact["title"] = "<script>alert('x')</script>"
        artifact["data"]["clusters"][0]["notes"][0]["text"] = '<img src=x onerror="alert(1)">'
        result = render_artifact(artifact)
        for output in (result["html"], result["svg"]):
            self.assertNotIn("<script>alert", output)
            self.assertNotIn("<img src=x", output)
            self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("onerror=\"alert(1)\"", result["html"])

    def test_evidence_bearing_record_requires_traceable_source(self) -> None:
        artifact = affinity_artifact()
        artifact["data"]["clusters"][0]["notes"][0]["source_ids"] = []
        with self.assertRaisesRegex(DesignCouncilError, "has no source_ids"):
            validate_artifact(artifact)

    def test_process_rejects_unknown_lane_and_transition_endpoint(self) -> None:
        bad_lane = process_artifact()
        bad_lane["data"]["steps"][0]["lane_id"] = "LANE-MISSING"
        with self.assertRaisesRegex(DesignCouncilError, "unknown lane"):
            validate_artifact(bad_lane)
        bad_transition = process_artifact()
        bad_transition["data"]["transitions"][0]["to_step_id"] = "STEP-MISSING"
        with self.assertRaisesRegex(DesignCouncilError, "unknown step"):
            validate_artifact(bad_transition)

    def test_rendering_is_deterministic_and_artifacts_are_immutable(self) -> None:
        first = render_artifact(affinity_artifact())
        second = render_artifact(affinity_artifact())
        self.assertEqual(first["svg"], second["svg"])
        self.assertEqual(first["html"], second["html"])
        self.assertEqual(first["markdown"], second["markdown"])
        with tempfile.TemporaryDirectory() as temporary:
            paths = write_artifact(first, temporary)
            self.assertEqual(set(paths), {"source", "html", "svg", "markdown", "manifest"})
            self.assertTrue(all(Path(path).is_file() for path in paths.values()))
            manifest = json.loads(Path(paths["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["input_sha256"], first["input_sha256"])
            self.assertEqual(manifest["source_ids"], first["source_ids"])
            self.assertEqual(json.loads(Path(paths["source"]).read_text(encoding="utf-8")), affinity_artifact())
            for key in ("source", "html", "svg", "markdown"):
                actual = hashlib.sha256(Path(paths[key]).read_bytes()).hexdigest()
                self.assertEqual(manifest["file_sha256"][key], actual)
            for path in paths.values():
                self.assertEqual(Path(path).stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH), 0)
            with self.assertRaisesRegex(DesignCouncilError, "Refusing to overwrite"):
                write_artifact(first, temporary)

    def test_synthesis_interpretations_must_reference_the_records_they_summarize(self) -> None:
        bad_summary = affinity_artifact()
        bad_summary["summary_record_ids"] = ["N-MISSING"]
        with self.assertRaisesRegex(DesignCouncilError, "summary_record_ids references unknown"):
            validate_artifact(bad_summary)

        bad_cluster = affinity_artifact()
        bad_cluster["data"]["clusters"][0]["record_ids"] = ["N-003"]
        with self.assertRaisesRegex(DesignCouncilError, "outside this cluster"):
            validate_artifact(bad_cluster)

        incomplete_cluster = affinity_artifact()
        incomplete_cluster["data"]["clusters"][0]["record_ids"] = ["N-001"]
        with self.assertRaisesRegex(DesignCouncilError, "include every clustered note"):
            validate_artifact(incomplete_cluster)

    def test_manual_validator_enforces_schema_limits_and_closed_objects(self) -> None:
        cases = []
        wrong_summary_provenance = affinity_artifact()
        wrong_summary_provenance["summary_provenance"] = "HUMAN_INTERVIEW"
        cases.append((wrong_summary_provenance, "summary_provenance must be DESIGN_COUNCIL"))
        wrong_cluster_provenance = affinity_artifact()
        wrong_cluster_provenance["data"]["clusters"][0]["interpretation_provenance"] = "ASSUMPTION"
        cases.append((wrong_cluster_provenance, "interpretation_provenance must be DESIGN_COUNCIL"))
        extra_root = affinity_artifact()
        extra_root["secret"] = "not allowed"
        cases.append((extra_root, "root contains unsupported properties"))
        extra_note = affinity_artifact()
        extra_note["data"]["clusters"][0]["notes"][0]["confidence"] = 1
        cases.append((extra_note, "contains unsupported properties"))
        long_title = affinity_artifact()
        long_title["title"] = "x" * 201
        cases.append((long_title, "title exceeds maximum length 200"))
        bad_mode = affinity_artifact()
        bad_mode["mode"] = "DISCOVER"
        cases.append((bad_mode, "mode must be one of"))
        bad_cycle = affinity_artifact()
        bad_cycle["cycle"] = 0
        cases.append((bad_cycle, "cycle must be an integer"))
        duplicate_limitations = affinity_artifact()
        duplicate_limitations["limitations"] = ["same", "same"]
        cases.append((duplicate_limitations, "limitations contains duplicates"))
        for artifact, message in cases:
            with self.subTest(message=message):
                self.assertFalse(schema_validation(artifact, "visual-artifact.schema.json")["valid"])
                with self.assertRaisesRegex(DesignCouncilError, message):
                    validate_artifact(artifact)

    def test_markdown_fallback_neutralizes_remote_link_and_image_syntax(self) -> None:
        artifact = affinity_artifact()
        payload = "![](https://tracker.example/pixel.png) [click](https://bad.example) # heading *bold*"
        artifact["title"] = payload
        artifact["data"]["clusters"][0]["label"] = payload
        artifact["data"]["clusters"][0]["notes"][0]["text"] = payload + "\n- injected list"
        result = render_artifact(artifact)
        self.assertNotIn("![](https://", result["markdown"])
        self.assertNotIn("](https://", result["markdown"])
        self.assertNotIn("\n- injected list", result["markdown"])
        self.assertIn(r"\!\[\]\(https://tracker\.example/pixel\.png\)", result["markdown"])
        self.assertRegex(result["markdown"], r"!\[.*\]\(va-001-[a-z0-9-]+\.svg\)")

    def test_browser_is_only_used_by_explicit_open_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rendered = render_artifact(process_artifact())
            paths = write_artifact(rendered, temporary)
            with patch("render_visual.webbrowser.open", return_value=True) as opener:
                self.assertTrue(open_artifact(paths["html"]))
                opener.assert_called_once()
                self.assertTrue(opener.call_args.args[0].startswith("file://"))

    def test_visual_artifact_schema_accepts_both_types(self) -> None:
        for artifact in (affinity_artifact(), process_artifact()):
            with self.subTest(artifact_type=artifact["artifact_type"]):
                result = schema_validation(artifact, "visual-artifact.schema.json")
                self.assertTrue(result["valid"], result["errors"])

    def test_note_and_step_detail_share_the_2000_character_limit(self) -> None:
        cases = (
            (
                "affinity note",
                affinity_artifact,
                lambda artifact, value: artifact["data"]["clusters"][0]["notes"][0].__setitem__("text", value),
            ),
            (
                "process step detail",
                process_artifact,
                lambda artifact, value: artifact["data"]["steps"][0].__setitem__("detail", value),
            ),
        )

        for label, factory, set_value in cases:
            with self.subTest(record=label, length=2000):
                artifact = factory()
                accepted_value = "x" * 2000
                set_value(artifact, accepted_value)
                schema_result = schema_validation(artifact, "visual-artifact.schema.json")
                self.assertTrue(schema_result["valid"], schema_result["errors"])
                validate_artifact(artifact)
                rendered = render_artifact(artifact)
                self.assertIn(accepted_value, rendered["html"])

            with self.subTest(record=label, length=2001):
                artifact = factory()
                set_value(artifact, "x" * 2001)
                schema_result = schema_validation(artifact, "visual-artifact.schema.json")
                self.assertFalse(schema_result["valid"])
                with self.assertRaisesRegex(DesignCouncilError, "exceeds maximum length 2000"):
                    validate_artifact(artifact)

    def test_cli_input_contract_remains_json_serializable(self) -> None:
        for artifact in (affinity_artifact(), process_artifact()):
            self.assertEqual(json.loads(json.dumps(artifact)), artifact)

    def test_shipped_examples_validate_and_render(self) -> None:
        examples = ROOT / "skills/mightshape/assets/examples"
        for path in sorted(path for path in examples.glob("*.json") if " 2." not in path.name):
            with self.subTest(example=path.name):
                artifact = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(schema_validation(artifact, "visual-artifact.schema.json")["valid"])
                rendered = render_artifact(artifact)
                self.assertTrue(rendered["html"].startswith("<!doctype html>"))
                self.assertNotIn("HUMAN_INTERVIEW", rendered["provenance_counts"])
                self.assertNotIn("OBSERVED_HUMAN_BEHAVIOR", rendered["provenance_counts"])
                limitation_text = " ".join(artifact["limitations"]).lower()
                self.assertIn("illustrative", limitation_text)
                self.assertTrue("not verified" in limitation_text or "not observation" in limitation_text)


if __name__ == "__main__":
    unittest.main()
