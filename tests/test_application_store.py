import csv
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


store = load("application_store_test", "scripts/application_store.py")
exporter = load("application_exporter_test", "scripts/export_application_tracker.py")
syncer = load("application_sync_test", "scripts/sync_application_tracker.py")


def row(**overrides):
    value = {
        "company": "Example AI",
        "role": "Senior Platform Engineer",
        "official_url": "https://example.com/jobs/1",
        "location": "Remote",
        "work_mode": "Remote",
        "employment_constraints": "Private visa detail",
        "tier": "P0_INTERVIEW",
        "fit_score": "90",
        "resume_track": "Agentic_AI",
        "status": "verified",
        "verified_date": "2026-09-02",
        "approved_date": "",
        "submitted_date": "",
        "next_action": "Review",
        "notes": "Private notes",
    }
    value.update(overrides)
    return value


def pilot_receipt(**overrides):
    coverage = {
        source: {"outcome": "not_checked", "count": 0}
        for source in store.PILOT_SOURCE_KEYS
    }
    coverage["linkedin"] = {"outcome": "checked", "count": 2}
    value = {
        "completed_at": "2026-09-12T18:30:00Z",
        "result": "completed",
        "source_coverage": coverage,
        "inbox_status": "checked",
        "inbox_actionable_count": 1,
        "discovered_count": 2,
        "verified_count": 1,
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
    }
    value.update(overrides)
    return value


