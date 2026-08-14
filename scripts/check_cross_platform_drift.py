#!/usr/bin/env python3
"""Fail when generated platform packages drift from the shared product core."""

from __future__ import annotations

import hashlib
import json
import fnmatch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BRAND = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
PRODUCT_SLUG = BRAND["product"]["slug"]
CANONICAL = ROOT / "skills" / PRODUCT_SLUG
SHARED_PARTS = ("references", "schemas", "scripts", "assets")
INVARIANTS = (
    "sealed responses",
    "anonymous cross-pollination",
    "MINORITY REPORT",
    "evidence firewall",
    "SOLUTION BLACKOUT",
    "REALITY CHECK",
    "Design Debt",
    "Evidence Debt",
    "Assumption Burn-down",
    "Build Gate advisory",
    "build it anyway",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_map(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): digest(path)
        for part in SHARED_PARTS
        for path in sorted((root / part).rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and not fnmatch.fnmatch(path.name, "* 2.*")
    }


def check() -> dict:
    errors: list[str] = []
    packages = {
        "openai": DIST / "openai" / PRODUCT_SLUG / "skills" / PRODUCT_SLUG,
        "claude": DIST / "claude" / PRODUCT_SLUG / "skills" / PRODUCT_SLUG,
    }
    canonical_map = file_map(CANONICAL)
    for name, root in packages.items():
        if not root.exists():
            errors.append(f"{name} package is absent; run build_packages.py")
            continue
        current = file_map(root)
        if current != canonical_map:
            missing = sorted(set(canonical_map) - set(current))
            extra = sorted(set(current) - set(canonical_map))
            changed = sorted(path for path in set(current) & set(canonical_map) if current[path] != canonical_map[path])
            errors.append(f"{name} shared-core drift: missing={missing}, extra={extra}, changed={changed}")

    canonical_skill = (CANONICAL / "SKILL.md").read_text(encoding="utf-8").rstrip()
    openai_skill = (packages["openai"] / "SKILL.md").read_text(encoding="utf-8").rstrip() if packages["openai"].exists() else ""
    claude_skill = (packages["claude"] / "SKILL.md").read_text(encoding="utf-8") if packages["claude"].exists() else ""
    if openai_skill != canonical_skill:
        errors.append("OpenAI adapter SKILL.md is not the canonical entry point")
    if not claude_skill.startswith(canonical_skill):
        errors.append("Claude adapter does not preserve the complete canonical SKILL.md prefix")
    for marker in INVARIANTS:
        for name, text in (("openai", openai_skill), ("claude", claude_skill)):
            if marker.lower() not in text.lower():
                errors.append(f"{name} adapter lost invariant marker: {marker}")

    expected_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    version_files = {
        "openai": DIST / "openai" / PRODUCT_SLUG / ".codex-plugin" / "plugin.json",
        "claude": DIST / "claude" / PRODUCT_SLUG / ".claude-plugin" / "plugin.json",
        "claude_marketplace": ROOT / ".claude-plugin/marketplace.json",
    }
    versions = {}
    for name, path in version_files.items():
        value = json.loads(path.read_text(encoding="utf-8"))
        versions[name] = value.get("version")
        if value.get("version") != expected_version:
            errors.append(f"{name} version {value.get('version')!r} != {expected_version!r}")

    state_schema = (CANONICAL / "schemas/project-state.schema.json").read_text(encoding="utf-8").lower()
    if "claude" in state_schema or "codex" in state_schema or "openai" in state_schema:
        errors.append("canonical project state contains platform-specific fields")
    profiles = [path.name for path in (CANONICAL / "references").glob("council-*.md") if path.name not in {"council-protocol.md", "council-roster.md"}]
    if len(profiles) != 10:
        errors.append(f"expected ten canonical Human Models, found {len(profiles)}")
    return {
        "valid": not errors,
        "shared_file_count": len(canonical_map),
        "human_model_count": len(profiles),
        "versions": versions,
        "errors": errors,
    }


def main() -> int:
    result = check()
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
