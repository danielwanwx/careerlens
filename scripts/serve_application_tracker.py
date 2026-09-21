#!/usr/bin/env python3
"""Serve the local, privacy-filtered CareerLens tracker on loopback only.

Static Pages assets come from the already-built local Pages directory.  The
tracker HTML and its JSON endpoint are generated in memory for each request so
private source changes appear on the next browser poll without writing a
schedule or Coach evidence into a publishable artifact.
"""
from __future__ import annotations

import argparse
import functools
import importlib.util
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
LOCAL_PAGES = Path.home() / "Library" / "Application Support" / "CareerLens" / "pages"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


exporter = _load("export_application_tracker", SCRIPTS / "export_application_tracker.py")
builder = _load("build_pages_site", SCRIPTS / "build_pages_site.py")


class LocalTrackerRequestHandler(SimpleHTTPRequestHandler):
    """Serve only public static files plus in-memory, local tracker routes."""

    _private_suffixes = {".db", ".sqlite", ".sqlite3", ".csv", ".md"}
    _private_parts = {"resume", "job-search", "data", "scripts"}

    def __init__(
        self,
        *args: Any,
        directory: str,
        db_path: Path,
        schedule_source: Path,
        coach_db_path: Path,
        **kwargs: Any,
    ) -> None:
        self._site_root = Path(directory).resolve()
        self._db_path = Path(db_path).resolve()
        self._schedule_source = Path(schedule_source).resolve()
        self._coach_db_path = Path(coach_db_path).resolve()
        self._private_paths = {
            self._db_path,
            self._db_path.with_name(self._db_path.name + "-wal"),
            self._db_path.with_name(self._db_path.name + "-shm"),
            self._db_path.with_name(self._db_path.name + "-journal"),
            self._schedule_source,
            self._coach_db_path,
            self._coach_db_path.with_name(self._coach_db_path.name + "-wal"),
            self._coach_db_path.with_name(self._coach_db_path.name + "-shm"),
            self._coach_db_path.with_name(self._coach_db_path.name + "-journal"),
            exporter.DEFAULT_SOURCE.resolve(),
            exporter.DEFAULT_DB.resolve(),
            exporter.DEFAULT_SCHEDULE_SOURCE.resolve(),
            exporter.DEFAULT_COACH_DB.resolve(),
        }
        super().__init__(*args, directory=str(self._site_root), **kwargs)

    def log_message(self, _format: str, *_args: Any) -> None:
        """Avoid recording request paths that could themselves be private."""

    def list_directory(self, _path: str) -> None:
        self._send_not_found()
        return None

    def _request_path(self) -> str:
        return unquote(urlsplit(self.path).path)

    def _is_local_authority(self, value: str, *, require_port: bool) -> bool:
        """Accept only the loopback origins this IPv4-only server can serve."""
        if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
            return False
        try:
            parsed = urlsplit("//" + value)
            port = parsed.port
        except ValueError:
            return False
        if (
            parsed.username is not None
            or parsed.password is not None
            or parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            return False
        return port == self.server.server_port if require_port else port in {
            None,
            self.server.server_port,
        }

    def _is_trusted_local_request(self) -> bool:
        """Reject DNS-rebound browser requests before any private projection."""
        if not self._is_local_authority(
            self.headers.get("Host", ""), require_port=False
        ):
            return False
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "http"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            return False
        authority = parsed.netloc
        return self._is_local_authority(authority, require_port=True)

    def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_not_found(self) -> None:
        self._send_bytes(404, "text/plain; charset=utf-8", b"Not found.\n")

    def _send_forbidden(self) -> None:
        self._send_bytes(403, "text/plain; charset=utf-8", b"Forbidden.\n")

    def _send_tracker_unavailable(self) -> None:
        self._send_bytes(
            503,
            "text/plain; charset=utf-8",
            b"Tracker data is temporarily unavailable.\n",
        )

    def _send_tracker_redirect(self) -> None:
        self.send_response(308)
        self.send_header("Location", "/application-tracker/")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _is_private_static_path(self, request_path: str) -> bool:
        if "\x00" in request_path:
            return True
        candidate = (self._site_root / request_path.lstrip("/")).resolve()
        try:
            candidate.relative_to(self._site_root)
        except ValueError:
            return True
        if candidate in self._private_paths or candidate.suffix.casefold() in self._private_suffixes:
            return True
        return any(part.casefold() in self._private_parts for part in candidate.parts)

    def _serve_dynamic_tracker(self, request_path: str) -> bool:
        if request_path == "/application-tracker":
            self._send_tracker_redirect()
            return True
        if request_path not in {
            "/application-tracker/",
            "/application-tracker/index.html",
            "/application-tracker/data.json",
        }:
            return False
        try:
            projection = exporter.build_local_projection(
                self._db_path,
                self._schedule_source,
                coach_db_path=self._coach_db_path,
            )
        except Exception:
            self._send_tracker_unavailable()
            return True
        if request_path == "/application-tracker/data.json":
            body = json.dumps(
                projection, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            self._send_bytes(200, "application/json; charset=utf-8", body)
            return True
        body = builder.tracker_page("/", projection).encode("utf-8")
        self._send_bytes(200, "text/html; charset=utf-8", body)
        return True

    def _handle(self) -> None:
        if not self._is_trusted_local_request():
            self._send_forbidden()
            return
        request_path = self._request_path()
        if self._serve_dynamic_tracker(request_path):
            return
        if self._is_private_static_path(request_path):
            self._send_not_found()
            return
        if self.command == "HEAD":
            super().do_HEAD()
        else:
            super().do_GET()

    def do_GET(self) -> None:
        self._handle()

    def do_HEAD(self) -> None:
        self._handle()


class LocalTrackerHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def create_server(
    site_root: Path | str,
    db_path: Path | str = exporter.DEFAULT_DB,
    schedule_source: Path | str = exporter.DEFAULT_SCHEDULE_SOURCE,
    coach_db_path: Path | str = exporter.DEFAULT_COACH_DB,
    *,
    port: int = 8766,
) -> LocalTrackerHTTPServer:
    """Create a loopback-only server suitable for a local browser session."""

    site_root = Path(site_root)
    if not site_root.is_dir():
        raise FileNotFoundError("local Pages directory is missing")
    handler = functools.partial(
        LocalTrackerRequestHandler,
        directory=str(site_root),
        db_path=Path(db_path),
        schedule_source=Path(schedule_source),
        coach_db_path=Path(coach_db_path),
    )
    return LocalTrackerHTTPServer(("127.0.0.1", port), handler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=LOCAL_PAGES)
    parser.add_argument("--db", type=Path, default=exporter.DEFAULT_DB)
    parser.add_argument(
        "--schedule-source", type=Path, default=exporter.DEFAULT_SCHEDULE_SOURCE
    )
    parser.add_argument("--coach-db", type=Path, default=exporter.DEFAULT_COACH_DB)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    try:
        server = create_server(
            args.site_root,
            args.db,
            args.schedule_source,
            args.coach_db,
            port=args.port,
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print(f"CareerLens tracker: http://127.0.0.1:{server.server_port}/application-tracker/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
