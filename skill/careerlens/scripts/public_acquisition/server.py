"""Small same-origin loopback boundary for the public acquisition monitor.

This module deliberately owns HTTP mechanics only.  Validation, concurrency,
event retention, and all public-fetch behavior remain in
``PublicAcquisitionRunRegistry``.
"""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

from .public_fetch import PublicFetchError
from .public_monitor import PublicAcquisitionRunRegistry


MAX_REQUEST_BYTES = 24 * 1024
MAX_REQUEST_TARGET_CHARS = 2_048
_RUN_ID = re.compile(r"^[0-9a-f]{32}$")
_RUN_STATUSES = frozenset({"queued", "running", "completed", "partial", "failed"})
_POST_FIELDS = frozenset(
    {"task", "seed_urls", "max_pages", "timeout_seconds", "use_jev", "detail"}
)
_SAFE_ERROR_CODES = frozenset(
    {
        "invalid_input",
        "invalid_cursor",
        "run_capacity_reached",
        "not_found",
        "same_origin_required",
        "payload_too_large",
        "unsupported_media_type",
        "method_not_allowed",
        "internal_error",
        "acquisition_unavailable",
    }
)
_STATIC = {
    "/acquire": ("public-acquisition.html", "text/html; charset=utf-8"),
    "/public-acquisition.css": ("public-acquisition.css", "text/css; charset=utf-8"),
    "/public-acquisition.js": ("public-acquisition.js", "application/javascript; charset=utf-8"),
    "/static/public-acquisition.css": ("public-acquisition.css", "text/css; charset=utf-8"),
    "/static/public-acquisition.js": ("public-acquisition.js", "application/javascript; charset=utf-8"),
}


def _safe_error_code(error: BaseException) -> str:
    """Return a documented code without turning exception text into an API."""

    code = str(error)
    return code if code in _SAFE_ERROR_CODES else "invalid_input"


def _parse_after(query: Dict[str, list[str]]) -> int:
    if not query:
        return 0
    if set(query) != {"after"} or len(query["after"]) != 1:
        raise PublicFetchError("invalid_input")
    value = query["after"][0]
    if not value.isascii() or not value.isdecimal():
        raise PublicFetchError("invalid_cursor")
    return int(value)


