#!/usr/bin/env python3
"""Fail when restricted third-party positioning leaks into runtime packages.

Maintainer-only legal/source records intentionally live outside these targets.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
PRODUCT_SLUG = BRAND["product"]["slug"]
TEXT_SUFFIXES = {".json", ".md", ".py", ".svg", ".yaml", ".yml", ".txt", ".toml"}
BANNED_BUNDLED_SUFFIXES = {".pdf", ".ppt", ".pptx", ".key"}
DUPLICATE_COPY_RE = re.compile(r" \d+(?:$|(?=\.))")
FORBIDDEN = {
    "institution name": re.compile(r"\bstanford\b", re.IGNORECASE),
    "institution unit": re.compile(r"\bd[.\-]?school\b|\bdschool\b", re.IGNORECASE),
    "legacy source family": re.compile(r"stanford_dschool", re.IGNORECASE),
    "branded resource name": re.compile(r"design thinking bootleg", re.IGNORECASE),
    "branded sticky note": re.compile(r"\bpost[ -]?it(?:®|™)?\b", re.IGNORECASE),
}

TARGETS = (
    Path(".codex-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path("platforms/claude/plugin.json"),
    Path("platforms/claude/adapter-appendix.md"),
    Path("platforms/claude/standalone-alias"),
    Path("skills") / PRODUCT_SLUG,
    Path("scripts/build_packages.py"),
    Path("collaboration-app/src"),
    Path("collaboration-app/manifests"),
    Path("interview-app/app"),
    Path("interview-app/lib"),
    Path("dist/openai") / PRODUCT_SLUG,
    Path("dist/claude") / PRODUCT_SLUG,
)


def release_archives() -> tuple[Path, ...]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return tuple(
        ROOT / "dist" / f"{PRODUCT_SLUG}-{platform}-{version}.zip"
        for platform in ("openai", "claude")
    )


def runtime_files(target: Path):
    absolute = ROOT / target
    if not absolute.exists():
        return
    if absolute.is_file():
        yield absolute
        return
    for path in sorted(absolute.rglob("*")):
        relative = path.relative_to(absolute)
        if any(DUPLICATE_COPY_RE.search(part) for part in relative.parts):
            continue
        if path.is_file():
            yield path


def main() -> int:
    findings: list[dict[str, object]] = []
    checked: set[Path] = set()
    for target in TARGETS:
        for path in runtime_files(target) or ():
            resolved = path.resolve()
            if resolved in checked:
                continue
            checked.add(resolved)
            if path.suffix.lower() in BANNED_BUNDLED_SUFFIXES:
                findings.append(
                    {
                        "rule": "bundled third-party course/document format",
                        "path": str(path.relative_to(ROOT)),
                        "line": None,
                    }
                )
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                for label, pattern in FORBIDDEN.items():
                    if pattern.search(line):
                        findings.append(
                            {
                                "rule": label,
                                "path": str(path.relative_to(ROOT)),
                                "line": line_number,
                            }
                        )

    archive_entries_checked = 0
    for archive_path in release_archives():
        if not archive_path.exists():
            findings.append(
                {
                    "rule": "release archive missing",
                    "path": str(archive_path.relative_to(ROOT)),
                    "line": None,
                }
            )
            continue
        with zipfile.ZipFile(archive_path) as archive:
            for entry in archive.infolist():
                if entry.is_dir():
                    continue
                entry_path = PurePosixPath(entry.filename)
                if any(DUPLICATE_COPY_RE.search(part) for part in entry_path.parts):
                    continue
                archive_entries_checked += 1
                display_path = f"{archive_path.relative_to(ROOT)}!{entry.filename}"
                suffix = entry_path.suffix.lower()
                if suffix in BANNED_BUNDLED_SUFFIXES:
                    findings.append(
                        {
                            "rule": "bundled third-party course/document format",
                            "path": display_path,
                            "line": None,
                        }
                    )
                    continue
                if suffix not in TEXT_SUFFIXES:
                    continue
                try:
                    content = archive.read(entry).decode("utf-8")
                except UnicodeDecodeError:
                    continue
                for line_number, line in enumerate(content.splitlines(), start=1):
                    for label, pattern in FORBIDDEN.items():
                        if pattern.search(line):
                            findings.append(
                                {
                                    "rule": label,
                                    "path": display_path,
                                    "line": line_number,
                                }
                            )

    result = {
        "valid": not findings,
        "files_checked": len(checked) + archive_entries_checked,
        "release_archive_entries_checked": archive_entries_checked,
        "findings": findings,
        "scope": [str(path) for path in TARGETS],
        "release_archives": [str(path.relative_to(ROOT)) for path in release_archives()],
        "note": "Maintainer legal/source records are deliberately outside runtime-package scope.",
    }
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
