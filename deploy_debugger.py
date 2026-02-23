#!/usr/bin/env python3
"""Deploy this repository's index.html to Proffix REST API debugger.html files.

Usage:
  python deploy_debugger.py
  python deploy_debugger.py --dry-run
  python deploy_debugger.py --assemblies "C:\\Program Files\\Proffix REST API\\Proffix REST API\\Assemblies"
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, List

SEMVER_DIR_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy ./index.html into debugger.html for all detected Proffix API versions."
    )
    parser.add_argument(
        "--assemblies",
        action="append",
        default=[],
        type=Path,
        help="Explicit Assemblies folder path (can be passed multiple times)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be updated; do not copy files.",
    )
    return parser.parse_args()


def candidate_assemblies_dirs(explicit: Iterable[Path]) -> List[Path]:
    candidates: List[Path] = list(explicit)

    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(
                Path(program_files)
                / "Proffix REST API"
                / "Proffix REST API"
                / "Assemblies"
            )
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/Applications/Proffix REST API/Proffix REST API/Assemblies"),
                Path.home()
                / "Applications"
                / "Proffix REST API"
                / "Proffix REST API"
                / "Assemblies",
            ]
        )
    else:
        candidates.extend(
            [
                Path("/opt/proffix-rest-api/Assemblies"),
                Path("/usr/local/proffix-rest-api/Assemblies"),
            ]
        )

    existing: List[Path] = []
    seen = set()
    for path in candidates:
        resolved = path.expanduser().resolve()
        key = os.path.normcase(str(resolved))
        if key in seen or not resolved.is_dir():
            continue
        seen.add(key)
        existing.append(resolved)
    return existing


def discover_version_dirs(assemblies_dir: Path) -> List[Path]:
    versions = [
        p
        for p in assemblies_dir.iterdir()
        if p.is_dir() and SEMVER_DIR_RE.match(p.name)
    ]
    return sorted(versions, key=lambda p: str(p).lower())


def destination_for_version(version_dir: Path) -> Path:
    modern = version_dir / "debugger" / "index.html"
    if modern.parent.is_dir():
        return modern
    return version_dir / "debugger.html"


def deploy(source_file: Path, version_dirs: Iterable[Path], dry_run: bool) -> int:
    updated = 0
    for version_dir in version_dirs:
        destination = destination_for_version(version_dir)
        if dry_run:
            print(f"[DRY-RUN] Would write: {destination}")
        else:
            shutil.copy2(source_file, destination)
            print(f"Updated: {destination}")
        updated += 1
    return updated


def main() -> int:
    args = parse_args()

    source_file = (Path(__file__).resolve().parent / "index.html").resolve()
    if not source_file.is_file():
        print(f"ERROR: Source file not found: {source_file}", file=sys.stderr)
        return 2

    assemblies_dirs = candidate_assemblies_dirs(args.assemblies)
    if not assemblies_dirs:
        print(
            "ERROR: Could not find an Assemblies directory. "
            "Use --assemblies <path>.",
            file=sys.stderr,
        )
        return 3

    all_targets: List[Path] = []
    for assemblies_dir in assemblies_dirs:
        all_targets.extend(discover_version_dirs(assemblies_dir))

    if not all_targets:
        print(
            "ERROR: No Proffix version folders found under Assemblies.",
            file=sys.stderr,
        )
        return 4

    total = deploy(source_file, all_targets, args.dry_run)
    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {total} version(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
