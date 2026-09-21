import importlib.util
import json
import sqlite3
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


server_module = load("local_tracker_server_test", "scripts/serve_application_tracker.py")
builder = load("local_tracker_builder_test", "scripts/build_pages_site.py")
store = load("local_tracker_store_test", "scripts/application_store.py")


def write_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE applications (
              company TEXT, role TEXT, official_url TEXT, location TEXT,
              work_mode TEXT, employment_constraints TEXT, tier TEXT,
              fit_score TEXT, resume_track TEXT, status TEXT,
              verified_date TEXT, approved_date TEXT, submitted_date TEXT,
              next_action TEXT, notes TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO applications VALUES (
              'Example AI', 'Platform Engineer', 'https://example.com/jobs/1',
              'Remote', 'Remote', 'private work authorization', 'P0', '88',
              'Agentic_AI', 'interview', '2026-09-01', '', '2026-09-02',
              'Prepare', 'private notes'
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
    db = store.connect(path)
    try:
        coverage = {
            source: {"outcome": "not_checked", "count": 0}
            for source in store.PILOT_SOURCE_KEYS
        }
        coverage["linkedin"] = {"outcome": "checked", "count": 2}
        store.record_pilot_run(
            db,
            {
                "completed_at": "2026-09-12T18:30:00Z",
                "result": "completed",
                "source_coverage": coverage,
                "inbox_status": "unavailable",
                "inbox_actionable_count": 0,
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
            },
        )
    finally:
        db.close()


def write_schedule(path: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    lines = [
        "# Events",
        "",
        "| Date / Time | Organization | Activity | Location | Status and next step |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class LocalApplicationTrackerServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.site_root = self.root / "site"
        self.site_root.mkdir()
        (self.site_root / "index.html").write_text("safe static page", encoding="utf-8")
        self.db_path = self.site_root / "applications.db"
        self.schedule_path = self.site_root / "interview-and-events.md"
        self.coach_db_path = self.site_root / "missing-coach.sqlite3"
        write_database(self.db_path)
        write_schedule(
            self.schedule_path,
            [
                (
                    "2026-09-15, 9:30 AM 10:00 AM PT",
                    "Example AI",
                    "Architecture interview",
                    "Remote",
                    "Message private@example.com for the next action",
                ),
                (
                    "2026-09-16, 9:30 AM 10:00 AM PT",
                    "H-1B Visa Company",
                    "Recruiter contact",
                    "Remote",
                    "Confirmed",
                ),
            ],
        )
        self.server = server_module.create_server(
            self.site_root,
            self.db_path,
            self.schedule_path,
            coach_db_path=self.coach_db_path,
            port=0,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.directory.cleanup()

    def get_json(self) -> dict[str, object]:
        with urlopen(self.base_url + "/application-tracker/data.json", timeout=3) as response:
            self.assertEqual(200, response.status)
            self.assertEqual("no-store", response.headers["Cache-Control"])
            return json.loads(response.read().decode("utf-8"))

    def test_local_endpoint_refreshes_safe_schedule_without_serving_sources(self):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", "/application-tracker")
        redirect = connection.getresponse()
        self.assertEqual(308, redirect.status)
        self.assertEqual("/application-tracker/", redirect.headers["Location"])
        connection.close()

        first = self.get_json()
        self.assertEqual("127.0.0.1", self.server.server_address[0])
        self.assertEqual(1, len(first["schedule"]))
        event = first["schedule"][0]
        self.assertEqual("Architecture interview", event["title"])
        self.assertEqual("Scheduled", event["status"])
        self.assertEqual("Prepare for the event", event["next_step"])
        self.assertEqual("unavailable", first["learning"]["status"])
        operations = first["pilot_operations"]
        self.assertEqual("available", operations["status"])
        self.assertEqual(2, operations["source_coverage"]["linkedin"]["count"])
        self.assertEqual("unavailable", operations["inbox"]["latest_status"])
        self.assertEqual("verified", operations["submission_verification"]["latest_status"])
        serialized = json.dumps(first)
        self.assertNotIn("private@example.com", serialized)
        self.assertNotIn("next action", serialized)
        self.assertNotIn("H-1B", serialized)
        self.assertNotIn("Visa", serialized)
        self.assertNotIn("Recruiter", serialized)

        write_schedule(
            self.schedule_path,
            [
                (
                    "2026-09-18, 11:00 AM 11:30 AM PT",
                    "Example Labs",
                    "Production interview",
                    "Online",
                    "Confirmed",
                )
            ],
        )
        refreshed = self.get_json()
        self.assertEqual("Production interview", refreshed["schedule"][0]["title"])
        self.assertNotIn("Architecture interview", json.dumps(refreshed))

        for path in (
            "/applications.db",
            "/interview-and-events.md",
            "/missing-coach.sqlite3",
            "/data/application-tracker.json",
        ):
            with self.subTest(path=path), self.assertRaises(HTTPError) as raised:
                urlopen(self.base_url + path, timeout=3)
            self.assertEqual(404, raised.exception.code)

    def test_tracker_rejects_rebound_host_and_cross_origin_requests(self):
        cases = (
            {"Host": "attacker.example"},
            {
                "Host": f"127.0.0.1:{self.server.server_port}",
                "Origin": "https://attacker.example",
            },
        )
        for headers in cases:
            with self.subTest(headers=headers):
                connection = HTTPConnection(
                    "127.0.0.1", self.server.server_port, timeout=3
                )
                connection.request("GET", "/application-tracker/data.json", headers=headers)
                response = connection.getresponse()
                self.assertEqual(403, response.status)
                self.assertEqual(b"Forbidden.\n", response.read())
                connection.close()

    def test_tracker_page_has_schedule_labels_and_escapes_inline_data(self):
        with urlopen(self.base_url + "/application-tracker/", timeout=3) as response:
            page = response.read().decode("utf-8")
        for label in (
            "Scheduled events",
            "Title: ",
            "Organization: ",
            "Date and time:",
            "Location:",
            "Status: ",
            "Next step:",
            "Learning &amp; Diagnosis",
            "Pilot Operations",
            "Source coverage",
            "Decision queue",
            "Submission verification",
            "Tracker transaction",
            "Cleanup",
            "Learning diagnosis",
            "Evidence status",
            "setInterval",
            "15000",
        ):
            self.assertIn(label, page)
        self.assertIn("esc(event.title)", page)
        projection = {
            "generated_date": "",
            "roles": [],
            "schedule": [
                {
                    "title": "<unsafe>",
                    "organization": "Example AI",
                    "datetime": "2026-09-15 · 9:30 AM",
                    "timezone": "PT",
                    "location": "Remote",
                    "status": "Scheduled",
                    "next_step": "Prepare for the event",
                }
            ],
        }
        inline_page = builder.tracker_page("/", projection)
        self.assertNotIn("<unsafe>", inline_page)
        self.assertIn("\\u003cunsafe>", inline_page)


if __name__ == "__main__":
    unittest.main()
