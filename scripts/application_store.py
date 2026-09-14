#!/usr/bin/env python3
"""Transactional SQLite store for Pilot's private application tracker."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
from contextlib import nullcontext
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_DIR_ENV = "CAREERLENS_PRIVATE_DATA_DIR"


def private_data_dir() -> Path:
    """Return the local-only directory for tracker data.

    The override is evaluated when this module is imported, so command-line
    users can move all CareerLens private data without changing source code.
    """

    configured = os.environ.get(PRIVATE_DATA_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "careerlens"


PRIVATE_DATA_DIR = private_data_dir()
DEFAULT_DB = PRIVATE_DATA_DIR / "applications.db"
DEFAULT_CSV = DEFAULT_DB.with_name("job-tracker.csv")

FIELDS = (
    "company", "role", "official_url", "location", "work_mode",
    "employment_constraints", "tier", "fit_score", "resume_track", "status",
    "verified_date", "approved_date", "submitted_date", "next_action", "notes",
)
STATUSES = {
    "discovered", "verified", "review_ready", "approved", "preparing",
    "submitted", "rejected", "interview", "offer", "withdrawn", "expired",
    "blocked", "skipped",
}

# A Pilot run receipt is a deliberately narrow operational audit record.  It
# must never contain a role, candidate, contact, URL, message, answer, path,
# or resume name.  The UI only consumes the aggregate of these fields through
# the loopback-only local projection.
PILOT_RUN_RESULTS = (
    "completed",
    "partial",
    "blocked",
    "failed",
)
PILOT_SOURCE_KEYS = (
    "linkedin",
    "indeed",
    "google",
    "greenhouse",
    "ashby",
    "lever",
    "workday",
    "company_careers",
    "wellfound",
    "yc_work_at_a_startup",
    "hacker_news",
    "reddit",
    "substack",
    "lenny",
)
PILOT_SOURCE_OUTCOMES = (
    "not_checked",
    "checked",
    "no_results",
    "blocked",
    "error",
)
PILOT_INBOX_STATUSES = (
    "not_checked",
    "checked",
    "unavailable",
    "failed",
)
PILOT_DECISION_KEYS = (
    "application",
    "reply",
    "connection",
    "comment",
    "handoff",
)
PILOT_SUBMISSION_VERIFICATION_RESULTS = (
    "not_needed",
    "verified",
    "unverified",
    "failed",
)
PILOT_TRACKER_TRANSACTION_RESULTS = (
    "not_needed",
    "committed",
    "failed",
)
PILOT_CLEANUP_RESULTS = (
    "not_needed",
    "completed",
    "failed",
)
PILOT_MAX_COUNT = 100_000
PILOT_RUN_RECEIPT_FIELDS = frozenset(
    {
        "completed_at",
        "result",
        "source_coverage",
        "inbox_status",
        "inbox_actionable_count",
        "discovered_count",
        "verified_count",
        "submitted_count",
        "blocked_count",
        "decision_counts",
        "submission_verification",
        "tracker_transaction",
        "cleanup",
    }
)


class StoreError(ValueError):
    pass


def require_private_path(path: Path | str, *, label: str) -> Path:
    """Reject tracker data paths inside this repository.

    Private application data is allowed in any user-selected external path,
    including a temporary directory for tests, but never in the checkout.
    """

    candidate = Path(path).expanduser()
    try:
        candidate.resolve(strict=False).relative_to(ROOT.resolve())
    except ValueError:
        return candidate
    raise StoreError(f"{label} must live outside the CareerLens repository")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    path = require_private_path(path, label="private tracker database")
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    db.execute("PRAGMA busy_timeout = 10000")
    return db


def initialize(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
          version INTEGER PRIMARY KEY,
          applied_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS applications (
          id INTEGER PRIMARY KEY,
          company TEXT NOT NULL,
          role TEXT NOT NULL,
          official_url TEXT NOT NULL UNIQUE,
          location TEXT NOT NULL DEFAULT '',
          work_mode TEXT NOT NULL DEFAULT '',
          employment_constraints TEXT NOT NULL DEFAULT '',
          tier TEXT NOT NULL DEFAULT '',
          fit_score INTEGER NOT NULL CHECK (fit_score BETWEEN 0 AND 100),
          resume_track TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL,
          verified_date TEXT NOT NULL DEFAULT '',
          approved_date TEXT NOT NULL DEFAULT '',
          submitted_date TEXT NOT NULL DEFAULT '',
          next_action TEXT NOT NULL DEFAULT '',
          notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS application_events (
          id INTEGER PRIMARY KEY,
          application_id INTEGER NOT NULL REFERENCES applications(id),
          event_time TEXT NOT NULL,
          event_type TEXT NOT NULL,
          old_status TEXT NOT NULL DEFAULT '',
          new_status TEXT NOT NULL DEFAULT '',
          source TEXT NOT NULL,
          reason TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS sync_runs (
          id INTEGER PRIMARY KEY,
          started_at TEXT NOT NULL,
          finished_at TEXT NOT NULL,
          database_revision INTEGER NOT NULL,
          result TEXT NOT NULL,
          checks TEXT NOT NULL DEFAULT '',
          published_commit TEXT NOT NULL DEFAULT '',
          error_summary TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS pilot_runs (
          id INTEGER PRIMARY KEY,
          completed_at TEXT NOT NULL,
          result TEXT NOT NULL CHECK (result IN ('completed', 'partial', 'blocked', 'failed')),
          source_linkedin_outcome TEXT NOT NULL CHECK (source_linkedin_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_linkedin_count INTEGER NOT NULL DEFAULT 0 CHECK (source_linkedin_count BETWEEN 0 AND 100000),
          source_indeed_outcome TEXT NOT NULL CHECK (source_indeed_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_indeed_count INTEGER NOT NULL DEFAULT 0 CHECK (source_indeed_count BETWEEN 0 AND 100000),
          source_google_outcome TEXT NOT NULL CHECK (source_google_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_google_count INTEGER NOT NULL DEFAULT 0 CHECK (source_google_count BETWEEN 0 AND 100000),
          source_greenhouse_outcome TEXT NOT NULL CHECK (source_greenhouse_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_greenhouse_count INTEGER NOT NULL DEFAULT 0 CHECK (source_greenhouse_count BETWEEN 0 AND 100000),
          source_ashby_outcome TEXT NOT NULL CHECK (source_ashby_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_ashby_count INTEGER NOT NULL DEFAULT 0 CHECK (source_ashby_count BETWEEN 0 AND 100000),
          source_lever_outcome TEXT NOT NULL CHECK (source_lever_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_lever_count INTEGER NOT NULL DEFAULT 0 CHECK (source_lever_count BETWEEN 0 AND 100000),
          source_workday_outcome TEXT NOT NULL CHECK (source_workday_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_workday_count INTEGER NOT NULL DEFAULT 0 CHECK (source_workday_count BETWEEN 0 AND 100000),
          source_company_careers_outcome TEXT NOT NULL CHECK (source_company_careers_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_company_careers_count INTEGER NOT NULL DEFAULT 0 CHECK (source_company_careers_count BETWEEN 0 AND 100000),
          source_wellfound_outcome TEXT NOT NULL CHECK (source_wellfound_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_wellfound_count INTEGER NOT NULL DEFAULT 0 CHECK (source_wellfound_count BETWEEN 0 AND 100000),
          source_yc_work_at_a_startup_outcome TEXT NOT NULL CHECK (source_yc_work_at_a_startup_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_yc_work_at_a_startup_count INTEGER NOT NULL DEFAULT 0 CHECK (source_yc_work_at_a_startup_count BETWEEN 0 AND 100000),
          source_hacker_news_outcome TEXT NOT NULL CHECK (source_hacker_news_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_hacker_news_count INTEGER NOT NULL DEFAULT 0 CHECK (source_hacker_news_count BETWEEN 0 AND 100000),
          source_reddit_outcome TEXT NOT NULL CHECK (source_reddit_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_reddit_count INTEGER NOT NULL DEFAULT 0 CHECK (source_reddit_count BETWEEN 0 AND 100000),
          source_substack_outcome TEXT NOT NULL CHECK (source_substack_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_substack_count INTEGER NOT NULL DEFAULT 0 CHECK (source_substack_count BETWEEN 0 AND 100000),
          source_lenny_outcome TEXT NOT NULL CHECK (source_lenny_outcome IN ('not_checked', 'checked', 'no_results', 'blocked', 'error')),
          source_lenny_count INTEGER NOT NULL DEFAULT 0 CHECK (source_lenny_count BETWEEN 0 AND 100000),
          inbox_status TEXT NOT NULL CHECK (inbox_status IN ('not_checked', 'checked', 'unavailable', 'failed')),
          inbox_actionable_count INTEGER NOT NULL DEFAULT 0 CHECK (inbox_actionable_count BETWEEN 0 AND 100000),
          discovered_count INTEGER NOT NULL DEFAULT 0 CHECK (discovered_count BETWEEN 0 AND 100000),
          verified_count INTEGER NOT NULL DEFAULT 0 CHECK (verified_count BETWEEN 0 AND 100000),
          submitted_count INTEGER NOT NULL DEFAULT 0 CHECK (submitted_count BETWEEN 0 AND 100000),
          blocked_count INTEGER NOT NULL DEFAULT 0 CHECK (blocked_count BETWEEN 0 AND 100000),
          application_decisions INTEGER NOT NULL DEFAULT 0 CHECK (application_decisions BETWEEN 0 AND 100000),
          reply_decisions INTEGER NOT NULL DEFAULT 0 CHECK (reply_decisions BETWEEN 0 AND 100000),
          connection_decisions INTEGER NOT NULL DEFAULT 0 CHECK (connection_decisions BETWEEN 0 AND 100000),
          comment_decisions INTEGER NOT NULL DEFAULT 0 CHECK (comment_decisions BETWEEN 0 AND 100000),
          handoff_decisions INTEGER NOT NULL DEFAULT 0 CHECK (handoff_decisions BETWEEN 0 AND 100000),
          submission_verification TEXT NOT NULL CHECK (submission_verification IN ('not_needed', 'verified', 'unverified', 'failed')),
          tracker_transaction TEXT NOT NULL CHECK (tracker_transaction IN ('not_needed', 'committed', 'failed')),
          cleanup TEXT NOT NULL CHECK (cleanup IN ('not_needed', 'completed', 'failed'))
        );
        """
    )
    db.execute(
        "INSERT OR IGNORE INTO schema_version(version, applied_at) VALUES(1, ?)",
        (utc_now(),),
    )
    db.commit()


