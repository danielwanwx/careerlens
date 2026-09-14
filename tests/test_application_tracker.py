import csv
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_exporter():
    path = ROOT / "scripts/export_application_tracker.py"
    spec = importlib.util.spec_from_file_location("export_application_tracker", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_store():
    path = ROOT / "scripts/application_store.py"
    spec = importlib.util.spec_from_file_location("application_store_for_tracker_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


HEADERS = [
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
]


def write_tracker(path: Path, **overrides) -> None:
    row = {
        "company": "Example AI",
        "role": "Senior Software Engineer, Platform",
        "official_url": "https://example.com/jobs/platform",
        "location": "Remote",
        "work_mode": "Remote",
        "employment_constraints": "Private work authorization detail",
        "tier": "P0_CALIBRATION",
        "fit_score": "87",
        "resume_track": "Agentic_AI",
        "status": "verified",
        "verified_date": "2026-09-01",
        "approved_date": "",
        "submitted_date": "",
        "next_action": "Review in first batch",
        "notes": "Agent runtime, APIs, and observability",
    }
    row.update(overrides)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerow(row)


def write_schedule(path: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    lines = [
        "# Interview and events",
        "",
        "| Date / Time | Organization | Interview stage | Location | Status and next step |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_coach_database(path: Path) -> None:
    """Create synthetic Coach evidence that must stay aggregate-only."""

    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE events (
              seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL,
              digest TEXT NOT NULL, occurred_at TEXT NOT NULL, mode TEXT NOT NULL,
              track TEXT NOT NULL, competency TEXT NOT NULL, received TEXT NOT NULL,
              context TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE evaluations (
              event_id TEXT PRIMARY KEY REFERENCES events(event_id), body TEXT NOT NULL
            );
            CREATE TABLE repairs (
              event_id TEXT PRIMARY KEY REFERENCES events(event_id), body TEXT NOT NULL
            );
            CREATE TABLE study_sections (
              seq INTEGER PRIMARY KEY, section_id TEXT UNIQUE NOT NULL,
              digest TEXT NOT NULL, occurred_at TEXT NOT NULL, track TEXT NOT NULL,
              topic TEXT NOT NULL, stage TEXT NOT NULL, breakdown TEXT NOT NULL,
              status TEXT NOT NULL, body TEXT NOT NULL
            );
            CREATE TABLE debriefs (
              seq INTEGER PRIMARY KEY, debrief_id TEXT UNIQUE NOT NULL,
              digest TEXT NOT NULL, occurred_at TEXT NOT NULL, mode TEXT NOT NULL,
              track TEXT NOT NULL, topic TEXT NOT NULL, body TEXT NOT NULL
            );
            CREATE TABLE gap_items (
              seq INTEGER PRIMARY KEY, gap_event_id TEXT UNIQUE NOT NULL,
              gap_key TEXT NOT NULL, debrief_id TEXT NOT NULL,
              track TEXT NOT NULL, topic TEXT NOT NULL, stage TEXT NOT NULL,
              breakdown TEXT NOT NULL, status TEXT NOT NULL, body TEXT NOT NULL
            );
            """
        )
        events = (
            (
                1,
                "synthetic-event-1",
                "digest-1",
                "2026-09-10T10:00:00-07:00",
                "Practice",
                "SYNTHETIC_PRIVATE_TRACK",
                "SYNTHETIC_PRIVATE_COMPETENCY",
                json.dumps(
                    {
                        "transcript": "SYNTHETIC_PRIVATE_TRANSCRIPT",
                        "original_answer": "SYNTHETIC_PRIVATE_ANSWER",
                        "hints": "",
                    }
                ),
                "{}",
                json.dumps(
                    {
                        "evidence_type": "independent",
                        "scope": "complete",
                        "dimensions": {"concepts": "SYNTHETIC_PRIVATE_EVALUATION"},
                        "state": "independent_today",
                        "attempt_outcome": "met",
                        "rubric_scores": {
                            "rubric_version": "knowloop-1",
                            "dimensions": {
                                "concepts": {
                                    "score": 2,
                                    "reason": "SYNTHETIC_PRIVATE_REASON",
                                }
                            },
                        },
                    }
                ),
            ),
            (
                2,
                "synthetic-event-2",
                "digest-2",
                "2026-09-10T11:00:00-07:00",
                "Practice",
                "SYNTHETIC_PRIVATE_TRACK",
                "SYNTHETIC_PRIVATE_COMPETENCY_TWO",
                json.dumps(
                    {
                        "transcript": "SYNTHETIC_PRIVATE_TRANSCRIPT_TWO",
                        "original_answer": "",
                        "hints": "SYNTHETIC_PRIVATE_HINT",
                    }
                ),
                "{}",
                json.dumps(
                    {
                        "evidence_type": "prompted",
                        "scope": "complete",
                        "dimensions": {"structure": "SYNTHETIC_PRIVATE_EVALUATION_TWO"},
                        "state": "needs_hint",
                    }
                ),
            ),
            (
                3,
                "synthetic-event-3",
                "digest-3",
                "2026-09-10T12:00:00-07:00",
                "Practice",
                "SYNTHETIC_PRIVATE_TRACK",
                "SYNTHETIC_PRIVATE_COMPETENCY_THREE",
                json.dumps(
                    {
                        "transcript": "SYNTHETIC_PRIVATE_TRANSCRIPT_THREE",
                        "original_answer": "SYNTHETIC_PRIVATE_PARTIAL_ANSWER",
                        "hints": "",
                    }
                ),
                "{}",
                json.dumps(
                    {
                        "evidence_type": "independent",
                        "scope": "incomplete",
                        "dimensions": {"application": "SYNTHETIC_PRIVATE_EVALUATION_THREE"},
                        "state": "needs_check",
                    }
                ),
            ),
        )
        for event in events:
            connection.execute(
                """
                INSERT INTO events(seq,event_id,digest,occurred_at,mode,track,competency,received,context)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                event[:9],
            )
            connection.execute(
                "INSERT INTO evaluations(event_id,body) VALUES(?,?)",
                (event[1], event[9]),
            )
            repair_body = (
                json.dumps(
                    [
                        {
                            "target": "SYNTHETIC_PRIVATE_REPAIR_TARGET",
                            "due_at": "2000-01-01T00:00:00+00:00",
                            "status": "open",
                        }
                    ]
                )
                if event[1] == "synthetic-event-1"
                else "[]"
            )
            connection.execute(
                "INSERT INTO repairs(event_id,body) VALUES(?,?)",
                (event[1], repair_body),
            )
        connection.executemany(
            """
            INSERT INTO study_sections(
              seq,section_id,digest,occurred_at,track,topic,stage,breakdown,status,body
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                (
                    1,
                    "synthetic-section-1",
                    "digest-section-1",
                    "2026-09-10T12:30:00-07:00",
                    "SYNTHETIC_PRIVATE_TRACK",
                    "SYNTHETIC_PRIVATE_TOPIC",
                    "Synthetic stage",
                    "Synthetic breakdown",
                    "complete",
                    "{}",
                ),
                (
                    2,
                    "synthetic-section-2",
                    "digest-section-2",
                    "2026-09-10T12:45:00-07:00",
                    "SYNTHETIC_PRIVATE_TRACK",
                    "SYNTHETIC_PRIVATE_TOPIC_TWO",
                    "Synthetic stage",
                    "Synthetic breakdown",
                    "in_progress",
                    "{}",
                ),
            ),
        )
        connection.executemany(
            """
            INSERT INTO gap_items(
              seq,gap_event_id,gap_key,debrief_id,track,topic,stage,breakdown,status,body
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                (
                    1,
                    "synthetic-gap-open",
                    "SYNTHETIC_PRIVATE_GAP",
                    "synthetic-debrief",
                    "SYNTHETIC_PRIVATE_TRACK",
                    "SYNTHETIC_PRIVATE_TOPIC",
                    "Synthetic stage",
                    "Synthetic breakdown",
                    "open",
                    json.dumps(
                        {
                            "due_at": "2000-01-01T00:00:00+00:00",
                            "observed_shortage": "SYNTHETIC_PRIVATE_GAP_DETAIL",
                        }
                    ),
                ),
                (
                    2,
                    "synthetic-gap-resolved",
                    "SYNTHETIC_PRIVATE_RESOLVED_GAP",
                    "synthetic-debrief",
                    "SYNTHETIC_PRIVATE_TRACK",
                    "SYNTHETIC_PRIVATE_TOPIC_TWO",
                    "Synthetic stage",
                    "Synthetic breakdown",
                    "resolved",
                    "{}",
                ),
            ),
        )
        connection.commit()
    finally:
        connection.close()


class ApplicationTrackerExportTests(unittest.TestCase):
    def test_allowlist_and_public_status_normalization(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            write_tracker(
                source,
                status="submitted",
                submitted_date="2026-09-01",
                employment_constraints="H-1B and private location detail",
            )
            projection = exporter.build_projection(source)
            self.assertEqual("2026-09-01", projection["generated_date"])
            record = projection["roles"][0]
            self.assertEqual(list(exporter.PUBLIC_FIELDS), list(record))
            self.assertEqual("Submitted", record["status"])
            self.assertEqual("2026-09-01", record["applied_date"])
            self.assertEqual("Agentic AI", record["resume_track"])
            self.assertNotIn("employment_constraints", record)
            self.assertNotIn("approved_date", record)
            self.assertNotIn("H-1B", json.dumps(projection))

    def test_private_note_is_dropped_and_generic_action_is_used(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            write_tracker(
                source,
                status="submitted",
                next_action="Email recruiter at private@example.com",
                notes="Application answers and confirmation: H-1B transfer discussed",
            )
            record = exporter.build_projection(source)["roles"][0]
            self.assertEqual("Monitor recruiter response", record["next_action"])
            self.assertEqual("", record["public_note"])
            self.assertNotIn("private@example.com", json.dumps(record))

    def test_next_action_is_status_derived_when_source_contains_private_workflow_text(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            private_action = (
                "Solve CAPTCHA, send recruiter a message, and paste the "
                "application answer into the handoff"
            )
            write_tracker(source, status="approved", next_action=private_action)
            record = exporter.build_projection(source)["roles"][0]
            self.assertEqual("Prepare application", record["next_action"])
            self.assertNotIn("CAPTCHA", json.dumps(record))
            self.assertNotIn("recruiter", json.dumps(record).casefold())

    def test_innocuous_looking_private_note_is_still_dropped(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            write_tracker(source, notes="Strong match based on my platform experience")
            record = exporter.build_projection(source)["roles"][0]
            self.assertEqual("", record["public_note"])
            self.assertNotIn("Strong match based on my platform experience", json.dumps(record))

    def test_terminal_states_map_to_closed(self):
        exporter = load_exporter()
        for private_status in ("expired", "rejected", "withdrawn", "blocked", "skipped"):
            self.assertEqual("Closed", exporter.normalize_status(private_status))

    def test_review_ready_maps_to_review(self):
        exporter = load_exporter()
        self.assertEqual("Review", exporter.normalize_status("review_ready"))

    def test_unknown_status_invalid_date_and_url_fail_closed(self):
        exporter = load_exporter()
        cases = (
            {"status": "maybe"},
            {"verified_date": "09/01/2026"},
            {"official_url": "javascript:alert(1)"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "tracker.csv"
                write_tracker(source, **overrides)
                with self.assertRaises(exporter.TrackerExportError):
                    exporter.build_projection(source)

    def test_missing_required_column_fails(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            source.write_text("company,role\nExample,Role\n", encoding="utf-8")
            with self.assertRaises(exporter.TrackerExportError):
                exporter.build_projection(source)

    def test_output_is_byte_deterministic(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            write_tracker(source)
            exporter.write_projection(first, source)
            exporter.write_projection(second, source)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                hashlib.sha256(second.read_bytes()).hexdigest(),
            )

    def test_static_projection_output_cannot_be_written_inside_the_repository(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            write_tracker(source)
            with self.assertRaisesRegex(
                exporter.TrackerExportError, "outside the CareerLens repository"
            ):
                exporter.write_projection(
                    ROOT / "data" / "application-tracker.json", source
                )

    def test_empty_tracker_is_valid_projection(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerow(HEADERS)
            self.assertEqual({"generated_date": "", "roles": []}, exporter.build_projection(source))

    def test_local_learning_projection_is_aggregate_only_and_not_public(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            schedule = Path(directory) / "interview-and-events.md"
            coach_db = Path(directory) / "coach.sqlite3"
            write_tracker(source)
            write_schedule(
                schedule,
                [
                    (
                        "2026-09-15, 9:30 AM to 10:00 AM PT",
                        "Example AI",
                        "Technical interview",
                        "Remote",
                        "Confirmed",
                    )
                ],
            )
            write_coach_database(coach_db)

            learning = exporter.build_learning_projection(coach_db)
            self.assertEqual("active", learning["status"])
            self.assertEqual(3, learning["attempts"]["total"])
            self.assertEqual(2, learning["attempts"]["complete"])
            self.assertEqual(1, learning["attempts"]["incomplete"])
            self.assertEqual(
                {"complete": 2, "total": 3, "percent": 67},
                learning["attempt_completion"],
            )
            self.assertEqual(
                {"met": 1, "total": 1, "percent": 100, "unscored": 0},
                learning["independent_success"],
            )
            self.assertEqual(
                {"complete": 1, "total": 2, "percent": 50},
                learning["section_completion"],
            )
            self.assertEqual(1, learning["open_gaps"])
            self.assertEqual(1, learning["due_gaps"])
            self.assertEqual(1, learning["open_repairs"])
            self.assertEqual(1, learning["due_repairs"])
            self.assertEqual(
                {"needs_check": 1, "needs_hint": 1, "independent_today": 1, "delayed_transfer": 0},
                learning["latest_states"],
            )
            self.assertEqual(
                [{"dimension": "concepts", "score": 2, "observed_at": "2026-09-10T17:00:00+00:00"}],
                learning["dimension_scores"],
            )
            serialized_learning = json.dumps(learning)
            for private_marker in (
                "SYNTHETIC_PRIVATE_TRACK",
                "SYNTHETIC_PRIVATE_COMPETENCY",
                "SYNTHETIC_PRIVATE_TRANSCRIPT",
                "SYNTHETIC_PRIVATE_ANSWER",
                "SYNTHETIC_PRIVATE_EVALUATION",
                "SYNTHETIC_PRIVATE_REASON",
                "SYNTHETIC_PRIVATE_GAP",
                "SYNTHETIC_PRIVATE_TOPIC",
                "SYNTHETIC_PRIVATE_REPAIR_TARGET",
            ):
                self.assertNotIn(private_marker, serialized_learning)

            public_projection = exporter.build_projection(source)
            local_projection = exporter.build_local_projection(
                source, schedule, coach_db_path=coach_db
            )
            self.assertEqual({"generated_date", "roles"}, set(public_projection))
            self.assertNotIn("learning", public_projection)
            self.assertIn("learning", local_projection)
            self.assertNotIn("SYNTHETIC_PRIVATE", json.dumps(local_projection))

    def test_pilot_operations_are_local_only_and_aggregate_safe(self):
        exporter = load_exporter()
        store = load_store()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "tracker.csv"
            schedule = root / "interview-and-events.md"
            pilot_db = root / "pilot.sqlite3"
            write_tracker(source)
            write_schedule(
                schedule,
                [
                    (
                        "2026-09-15, 9:30 AM to 10:00 AM PT",
                        "Example AI",
                        "Technical interview",
                        "Remote",
                        "Confirmed",
                    )
                ],
            )
            coverage = {
                source_key: {"outcome": "not_checked", "count": 0}
                for source_key in store.PILOT_SOURCE_KEYS
            }
            coverage["linkedin"] = {"outcome": "checked", "count": 3}
            db = store.connect(pilot_db)
            store.record_pilot_run(
                db,
                {
                    "completed_at": "2026-09-12T18:30:00Z",
                    "result": "completed",
                    "source_coverage": coverage,
                    "inbox_status": "failed",
                    "inbox_actionable_count": 0,
                    "discovered_count": 3,
                    "verified_count": 2,
                    "submitted_count": 1,
                    "blocked_count": 0,
                    "decision_counts": {
                        "application": 1,
                        "reply": 0,
                        "connection": 0,
                        "comment": 0,
                        "handoff": 0,
                    },
                    "submission_verification": "verified",
                    "tracker_transaction": "committed",
                    "cleanup": "completed",
                },
            )
            public_projection = exporter.build_projection(source)
            local_projection = exporter.build_local_projection(
                source,
                schedule,
                coach_db_path=root / "missing-coach.sqlite3",
                pilot_db_path=pilot_db,
            )
            self.assertEqual({"generated_date", "roles"}, set(public_projection))
            self.assertNotIn("pilot_operations", public_projection)
            self.assertEqual(
                {"generated_date", "roles", "schedule", "learning", "pilot_operations"},
                set(local_projection),
            )
            operations = local_projection["pilot_operations"]
            self.assertEqual("available", operations["status"])
            self.assertEqual("2026-09-12T18:30:00+00:00", operations["latest"]["completed_at"])
            self.assertEqual("completed", operations["latest"]["status"])
            self.assertEqual(3, operations["source_coverage"]["linkedin"]["count"])
            self.assertEqual("checked", operations["source_coverage"]["linkedin"]["latest_outcome"])
            self.assertEqual("failed", operations["inbox"]["latest_status"])
            self.assertEqual("verified", operations["submission_verification"]["latest_status"])
            self.assertEqual("committed", operations["tracker_transaction"]["latest_status"])
            self.assertEqual("completed", operations["cleanup"]["latest_status"])
            serialized = json.dumps(local_projection)
            self.assertNotIn("official_url", serialized)
            self.assertNotIn("SYNTHETIC_PRIVATE", serialized)
            missing_operations = exporter.build_pilot_operations_projection(
                root / "missing-pilot.sqlite3"
            )
            self.assertEqual("unavailable", missing_operations["status"])
            self.assertEqual(0, missing_operations["run_count"])
            empty_db_path = root / "empty-pilot.sqlite3"
            empty_db = store.connect(empty_db_path)
            store.initialize(empty_db)
            empty_db.close()
            no_runs_operations = exporter.build_pilot_operations_projection(empty_db_path)
            self.assertEqual("no_runs", no_runs_operations["status"])
            self.assertEqual(0, no_runs_operations["run_count"])
            output = root / "public.json"
            exporter.write_projection(output, source)
            self.assertNotIn("pilot_operations", output.read_text(encoding="utf-8"))

    def test_missing_coach_database_returns_unavailable_local_learning(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-coach.sqlite3"
            learning = exporter.build_learning_projection(missing)
            self.assertEqual("unavailable", learning["status"])
            self.assertEqual(0, learning["attempts"]["total"])
            self.assertEqual([], learning["dimension_scores"])

    def test_local_schedule_projection_is_allowlisted_and_public_export_omits_it(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tracker.csv"
            schedule = Path(directory) / "interview-and-events.md"
            write_tracker(source)
            write_schedule(
                schedule,
                [
                    (
                        "2026-09-15, 9:30 AM to 10:00 AM PT",
                        "Example AI",
                        "Technical interview",
                        "Remote",
                        "Confirmed",
                    ),
                    (
                        "2026-09-16, 9:30 AM to 10:00 AM PT (2026-09-16, 12:30 PM to 1:00 PM ET)",
                        "Example Labs",
                        "System design interview",
                        "Online",
                        "Send a private message at https://private-message.example",
                    ),
                    (
                        "2026-09-17, 9:30 AM to 10:00 AM PT",
                        "Visa Detail Company",
                        "Interview",
                        "Remote",
                        "Confirmed",
                    ),
                    (
                        "2026-09-18, 9:30 AM to 10:00 AM PT",
                        "Example AI",
                        "Interview",
                        "https://private-link.example/event",
                        "Confirmed",
                    ),
                ],
            )

            public_projection = exporter.build_projection(source)
            local_projection = exporter.build_local_projection(
                source,
                schedule,
                coach_db_path=Path(directory) / "missing-coach.sqlite3",
            )

            self.assertEqual({"generated_date", "roles"}, set(public_projection))
            self.assertNotIn("schedule", public_projection)
            self.assertEqual(
                {"generated_date", "roles", "schedule", "learning", "pilot_operations"},
                set(local_projection),
            )
            self.assertEqual("unavailable", local_projection["learning"]["status"])
            self.assertEqual(2, len(local_projection["schedule"]))
            first, second = local_projection["schedule"]
            self.assertEqual(list(exporter.SCHEDULE_PUBLIC_FIELDS), list(first))
            self.assertEqual("2026-09-15 · 9:30 AM–10:00 AM", first["datetime"])
            self.assertEqual("PT", first["timezone"])
            self.assertEqual("Scheduled", first["status"])
            self.assertEqual("Prepare for the event", first["next_step"])
            self.assertEqual("Scheduled", second["status"])
            self.assertEqual("Prepare for the event", second["next_step"])
            serialized_local = json.dumps(local_projection)
            self.assertNotIn("private-message.example", serialized_local)
            self.assertNotIn("Send a private message", serialized_local)
            self.assertNotIn("Visa Detail Company", serialized_local)
            self.assertNotIn("private-link.example", serialized_local)
            self.assertNotIn("Technical interview", json.dumps(public_projection))

    def test_schedule_title_canonicalizes_generic_recruiter_wording(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as directory:
            schedule = Path(directory) / "interview-and-events.md"
            write_schedule(
                schedule,
                [
                    (
                        "2026-09-15, 9:30 AM to 10:00 AM PT",
                        "Example AI",
                        "Eng Recruiter Screen — Alex Example",
                        "Remote",
                        "Confirmed",
                    ),
                    (
                        "2026-09-16, 9:30 AM to 10:00 AM PT",
                        "Example Labs",
                        "recruiter discussion",
                        "Online",
                        "Confirmed",
                    ),
                    (
                        "2026-09-17, 9:30 AM to 10:00 AM PT",
                        "Example Hiring",
                        "Alex Example Recruiter Screen",
                        "Remote",
                        "Confirmed",
                    ),
                ],
            )

            projection = exporter.export_schedule_events(schedule)

            serialized = json.dumps(projection)
            self.assertEqual(2, len(projection))
            self.assertTrue(any(event["title"] == "Eng Recruiter Screen" for event in projection))
            self.assertTrue(any(event["title"] == "Recruiter Discussion" for event in projection))
            self.assertNotIn("Alex Example", serialized)

    def test_schedule_datetime_uses_fully_parsed_pacific_alternate(self):
        exporter = load_exporter()

        self.assertEqual(
            (
                "2026-09-15T19:00",
                "2026-09-15 · 7:00 PM–8:00 PM",
                "PDT",
            ),
            exporter._parse_schedule_datetime(
                "2026-09-16, 10:00 AM to 11:00 AM UTC+8 "
                "(2026-09-15, 7:00 PM to 8:00 PM PDT)"
            ),
        )

        self.assertEqual(
            (
                "2026-09-16T10:00",
                "2026-09-16 · 10:00 AM–11:00 AM",
                "PDT",
            ),
            exporter._parse_schedule_datetime(
                "2026-09-16, 10:00 AM to 11:00 AM PDT "
                "(2026-09-16, 1:00 PM to 2:00 PM EDT)"
            ),
        )

        self.assertIsNone(
            exporter._parse_schedule_datetime(
                "2026-09-16, 10:00 AM to 11:00 AM UTC+8 "
                "(2026-09-15, 7:00 PM to 8:00 PM PDT"
            )
        )


if __name__ == "__main__":
    unittest.main()
