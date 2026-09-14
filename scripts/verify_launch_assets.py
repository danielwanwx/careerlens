#!/usr/bin/env python3
"""Verify the public case, deterministic projections, and launch media."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_DIRS = tuple(sorted(path for path in (ROOT / "case-studies").iterdir() if (path / "source-manifest.json").is_file()))
PRIVATE_RE = re.compile(r"(?:/Users/|/home/|[A-Z]:\\Users\\|-----BEGIN [A-Z ]+PRIVATE KEY-----)")
SECRET_RE = re.compile(r"(?i)(api[_-]?key|password|bearer\s+[a-z0-9._-]{12,})")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validator() -> Any:
    path = ROOT / "skill" / "careerlens" / "scripts" / "validate_runbook.py"
    spec = importlib.util.spec_from_file_location("careerlens_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load CareerLens validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def media_metadata(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json", str(path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def manifest_files(case_dir: Path, manifest: dict[str, Any]) -> list[tuple[Path, str]]:
    if "files" in manifest:
        return [(case_dir / item["path"], item["sha256"]) for item in manifest["files"]]
    return [
        (case_dir / manifest["candidate"]["local_path"], manifest["candidate"]["sha256"]),
        (case_dir / manifest["target"]["local_markdown_path"], manifest["target"]["local_markdown_sha256"]),
        (case_dir / manifest["target"]["local_json_path"], manifest["target"]["local_json_sha256"]),
    ]


def verify_case(case_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest = json.loads((case_dir / "source-manifest.json").read_text(encoding="utf-8"))
    for path, expected_hash in manifest_files(case_dir, manifest):
        if not path.is_file():
            errors.append(f"missing source: {path.relative_to(ROOT)}")
        elif sha256(path) != expected_hash:
            errors.append(f"source hash mismatch: {path.relative_to(ROOT)}")

    runbook_path = case_dir / "output" / "runbook.json"
    data = json.loads(runbook_path.read_text(encoding="utf-8"))
    receipt = load_validator().validate(data, strict=True)
    errors.extend(f"runbook: {item}" for item in receipt["errors"])
    if data["decision_state"].get("show_numeric_score") is not False:
        errors.append("numeric fit score must remain suppressed")
    if data["decision_state"].get("kind") != "conditional":
        errors.append(f"{case_dir.name}: public case decision must remain conditional")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_case_study.py"),
             "--runbook", str(runbook_path), "--output-dir", str(temp)],
            check=True,
        )
        for filename in ("report.md", "report.html"):
            checked_in = case_dir / "output" / filename
            if not checked_in.is_file():
                errors.append(f"missing generated report: {filename}")
            elif checked_in.read_bytes() != (temp / filename).read_bytes():
                errors.append(f"generated report is stale: {filename}")
        demo_temp = temp / "runbook-demo.html"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_runbook_demo.py"),
             "--runbook", str(runbook_path), "--output", str(demo_temp)],
            check=True,
        )
        checked_demo = case_dir / "output" / "runbook-demo.html"
        if not checked_demo.is_file():
            errors.append("missing generated report: runbook-demo.html")
        elif checked_demo.read_bytes() != demo_temp.read_bytes():
            errors.append("generated report is stale: runbook-demo.html")

    scan_paths = [
        case_dir / "output" / "runbook.json",
        case_dir / "output" / "report.md",
        case_dir / "output" / "report.html",
        case_dir / "output" / "runbook-demo.html",
    ]
    for path in scan_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if PRIVATE_RE.search(text):
            errors.append(f"private local path in {path.relative_to(ROOT)}")
        if SECRET_RE.search(text):
            errors.append(f"secret-like value in {path.relative_to(ROOT)}")
        for required in ("conditional", "proved", "claimed", "missing", "unknown"):
            if required not in text:
                errors.append(f"{path.relative_to(ROOT)} missing required state: {required}")

    return errors


def verify(*, allow_missing_media: bool = False) -> list[str]:
    errors = []
    for case_dir in CASE_DIRS:
        errors.extend(verify_case(case_dir))

    if allow_missing_media:
        return errors

    media_dir = ROOT / "assets" / "launch"
    media = {
        "social-preview.png": (1280, 640),
        "case-report.png": (1440, 900),
        "runbook-demo.png": (1280, 720),
    }
    for filename, dimensions in media.items():
        path = media_dir / filename
        if not path.is_file():
            errors.append(f"missing launch asset: assets/launch/{filename}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"empty launch asset: assets/launch/{filename}")
        if dimensions and filename.endswith((".png", ".mp4")):
            try:
                metadata = media_metadata(path)
                stream = metadata["streams"][0]
                actual = (int(stream["width"]), int(stream["height"]))
                if actual != dimensions:
                    errors.append(f"{filename} dimensions {actual}, expected {dimensions}")
                if filename.endswith(".mp4"):
                    duration = float(metadata["format"]["duration"])
                    if not 30 <= duration <= 40:
                        errors.append(f"video duration {duration:.2f}s outside 30 to 40s")
            except (FileNotFoundError, KeyError, ValueError, subprocess.CalledProcessError) as exc:
                errors.append(f"cannot inspect {filename}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing-media", action="store_true")
    args = parser.parse_args()
    errors = verify(allow_missing_media=args.allow_missing_media)
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
