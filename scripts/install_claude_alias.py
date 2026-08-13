#!/usr/bin/env python3
"""Install the optional exact `/design-think` alias for Claude Code.

The alias delegates to the installed Design Council plugin. It does not copy the product core.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "platforms" / "claude" / "standalone-alias" / "design-think" / "SKILL.md"


class AliasInstallError(RuntimeError):
    """Raised when an alias install would be unsafe or incomplete."""


def target_skill_dir(*, scope: str, project_root: Path | None = None) -> Path:
    if scope == "user":
        return Path.home() / ".claude" / "skills" / "design-think"
    if scope == "project":
        if project_root is None:
            raise AliasInstallError("--project-root is required for project scope")
        return project_root.resolve() / ".claude" / "skills" / "design-think"
    raise AliasInstallError(f"unsupported scope: {scope}")


def install_alias(*, target_dir: Path, force: bool = False) -> dict[str, object]:
    if not SOURCE.is_file():
        raise AliasInstallError(f"alias source is missing: {SOURCE}")

    source_bytes = SOURCE.read_bytes()
    target = target_dir / "SKILL.md"
    if target.exists():
        if not target.is_file():
            raise AliasInstallError(f"target exists and is not a file: {target}")
        if target.read_bytes() == source_bytes:
            return {"status": "UNCHANGED", "path": str(target), "delegates_to": "design-council:design-think"}
        if not force:
            raise AliasInstallError(
                f"refusing to overwrite an existing alias: {target}; rerun with --force only after review"
            )

    target_dir.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".SKILL.md.", dir=target_dir)
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(source_bytes)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, target)
    finally:
        temporary_path = Path(temporary_name)
        if temporary_path.exists():
            temporary_path.unlink()

    return {"status": "INSTALLED", "path": str(target), "delegates_to": "design-council:design-think"}


def uninstall_alias(*, target_dir: Path) -> dict[str, object]:
    """Remove only the unmodified alias shipped by this checkout.

    A changed or foreign skill is user-owned data. Refuse to delete it, and never
    remove sibling files that may share the skill directory.
    """

    if not SOURCE.is_file():
        raise AliasInstallError(f"alias source is missing: {SOURCE}")

    target = target_dir / "SKILL.md"
    if not target.exists():
        return {"status": "NOT_INSTALLED", "path": str(target)}
    if not target.is_file():
        raise AliasInstallError(f"target exists and is not a file: {target}")
    if target.read_bytes() != SOURCE.read_bytes():
        raise AliasInstallError(
            f"refusing to remove a modified or foreign alias: {target}; review and remove it manually"
        )

    target.unlink()
    try:
        target_dir.rmdir()
    except OSError:
        # Preserve sibling files and non-empty directories.
        pass
    return {"status": "REMOVED", "path": str(target)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install an exact /design-think Claude alias that delegates to the installed Design Council plugin."
    )
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project-root", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--force", action="store_true", help="replace a reviewed, conflicting alias")
    action.add_argument(
        "--uninstall",
        action="store_true",
        help="remove the alias only when it still exactly matches this checkout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        target_dir = target_skill_dir(scope=args.scope, project_root=args.project_root)
        if args.uninstall:
            result = uninstall_alias(target_dir=target_dir)
        else:
            result = install_alias(target_dir=target_dir, force=args.force)
    except AliasInstallError as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
