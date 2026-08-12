from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InterviewPersistenceContractTests(unittest.TestCase):
    def test_late_model_turn_cannot_write_after_participant_stop(self) -> None:
        repository = (ROOT / "interview-app/lib/repository.ts").read_text(
            encoding="utf-8"
        )
        route = (
            ROOT / "interview-app/app/api/studies/[token]/messages/route.ts"
        ).read_text(encoding="utf-8")

        save_block = repository.split(
            "export async function saveInterviewTurn", 1
        )[1].split("export async function stopParticipant", 1)[0]
        guard = "status = 'ACTIVE' AND processing = 1"
        self.assertGreaterEqual(save_block.count(guard), 3)
        self.assertIn("const results = await db.batch", save_block)
        self.assertIn("results[2]?.meta.changes", save_block)
        self.assertIn("const committed = await saveInterviewTurn", route)
        self.assertIn("if (!committed)", route)
        self.assertIn('status: "STOPPED"', route)
        self.assertIn("No late response was added", route)


if __name__ == "__main__":
    unittest.main()
