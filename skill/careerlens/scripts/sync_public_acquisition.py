#!/usr/bin/env python3
"""Synchronize the explicit, portable CareerOS public-acquisition subset.

The source root is intentionally mandatory.  This makes the operation
reproducible without assuming a maintainer checkout, installed package, home
directory, or private workspace exists on the receiving machine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple


FORMAT_VERSION = 1
PACKAGE_DIR = Path(__file__).resolve().parent / "public_acquisition"
MANIFEST_PATH = PACKAGE_DIR / "VENDORED_FROM_CAREEROS.json"
FILES: Tuple[Tuple[str, str], ...] = (
    ("career_os/errors.py", "errors.py"),
    ("career_os/schema.py", "schema.py"),
    ("career_os/providers.py", "providers.py"),
    ("career_os/public_fetch.py", "public_fetch.py"),
    ("career_os/public_monitor.py", "public_monitor.py"),
    ("career_os/static/public-acquisition.html", "static/public-acquisition.html"),
    ("career_os/static/public-acquisition.css", "static/public-acquisition.css"),
    ("career_os/static/public-acquisition.js", "static/public-acquisition.js"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _revision(source_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(source_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    revision = completed.stdout.strip()
    return revision if len(revision) == 40 else "unavailable"


def _entry(source_relative: str, destination_relative: str, source_path: Path) -> Dict[str, str]:
    return {
        "source_path": source_relative,
        "destination_path": "public_acquisition/" + destination_relative,
        "sha256": _sha256(source_path),
    }


def build_manifest(source_root: Path) -> Dict[str, object]:
    entries: List[Dict[str, str]] = []
    for source_relative, destination_relative in FILES:
        source_path = source_root / source_relative
        if not source_path.is_file():
            raise FileNotFoundError(source_relative)
        entries.append(_entry(source_relative, destination_relative, source_path))
    return {
        "format_version": FORMAT_VERSION,
        "source_root_contract": "explicit root containing career_os/",
        "source_revision": _revision(source_root),
        "files": entries,
    }


def _read_manifest() -> Dict[str, object]:
    try:
        value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("manifest_unavailable") from error
    if not isinstance(value, dict):
        raise ValueError("manifest_unavailable")
    return value


def sync(source_root: Path) -> Dict[str, object]:
    manifest = build_manifest(source_root)
    for source_relative, destination_relative in FILES:
        destination = PACKAGE_DIR / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source_root / source_relative), str(destination))
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def check(source_root: Path) -> List[str]:
    errors: List[str] = []
    try:
        expected = build_manifest(source_root)
        actual = _read_manifest()
    except (FileNotFoundError, ValueError) as error:
        return [str(error)]
    if actual.get("format_version") != FORMAT_VERSION:
        errors.append("manifest_format")
    if actual.get("files") != expected.get("files"):
        errors.append("manifest_source_mismatch")
    for source_relative, destination_relative in FILES:
        source_path = source_root / source_relative
        destination = PACKAGE_DIR / destination_relative
        if not destination.is_file() or _sha256(destination) != _sha256(source_path):
            errors.append("hash_mismatch:" + destination_relative)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="byte-exact public acquisition vendor sync/check")
    parser.add_argument(
        "--source-root",
        required=True,
        type=Path,
        help="explicit CareerOS repository root containing career_os/",
    )
    parser.add_argument("--check", action="store_true", help="verify only; do not copy files")
    return parser


def run(argv: Optional[Sequence[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    source_root = arguments.source_root.resolve()
    if not source_root.is_dir():
        print(json.dumps({"ok": False, "errors": ["source_root_invalid"]}), file=sys.stderr)
        return 2
    if arguments.check:
        errors = check(source_root)
        print(json.dumps({"ok": not errors, "errors": errors}, separators=(",", ":")))
        return 0 if not errors else 1
    try:
        manifest = sync(source_root)
    except FileNotFoundError as error:
        print(json.dumps({"ok": False, "errors": ["source_file_missing:" + str(error)]}), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"ok": True, "files": len(manifest["files"]), "source_revision": manifest["source_revision"]},
            separators=(",", ":"),
        )
    )
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
