from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RuntimeBrandingBoundaryTests(unittest.TestCase):
    def test_runtime_and_generated_packages_have_no_restricted_positioning(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/check_runtime_branding.py"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertTrue(result["valid"], result["findings"])
        self.assertEqual(result["findings"], [])

    def test_registry_uses_neutral_lineage_categories(self) -> None:
        registry = json.loads(
            (ROOT / "skills/mightshape/references/method-registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            set(registry["source_families"]),
            {
                "public_design_practice",
                "supplemental_design_practice",
                "mightshape_original",
            },
        )
        self.assertTrue(
            all(
                method["source_family"] in registry["source_families"]
                for method in registry["methods"]
            )
        )


if __name__ == "__main__":
    unittest.main()
