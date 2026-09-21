#!/usr/bin/env python3
"""Build local, allowlisted projections of Pilot's private application tracker.

The source tracker intentionally lives outside this repository.  This module is
the privacy boundary for the loopback tracker: only the fields in
:data:`PUBLIC_FIELDS` are emitted and public notes/actions are treated as text
with an additional safety filter.  A projection may be written only to local
storage outside the repository; the local server normally generates it in
memory for each request.

The output is deterministic.  It contains a date derived from the source rows
instead of the current clock, so running the exporter twice with the same CSV
produces byte-for-byte identical JSON.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_DIR_ENV = "CAREERLENS_PRIVATE_DATA_DIR"


def private_data_dir() -> Path:
    """Return the portable local-only CareerLens data directory."""

    configured = os.environ.get(PRIVATE_DATA_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "careerlens"


PRIVATE_DATA_DIR = private_data_dir()
DEFAULT_SOURCE = PRIVATE_DATA_DIR / "job-tracker.csv"
DEFAULT_OUTPUT = PRIVATE_DATA_DIR / "application-tracker.local.json"
DEFAULT_DB = DEFAULT_SOURCE.with_name("applications.db")
DEFAULT_SCHEDULE_SOURCE = DEFAULT_SOURCE.with_name("interview-and-events.md")
DEFAULT_LOCAL_PAGES = PRIVATE_DATA_DIR / "pages"
DEFAULT_COACH_DB = Path.home() / ".local" / "share" / "interview-coach" / "coach.sqlite3"

# This is deliberately an explicit allowlist.  Do not replace it with a
# dictionary copy or ``row.keys()``: the private source has employment,
# approval, and notes fields that must not cross the public boundary.
PUBLIC_FIELDS = (
    "company",
    "role",
    "job_url",
    "location",
    "work_mode",
    "tier",
    "fit_score",
    "resume_track",
    "status",
    "verified_date",
    "applied_date",
    "next_action",
    "public_note",
)

# Schedule events are intentionally a separate, local-only projection.  They
# must never be added to ``PUBLIC_FIELDS`` or ``build_projection`` because the
# latter is the artifact that can be committed and published.
SCHEDULE_PUBLIC_FIELDS = (
    "title",
    "organization",
    "datetime",
    "timezone",
    "location",
    "status",
    "next_step",
)

# Learning evidence has a separate local-only boundary.  It is intentionally
# absent from PUBLIC_FIELDS and build_projection because the Coach database
# contains private learner evidence.  The loopback tracker receives only these
# aggregate fields, never a track, topic, competency, answer, reason, repair
# target, contact, or source path.
LEARNING_LOCAL_FIELDS = (
    "status",
    "updated_at",
    "attempts",
    "attempt_completion",
    "independent_success",
    "section_completion",
    "open_repairs",
    "due_repairs",
    "open_gaps",
    "due_gaps",
    "latest_states",
    "dimension_scores",
)
LEARNING_STATES = (
    "needs_check",
    "needs_hint",
    "independent_today",
    "delayed_transfer",
)
LEARNING_DIMENSIONS = (
    "concepts",
    "causality",
    "application",
    "edges",
    "tradeoffs",
    "structure",
    "expression",
    "retention",
)

# Pilot receipt aggregates have the same local-only boundary as Learning.
# They are never part of PUBLIC_FIELDS, build_projection, write_projection, or
# the static Pages data artifact.  Every nested key below is fixed so the
# loopback UI can render counts without receiving run text or identities.
PILOT_OPERATIONS_LOCAL_FIELDS = (
    "status",
    "latest",
    "run_count",
    "source_coverage",
    "inbox",
    "totals",
    "queue_counts",
    "submission_verification",
    "tracker_transaction",
    "cleanup",
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
PILOT_INBOX_STATUSES = ("not_checked", "checked", "unavailable", "failed")
PILOT_RUN_RESULTS = ("completed", "partial", "blocked", "failed")
PILOT_DECISION_KEYS = ("application", "reply", "connection", "comment", "handoff")
PILOT_SUBMISSION_VERIFICATION_RESULTS = (
    "not_needed",
    "verified",
    "unverified",
    "failed",
)
PILOT_TRACKER_TRANSACTION_RESULTS = ("not_needed", "committed", "failed")
PILOT_CLEANUP_RESULTS = ("not_needed", "completed", "failed")
PILOT_MAX_COUNT = 100_000

SOURCE_REQUIRED_COLUMNS = (
    "company",
    "role",
    "official_url",
    "location",
    "work_mode",
    "employment_constraints",
    "tier",
    "fit_score",
    "resume_track",
    "status",
    "verified_date",
    "approved_date",
    "submitted_date",
    "next_action",
    "notes",
)

PUBLIC_STATUSES = (
    "Discovered",
    "Verified",
    "Review",
    "Approved",
    "Submitted",
    "Interview",
    "Offer",
    "Closed",
)

_STATUS_ALIASES = {
    "discovered": "Discovered",
    "new": "Discovered",
    "verified": "Verified",
    "review": "Review",
    "review_ready": "Review",
    "pending_review": "Review",
    "approved": "Approved",
    "preparing": "Approved",
    "submitted": "Submitted",
    "applied": "Submitted",
    "interview": "Interview",
    "interviewing": "Interview",
    "offer": "Offer",
    "closed": "Closed",
    "rejected": "Closed",
    "expired": "Closed",
    "withdrawn": "Closed",
    "blocked": "Closed",
    "skipped": "Closed",
    "exclude": "Closed",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAFE_TEXT_RE = re.compile(r"^[^\x00-\x1f\x7f]+$")

# The private schedule is a deliberately small Markdown table.  Keeping this
# grammar narrow makes it possible to discard a row that gains a note, a
# contact detail, or a private link instead of trying to redact it.
_SCHEDULE_TIME_PATTERN = r"\d{1,2}:\d{2}\s*[AaPp][Mm]"
_SCHEDULE_TIMEZONE_PATTERN = (
    r"(?:[A-Za-z]{2,5}(?:[+-]\d{1,2}(?::?\d{2})?)?)"
)
_SCHEDULE_DATETIME_RE = re.compile(
    r"^(?P<day>\d{4}-\d{2}-\d{2}),\s*"
    rf"(?P<start>{_SCHEDULE_TIME_PATTERN})(?:\s+to)?\s+"
    rf"(?P<end>{_SCHEDULE_TIME_PATTERN})\s+"
    rf"(?P<timezone>{_SCHEDULE_TIMEZONE_PATTERN})$"
)
_SCHEDULE_T_DATETIME_RE = re.compile(
    r"^(?P<day>\d{4}-\d{2}-\d{2})T"
    rf"(?P<start>{_SCHEDULE_TIME_PATTERN})"
    rf"(?:\s*(?:-|–)\s*(?P<end>{_SCHEDULE_TIME_PATTERN}))?"
    rf",\s*(?:\((?P<parenthesized_timezone>{_SCHEDULE_TIMEZONE_PATTERN})\)|"
    rf"(?P<timezone>{_SCHEDULE_TIMEZONE_PATTERN}))$"
)
_SCHEDULE_SAFE_TEXT_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9 .,&()/'’+\-]{0,159}$"
)
_SCHEDULE_PHONE_RE = re.compile(
    r"(?:\+?\d[\d .()\-]{6,}\d)"
)
_SCHEDULE_H1B_RE = re.compile(r"\bh[\s-]*1[\s-]*b\b", re.IGNORECASE)
_SCHEDULE_LINK_RE = re.compile(
    r"(?:https?://|www\.|\]\(|mailto:|tel:|slack:|teams:|discord:|linkedin\.com|"
    r"\b[A-Za-z0-9-]+\.(?:com|net|org|io|co|ly|app|dev|ai|us)(?:/|\b))",
    re.IGNORECASE,
)
_SCHEDULE_PRIVATE_MARKERS = (
    "h-1b",
    "h1b",
    "visa",
    "immigration",
    "sponsorship",
    "work authorization",
    "employment authorization",
    "recruiter",
    "private",
    "internal",
    "contact",
    "email",
    "phone",
    "message",
    "direct message",
    "follow up",
    "next action",
    "action item",
    "notes",
    "note:",
)
_SCHEDULE_GENERIC_RECRUITER_TITLE_RE = re.compile(
    r"(?P<eng_screen>\beng\s+recruiter\s+screen\b)|"
    r"(?P<discussion>\brecruiter\s+discussion\b)",
    re.IGNORECASE,
)
_SCHEDULE_HEADER_ALIASES = {
    0: {"date_time", "date_and_time", "datetime", "date", "when"},
    1: {"organization", "organisation", "company", "employer", "org"},
    2: {"activity", "title", "event", "event_type", "interview", "interview_stage", "stage", "round", "session"},
    3: {"location", "where", "venue"},
    4: {"status", "state", "status_and_next_step"},
}
_SCHEDULE_STATUS_ALIASES = {
    "scheduled": "Scheduled",
    "confirmed": "Scheduled",
    "upcoming": "Scheduled",
    "booked": "Scheduled",
    "pending": "Pending",
    "awaiting_confirmation": "Pending",
    "tentative": "Pending",
    "completed": "Completed",
    "complete": "Completed",
    "done": "Completed",
    "finished": "Completed",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "withdrawn": "Cancelled",
    "rescheduled": "Rescheduled",
    "moved": "Rescheduled",
}

# These markers are deliberately conservative.  If one reaches a field that
# is eligible for a public projection, that text is dropped rather than
# guessing whether it is safe.  Source columns that are wholly private are
# never inspected for copying in the first place.
class TrackerExportError(ValueError):
    """Raised when the private tracker cannot safely be exported."""


def require_local_path(path: Path | str, *, label: str) -> Path:
    """Reject local tracker files inside this repository.

    Local projections are intentionally external to Git.  Callers can still
    select any external directory, including a temporary directory for tests.
    """

    candidate = Path(path).expanduser()
    try:
        candidate.resolve(strict=False).relative_to(ROOT.resolve())
    except ValueError:
        return candidate
    raise TrackerExportError(f"{label} must live outside the CareerLens repository")


def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _validate_url(value: str, row_number: int) -> str:
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise TrackerExportError(
            f"row {row_number}: official_url must be an absolute http(s) URL"
        )
    return url


def _validate_date(value: str, field: str, row_number: int) -> str:
    value = value.strip()
    if not value:
        return ""
    if not _DATE_RE.fullmatch(value):
        raise TrackerExportError(
            f"row {row_number}: {field} must be an ISO date (YYYY-MM-DD)"
        )
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise TrackerExportError(
            f"row {row_number}: {field} is not a valid calendar date"
        ) from exc
    return value


def normalize_status(value: str, row_number: int = 0) -> str:
    """Return the public status for a private status or fail closed."""

    key = _clean(value).lower().replace("-", "_").replace(" ", "_")
    try:
        return _STATUS_ALIASES[key]
    except KeyError as exc:
        prefix = f"row {row_number}: " if row_number else ""
        raise TrackerExportError(f"{prefix}unknown status {value!r}") from exc


def _schedule_header_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _clean(value).casefold()).strip("_")


def _schedule_table_cells(line: str) -> list[str] | None:
    """Return strict pipe-table cells, rejecting Markdown extensions.

    The local schedule does not need rich Markdown.  A narrow reader avoids
    interpreting links, HTML, or a second ad-hoc table as public data.
    """

    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells = [_clean(cell) for cell in stripped[1:-1].split("|")]
    return cells


def _is_schedule_separator(cells: list[str]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
    )


def _schedule_rows(source: Path) -> list[tuple[int, list[str]]]:
    """Read only the one constrained five-column schedule table.

    Structural errors stop the local projection.  Individual unsafe rows are
    handled later and omitted, which leaves unrelated safe events available
    without ever carrying the unsafe source text into the projection.
    """

    if not source.is_file():
        raise FileNotFoundError("private schedule source is missing")
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    for index in range(len(lines) - 1):
        header = _schedule_table_cells(lines[index])
        separator = _schedule_table_cells(lines[index + 1])
        if header is None or separator is None:
            continue
        if len(header) != 5 or len(separator) != 5 or not _is_schedule_separator(separator):
            continue
        if any(
            _schedule_header_token(header[column]) not in aliases
            for column, aliases in _SCHEDULE_HEADER_ALIASES.items()
        ):
            continue
        if not header[2]:
            continue
        rows: list[tuple[int, list[str]]] = []
        for row_index in range(index + 2, len(lines)):
            cells = _schedule_table_cells(lines[row_index])
            if cells is None:
                break
            if len(cells) != 5 or _is_schedule_separator(cells):
                raise TrackerExportError("private schedule has an invalid event row")
            rows.append((row_index + 1, cells))
        return rows
    raise TrackerExportError("private schedule is missing its expected event table")


def _is_safe_schedule_text(value: str) -> bool:
    value = _clean(value)
    lowered = value.casefold()
    return (
        bool(_SCHEDULE_SAFE_TEXT_RE.fullmatch(value))
        and bool(_SAFE_TEXT_RE.fullmatch(value))
        and "@" not in value
        and _SCHEDULE_LINK_RE.search(value) is None
        and _SCHEDULE_PHONE_RE.search(value) is None
        and _SCHEDULE_H1B_RE.search(value) is None
        and not any(marker in lowered for marker in _SCHEDULE_PRIVATE_MARKERS)
    )


def public_schedule_title(value: str) -> str | None:
    value = _clean(value)
    if "recruiter" in value.casefold():
        lowered = value.casefold()
        if (
            not _SAFE_TEXT_RE.fullmatch(value)
            or "@" in value
            or _SCHEDULE_LINK_RE.search(value) is not None
            or _SCHEDULE_PHONE_RE.search(value) is not None
            or _SCHEDULE_H1B_RE.search(value) is not None
            or any(
                marker in lowered
                for marker in _SCHEDULE_PRIVATE_MARKERS
                if marker != "recruiter"
            )
        ):
            return None
        match = _SCHEDULE_GENERIC_RECRUITER_TITLE_RE.search(value)
        if match is None:
            return None
        return "Eng Recruiter Screen" if match.group("eng_screen") else "Recruiter Discussion"
    return value if _is_safe_schedule_text(value) else None


def _normalize_schedule_time(value: str) -> str:
    parsed = datetime.strptime(_clean(value).upper(), "%I:%M %p")
    return parsed.strftime("%I:%M %p").lstrip("0")


def _parse_schedule_datetime_base(value: str) -> tuple[str, str, str] | None:
    match = _SCHEDULE_T_DATETIME_RE.fullmatch(value)
    if match is None:
        match = _SCHEDULE_DATETIME_RE.fullmatch(value)
    if match is None:
        return None
    try:
        day = date.fromisoformat(match.group("day"))
        start = _normalize_schedule_time(match.group("start"))
        end = (
            _normalize_schedule_time(match.group("end"))
            if match.group("end")
            else ""
        )
    except ValueError:
        return None
    raw_timezone = match.groupdict().get("parenthesized_timezone") or match.group("timezone") or ""
    timezone_match = re.match(r"[A-Za-z]+", raw_timezone)
    timezone = timezone_match.group(0).upper() if timezone_match else ""
    allowed_timezones = {
        "PT", "PST", "PDT", "MT", "MST", "MDT", "CT", "CST", "CDT",
        "ET", "EST", "EDT", "UTC", "GMT",
    }
    if timezone not in allowed_timezones:
        return None
    display = f"{day.isoformat()} · {start}"
    if end:
        display += f"–{end}"
    sort_time = datetime.strptime(start, "%I:%M %p").strftime("%H:%M")
    return day.isoformat() + "T" + sort_time, display, timezone


def _parse_schedule_datetime(value: str) -> tuple[str, str, str] | None:
    value = _clean(value)
    parsed = _parse_schedule_datetime_base(value)
    if parsed is not None or " (" not in value:
        return parsed
    primary, alternate = value.rsplit(" (", 1)
    if not alternate.endswith(")"):
        return None
    primary_parsed = _parse_schedule_datetime_base(primary)
    alternate_parsed = _parse_schedule_datetime_base(alternate[:-1])
    if primary_parsed is None or alternate_parsed is None:
        return None
    if primary_parsed[2] in {"PT", "PST", "PDT"}:
        return primary_parsed
    if alternate_parsed[2] in {"PT", "PST", "PDT"}:
        return alternate_parsed
    return primary_parsed


def _schedule_status(value: str) -> str:
    # The source combines status and next step.  That cell may carry a private
    # action or link, so it never crosses the boundary verbatim.  Preserve a
    # safely identified event with a generic scheduled state instead.
    if not _is_safe_schedule_text(value):
        return "Scheduled"
    key = _schedule_header_token(value)
    # A safe, unfamiliar source label does not cross the boundary.  An event
    # with a valid date is represented as scheduled rather than exposing the
    # private wording that accompanied it.
    return _SCHEDULE_STATUS_ALIASES.get(key, "Scheduled")


def _schedule_next_step(status: str) -> str:
    return {
        "Scheduled": "Prepare for the event",
        "Pending": "Await event confirmation",
        "Completed": "No action",
        "Cancelled": "No action",
        "Rescheduled": "Check the updated event time",
    }[status]


def export_schedule_events(source: Path | str = DEFAULT_SCHEDULE_SOURCE) -> list[dict[str, str]]:
    """Create a strict local-only schedule projection from private Markdown.

    The returned records contain only the schedule allowlist.  Rows with an
    unsafe title, organization, location, or time are dropped.  The combined
    private status/next-step source cell is replaced with a generic state, so
    no raw action, note, URL, contact, or employment detail is copied.
    """

    events_with_sort_keys: list[tuple[str, dict[str, str]]] = []
    for _row_number, row in _schedule_rows(Path(source)):
        sort_key_and_display = _parse_schedule_datetime(row[0])
        if sort_key_and_display is None:
            continue
        title, organization, location = row[2], row[1], row[3]
        safe_title = public_schedule_title(title)
        if safe_title is None or not all(
            _is_safe_schedule_text(value) for value in (organization, location)
        ):
            continue
        status = _schedule_status(row[4])
        sort_key, display, timezone = sort_key_and_display
        event = {
            "title": safe_title,
            "organization": _clean(organization),
            "datetime": display,
            "timezone": timezone,
            "location": _clean(location),
            "status": status,
            "next_step": _schedule_next_step(status),
        }
        if tuple(event) != SCHEDULE_PUBLIC_FIELDS:
            raise TrackerExportError("internal error: local schedule schema is not allowlisted")
        events_with_sort_keys.append((sort_key, event))
    events_with_sort_keys.sort(
        key=lambda item: (
            item[0],
            item[1]["organization"].casefold(),
            item[1]["title"].casefold(),
        )
    )
    return [event for _sort_key, event in events_with_sort_keys]


def _public_next_action(_raw: str, status: str) -> str:
    """Return a status-derived action without copying private source prose."""

    defaults = {
        "Discovered": "Verify official role page",
        "Verified": "Review before applying",
        "Review": "Review before applying",
        "Approved": "Prepare application",
        "Submitted": "Monitor recruiter response",
        "Interview": "Prepare for next interview",
        "Offer": "Review offer",
        "Closed": "No action",
    }
    return defaults[status]


def _public_note(raw: str, private_status: str, _public_status: str) -> str:
    value = _clean(raw)
    if not value:
        return ""
    # The private notes column is never copied.  The sole exception is a
    # deterministic, generic expiration label when the note itself records
    # an official-page condition that is already public.  This intentionally
    # rejects otherwise harmless-looking internal prose instead of trying to
    # infer whether a note is safe.
    lowered = value.casefold()
    official_page_reference = "official" in lowered and (
        "page" in lowered or "listing" in lowered
    )
    official_expiry = any(
        marker in lowered for marker in ("job not found", "no longer", "expired", "closed")
    )
    if private_status in {"expired", "closed"} and official_page_reference and official_expiry:
        return "Official role page appears expired."
    return ""


def _fit_score(value: str, row_number: int) -> int:
    raw = value.strip()
    try:
        score = int(raw)
    except ValueError as exc:
        raise TrackerExportError(
            f"row {row_number}: fit_score must be an integer from 0 to 100"
        ) from exc
    if not 0 <= score <= 100:
        raise TrackerExportError(
            f"row {row_number}: fit_score must be an integer from 0 to 100"
        )
    return score


def _humanize(value: str) -> str:
    return _clean(value).replace("_", " ")


def _read_rows(source: Path) -> list[dict[str, str]]:
    if source.suffix == ".db":
        if not source.is_file():
            raise FileNotFoundError(f"private tracker database is missing: {source}")
        query = (
            "SELECT " + ", ".join(SOURCE_REQUIRED_COLUMNS)
            + " FROM applications ORDER BY company COLLATE NOCASE, role COLLATE NOCASE, official_url"
        )
        try:
            with sqlite3.connect(source) as db:
                db.row_factory = sqlite3.Row
                return [
                    {key: str(value if value is not None else "") for key, value in dict(row).items()}
                    for row in db.execute(query).fetchall()
                ]
        except sqlite3.Error as exc:
            raise TrackerExportError(
                f"could not read private tracker database: {exc}"
            ) from exc
    if not source.is_file():
        raise FileNotFoundError(f"private tracker is missing: {source}")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [field for field in SOURCE_REQUIRED_COLUMNS if field not in fieldnames]
        if missing:
            raise TrackerExportError(
                "private tracker is missing required columns: " + ", ".join(missing)
            )
        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            # A completely blank trailing line is harmless; a partially blank
            # row is not silently turned into a public record.
            if not any(_clean(value) for value in row.values() if value is not None):
                continue
            rows.append({key: value or "" for key, value in row.items()})
        return rows


def export_records(source: Path | str = DEFAULT_SOURCE) -> list[dict[str, object]]:
    """Parse and sanitize ``source`` into sorted public role records."""

    source = Path(source)
    rows = _read_rows(source)
    records: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=2):
        company = _clean(row["company"])
        role = _clean(row["role"])
        location = _clean(row["location"])
        work_mode = _clean(row["work_mode"])
        tier = _humanize(row["tier"])
        resume_track = _humanize(row["resume_track"])
        if not company or not role:
            raise TrackerExportError(f"row {row_number}: company and role are required")
        official_url = _validate_url(row["official_url"], row_number)
        private_status = _clean(row["status"]).lower().replace("-", "_").replace(" ", "_")
        status = normalize_status(row["status"], row_number)
        verified_date = _validate_date(row["verified_date"], "verified_date", row_number)
        submitted_date = _validate_date(row["submitted_date"], "submitted_date", row_number)
        _validate_date(row["approved_date"], "approved_date", row_number)
        record: dict[str, object] = {
            "company": company,
            "role": role,
            "job_url": official_url,
            "location": location,
            "work_mode": work_mode,
            "tier": tier,
            "fit_score": _fit_score(row["fit_score"], row_number),
            "resume_track": resume_track,
            "status": status,
            "verified_date": verified_date,
            "applied_date": submitted_date,
            "next_action": _public_next_action(row["next_action"], status),
            "public_note": _public_note(row["notes"], private_status, status),
        }
        # A final schema assertion protects future edits from accidentally
        # adding an unreviewed key to the public artifact.
        if tuple(record) != PUBLIC_FIELDS:
            raise TrackerExportError("internal error: public schema is not allowlisted")
        records.append(record)
    records.sort(
        key=lambda item: (
            str(item["company"]).casefold(),
            str(item["role"]).casefold(),
            str(item["job_url"]),
        )
    )
    return records


def build_projection(source: Path | str = DEFAULT_SOURCE) -> dict[str, object]:
    """Return the deterministic JSON document for a private tracker."""

    records = export_records(source)
    dates = [
        str(record[field])
        for record in records
        for field in ("verified_date", "applied_date")
        if record[field]
    ]
    return {
        "generated_date": max(dates) if dates else "",
        "roles": records,
    }


def _learning_percent(numerator: int, denominator: int) -> int | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator * 100)


def _empty_learning_projection(status: str = "unavailable") -> dict[str, object]:
    """Return the stable, deliberately small local Learning schema."""

    projection: dict[str, object] = {
        "status": status,
        "updated_at": "",
        "attempts": {"total": 0, "complete": 0, "incomplete": 0},
        "attempt_completion": {"complete": 0, "total": 0, "percent": None},
        "independent_success": {
            "met": 0,
            "total": 0,
            "percent": None,
            "unscored": 0,
        },
        "section_completion": {"complete": 0, "total": 0, "percent": None},
        "open_repairs": 0,
        "due_repairs": 0,
        "open_gaps": 0,
        "due_gaps": 0,
        "latest_states": {state: 0 for state in LEARNING_STATES},
        "dimension_scores": [],
    }
    if tuple(projection) != LEARNING_LOCAL_FIELDS:
        raise TrackerExportError("internal error: local learning schema is not allowlisted")
    return projection


def _learning_json_object(value: object) -> dict[str, object] | None:
    if not isinstance(value, str):
        return None
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _learning_json_list(value: object) -> list[object] | None:
    if not isinstance(value, str):
        return None
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError):
        return None
    return decoded if isinstance(decoded, list) else None


def _learning_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _learning_connection(path: Path | str) -> sqlite3.Connection | None:
    """Open the private Coach evidence store read-only, or return no data.

    This endpoint is intentionally resilient to an unavailable Coach store so
    the application tracker remains usable when the learner has not started a
    Coach session yet.  It never creates a database, writes a pragma, or
    returns an exception containing a private path or database detail.
    """

    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.is_file():
        return None
    try:
        resolved = candidate.resolve(strict=True)
        connection = sqlite3.connect(
            resolved.as_uri() + "?mode=ro",
            uri=True,
        )
        connection.row_factory = sqlite3.Row
        return connection
    except (OSError, ValueError, sqlite3.Error):
        return None


def build_learning_projection(
    coach_db_path: Path | str = DEFAULT_COACH_DB,
) -> dict[str, object]:
    """Build a privacy-preserving live summary of Coach evidence.

    The projection is a local UI contract, not a Coach scorecard.  It exposes
    only evidence counts, current state counts, and individually saved rubric
    observations.  It never averages unrelated attempts into a readiness or
    mastery score, and it deliberately omits all learner wording and context.
    """

    projection = _empty_learning_projection()
    connection = _learning_connection(coach_db_path)
    if connection is None:
        return projection

    try:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if not {"events", "evaluations"}.issubset(table_names):
            return projection

        event_rows = connection.execute(
            """
            SELECT events.seq, events.occurred_at, events.track,
                   events.competency, events.received, evaluations.body
            FROM events JOIN evaluations USING(event_id)
            ORDER BY events.seq
            """
        ).fetchall()
        repair_rows = []
        if "repairs" in table_names:
            repair_rows = connection.execute(
                """
                SELECT events.seq, events.track, events.competency, repairs.body
                FROM events JOIN repairs USING(event_id)
                ORDER BY events.seq
                """
            ).fetchall()
        section_rows = []
        if "study_sections" in table_names:
            section_rows = connection.execute(
                """
                SELECT seq, occurred_at, track, topic, stage, breakdown, status
                FROM study_sections ORDER BY seq
                """
            ).fetchall()
        gap_rows = []
        if "gap_items" in table_names:
            gap_rows = connection.execute(
                """
                SELECT seq, track, topic, gap_key, status, body
                FROM gap_items ORDER BY seq
                """
            ).fetchall()
        debrief_rows = []
        if "debriefs" in table_names:
            debrief_rows = connection.execute(
                "SELECT occurred_at FROM debriefs ORDER BY seq"
            ).fetchall()
    except sqlite3.Error:
        return projection
    finally:
        connection.close()

    attempt_total = 0
    attempt_complete = 0
    independent_met = 0
    independent_total = 0
    independent_unscored = 0
    latest_states_by_capability: dict[tuple[object, object], str] = {}
    latest_dimensions: dict[str, tuple[datetime, int, int]] = {}
    activity_times: list[datetime] = []

    for row in event_rows:
        occurred_at = _learning_timestamp(row["occurred_at"])
        if occurred_at is not None:
            activity_times.append(occurred_at)
        evaluation = _learning_json_object(row["body"])
        if evaluation is None:
            continue
        evidence_type = evaluation.get("evidence_type")
        scope = evaluation.get("scope")
        state = evaluation.get("state")
        attempted = evidence_type in {"prompted", "independent"}
        complete = attempted and scope == "complete"
        if attempted:
            attempt_total += 1
            if complete:
                attempt_complete += 1

        if state in LEARNING_STATES:
            capability = (row["track"], row["competency"])
            if attempted or capability not in latest_states_by_capability:
                latest_states_by_capability[capability] = state

        received = _learning_json_object(row["received"])
        unhinted_independent = (
            complete
            and evidence_type == "independent"
            and received is not None
            and isinstance(received.get("hints", ""), str)
            and not received.get("hints", "").strip()
        )
        outcome = evaluation.get("attempt_outcome")
        if unhinted_independent:
            if outcome in {"met", "not_met"}:
                independent_total += 1
                if outcome == "met":
                    independent_met += 1
            else:
                independent_unscored += 1

        rubric_scores = evaluation.get("rubric_scores")
        if not isinstance(rubric_scores, dict) or occurred_at is None:
            continue
        dimensions = rubric_scores.get("dimensions")
        if not isinstance(dimensions, dict):
            continue
        for dimension, observation in dimensions.items():
            if dimension not in LEARNING_DIMENSIONS or not isinstance(observation, dict):
                continue
            score = observation.get("score")
            if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 3:
                continue
            previous = latest_dimensions.get(dimension)
            candidate = (occurred_at, int(row["seq"]), score)
            if previous is None or candidate[:2] >= previous[:2]:
                latest_dimensions[dimension] = candidate

    latest_sections: dict[tuple[object, object, object, object], str] = {}
    for row in section_rows:
        occurred_at = _learning_timestamp(row["occurred_at"])
        if occurred_at is not None:
            activity_times.append(occurred_at)
        status = row["status"]
        if status not in {"complete", "in_progress"}:
            continue
        section_key = (row["track"], row["topic"], row["stage"], row["breakdown"])
        latest_sections[section_key] = status

    latest_repairs: dict[tuple[object, object, str], tuple[str, datetime | None]] = {}
    for row in repair_rows:
        repairs = _learning_json_list(row["body"])
        if repairs is None:
            continue
        for repair in repairs:
            if not isinstance(repair, dict):
                continue
            target = repair.get("target")
            status = repair.get("status", "open")
            if not isinstance(target, str) or not target.strip() or status not in {"open", "resolved"}:
                continue
            repair_key = (row["track"], row["competency"], target)
            latest_repairs[repair_key] = (
                status,
                _learning_timestamp(repair.get("due_at")),
            )

    latest_gaps: dict[tuple[object, object, object], tuple[str, datetime | None]] = {}
    for row in gap_rows:
        status = row["status"]
        gap_key = row["gap_key"]
        if status not in {"open", "resolved"} or not isinstance(gap_key, str) or not gap_key:
            continue
        body = _learning_json_object(row["body"])
        gap_identity = (row["track"], row["topic"], gap_key)
        latest_gaps[gap_identity] = (
            status,
            _learning_timestamp(body.get("due_at") if body else None),
        )

    for row in debrief_rows:
        occurred_at = _learning_timestamp(row["occurred_at"])
        if occurred_at is not None:
            activity_times.append(occurred_at)

    now = datetime.now(timezone.utc)
    latest_states = {state: 0 for state in LEARNING_STATES}
    for state in latest_states_by_capability.values():
        latest_states[state] += 1
    section_total = len(latest_sections)
    section_complete = sum(status == "complete" for status in latest_sections.values())
    open_repairs = [
        due_at
        for status, due_at in latest_repairs.values()
        if status == "open"
    ]
    open_gaps = [
        due_at
        for status, due_at in latest_gaps.values()
        if status == "open"
    ]
    dimension_scores = [
        {
            "dimension": dimension,
            "score": latest_dimensions[dimension][2],
            "observed_at": latest_dimensions[dimension][0].isoformat(timespec="seconds"),
        }
        for dimension in LEARNING_DIMENSIONS
        if dimension in latest_dimensions
    ]
    has_evidence = bool(
        event_rows or repair_rows or section_rows or gap_rows or debrief_rows
    )
    projection = {
        "status": "active" if has_evidence else "no_evidence",
        "updated_at": max(activity_times).isoformat(timespec="seconds") if activity_times else "",
        "attempts": {
            "total": attempt_total,
            "complete": attempt_complete,
            "incomplete": attempt_total - attempt_complete,
        },
        "attempt_completion": {
            "complete": attempt_complete,
            "total": attempt_total,
            "percent": _learning_percent(attempt_complete, attempt_total),
        },
        "independent_success": {
            "met": independent_met,
            "total": independent_total,
            "percent": _learning_percent(independent_met, independent_total),
            "unscored": independent_unscored,
        },
        "section_completion": {
            "complete": section_complete,
            "total": section_total,
            "percent": _learning_percent(section_complete, section_total),
        },
        "open_repairs": len(open_repairs),
        "due_repairs": sum(due_at is not None and due_at <= now for due_at in open_repairs),
        "open_gaps": len(open_gaps),
        "due_gaps": sum(due_at is not None and due_at <= now for due_at in open_gaps),
        "latest_states": latest_states,
        "dimension_scores": dimension_scores,
    }
    if tuple(projection) != LEARNING_LOCAL_FIELDS:
        return _empty_learning_projection()
    return projection


def _empty_pilot_operations_projection(status: str = "unavailable") -> dict[str, object]:
    """Return the stable aggregate-only local Pilot Operations schema."""

    projection = {
        "status": status,
        "latest": {"completed_at": "", "status": ""},
        "run_count": 0,
        "source_coverage": {
            source: {
                "count": 0,
                "latest_outcome": "not_checked",
                "outcome_counts": {
                    outcome: 0 for outcome in PILOT_SOURCE_OUTCOMES
                },
            }
            for source in PILOT_SOURCE_KEYS
        },
        "inbox": {
            "latest_status": "not_checked",
            "status_counts": {status: 0 for status in PILOT_INBOX_STATUSES},
            "actionable": 0,
        },
        "totals": {"discovered": 0, "verified": 0, "submitted": 0, "blocked": 0},
        "queue_counts": {key: 0 for key in PILOT_DECISION_KEYS},
        "submission_verification": {
            "latest_status": "not_needed",
            "status_counts": {
                result: 0 for result in PILOT_SUBMISSION_VERIFICATION_RESULTS
            },
        },
        "tracker_transaction": {
            "latest_status": "not_needed",
            "status_counts": {
                result: 0 for result in PILOT_TRACKER_TRANSACTION_RESULTS
            },
        },
        "cleanup": {
            "latest_status": "not_needed",
            "status_counts": {
                result: 0 for result in PILOT_CLEANUP_RESULTS
            },
        },
    }
    if tuple(projection) != PILOT_OPERATIONS_LOCAL_FIELDS:
        raise AssertionError("Pilot Operations local schema is not allowlisted")
    return projection


def _pilot_operations_connection(path: Path | str) -> sqlite3.Connection | None:
    try:
        resolved = Path(path).resolve(strict=True)
        connection = sqlite3.connect(resolved.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection
    except (OSError, ValueError, sqlite3.Error):
        return None


def _pilot_operations_timestamp(value: object) -> tuple[datetime, str] | None:
    if not isinstance(value, str) or not value or len(value) > 64:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    normalized = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return normalized, normalized.isoformat()


def _pilot_operations_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if 0 <= value <= PILOT_MAX_COUNT else None


def build_pilot_operations_projection(
    pilot_db_path: Path | str = DEFAULT_DB,
) -> dict[str, object]:
    """Read safe Pilot run aggregates from SQLite without exposing receipts.

    The source is opened with SQLite's read-only URI mode.  Any unavailable,
    malformed, or incomplete schema returns the same empty local shape rather
    than revealing a path, database error, or unvalidated column value.
    """

    projection = _empty_pilot_operations_projection()
    connection = _pilot_operations_connection(pilot_db_path)
    if connection is None:
        return projection
    columns = (
        "id",
        "completed_at",
        "result",
        *(
            column
            for source in PILOT_SOURCE_KEYS
            for column in (f"source_{source}_outcome", f"source_{source}_count")
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
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'pilot_runs'"
        ).fetchone()
        if table is None:
            return projection
        rows = connection.execute(
            f"SELECT {', '.join(columns)} FROM pilot_runs ORDER BY id"
        ).fetchall()
    except sqlite3.Error:
        return projection
    finally:
        connection.close()

    latest: tuple[datetime, int, str] | None = None
    for row in rows:
        timestamp = _pilot_operations_timestamp(row["completed_at"])
        row_id = row["id"] if isinstance(row["id"], int) and row["id"] >= 0 else None
        result = row["result"]
        if timestamp is None or row_id is None or result not in PILOT_RUN_RESULTS:
            continue
        source_values: dict[str, tuple[str, int]] = {}
        for source in PILOT_SOURCE_KEYS:
            outcome = row[f"source_{source}_outcome"]
            count = _pilot_operations_count(row[f"source_{source}_count"])
            if (
                outcome not in PILOT_SOURCE_OUTCOMES
                or count is None
                or (outcome != "checked" and count != 0)
            ):
                source_values = {}
                break
            source_values[source] = (outcome, count)
        if not source_values:
            continue
        inbox_status = row["inbox_status"]
        inbox_actionable = _pilot_operations_count(row["inbox_actionable_count"])
        totals = {
            key: _pilot_operations_count(row[f"{key}_count"])
            for key in ("discovered", "verified", "submitted", "blocked")
        }
        decisions = {
            key: _pilot_operations_count(row[f"{key}_decisions"])
            for key in PILOT_DECISION_KEYS
        }
        verification = row["submission_verification"]
        tracker = row["tracker_transaction"]
        cleanup = row["cleanup"]
        if (
            inbox_status not in PILOT_INBOX_STATUSES
            or inbox_actionable is None
            or (inbox_status != "checked" and inbox_actionable != 0)
            or any(value is None for value in totals.values())
            or any(value is None for value in decisions.values())
            or verification not in PILOT_SUBMISSION_VERIFICATION_RESULTS
            or tracker not in PILOT_TRACKER_TRANSACTION_RESULTS
            or cleanup not in PILOT_CLEANUP_RESULTS
        ):
            continue
        projection["run_count"] += 1
        projection["inbox"]["status_counts"][inbox_status] += 1
        projection["inbox"]["actionable"] += inbox_actionable
        for key, count in totals.items():
            projection["totals"][key] += count
        for key, count in decisions.items():
            projection["queue_counts"][key] += count
        projection["submission_verification"]["status_counts"][verification] += 1
        projection["tracker_transaction"]["status_counts"][tracker] += 1
        projection["cleanup"]["status_counts"][cleanup] += 1
        for source, (outcome, count) in source_values.items():
            projection["source_coverage"][source]["count"] += count
            projection["source_coverage"][source]["outcome_counts"][outcome] += 1
        occurred_at, serialized_at = timestamp
        candidate = (occurred_at, row_id, result)
        if latest is None or candidate[:2] >= latest[:2]:
            latest = candidate
            projection["latest"] = {
                "completed_at": serialized_at,
                "status": result,
            }
            projection["inbox"]["latest_status"] = inbox_status
            projection["submission_verification"]["latest_status"] = verification
            projection["tracker_transaction"]["latest_status"] = tracker
            projection["cleanup"]["latest_status"] = cleanup
            for source, (outcome, _count) in source_values.items():
                projection["source_coverage"][source]["latest_outcome"] = outcome
    if not projection["run_count"]:
        return _empty_pilot_operations_projection("no_runs")
    projection["status"] = "available"
    if tuple(projection) != PILOT_OPERATIONS_LOCAL_FIELDS:
        return _empty_pilot_operations_projection()
    return projection


def build_local_projection(
    source: Path | str = DEFAULT_DB,
    schedule_source: Path | str = DEFAULT_SCHEDULE_SOURCE,
    *,
    coach_db_path: Path | str = DEFAULT_COACH_DB,
    pilot_db_path: Path | str | None = None,
) -> dict[str, object]:
    """Return the loopback-only tracker view, including local-only aggregates.

    This helper is intentionally separate from :func:`build_projection` and
    is for the local HTTP server only.  Callers must keep its result in memory
    or in local-only storage outside the repository.
    """

    public_projection = build_projection(source)
    return {
        "generated_date": public_projection["generated_date"],
        "roles": public_projection["roles"],
        "schedule": export_schedule_events(schedule_source),
        "learning": build_learning_projection(coach_db_path),
        "pilot_operations": build_pilot_operations_projection(
            source if pilot_db_path is None else pilot_db_path
        ),
    }


def write_projection(
    output: Path | str = DEFAULT_OUTPUT,
    source: Path | str = DEFAULT_SOURCE,
) -> Path:
    """Write a deterministic local projection outside the repository."""

    output = require_local_path(output, label="local tracker projection")
    output.parent.mkdir(parents=True, exist_ok=True)
    projection = build_projection(source)
    serialized = json.dumps(
        projection,
        ensure_ascii=False,
        indent=2,
        separators=(",", ": "),
    )
    output.write_text(serialized + "\n", encoding="utf-8")
    return output


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        path = write_projection(args.output, args.source)
    except (FileNotFoundError, TrackerExportError) as exc:
        print(f"application tracker export failed: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
