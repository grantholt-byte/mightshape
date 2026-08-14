#!/usr/bin/env python3
"""Validate the current MightShape identity without breaking legacy data contracts."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
PRODUCT = BRAND["product"]
LEGACY = BRAND["legacy_contracts"]
DISPLAY_NAME = PRODUCT["display_name"]
PRODUCT_SLUG = PRODUCT["slug"]
FORMER_DISPLAY_NAME = LEGACY["former_display_name"]
FORMER_SLUG = LEGACY["former_slug"]
RETIRED_DISPLAY_NAMES = (FORMER_DISPLAY_NAME, *LEGACY.get("transitional_display_names", []))
RETIRED_SLUGS = (FORMER_SLUG, *LEGACY.get("transitional_slugs", []))
TEXT_SUFFIXES = {".json", ".md", ".py", ".svg", ".ts", ".tsx", ".yaml", ".yml", ".txt"}
DUPLICATE_COPY_RE = re.compile(r" \d+(?:$|(?=\.))")
FORMER_DISPLAY_RE = re.compile(
    "|".join(rf"\b{re.escape(name)}\b" for name in RETIRED_DISPLAY_NAMES),
    re.IGNORECASE,
)
FORMER_LINEAGE_RE = re.compile(r"\bdesign_council_original\b", re.IGNORECASE)
FORMER_PACKAGE_RE = re.compile(
    rf"(?:skills|dist/(?:openai|claude))/(?:{'|'.join(map(re.escape, RETIRED_SLUGS))})(?:/|\b)|"
    rf"\b(?:{'|'.join(map(re.escape, RETIRED_SLUGS))})(?::sealed-member|@(?:{'|'.join(map(re.escape, RETIRED_SLUGS))}))\b",
    re.IGNORECASE,
)

# These are deliberately narrow, machine-only migration shims. They preserve
# upgrades from the two retired package identities without allowing either name
# back into user-visible product copy or generated plugin packages.
APPROVED_COMPATIBILITY_LINES = {
    ".claude-plugin/marketplace.json": (
        re.compile(r'^\s*"(?:design-council|hunchgarden)"\s*:\s*"mightshape"\s*,?\s*$'),
    ),
    "collaboration-app/src/core/facilitator.ts": (
        re.compile(r'^\s*resolve\([^\n]*"[^"\n]*skills/hunchgarden/references/team-workshops\.md"\),\s*$'),
    ),
    "collaboration-app/src/core/visual.ts": (
        re.compile(r'^\s*resolve\(root, "skills/hunchgarden/scripts/render_visual\.py"\),\s*$'),
    ),
}


def is_duplicate(path: Path | PurePosixPath) -> bool:
    return any(DUPLICATE_COPY_RE.search(part) for part in path.parts)


def source_targets() -> tuple[Path, ...]:
    return (
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / "platforms" / "openai",
        ROOT / "platforms" / "claude",
        ROOT / "skills" / PRODUCT_SLUG,
        ROOT / "hooks",
        ROOT / "collaboration-app" / "src",
        ROOT / "collaboration-app" / "manifests",
        ROOT / "interview-app" / "app",
        ROOT / "interview-app" / "components",
        ROOT / "interview-app" / "lib",
        ROOT / "assets" / "icon.svg",
        ROOT / "assets" / "logo.svg",
        ROOT / "dist" / "openai" / PRODUCT_SLUG,
        ROOT / "dist" / "claude" / PRODUCT_SLUG,
    )


def iter_files(target: Path):
    if not target.exists():
        return
    if target.is_file():
        yield target
        return
    for path in sorted(target.rglob("*")):
        if path.is_file() and not is_duplicate(path.relative_to(target)):
            yield path


def inspect_text(content: str, label: str, findings: list[dict[str, object]]) -> None:
    for line_number, line in enumerate(content.splitlines(), start=1):
        if any(pattern.fullmatch(line) for pattern in APPROVED_COMPATIBILITY_LINES.get(label, ())):
            continue
        if FORMER_DISPLAY_RE.search(line):
            findings.append(
                {
                    "rule": "former display name in current runtime",
                    "path": label,
                    "line": line_number,
                }
            )
        if FORMER_LINEAGE_RE.search(line):
            findings.append(
                {
                    "rule": "former product lineage in current runtime",
                    "path": label,
                    "line": line_number,
                }
            )
        if FORMER_PACKAGE_RE.search(line):
            findings.append(
                {
                    "rule": "former package coordinate in current runtime",
                    "path": label,
                    "line": line_number,
                }
            )


def release_archives() -> tuple[Path, ...]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return tuple(ROOT / "dist" / f"{PRODUCT_SLUG}-{platform}-{version}.zip" for platform in ("openai", "claude"))


def manifest_findings() -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    checks = (
        (ROOT / ".codex-plugin" / "plugin.json", "name"),
        (ROOT / "platforms" / "claude" / "plugin.json", "name"),
        (ROOT / ".agents" / "plugins" / "marketplace.json", "name"),
        (ROOT / ".claude-plugin" / "marketplace.json", "name"),
    )
    for path, field in checks:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append({"rule": "identity manifest unreadable", "path": str(path.relative_to(ROOT)), "detail": str(exc)})
            continue
        if value.get(field) != PRODUCT_SLUG:
            findings.append(
                {
                    "rule": "current package slug mismatch",
                    "path": str(path.relative_to(ROOT)),
                    "detail": f"expected {PRODUCT_SLUG!r}, found {value.get(field)!r}",
                }
            )
    if PRODUCT_SLUG in RETIRED_SLUGS or DISPLAY_NAME.casefold() in {
        name.casefold() for name in RETIRED_DISPLAY_NAMES
    }:
        findings.append({"rule": "current and former identity must differ", "path": "brand.json"})
    if PRODUCT.get("primary_skill") != "design-think":
        findings.append({"rule": "stable invocation changed", "path": "brand.json"})
    if LEGACY.get("state_directory") != ".design-council" or LEGACY.get("provenance_value") != "DESIGN_COUNCIL":
        findings.append({"rule": "legacy state contract changed", "path": "brand.json"})
    return findings


def main() -> int:
    findings = manifest_findings()
    checked = 0
    for target in source_targets():
        for path in iter_files(target) or ():
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            checked += 1
            inspect_text(content, str(path.relative_to(ROOT)), findings)

    archive_entries = 0
    for archive_path in release_archives():
        if not archive_path.is_file():
            findings.append({"rule": "current release archive missing", "path": str(archive_path.relative_to(ROOT))})
            continue
        with zipfile.ZipFile(archive_path) as archive:
            roots = {PurePosixPath(item.filename).parts[0] for item in archive.infolist() if item.filename}
            if roots != {PRODUCT_SLUG}:
                findings.append(
                    {
                        "rule": "release root uses wrong product slug",
                        "path": str(archive_path.relative_to(ROOT)),
                        "detail": sorted(roots),
                    }
                )
            for item in archive.infolist():
                entry = PurePosixPath(item.filename)
                if item.is_dir() or is_duplicate(entry) or entry.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                try:
                    content = archive.read(item).decode("utf-8")
                except UnicodeDecodeError:
                    continue
                archive_entries += 1
                inspect_text(content, f"{archive_path.relative_to(ROOT)}!{item.filename}", findings)

    result = {
        "valid": not findings,
        "display_name": DISPLAY_NAME,
        "slug": PRODUCT_SLUG,
        "source_files_checked": checked,
        "archive_entries_checked": archive_entries,
        "findings": findings,
        "legacy_contracts_preserved": {
            "state_directory": LEGACY["state_directory"],
            "provenance_value": LEGACY["provenance_value"],
            "schema_id_host": LEGACY["schema_id_host"],
            "interview_consent_version": LEGACY["interview_consent_version"],
            "interview_resource_name": LEGACY["interview_resource_name"],
        },
    }
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