def _validate(row: dict[str, object]) -> dict[str, object]:
    clean = {field: str(row.get(field, "") or "").strip() for field in FIELDS}
    if not clean["company"] or not clean["role"]:
        raise StoreError("company and role are required")
    parsed = urlparse(clean["official_url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise StoreError("official_url must be an absolute HTTP(S) URL")
    status = clean["status"].lower().replace("-", "_").replace(" ", "_")
    if status not in STATUSES:
        raise StoreError(f"unknown status: {clean['status']!r}")
    clean["status"] = status
    try:
        score = int(clean["fit_score"])
    except ValueError as exc:
        raise StoreError("fit_score must be an integer") from exc
    if not 0 <= score <= 100:
        raise StoreError("fit_score must be between 0 and 100")
    clean["fit_score"] = score
    for field in ("verified_date", "approved_date", "submitted_date"):
        if clean[field]:
            try:
                date.fromisoformat(clean[field])
            except ValueError as exc:
                raise StoreError(f"{field} must be a valid ISO date") from exc
    if status == "submitted" and not clean["submitted_date"]:
        raise StoreError("submitted status requires submitted_date")
    return clean


def _pilot_count(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StoreError(f"{field} must be a nonnegative integer")
    if not 0 <= value <= PILOT_MAX_COUNT:
        raise StoreError(
            f"{field} must be between 0 and {PILOT_MAX_COUNT}"
        )
    return value


def _pilot_enum(value: object, field: str, allowed: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise StoreError(f"{field} must be one of: {', '.join(allowed)}")
    return value


def _pilot_completed_at(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise StoreError("completed_at must be a timezone-aware ISO timestamp")
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise StoreError("completed_at must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StoreError("completed_at must be a timezone-aware ISO timestamp")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _pilot_count_map(
    value: object,
    field: str,
    keys: tuple[str, ...],
) -> dict[str, int]:
    if value is None:
        return {key: 0 for key in keys}
    if not isinstance(value, Mapping):
        raise StoreError(f"{field} must be an object with fixed keys")
    unknown = set(value) - set(keys)
    if unknown:
        raise StoreError(f"{field} contains an unsupported key")
    return {key: _pilot_count(value.get(key, 0), f"{field}.{key}") for key in keys}


def _pilot_source_coverage(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, Mapping):
        raise StoreError("source_coverage must include every fixed Pilot source")
    source_keys = set(value)
    expected = set(PILOT_SOURCE_KEYS)
    if source_keys != expected:
        raise StoreError("source_coverage must use exactly the fixed source keys")
    clean: dict[str, dict[str, object]] = {}
    for source in PILOT_SOURCE_KEYS:
        source_receipt = value[source]
        if not isinstance(source_receipt, Mapping):
            raise StoreError(f"source_coverage.{source} must be an object")
        if set(source_receipt) != {"outcome", "count"}:
            raise StoreError(
                f"source_coverage.{source} must contain only outcome and count"
            )
        clean[source] = {
            "outcome": _pilot_enum(
                source_receipt["outcome"],
                f"source_coverage.{source}.outcome",
                PILOT_SOURCE_OUTCOMES,
            ),
            "count": _pilot_count(
                source_receipt["count"],
                f"source_coverage.{source}.count",
            ),
        }
        if clean[source]["outcome"] != "checked" and clean[source]["count"]:
            raise StoreError(
                f"source_coverage.{source}.count must be 0 unless outcome is checked"
            )
    return clean


def validate_pilot_run_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    """Validate the only supported, non-identifying Pilot receipt payload.

    ``receipt`` accepts fixed source and decision-count maps plus enum states.
    It intentionally has no text, identity, contact, URL, employment, message,
    answer, path, or resume fields.  Every value is checked before insertion.
    """

    if not isinstance(receipt, Mapping):
        raise StoreError("pilot receipt must be an object")
    unknown = set(receipt) - PILOT_RUN_RECEIPT_FIELDS
    if unknown:
        raise StoreError("pilot receipt contains an unsupported field")
    required = {"completed_at", "result", "source_coverage", "inbox_status"}
    missing = required - set(receipt)
    if missing:
        raise StoreError("pilot receipt is missing a required field")
    inbox_status = _pilot_enum(
        receipt["inbox_status"], "inbox_status", PILOT_INBOX_STATUSES
    )
    inbox_actionable_count = _pilot_count(
        receipt.get("inbox_actionable_count", 0), "inbox_actionable_count"
    )
    if inbox_status != "checked" and inbox_actionable_count:
        raise StoreError("inbox_actionable_count must be 0 unless inbox_status is checked")
    return {
        "completed_at": _pilot_completed_at(receipt["completed_at"]),
        "result": _pilot_enum(receipt["result"], "result", PILOT_RUN_RESULTS),
        "source_coverage": _pilot_source_coverage(receipt["source_coverage"]),
        "inbox_status": inbox_status,
        "inbox_actionable_count": inbox_actionable_count,
        "discovered_count": _pilot_count(
            receipt.get("discovered_count", 0), "discovered_count"
        ),
        "verified_count": _pilot_count(
            receipt.get("verified_count", 0), "verified_count"
        ),
        "submitted_count": _pilot_count(
            receipt.get("submitted_count", 0), "submitted_count"
        ),
        "blocked_count": _pilot_count(
            receipt.get("blocked_count", 0), "blocked_count"
        ),
        "decision_counts": _pilot_count_map(
            receipt.get("decision_counts"), "decision_counts", PILOT_DECISION_KEYS
        ),
        "submission_verification": _pilot_enum(
            receipt.get("submission_verification", "not_needed"),
            "submission_verification",
            PILOT_SUBMISSION_VERIFICATION_RESULTS,
        ),
        "tracker_transaction": _pilot_enum(
            receipt.get("tracker_transaction", "not_needed"),
            "tracker_transaction",
            PILOT_TRACKER_TRANSACTION_RESULTS,
        ),
        "cleanup": _pilot_enum(
            receipt.get("cleanup", "not_needed"),
            "cleanup",
            PILOT_CLEANUP_RESULTS,
        ),
    }


def record_pilot_run(
    db: sqlite3.Connection,
    receipt: Mapping[str, object],
) -> int:
    """Transactionally save one validated, local-only Pilot run receipt."""

    clean = validate_pilot_run_receipt(receipt)
    initialize(db)
    columns = (
        "completed_at",
        "result",
        *(
            column
            for key in PILOT_SOURCE_KEYS
            for column in (f"source_{key}_outcome", f"source_{key}_count")
        ),
        "inbox_status",
        "inbox_actionable_count",
        "discovered_count",
        "verified_count",
        "submitted_count",
        "blocked_count",
        *(f"{key}_decisions" for key in PILOT_DECISION_KEYS),
        "submission_verification",
        "tracker_transaction",
        "cleanup",
    )
    values = (
        clean["completed_at"],
        clean["result"],
        *(
            value
            for key in PILOT_SOURCE_KEYS
            for value in (
                clean["source_coverage"][key]["outcome"],
                clean["source_coverage"][key]["count"],
            )
        ),
        clean["inbox_status"],
        clean["inbox_actionable_count"],
        clean["discovered_count"],
        clean["verified_count"],
        clean["submitted_count"],
        clean["blocked_count"],
        *(clean["decision_counts"][key] for key in PILOT_DECISION_KEYS),
        clean["submission_verification"],
        clean["tracker_transaction"],
        clean["cleanup"],
    )
    with db:
        cursor = db.execute(
            f"INSERT INTO pilot_runs ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            values,
        )
    return int(cursor.lastrowid)


def upsert(
    db: sqlite3.Connection,
    row: dict[str, object],
    *,
    source: str = "pilot",
    reason: str = "",
    _manage_transaction: bool = True,
) -> int:
    clean = _validate(row)
    existing = db.execute(
        "SELECT * FROM applications WHERE official_url = ?", (clean["official_url"],)
    ).fetchone()
    now = utc_now()
    with (db if _manage_transaction else nullcontext()):
        if existing is None:
            columns = ", ".join(FIELDS)
            placeholders = ", ".join("?" for _ in FIELDS)
            values = [clean[field] for field in FIELDS]
            cursor = db.execute(
                f"INSERT INTO applications ({columns}, created_at, updated_at) "
                f"VALUES ({placeholders}, ?, ?)",
                (*values, now, now),
            )
            application_id = int(cursor.lastrowid)
            old_status = ""
            event_type = "created"
        else:
            application_id = int(existing["id"])
            old_status = str(existing["status"])
            if all(str(existing[field]) == str(clean[field]) for field in FIELDS):
                return application_id
            assignments = ", ".join(f"{field} = ?" for field in FIELDS)
            db.execute(
                f"UPDATE applications SET {assignments}, updated_at = ? WHERE id = ?",
                (*[clean[field] for field in FIELDS], now, application_id),
            )
            event_type = "transition" if old_status != clean["status"] else "updated"
        db.execute(
            """INSERT INTO application_events
               (application_id,event_time,event_type,old_status,new_status,source,reason)
               VALUES(?,?,?,?,?,?,?)""",
            (application_id, now, event_type, old_status, clean["status"], source, reason),
        )
    return application_id


def read_rows(db: sqlite3.Connection) -> list[dict[str, str]]:
    initialize(db)
    rows = db.execute(
        f"SELECT {', '.join(FIELDS)} FROM applications "
        "ORDER BY company COLLATE NOCASE, role COLLATE NOCASE, official_url"
    ).fetchall()
    return [{field: str(row[field]) for field in FIELDS} for row in rows]


def import_csv(
    db: sqlite3.Connection, source: Path | str = DEFAULT_CSV, *, source_name: str = "csv-migration"
) -> int:
    source = require_private_path(source, label="private tracker CSV")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise StoreError("CSV missing fields: " + ", ".join(missing))
        rows = [dict(row) for row in reader if any((value or "").strip() for value in row.values())]
    with db:
        for row in rows:
            upsert(
                db, row, source=source_name, reason="Imported from canonical CSV",
                _manage_transaction=False,
            )
    return len(rows)


def export_csv(db: sqlite3.Connection, output: Path | str = DEFAULT_CSV) -> Path:
    output = require_private_path(output, label="private tracker CSV")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(read_rows(db))
    temp.replace(output)
    return output


def revision(db: sqlite3.Connection) -> int:
    initialize(db)
    return int(db.execute("SELECT COALESCE(MAX(id), 0) FROM application_events").fetchone()[0])


def record_sync(
    db: sqlite3.Connection, *, started_at: str, result: str, checks: Iterable[str],
    published_commit: str = "", error_summary: str = ""
) -> None:
    with db:
        db.execute(
            """INSERT INTO sync_runs
               (started_at,finished_at,database_revision,result,checks,published_commit,error_summary)
               VALUES(?,?,?,?,?,?,?)""",
            (started_at, utc_now(), revision(db), result, json.dumps(list(checks)),
             published_commit, error_summary[:2000]),
        )


def integrity_check(db: sqlite3.Connection) -> None:
    initialize(db)
    result = db.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise StoreError(f"SQLite integrity check failed: {result}")


def transition(
    db: sqlite3.Connection, official_url: str, status: str, *, event_date: str = "",
    source: str = "pilot", reason: str = ""
) -> int:
    existing = db.execute(
        f"SELECT {', '.join(FIELDS)} FROM applications WHERE official_url = ?",
        (official_url,),
    ).fetchone()
    if existing is None:
        raise StoreError(f"application not found: {official_url}")
    row = dict(existing)
    normalized = status.lower().replace("-", "_").replace(" ", "_")
    row["status"] = normalized
    if normalized == "submitted" and event_date:
        row["submitted_date"] = event_date
    if normalized == "approved" and event_date:
        row["approved_date"] = event_date
    return upsert(db, row, source=source, reason=reason)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    migrate = sub.add_parser("import-csv")
    migrate.add_argument("--source", type=Path, default=DEFAULT_CSV)
    export = sub.add_parser("export-private-csv")
    export.add_argument("--output", type=Path, default=DEFAULT_CSV)
    put = sub.add_parser("upsert")
    put.add_argument("--record-json", required=True)
    put.add_argument("--source", default="pilot")
    put.add_argument("--reason", default="")
    move = sub.add_parser("transition")
    move.add_argument("--url", required=True)
    move.add_argument("--status", required=True)
    move.add_argument("--date", default="")
    move.add_argument("--source", default="pilot")
    move.add_argument("--reason", default="")
    pilot_run = sub.add_parser(
        "record-pilot-run",
        help="record a validated, non-identifying Pilot run receipt",
    )
    pilot_run.add_argument("--receipt-json", required=True)
    sub.add_parser("list")
    args = parser.parse_args(list(argv) if argv is not None else None)
    db = connect(args.db)
    initialize(db)
    if args.command == "import-csv":
        print(import_csv(db, args.source))
    elif args.command == "export-private-csv":
        print(export_csv(db, args.output))
    elif args.command == "upsert":
        print(upsert(db, json.loads(args.record_json), source=args.source, reason=args.reason))
    elif args.command == "transition":
        print(transition(db, args.url, args.status, event_date=args.date,
                         source=args.source, reason=args.reason))
    elif args.command == "record-pilot-run":
        try:
            receipt = json.loads(args.receipt_json)
        except json.JSONDecodeError as exc:
            parser.error("--receipt-json must be a JSON object")
            raise AssertionError("argparse exits") from exc
        print(record_pilot_run(db, receipt))
    else:
        print(json.dumps(read_rows(db), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
