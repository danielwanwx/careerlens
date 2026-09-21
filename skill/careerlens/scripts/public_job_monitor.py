#!/usr/bin/env python3
"""Serve or follow the portable public-only CareerLens acquisition monitor.

This wrapper intentionally has no credential command-line value.  ``serve
--prompt-key`` uses a masked terminal prompt and keeps the resulting key only
in that server process's environment.
"""

from __future__ import annotations

import argparse
import getpass
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, Iterable, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


DEFAULT_MONITOR_URL = "http://127.0.0.1:8768"
TERMINAL_STATUSES = frozenset({"completed", "partial", "failed"})
_RUN_ID = re.compile(r"^[0-9a-f]{32}$")
_SAFE_REMOTE_ERROR_CODES = frozenset(
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
    }
)


class _NoRedirect(HTTPRedirectHandler):
    """A local monitor request must never be redirected to another origin."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def _require_python_311() -> None:
    if sys.version_info < (3, 11):
        raise RuntimeError("the optional public monitor requires Python 3.11 or later")


def _script_root() -> Path:
    return Path(__file__).resolve().parent


def _load_server() -> Any:
    _require_python_311()
    script_root = str(_script_root())
    if script_root not in sys.path:
        sys.path.insert(0, script_root)
    from public_acquisition.server import create_server

    return create_server


def _normalize_monitor_url(value: str) -> str:
    """Permit only a local server created by this wrapper, never arbitrary URLs."""

    parsed = urlsplit(value.strip())
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or parsed.port is None
    ):
        raise ValueError("monitor URL must be an http://127.0.0.1:<port> origin")
    return urlunsplit(("http", "127.0.0.1:{0}".format(parsed.port), "", "", ""))


def _origin_for_endpoint(url: str) -> str:
    parsed = urlsplit(url)
    return _normalize_monitor_url(urlunsplit((parsed.scheme, parsed.netloc, "", "", "")))


def _json_request(url: str, *, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Origin"] = _origin_for_endpoint(url)
    request = Request(url, data=data, headers=headers, method=method)
    try:
        opener = build_opener(_NoRedirect())
        with opener.open(request, timeout=10) as response:  # nosec B310 - normalized loopback origin only
            raw = response.read(256 * 1024)
    except HTTPError as error:
        try:
            raw = error.read(8 * 1024)
            decoded = json.loads(raw.decode("utf-8"))
            if (
                isinstance(decoded, dict)
                and isinstance(decoded.get("error_code"), str)
                and decoded["error_code"] in _SAFE_REMOTE_ERROR_CODES
            ):
                raise RuntimeError(decoded["error_code"])
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        raise RuntimeError("monitor_request_failed")
    except (URLError, OSError):
        raise RuntimeError("monitor_unavailable")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("monitor_invalid_response")
    if not isinstance(decoded, dict):
        raise RuntimeError("monitor_invalid_response")
    return decoded


def _event_lines(events: Iterable[Any]) -> None:
    for event in events:
        if isinstance(event, dict):
            print(json.dumps(event, ensure_ascii=False, separators=(",", ":")), file=sys.stderr, flush=True)


def _prompt_key() -> None:
    try:
        key = getpass.getpass("TYPESAFE_API_KEY (not saved): ").strip()
    except (EOFError, OSError):
        raise RuntimeError("key_prompt_unavailable")
    if not key:
        raise RuntimeError("empty_key")
    # This alters this process and its worker threads only; it is never written
    # to the API, a URL, the browser, a file, or output.
    os.environ["TYPESAFE_API_KEY"] = key


def _bounded_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _bounded_pages(value: str) -> int:
    try:
        pages = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("max pages must be an integer") from error
    if pages < 1 or pages > 8:
        raise argparse.ArgumentTypeError("max pages must be between 1 and 8")
    return pages


def _bounded_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("timeout must be a number") from error
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 30:
        raise argparse.ArgumentTypeError("timeout must be greater than 0 and at most 30 seconds")
    return timeout


def _bounded_poll(value: str) -> float:
    try:
        interval = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("poll interval must be a number") from error
    if not math.isfinite(interval) or interval < 0.05 or interval > 2:
        raise argparse.ArgumentTypeError("poll interval must be between 0.05 and 2 seconds")
    return interval


def _bounded_wait(value: str) -> float:
    try:
        wait = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("wait seconds must be a number") from error
    if not math.isfinite(wait) or wait <= 0 or wait > 600:
        raise argparse.ArgumentTypeError("wait seconds must be greater than 0 and at most 600")
    return wait


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local, public-only Ashby/Greenhouse acquisition monitor (Python 3.11+)."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    serve = subcommands.add_parser("serve", help="start the fixed 127.0.0.1 monitor")
    serve.add_argument("--port", type=_bounded_port, default=8768)
    serve.add_argument(
        "--prompt-key",
        action="store_true",
        help="masked prompt; retain TYPESAFE_API_KEY only in this server process",
    )

    fetch = subcommands.add_parser("fetch", help="start and follow one run through an existing local monitor")
    fetch.add_argument("--monitor-url", default=DEFAULT_MONITOR_URL)
    fetch.add_argument("--task", required=True, help="public-only role/evidence question")
    fetch.add_argument("--seed-url", action="append", dest="seed_urls", required=True)
    fetch.add_argument("--max-pages", type=_bounded_pages, default=8)
    fetch.add_argument("--timeout-seconds", type=_bounded_timeout, default=8.0)
    fetch.add_argument("--no-jev", action="store_true", help="do not call the optional observed-link selector")
    fetch.add_argument("--detail", action="store_true", help="include bounded public source text")
    fetch.add_argument("--poll-interval", type=_bounded_poll, default=0.25)
    fetch.add_argument("--wait-seconds", type=_bounded_wait, default=300.0)
    return parser


def _serve(arguments: argparse.Namespace) -> int:
    _require_python_311()
    if arguments.prompt_key:
        _prompt_key()
    create_server = _load_server()
    server = create_server(port=arguments.port)
    print(json.dumps({"monitor_url": server.monitor_url}, separators=(",", ":")), flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


def _fetch(arguments: argparse.Namespace) -> int:
    _require_python_311()
    monitor_url = _normalize_monitor_url(arguments.monitor_url)
    payload = {
        "task": arguments.task,
        "seed_urls": arguments.seed_urls,
        "max_pages": arguments.max_pages,
        "timeout_seconds": arguments.timeout_seconds,
        "use_jev": not arguments.no_jev,
        "detail": arguments.detail,
    }
    started = _json_request(monitor_url + "/api/public-acquisition/runs", method="POST", payload=payload)
    run_id = started.get("run_id")
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        raise RuntimeError("monitor_invalid_response")
    # Do not display a URL controlled by a different loopback process.  The
    # checked monitor route is deterministic from the validated origin.
    monitor_page = monitor_url + "/acquire"
    print(
        json.dumps({"monitor_url": monitor_page, "run_id": run_id}, ensure_ascii=False, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )
    after = 0
    deadline = time.monotonic() + arguments.wait_seconds
    while time.monotonic() < deadline:
        snapshot = _json_request(
            monitor_url + "/api/public-acquisition/runs/{0}?after={1}".format(run_id, after)
        )
        events = snapshot.get("events")
        if isinstance(events, list):
            _event_lines(events)
            for event in events:
                if isinstance(event, dict) and isinstance(event.get("event_id"), int):
                    after = max(after, event["event_id"])
        status = snapshot.get("status")
        if status in TERMINAL_STATUSES:
            final = {"monitor_url": monitor_page, "run_id": run_id, "status": status}
            if isinstance(snapshot.get("result"), dict):
                final["result"] = snapshot["result"]
            if isinstance(snapshot.get("error_code"), str):
                final["error_code"] = snapshot["error_code"]
            print(json.dumps(final, ensure_ascii=False, separators=(",", ":")))
            return 0 if status in {"completed", "partial"} else 1
        time.sleep(arguments.poll_interval)
    print(
        json.dumps(
            {"monitor_url": monitor_page, "run_id": run_id, "status": "monitor_wait_timeout"},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 1


def run(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "serve":
            return _serve(arguments)
        if arguments.command == "fetch":
            return _fetch(arguments)
        raise RuntimeError("invalid_command")
    except ValueError:
        print("error: invalid_monitor_url", file=sys.stderr)
        return 2
    except OSError:
        print("error: monitor_port_unavailable; choose another port such as --port 8769", file=sys.stderr)
        return 2
    except RuntimeError as error:
        # All errors are local contract codes.  Avoid echoing remote response
        # text, task text, URLs, or credential values.
        print("error: {0}".format(str(error)), file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
