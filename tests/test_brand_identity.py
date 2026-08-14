from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrandIdentityTests(unittest.TestCase):
    def test_current_identity_and_legacy_contracts_are_explicit(self) -> None:
        brand = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
        self.assertEqual(brand["product"]["display_name"], "MightShape")
        self.assertEqual(brand["product"]["slug"], "mightshape")
        self.assertEqual(brand["product"]["primary_skill"], "design-think")
        self.assertEqual(brand["legacy_contracts"]["state_directory"], ".design-council")
        self.assertEqual(brand["legacy_contracts"]["provenance_value"], "DESIGN_COUNCIL")
        self.assertEqual(brand["legacy_contracts"]["schema_id_host"], "design-council.local")
        self.assertEqual(
            brand["legacy_contracts"]["interview_consent_version"],
            "design-council-live-interview-v1",
        )

    def test_source_manifests_use_the_new_package_identity(self) -> None:
        openai = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / "platforms/claude/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual((openai["name"], openai["interface"]["displayName"]), ("mightshape", "MightShape"))
        self.assertEqual((claude["name"], claude["displayName"]), ("mightshape", "MightShape"))

    def test_method_registry_uses_the_new_original_lineage(self) -> None:
        registry = json.loads(
            (ROOT / "skills/mightshape/references/method-registry.json").read_text(encoding="utf-8")
        )
        self.assertIn("mightshape_original", registry["source_families"])
        self.assertNotIn("design_council_original", registry["source_families"])


if __name__ == "__main__":
    unittest.main()
