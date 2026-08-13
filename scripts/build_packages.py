#!/usr/bin/env python3
"""Build deterministic OpenAI and Claude plugin packages from one core."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CANONICAL_SKILL = ROOT / "skills" / "design-council"
SHARED_PARTS = ("references", "schemas", "scripts", "assets")
PLATFORMS = ("openai", "claude")


def version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path, *extra_ignores: str) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".DS_Store", "* 2.*", *extra_ignores
        ),
    )


def normalized_manifest(source: Path) -> dict:
    value = json.loads(source.read_text(encoding="utf-8"))
    value["version"] = version()
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def package_readme(platform: str) -> str:
    invocation = "$design-council" if platform == "OpenAI / Codex" else "/design-council:design-council"
    return f"""# ◇ Design Council — {platform}

Think wider. Frame better. Build what matters.

This is the generated {platform} distribution of Design Council {version()}. Invoke
it with `{invocation}` or a matching natural-language request. Canonical source,
tests, research notes, privacy documentation, and the optional interview Site
live in the source repository from which this package was built.

Design Council is independent and is not affiliated with or endorsed by
Stanford University or the Stanford d.school.
"""


def build_openai(target: Path) -> None:
    write_json(target / ".codex-plugin" / "plugin.json", normalized_manifest(ROOT / ".codex-plugin" / "plugin.json"))
    copy_tree(ROOT / "assets", target / "assets", "concepts")
    copy_tree(ROOT / "hooks", target / "hooks")
    copy_tree(CANONICAL_SKILL, target / "skills" / "design-council")
    copy_file(ROOT / "LICENSE", target / "LICENSE")
    (target / "README.md").write_text(package_readme("OpenAI / Codex"), encoding="utf-8")


def build_claude(target: Path) -> None:
    write_json(target / ".claude-plugin" / "plugin.json", normalized_manifest(ROOT / "platforms" / "claude" / "plugin.json"))
    skill_target = target / "skills" / "design-council"
    skill_target.mkdir(parents=True)
    for part in SHARED_PARTS:
        copy_tree(CANONICAL_SKILL / part, skill_target / part)
    canonical = (CANONICAL_SKILL / "SKILL.md").read_text(encoding="utf-8").rstrip()
    appendix = (ROOT / "platforms" / "claude" / "adapter-appendix.md").read_text(encoding="utf-8")
    (skill_target / "SKILL.md").write_text(canonical + "\n" + appendix, encoding="utf-8")
    copy_tree(ROOT / "platforms" / "claude" / "agents", target / "agents")
    copy_tree(ROOT / "assets", target / "assets", "concepts")
    copy_file(ROOT / "LICENSE", target / "LICENSE")
    (target / "README.md").write_text(package_readme("Claude Code"), encoding="utf-8")


def zip_tree(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            info = zipfile.ZipInfo(str(path.relative_to(source.parent)))
            info.date_time = (2020, 1, 1, 0, 0, 0)
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_checksums() -> Path:
    checksum_path = DIST / "SHA256SUMS"
    # Only checksum the two canonical current-version outputs. Files such as
    # ``* 2.*`` are user-owned duplicate backups and must remain untouched and
    # absent from release metadata.
    archives = sorted(
        path for platform in PLATFORMS if (path := archive_target(platform)).is_file()
    )
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in archives]
    checksum_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return checksum_path


def package_target(platform: str) -> Path:
    return DIST / platform / "design-council"


def archive_target(platform: str) -> Path:
    return DIST / f"design-council-{platform}-{version()}.zip"


def clean_platform(platform: str) -> None:
    target = package_target(platform)
    archive = archive_target(platform)
    if target.exists():
        shutil.rmtree(target)
    if archive.exists():
        archive.unlink()


def clean_generated_dist() -> list[str]:
    """Remove generated package outputs without deleting unrelated dist files."""

    removed: list[str] = []
    for platform in PLATFORMS:
        target = package_target(platform)
        if target.exists():
            removed.append(str(target))
            shutil.rmtree(target)
    for platform in PLATFORMS:
        for archive in sorted(DIST.glob(f"design-council-{platform}-*.zip")):
            if " 2." in archive.name:
                continue
            removed.append(str(archive))
            archive.unlink()
    return removed


def build(clean: bool = False, platform: str = "all") -> dict:
    selected = PLATFORMS if platform == "all" else (platform,)
    if clean and platform == "all" and DIST.exists():
        clean_generated_dist()
    else:
        for name in selected:
            clean_platform(name)

    builders = {"openai": build_openai, "claude": build_claude}
    packages: dict[str, str] = {}
    archives: list[str] = []
    for name in selected:
        target = package_target(name)
        target.mkdir(parents=True)
        builders[name](target)
        archive = archive_target(name)
        zip_tree(target, archive)
        packages[name] = str(target)
        archives.append(str(archive))

    checksum_path = write_checksums()

    result = {
        "version": version(),
        "platforms": list(selected),
        "packages": packages,
        "archives": sorted(archives),
        "checksums": str(checksum_path),
    }
    # Preserve the original combined-build result keys for callers that use the
    # helper as a Python API while exposing the explicit platform map.
    result.update(packages)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--clean-only", action="store_true")
    parser.add_argument("--platform", choices=("all",) + PLATFORMS, default="all")
    args = parser.parse_args()
    if args.clean_only:
        if args.platform == "all" and DIST.exists():
            removed: str | list[str] = clean_generated_dist()
            write_checksums()
        else:
            removed = []
            for name in PLATFORMS if args.platform == "all" else (args.platform,):
                targets = (package_target(name), archive_target(name))
                removed.extend(str(target) for target in targets if target.exists())
                clean_platform(name)
            if DIST.exists():
                write_checksums()
        print(json.dumps({"removed": removed}, indent=2))
        return 0
    print(json.dumps(build(args.clean, args.platform), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
