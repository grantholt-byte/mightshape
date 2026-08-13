from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.export_benchmark_evidence import (
    EvidenceExportError,
    build_bundle,
    sha256_bytes,
    write_bundle,
)
from scripts.verify_v1_trajectory_gate import V1TrajectoryGateError


class ExportBenchmarkEvidenceTests(unittest.TestCase):
    def _run(self, root: Path, *, complete: bool = True) -> Path:
        run = root / "run-001"
        run.mkdir()
        manifest = {
            "run_id": "run-001",
            "planned_candidate_turn_calls": 8,
            "stdout": "must disappear",
        }
        summary = {
            "completion": {
                "realized_design_complete": complete,
                "judgment_plan_complete": complete,
            }
        }
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (run / "summary.md").write_text("# Result\n", encoding="utf-8")
        (run / "generations.jsonl").write_text(
            json.dumps({"response": "answer", "stderr": "private"}) + "\n",
            encoding="utf-8",
        )
        (run / "judgments.jsonl").write_text(
            json.dumps({"judgment": {"winner": "A"}, "environment": {"KEY": "secret"}})
            + "\n",
            encoding="utf-8",
        )
        (run / "blinded-pairs.jsonl").write_text(
            json.dumps({"candidate_a": "answer", "candidate_b": "other"}) + "\n",
            encoding="utf-8",
        )
        return run

    def _one_shot_run(self, root: Path, *, complete: bool = True) -> Path:
        run = self._run(root)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        manifest.pop("planned_candidate_turn_calls")
        manifest["planned_generation_calls"] = 48
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        summary = {
            "planned_pairs": 24,
            "complete_pairs": 24 if complete else 23,
            "realized_design": {
                "minimum_design_met": complete,
                "all_planned_pairs_usable": complete,
                "plan_shape_complete": True,
                "requested_repeats_realized": complete,
                "requested_judgments_realized": complete,
            },
        }
        (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        return run

    def test_bundle_retains_outcomes_and_removes_process_streams(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, files = build_bundle(self._run(root))
            self.assertEqual(run_id, "run-001")
            self.assertIn(b'"response":"answer"', files["generations.jsonl"])
            self.assertNotIn(b"stderr", files["generations.jsonl"])
            self.assertNotIn(b"environment", files["judgments.jsonl"])
            self.assertNotIn(b"must disappear", files["manifest.json"])
            self.assertIn(sha256_bytes(files["summary.json"]).encode(), files["SHA256SUMS"])

    def test_incomplete_run_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(EvidenceExportError, "complete realized"):
                build_bundle(self._run(Path(temporary), complete=False))

    def test_v1_gate_is_fail_closed_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, patch(
            "scripts.export_benchmark_evidence.require_v1_trajectory_gate",
            side_effect=V1TrajectoryGateError(
                "V1 trajectory gate failed: dirty source"
            ),
        ):
            with self.assertRaisesRegex(EvidenceExportError, "dirty source"):
                build_bundle(self._run(Path(temporary)), require_v1_gate=True)

    def test_v1_gate_receipt_is_embedded_when_requested(self) -> None:
        receipt = {
            "policy_id": "policy",
            "policy_sha256": "a" * 64,
            "source_commit": "b" * 40,
            "passed": True,
        }
        with tempfile.TemporaryDirectory() as temporary, patch(
            "scripts.export_benchmark_evidence.require_v1_trajectory_gate",
            return_value=receipt,
        ):
            _, files = build_bundle(
                self._run(Path(temporary)), require_v1_gate=True
            )
            evidence_manifest = json.loads(files["evidence-manifest.json"])
            self.assertTrue(evidence_manifest["v1_trajectory_gate"]["verified"])
            self.assertEqual(
                json.loads(files["v1-trajectory-gate.json"])["source_commit"],
                "b" * 40,
            )

    def test_complete_one_shot_run_uses_its_native_completion_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_id, files = build_bundle(self._one_shot_run(Path(temporary)))
            self.assertEqual(run_id, "run-001")
            evidence_manifest = json.loads(files["evidence-manifest.json"])
            self.assertEqual(evidence_manifest["benchmark_kind"], "one_shot_ab")

    def test_incomplete_one_shot_run_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(EvidenceExportError, "complete realized"):
                build_bundle(
                    self._one_shot_run(Path(temporary), complete=False)
                )

    def test_write_is_immutable_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, files = build_bundle(self._run(root))
            destination = write_bundle(root / "evidence", run_id, files)
            self.assertTrue((destination / "SHA256SUMS").is_file())
            with self.assertRaisesRegex(EvidenceExportError, "already exists"):
                write_bundle(root / "evidence", run_id, files)


if __name__ == "__main__":
    unittest.main()