class ApplicationStoreTests(unittest.TestCase):
    def test_private_defaults_are_portable_and_outside_the_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            private_root = Path(directory) / "private-careerlens"
            with mock.patch.dict(
                os.environ,
                {"CAREERLENS_PRIVATE_DATA_DIR": str(private_root)},
            ):
                portable_store = load("portable_application_store", "scripts/application_store.py")
                portable_exporter = load(
                    "portable_application_exporter", "scripts/export_application_tracker.py"
                )
            self.assertEqual(private_root, portable_store.PRIVATE_DATA_DIR)
            self.assertEqual(private_root / "applications.db", portable_store.DEFAULT_DB)
            self.assertEqual(private_root / "job-tracker.csv", portable_store.DEFAULT_CSV)
            self.assertEqual(private_root, portable_exporter.PRIVATE_DATA_DIR)
            self.assertEqual(private_root / "applications.db", portable_exporter.DEFAULT_DB)
            self.assertEqual(private_root / "job-tracker.csv", portable_exporter.DEFAULT_SOURCE)
            self.assertEqual(private_root / "pages", portable_exporter.DEFAULT_LOCAL_PAGES)
            self.assertEqual(
                private_root / "application-tracker.local.json",
                portable_exporter.DEFAULT_OUTPUT,
            )

        with mock.patch.dict(os.environ, {"CAREERLENS_PRIVATE_DATA_DIR": ""}):
            default_store = load("default_application_store", "scripts/application_store.py")
        self.assertEqual(
            Path.home() / ".local" / "share" / "careerlens",
            default_store.PRIVATE_DATA_DIR,
        )
        with self.assertRaises(store.StoreError):
            store.connect(ROOT / "applications.db")

    def test_import_transition_event_and_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "tracker.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=store.FIELDS)
                writer.writeheader()
                writer.writerow(row())
            db_path = root / "applications.db"
            db = store.connect(db_path)
            store.initialize(db)
            self.assertEqual(1, store.import_csv(db, source))
            self.assertEqual(1, store.import_csv(db, source))
            self.assertEqual(
                1, db.execute("SELECT count(*) FROM application_events").fetchone()[0]
            )
            store.transition(
                db, "https://example.com/jobs/1", "submitted",
                event_date="2026-09-02", reason="Application confirmation",
            )
            records = store.read_rows(db)
            self.assertEqual("submitted", records[0]["status"])
            self.assertEqual("2026-09-02", records[0]["submitted_date"])
            events = db.execute(
                "SELECT event_type, old_status, new_status FROM application_events ORDER BY id"
            ).fetchall()
            self.assertEqual(("created", "", "verified"), tuple(events[0]))
            self.assertEqual(("transition", "verified", "submitted"), tuple(events[1]))
            output = root / "generated.csv"
            store.export_csv(db, output)
            with output.open(encoding="utf-8") as handle:
                self.assertEqual(1, len(list(csv.DictReader(handle))))
            public = exporter.build_projection(db_path)
            self.assertEqual("Submitted", public["roles"][0]["status"])
            self.assertNotIn("employment_constraints", public["roles"][0])

    def test_submitted_requires_date_and_url_is_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            db = store.connect(Path(directory) / "applications.db")
            store.initialize(db)
            with self.assertRaises(store.StoreError):
                store.upsert(db, row(status="submitted"))
            with self.assertRaises(store.StoreError):
                store.upsert(db, row(verified_date="09/02/2026"))
            first_id = store.upsert(db, row())
            second_id = store.upsert(db, row(role="Updated role"))
            self.assertEqual(first_id, second_id)
            self.assertEqual(1, len(store.read_rows(db)))

    def test_integrity_and_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            db = store.connect(Path(directory) / "applications.db")
            store.initialize(db)
            store.integrity_check(db)
            self.assertEqual(0, store.revision(db))
            store.upsert(db, row())
            self.assertEqual(1, store.revision(db))

    def test_pilot_receipts_are_bounded_and_transactional(self):
        with tempfile.TemporaryDirectory() as directory:
            db = store.connect(Path(directory) / "applications.db")
            store.initialize(db)
            receipt_id = store.record_pilot_run(db, pilot_receipt())
            saved = db.execute(
                "SELECT completed_at, result, source_linkedin_count, inbox_status, "
                "submitted_count, tracker_transaction FROM pilot_runs WHERE id = ?",
                (receipt_id,),
            ).fetchone()
            self.assertEqual(
                (
                    "2026-09-12T18:30:00+00:00",
                    "completed",
                    2,
                    "checked",
                    1,
                    "committed",
                ),
                tuple(saved),
            )
            invalid_receipts = (
                pilot_receipt(candidate_name="SYNTHETIC_PRIVATE_CANDIDATE"),
                pilot_receipt(
                    source_coverage={
                        **pilot_receipt()["source_coverage"],
                        "unknown_source": {"outcome": "checked", "count": 1},
                    }
                ),
                pilot_receipt(discovered_count=-1),
                pilot_receipt(completed_at="2026-09-12T18:30:00"),
                pilot_receipt(
                    source_coverage={
                        **pilot_receipt()["source_coverage"],
                        "indeed": {"outcome": "blocked", "count": 1},
                    }
                ),
                pilot_receipt(inbox_status="failed", inbox_actionable_count=1),
            )
            for receipt in invalid_receipts:
                with self.subTest(receipt=receipt), self.assertRaises(store.StoreError):
                    store.record_pilot_run(db, receipt)
            self.assertEqual(
                1, db.execute("SELECT count(*) FROM pilot_runs").fetchone()[0]
            )
            cli_receipt = pilot_receipt(completed_at="2026-09-12T20:00:00+00:00")
            with mock.patch("sys.argv", ["application_store.py"]):
                self.assertEqual(
                    0,
                    store.main(
                        [
                            "--db",
                            str(Path(directory) / "applications.db"),
                            "record-pilot-run",
                            "--receipt-json",
                            json.dumps(cli_receipt),
                        ]
                    ),
                )
            self.assertEqual(
                2, db.execute("SELECT count(*) FROM pilot_runs").fetchone()[0]
            )

    def test_sync_refreshes_only_local_csv_and_never_writes_static_tracker_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "applications.db"
            csv_path = root / "tracker.csv"
            db = store.connect(db_path)
            store.initialize(db)
            store.upsert(db, row())
            static_output = ROOT / "data" / "application-tracker.json"
            before = static_output.read_bytes() if static_output.exists() else None
            result = syncer.synchronize(db_path, csv_path, publish=False, dry_run=True)
            self.assertIn("dry-run", result)
            self.assertFalse(csv_path.exists())
            self.assertEqual(
                before,
                static_output.read_bytes() if static_output.exists() else None,
            )
            recorded = db.execute(
                "SELECT result FROM sync_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
            self.assertEqual("dry-run", recorded)
            result = syncer.synchronize(db_path, csv_path, publish=False, dry_run=False)
            self.assertIn("local tracker refreshed", result)
            self.assertTrue(csv_path.is_file())
            self.assertEqual(
                before,
                static_output.read_bytes() if static_output.exists() else None,
            )
            source = Path(syncer.__file__).read_text(encoding="utf-8")
            self.assertNotIn("application-tracker.json", source)
            self.assertNotIn("build_pages_site", source)
            self.assertNotIn("git", source)

    def test_sync_rejects_publication_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "applications.db"
            csv_path = root / "tracker.csv"
            db = store.connect(db_path)
            store.initialize(db)
            store.upsert(db, row())
            with self.assertRaisesRegex(syncer.store.StoreError, "publication is disabled"):
                syncer.synchronize(db_path, csv_path, publish=True, dry_run=False)
            self.assertFalse(csv_path.exists())
            self.assertEqual(
                0,
                db.execute("SELECT count(*) FROM sync_runs").fetchone()[0],
            )


if __name__ == "__main__":
    unittest.main()
