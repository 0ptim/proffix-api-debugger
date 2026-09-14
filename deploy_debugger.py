#!/usr/bin/env python3
"""Deploy the debugger and its assets to Proffix REST API installations.

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
import tempfile
from pathlib import Path
from typing import Iterable, List

SEMVER_DIR_RE = re.compile(r"^\d+\.\d+\.\d+$")
CSP_NONCE_PLACEHOLDER = "__CSP_NONCE__"
LOCAL_BASE_TAG = '<base href="./" data-deploy-href="/debugger/" />'
DEPLOYED_BASE_TAG = '<base href="/debugger/" />'
STYLESHEET_NAME = "debugger.css"
LOCAL_JQUERY_SRC = 'src="node_modules/jquery/dist/jquery.min.js"'
DEPLOYED_JQUERY_SRC = 'src="jquery-3.7.1.min.js"'
JQUERY_DEPLOY_MARKER = 'data-deploy-src="jquery-3.7.1.min.js"'
JQUERY_SOURCE = Path("node_modules/jquery/dist/jquery.min.js")
JQUERY_DESTINATION_NAME = "jquery-3.7.1.min.js"
STATIC_ASSET_NAMES = (STYLESHEET_NAME, "THIRD_PARTY_NOTICES.md")
OBSOLETE_VENDOR_DIR_NAME = "debugger-vendor"


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
    parser.add_argument(
        "--version",
        action="append",
        default=[],
        help="Only deploy the given version (can be passed multiple times)",
    )
    return parser.parse_args()


def candidate_assemblies_dirs(explicit: Iterable[Path]) -> List[Path]:
    candidates: List[Path] = list(explicit)

    if not candidates and os.name == "nt":
        for env_name in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            program_files = os.environ.get(env_name)
            if not program_files:
                continue

            root = Path(program_files)
            candidates.extend(
                [
                    root / "Proffix REST API" / "Proffix REST API" / "Assemblies",
                    root / "Proffix Server-Manager" / "PROFFIX REST API",
                ]
            )
    elif not candidates and sys.platform == "darwin":
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
    elif not candidates:
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
        for probe in (resolved, resolved / "Assemblies"):
            key = os.path.normcase(str(probe))
            if key in seen or not probe.is_dir():
                continue
            seen.add(key)
            existing.append(probe)
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
    source_html = source_file.read_text(encoding="utf-8")
    source_dir = source_file.parent
    assets = [(source_dir / name, name) for name in STATIC_ASSET_NAMES]
    missing_assets = [source for source, _ in assets if not source.is_file()]
    if missing_assets:
        missing = ", ".join(str(asset) for asset in missing_assets)
        raise ValueError(f"Required debugger assets not found: {missing}")

    jquery_source = source_dir / JQUERY_SOURCE
    if not jquery_source.is_file():
        raise ValueError(
            f"jQuery dependency not found at {jquery_source}. Run `npm ci` first."
        )
    assets.append((jquery_source, JQUERY_DESTINATION_NAME))
    if LOCAL_JQUERY_SRC not in source_html or JQUERY_DEPLOY_MARKER not in source_html:
        raise ValueError(
            "Source file must contain the deployable local jQuery source and "
            "data-deploy-src marker."
        )

    updated = 0
    for version_dir in version_dirs:
        destination = destination_for_version(version_dir)
        obsolete_vendor_dir = destination.parent / OBSOLETE_VENDOR_DIR_NAME
        is_modern_debugger = destination.name == "index.html"
        if is_modern_debugger and CSP_NONCE_PLACEHOLDER not in source_html:
            raise ValueError(
                f"Source file must contain {CSP_NONCE_PLACEHOLDER} before it can "
                f"replace the CSP-protected debugger at {destination}."
            )
        if is_modern_debugger and LOCAL_BASE_TAG not in source_html:
            raise ValueError(
                f"Source file must contain the deployable base tag {LOCAL_BASE_TAG} "
                f"before it can replace the debugger at {destination}."
            )
        if dry_run:
            for _, destination_name in assets:
                print(f"[DRY-RUN] Would write: {destination.parent / destination_name}")
            if obsolete_vendor_dir.is_dir():
                print(f"[DRY-RUN] Would remove: {obsolete_vendor_dir}")
            print(f"[DRY-RUN] Would write: {destination}")
        else:
            deployed_html = source_html.replace(
                LOCAL_JQUERY_SRC,
                DEPLOYED_JQUERY_SRC,
                1,
            )
            deployed_html = deployed_html.replace(JQUERY_DEPLOY_MARKER, "", 1)
            if is_modern_debugger:
                deployed_html = deployed_html.replace(
                    LOCAL_BASE_TAG,
                    DEPLOYED_BASE_TAG,
                    1,
                )

            with tempfile.TemporaryDirectory(
                prefix=".debugger-deploy-",
                dir=destination.parent,
            ) as staging_dir_name:
                staging_dir = Path(staging_dir_name)
                for source, destination_name in assets:
                    shutil.copy2(source, staging_dir / destination_name)

                staged_html = staging_dir / destination.name
                staged_html.write_text(deployed_html, encoding="utf-8")

                for _, destination_name in assets:
                    (staging_dir / destination_name).replace(
                        destination.parent / destination_name
                    )
                staged_html.replace(destination)

            if obsolete_vendor_dir.is_dir():
                shutil.rmtree(obsolete_vendor_dir)
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

    if args.version:
        requested_versions = set(args.version)
        all_targets = [
            target for target in all_targets if target.name in requested_versions
        ]

    if not all_targets:
        print(
            "ERROR: No matching Proffix version folders found under Assemblies.",
            file=sys.stderr,
        )
        return 4

    try:
        total = deploy(source_file, all_targets, args.dry_run)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 5
    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {total} version(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
