#!/usr/bin/env python3
"""Synchronize the SQLite tracker into its local-only CSV mirror."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
LOCK_PATH = Path(tempfile.gettempdir()) / "careerlens-tracker-sync.lock"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


store = _load("application_store", SCRIPTS / "application_store.py")
exporter = _load("export_application_tracker", SCRIPTS / "export_application_tracker.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def synchronize(db_path: Path, private_csv: Path, *, publish: bool, dry_run: bool) -> str:
    """Refresh local tracker data without producing any public artifact.

    The loopback server reads the SQLite database and builds its response in
    memory.  This command only maintains the optional local CSV mirror.
    """

    if publish:
        raise store.StoreError("application tracker publication is disabled")
    started = store.utc_now()
    checks: list[str] = []
    db = store.connect(db_path)
    store.initialize(db)
    try:
        store.integrity_check(db)
        checks.append("sqlite-integrity")
        rows = store.read_rows(db)
        if not rows:
            raise store.StoreError("refusing to sync an empty tracker")
        with tempfile.TemporaryDirectory(prefix="careerlens-sync-") as directory:
            temp = Path(directory)
            temp_csv = temp / "job-tracker.csv"
            store.export_csv(db, temp_csv)
            projection = exporter.build_projection(db_path)
            if len(projection["roles"]) != len(rows):
                raise store.StoreError("local projection record count mismatch")
            checks.extend(["record-count", "local-projection-allowlist"])
            changed = digest(temp_csv) != digest(private_csv)
            if dry_run:
                store.record_sync(db, started_at=started, result="dry-run", checks=checks)
                return "dry-run: local CSV would change" if changed else "dry-run: no change"
            store.export_csv(db, private_csv)
            checks.append("local-csv-refresh")
        store.record_sync(
            db, started_at=started, result="success", checks=checks,
        )
        return f"success: {len(rows)} roles; local tracker refreshed"
    except Exception as exc:
        store.record_sync(
            db, started_at=started, result="failed", checks=checks,
            error_summary=f"{type(exc).__name__}: {exc}",
        )
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=store.DEFAULT_DB)
    parser.add_argument("--private-csv", type=Path, default=store.DEFAULT_CSV)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("tracker sync already running", file=sys.stderr)
            return 3
        try:
            print(synchronize(args.db, args.private_csv, publish=args.publish, dry_run=args.dry_run))
        except Exception as exc:
            print(f"tracker sync failed: {exc}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
