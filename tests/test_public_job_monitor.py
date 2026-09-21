from __future__ import annotations

import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skill" / "careerlens"
SCRIPTS_DIR = SKILL_DIR / "scripts"
PACKAGE_DIR = SCRIPTS_DIR / "public_acquisition"
SYNC_SCRIPT = SCRIPTS_DIR / "sync_public_acquisition.py"
MONITOR_SCRIPT = SCRIPTS_DIR / "public_job_monitor.py"
RUN_ID = "a" * 32


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VendorSyncTests(unittest.TestCase):
    def test_sync_copies_only_the_explicit_files_and_check_detects_tampering(self):
        sync = _load(SYNC_SCRIPT, "careerlens_vendor_sync_test")
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            source_root = temp / "source"
            destination = temp / "destination" / "public_acquisition"
            for index, (source_relative, _) in enumerate(sync.FILES):
                path = source_root / source_relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(("source-{0}\n".format(index)).encode("utf-8"))
            original_package_dir = sync.PACKAGE_DIR
            original_manifest_path = sync.MANIFEST_PATH
            try:
                sync.PACKAGE_DIR = destination
                sync.MANIFEST_PATH = destination / "VENDORED_FROM_CAREEROS.json"
                manifest = sync.sync(source_root)
                self.assertEqual(len(sync.FILES), len(manifest["files"]))
                self.assertEqual([], sync.check(source_root))
                for source_relative, destination_relative in sync.FILES:
                    self.assertEqual(
                        (source_root / source_relative).read_bytes(),
                        (destination / destination_relative).read_bytes(),
                    )
                (destination / sync.FILES[0][1]).write_bytes(b"tampered\n")
                self.assertIn("hash_mismatch:" + sync.FILES[0][1], sync.check(source_root))
            finally:
                sync.PACKAGE_DIR = original_package_dir
                sync.MANIFEST_PATH = original_manifest_path

    def test_checked_in_manifest_matches_each_vendored_byte(self):
        manifest_path = PACKAGE_DIR / "VENDORED_FROM_CAREEROS.json"
        self.assertTrue(manifest_path.is_file(), "run sync_public_acquisition.py with an explicit source root")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(1, manifest.get("format_version"))
        self.assertEqual("explicit root containing career_os/", manifest.get("source_root_contract"))
        files = manifest.get("files")
        self.assertIsInstance(files, list)
        self.assertEqual(8, len(files))
        for item in files:
            self.assertIsInstance(item, dict)
            destination = item.get("destination_path")
            self.assertIsInstance(destination, str)
            self.assertTrue(destination.startswith("public_acquisition/"))
            path = SCRIPTS_DIR / destination
            self.assertTrue(path.is_file(), destination)
            self.assertEqual(item.get("sha256"), _sha256(path))