class PublicAcquisitionServer(ThreadingHTTPServer):
    """A loopback-only HTTP server with no request logging or CORS surface."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        port: int = 8768,
        registry: Optional[PublicAcquisitionRunRegistry] = None,
    ) -> None:
        self.registry = registry or PublicAcquisitionRunRegistry()
        self.static_dir = Path(__file__).resolve().parent / "static"
        super().__init__(("127.0.0.1", port), PublicAcquisitionHandler)

    @property
    def origin(self) -> str:
        return "http://127.0.0.1:{0}".format(self.server_port)

    @property
    def monitor_url(self) -> str:
        return self.origin + "/acquire"

    def handle_error(self, request: Any, client_address: Any) -> None:
        """Do not emit request details (which can include untrusted data) to stderr."""

        return


class PublicAcquisitionHandler(BaseHTTPRequestHandler):
    """Strict routes for a one-user, same-origin local monitor."""

    protocol_version = "HTTP/1.1"
    server_version = "CareerLensPublicMonitor"
    sys_version = ""

    @property
    def public_server(self) -> PublicAcquisitionServer:
        return self.server  # type: ignore[return-value]

    def setup(self) -> None:
        super().setup()
        # A client that declares a body and then stops cannot occupy a worker
        # forever. Rejected requests are also closed below, so unread bytes
        # cannot become a later request on the same connection.
        self.connection.settimeout(10.0)

    def log_message(self, format: str, *args: Any) -> None:
        """Never log endpoint payloads, task text, or potentially sensitive URLs."""

        return

    def _headers(self, content_type: str, content_length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'none'; form-action 'self'; "
            "frame-ancestors 'none'; connect-src 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self'",
        )

    def _send_bytes(self, status: HTTPStatus, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self._headers(content_type, len(payload))
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _send_json(self, status: HTTPStatus, value: Dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(status, payload, "application/json; charset=utf-8")

    def _error(self, status: HTTPStatus, code: str) -> None:
        self._send_json(status, {"error_code": code if code in _SAFE_ERROR_CODES else "internal_error"})

    def _same_origin(self, *, require_origin: bool) -> bool:
        expected_host = "127.0.0.1:{0}".format(self.public_server.server_port)
        if self.headers.get("Host") != expected_host:
            return False
        if require_origin:
            origin = self.headers.get("Origin")
            if origin != self.public_server.origin:
                return False
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                return False
        return True

    def _request_parts(self) -> Optional[Tuple[str, Dict[str, list[str]]]]:
        if len(self.path) > MAX_REQUEST_TARGET_CHARS:
            self._error(HTTPStatus.REQUEST_URI_TOO_LONG, "invalid_input")
            return None
        parsed = urlsplit(self.path)
        if parsed.scheme or parsed.netloc or parsed.fragment:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return None
        return parsed.path, parse_qs(parsed.query, keep_blank_values=True)

    def _json_body(self) -> Optional[Dict[str, Any]]:
        if self.headers.get("Transfer-Encoding"):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return None
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "unsupported_media_type")
            return None
        raw_length = self.headers.get("Content-Length")
        if raw_length is None or not raw_length.isdecimal():
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return None
        content_length = int(raw_length)
        if content_length > MAX_REQUEST_BYTES:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "payload_too_large")
            return None
        try:
            decoded = self.rfile.read(content_length).decode("utf-8")
            value = json.loads(decoded)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return None
        if not isinstance(value, dict) or set(value) - _POST_FIELDS:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return None
        return value

    def _empty_body(self) -> bool:
        """Accept a rerun only when it cannot smuggle a replacement config."""

        if self.headers.get("Transfer-Encoding"):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return False
        raw_length = self.headers.get("Content-Length")
        if raw_length is not None and (not raw_length.isdecimal() or int(raw_length) != 0):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return False
        return True

    def _rerun(self, run_id: str) -> None:
        """Start one new run from server-retained, already validated settings only."""

        try:
            started = self.public_server.registry.rerun(run_id)
        except PublicFetchError as error:
            if _safe_error_code(error) == "run_capacity_reached":
                self._error(HTTPStatus.TOO_MANY_REQUESTS, "run_capacity_reached")
            else:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE, "acquisition_unavailable")
            return
        except Exception:
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "acquisition_unavailable")
            return
        if started is None:
            self._error(HTTPStatus.NOT_FOUND, "not_found")
            return
        if not isinstance(started, dict):
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "acquisition_unavailable")
            return
        next_run_id = started.get("run_id")
        status = started.get("status")
        if (
            not isinstance(next_run_id, str)
            or not _RUN_ID.fullmatch(next_run_id)
            or status not in _RUN_STATUSES
        ):
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "acquisition_unavailable")
            return
        self._send_json(
            HTTPStatus.ACCEPTED,
            {
                "run_id": next_run_id,
                "status": status,
                "monitor_url": self.public_server.monitor_url + "#run_id=" + next_run_id,
            },
        )

    def _serve_static(self, path: str) -> bool:
        entry = _STATIC.get(path)
        if entry is None:
            return False
        name, content_type = entry
        asset = self.public_server.static_dir / name
        try:
            payload = asset.read_bytes()
        except OSError:
            self._error(HTTPStatus.NOT_FOUND, "not_found")
            return True
        self._send_bytes(HTTPStatus.OK, payload, content_type)
        return True

    def do_GET(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        if not self._same_origin(require_origin=False):
            self._error(HTTPStatus.FORBIDDEN, "same_origin_required")
            return
        parts = self._request_parts()
        if parts is None:
            return
        path, query = parts
        if self._serve_static(path):
            return
        try:
            if path == "/api/public-acquisition/runs":
                if query:
                    raise PublicFetchError("invalid_input")
                latest = self.public_server.registry.latest()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "runs": self.public_server.registry.list_runs(),
                        "latest_run_id": latest.get("run_id") if latest else None,
                    },
                )
                return
            if path == "/api/public-acquisition/runs/latest":
                after = _parse_after(query)
                latest = self.public_server.registry.latest()
                if latest is None:
                    self._error(HTTPStatus.NOT_FOUND, "not_found")
                    return
                snapshot = self.public_server.registry.snapshot(latest["run_id"], after=after)
                if snapshot is None:
                    self._error(HTTPStatus.NOT_FOUND, "not_found")
                    return
                self._send_json(HTTPStatus.OK, snapshot)
                return
            prefix = "/api/public-acquisition/runs/"
            if path.startswith(prefix):
                run_id = path[len(prefix) :]
                if not _RUN_ID.fullmatch(run_id):
                    raise PublicFetchError("invalid_input")
                snapshot = self.public_server.registry.snapshot(run_id, after=_parse_after(query))
                if snapshot is None:
                    self._error(HTTPStatus.NOT_FOUND, "not_found")
                    return
                self._send_json(HTTPStatus.OK, snapshot)
                return
        except PublicFetchError as error:
            self._error(HTTPStatus.BAD_REQUEST, _safe_error_code(error))
            return
        except Exception:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error")
            return
        self._error(HTTPStatus.NOT_FOUND, "not_found")

    def do_POST(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        if not self._same_origin(require_origin=True):
            self._error(HTTPStatus.FORBIDDEN, "same_origin_required")
            return
        parts = self._request_parts()
        if parts is None:
            return
        path, query = parts
        prefix = "/api/public-acquisition/runs/"
        rerun_suffix = "/rerun"
        if path.startswith(prefix) and path.endswith(rerun_suffix):
            run_id = path[len(prefix) : -len(rerun_suffix)]
            if query or not _RUN_ID.fullmatch(run_id):
                self._error(HTTPStatus.NOT_FOUND, "not_found")
                return
            if not self._empty_body():
                return
            self._rerun(run_id)
            return
        if path != "/api/public-acquisition/runs" or query:
            self._error(HTTPStatus.NOT_FOUND, "not_found")
            return
        payload = self._json_body()
        if payload is None:
            return
        if "task" not in payload or "seed_urls" not in payload:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_input")
            return
        try:
            started = self.public_server.registry.start(
                payload["task"],
                payload["seed_urls"],
                **{key: value for key, value in payload.items() if key not in {"task", "seed_urls"}}
            )
        except PublicFetchError as error:
            self._error(HTTPStatus.BAD_REQUEST, _safe_error_code(error))
            return
        except Exception:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error")
            return
        safe_start = {
            "run_id": started.get("run_id"),
            "status": started.get("status"),
            "created_at": started.get("created_at"),
            "monitor_url": self.public_server.monitor_url,
        }
        self._send_json(HTTPStatus.ACCEPTED, safe_start)

    def do_HEAD(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        self.do_GET()

    def _method_not_allowed(self) -> None:
        # A preflight or non-GET method from another origin must not receive a
        # route-specific response.  Direct local diagnostics with no Origin
        # still receive the standard method error after the Host check.
        if not self._same_origin(require_origin=self.headers.get("Origin") is not None):
            self._error(HTTPStatus.FORBIDDEN, "same_origin_required")
            return
        self._error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed")

    def do_OPTIONS(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        self._method_not_allowed()

    def do_PUT(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler entry point
        self._method_not_allowed()


def create_server(
    port: int = 8768,
    registry: Optional[PublicAcquisitionRunRegistry] = None,
) -> PublicAcquisitionServer:
    """Create a loopback-only monitor server; ``port=0`` is useful in tests."""

    if isinstance(port, bool) or not isinstance(port, int) or port < 0 or port > 65535:
        raise ValueError("port must be an integer between 0 and 65535")
    return PublicAcquisitionServer(port=port, registry=registry)