@unittest.skipUnless(sys.version_info >= (3, 11), "optional public monitor requires Python 3.11+")
class PublicJobMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = str(SCRIPTS_DIR)
        if script_path not in sys.path:
            sys.path.insert(0, script_path)
        from public_acquisition import server

        cls.server_module = server

    def setUp(self):
        self.registry = _Registry()
        self.server = self.server_module.create_server(port=0, registry=self.registry)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        self.origin = self.server.origin

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _raw(self, method: str, path: str, *, body: bytes = b"", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        request_headers = {"Host": "127.0.0.1:{0}".format(self.server.server_port)}
        if headers:
            request_headers.update(headers)
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, dict(response.getheaders()), payload

    def test_same_origin_post_starts_a_run_and_missing_origin_is_rejected(self):
        body = json.dumps(
            {"task": "public platform role", "seed_urls": ["https://job-boards.greenhouse.io/example"]}
        ).encode("utf-8")
        status, headers, payload = self._raw(
            "POST",
            "/api/public-acquisition/runs",
            body=body,
            headers={"Content-Type": "application/json", "Origin": self.origin},
        )
        self.assertEqual(202, status)
        self.assertEqual("close", headers.get("Connection"))
        self.assertEqual(RUN_ID, json.loads(payload)["run_id"])
        self.assertEqual(1, len(self.registry.starts))

        status, _, payload = self._raw(
            "POST",
            "/api/public-acquisition/runs",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(403, status)
        self.assertEqual("same_origin_required", json.loads(payload)["error_code"])
        self.assertEqual(1, len(self.registry.starts))

    def test_cross_site_and_wrong_host_are_rejected_without_starting_a_run(self):
        body = json.dumps(
            {"task": "public platform role", "seed_urls": ["https://job-boards.greenhouse.io/example"]}
        ).encode("utf-8")
        status, _, _ = self._raw(
            "POST",
            "/api/public-acquisition/runs",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": self.origin,
                "Sec-Fetch-Site": "cross-site",
            },
        )
        self.assertEqual(403, status)
        status, _, _ = self._raw("GET", "/acquire", headers={"Host": "attacker.invalid"})
        self.assertEqual(403, status)
        self.assertEqual([], self.registry.starts)

    def test_rerun_uses_only_stored_settings_and_rejects_any_replacement_body(self):
        path = "/api/public-acquisition/runs/{0}/rerun".format(RUN_ID)
        status, _, payload = self._raw("POST", path, headers={"Origin": self.origin})
        self.assertEqual(202, status)
        started = json.loads(payload)
        self.assertEqual({"run_id", "status", "monitor_url"}, set(started))
        self.assertEqual("b" * 32, started["run_id"])
        self.assertEqual("queued", started["status"])
        self.assertEqual(self.origin + "/acquire#run_id=" + ("b" * 32), started["monitor_url"])
        self.assertEqual([RUN_ID], self.registry.reruns)

        injected = json.dumps(
            {"task": "replace stored settings", "seed_urls": ["https://attacker.invalid"]}
        ).encode("utf-8")
        status, _, payload = self._raw(
            "POST",
            path,
            body=injected,
            headers={"Origin": self.origin, "Content-Type": "application/json"},
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_input", json.loads(payload)["error_code"])
        self.assertEqual([RUN_ID], self.registry.reruns)

    def test_rerun_returns_a_direct_link_even_when_the_new_run_finishes_immediately(self):
        self.registry.rerun_result = {
            "run_id": "c" * 32,
            "status": "completed",
            "created_at": "2026-09-20T00:00:01Z",
        }
        status, _, payload = self._raw(
            "POST",
            "/api/public-acquisition/runs/{0}/rerun".format(RUN_ID),
            headers={"Origin": self.origin},
        )
        self.assertEqual(202, status)
        started = json.loads(payload)
        self.assertEqual("completed", started["status"])
        self.assertEqual(self.origin + "/acquire#run_id=" + ("c" * 32), started["monitor_url"])

    def test_rerun_error_mapping_and_origin_guards(self):
        path = "/api/public-acquisition/runs/{0}/rerun".format(RUN_ID)
        status, _, payload = self._raw("POST", path)
        self.assertEqual(403, status)
        self.assertEqual("same_origin_required", json.loads(payload)["error_code"])
        self.assertEqual([], self.registry.reruns)

        self.registry.rerun_result = None
        status, _, payload = self._raw("POST", path, headers={"Origin": self.origin})
        self.assertEqual(404, status)
        self.assertEqual("not_found", json.loads(payload)["error_code"])

        self.registry.rerun_result = {"run_id": "b" * 32, "status": "queued", "created_at": "2026-09-20T00:00:01Z"}
        self.registry.rerun_error = self.server_module.PublicFetchError("run_capacity_reached")
        status, _, payload = self._raw("POST", path, headers={"Origin": self.origin})
        self.assertEqual(429, status)
        self.assertEqual("run_capacity_reached", json.loads(payload)["error_code"])

        self.registry.rerun_error = RuntimeError("private configured task must not be reflected")
        status, _, payload = self._raw("POST", path, headers={"Origin": self.origin})
        self.assertEqual(503, status)
        response = json.loads(payload)
        self.assertEqual("acquisition_unavailable", response["error_code"])
        self.assertNotIn("private configured task", json.dumps(response))

    def test_safe_routes_and_incremental_events_are_available(self):
        status, headers, payload = self._raw("GET", "/acquire")
        self.assertEqual(200, status)
        self.assertIn("text/html", headers["Content-Type"])
        page = payload.decode("utf-8", errors="ignore")
        title = re.search(r"<title>(.*?)</title>", page, flags=re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(title)
        self.assertNotRegex(title.group(1).lower(), r"private|credential|api.?key|keychain|workspace|coach")
        status, _, payload = self._raw("GET", "/api/public-acquisition/runs/{0}?after=0".format(RUN_ID))
        self.assertEqual(200, status)
        snapshot = json.loads(payload)
        self.assertEqual("completed", snapshot["status"])
        self.assertEqual(1, snapshot["events"][0]["event_id"])
        status, _, payload = self._raw("GET", "/not-an-asset")
        self.assertEqual(404, status)
        self.assertEqual("not_found", json.loads(payload)["error_code"])

    def test_wrapper_fetch_uses_a_real_endpoint_path_origin_and_clean_copy_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            copied_skill = temp / "installed" / "careerlens"
            shutil.copytree(SKILL_DIR, copied_skill)
            isolated = temp / "arbitrary-cwd"
            isolated.mkdir()
            env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME", "TYPESAFE_API_KEY"}}
            import_check = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.insert(0, sys.argv[1]); import public_acquisition.public_monitor; import public_acquisition.server; print('portable-ok')",
                    str(copied_skill / "scripts"),
                ],
                cwd=isolated,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, import_check.returncode, import_check.stderr)
            self.assertEqual("portable-ok", import_check.stdout.strip())
            completed = subprocess.run(
                [
                    sys.executable,
                    str(copied_skill / "scripts" / "public_job_monitor.py"),
                    "fetch",
                    "--monitor-url",
                    self.origin,
                    "--task",
                    "public platform role",
                    "--seed-url",
                    "https://job-boards.greenhouse.io/example",
                    "--no-jev",
                    "--wait-seconds",
                    "2",
                ],
                cwd=isolated,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        final = json.loads(completed.stdout)
        self.assertEqual("completed", final["status"])
        self.assertEqual(RUN_ID, final["run_id"])
        self.assertIn('"event_id":1', completed.stderr)


class _Registry:
    """A no-network registry double; server tests never call a provider."""

    def __init__(self):
        self.starts = []
        self.reruns = []
        self.rerun_result = {"run_id": "b" * 32, "status": "queued", "created_at": "2026-09-20T00:00:01Z"}
        self.rerun_error = None

    def start(self, task, seed_urls, **options):
        self.starts.append({"task": task, "seed_urls": list(seed_urls), "options": options})
        return {"run_id": RUN_ID, "status": "queued", "created_at": "2026-09-20T00:00:00Z"}

    def snapshot(self, run_id, *, after=0):
        if run_id != RUN_ID:
            return None
        return {
            "run_id": RUN_ID,
            "status": "completed",
            "created_at": "2026-09-20T00:00:00Z",
            "finished_at": "2026-09-20T00:00:01Z",
            "events": [] if after else [{"event_id": 1, "type": "completed", "at": "2026-09-20T00:00:01Z"}],
            "next_event_id": 1,
            "result": {"roles": []},
        }

    def latest(self):
        return {"run_id": RUN_ID, "status": "completed", "created_at": "2026-09-20T00:00:00Z"}

    def list_runs(self):
        return [self.latest()]

    def rerun(self, run_id):
        self.reruns.append(run_id)
        if self.rerun_error is not None:
            raise self.rerun_error
        return self.rerun_result


if __name__ == "__main__":
    unittest.main()
