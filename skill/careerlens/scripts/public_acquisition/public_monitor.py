"""Memory-only live monitor for bounded public job-evidence acquisition.

This module is deliberately HTTP-independent so a loopback server (or a
portable wrapper) can expose the same bounded run contract without importing
the Career OS workspace, personal stores, or private-data adapters.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import os
import re
from threading import Lock, Thread
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import parse_qsl, urlsplit, urlunsplit
from uuid import uuid4

from . import public_fetch


DEFAULT_MAX_RUNS = 8
DEFAULT_MAX_CONCURRENT_RUNS = 2
DEFAULT_MAX_EVENTS = 256
_RUN_ID = re.compile(r"[0-9a-f]{32}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
_CODE = re.compile(r"[A-Za-z0-9_:-]{1,160}\Z")
_MODEL = re.compile(r"[A-Za-z0-9._-]{1,120}\Z")
_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
_CHOICE = re.compile(r"(?:done|needs_followup|link_[0-9]{1,3})\Z")
_EVENT_TYPES = frozenset(
    {
        "fetch_started",
        "fetch_finished",
        "jev_choice_started",
        "jev_choice_finished",
        "selected_link",
    }
)
_STAGES = frozenset(("initial_parallel_fetch", "jev_selected_observed_link"))
_SECRET_QUERY_TERMS = frozenset(
    {"token", "key", "secret", "signature", "sig", "auth", "password", "credential"}
)


@dataclass
class _Run:
    run_id: str
    task: str
    seed_urls: tuple[str, ...]
    max_pages: int
    timeout_seconds: float
    use_jev: bool
    detail: bool
    created_at: str
    created_at_epoch_ms: int
    status: str = "queued"
    started_at: str | None = None
    finished_at: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    next_event_id: int = 1
    result: dict[str, Any] | None = None
    error_code: str | None = None


def _now() -> tuple[str, int]:
    wall = datetime.now(timezone.utc)
    return wall.isoformat(timespec="milliseconds").replace("+00:00", "Z"), int(time.time() * 1000)


def _finite_number(value: Any, maximum: float = 600_000) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)) or not 0 <= float(value) <= maximum:
        return None
    return value


def _nonnegative_int(value: Any, maximum: int) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        return None
    return value


def _safe_token(value: Any) -> str | None:
    return value if isinstance(value, str) and _TOKEN.fullmatch(value) and not _contains_configured_secret(value) else None


def _safe_model(value: Any) -> str | None:
    return value if isinstance(value, str) and _MODEL.fullmatch(value) and not _contains_configured_secret(value) else None


def _safe_code(value: Any) -> str | None:
    return value if isinstance(value, str) and _CODE.fullmatch(value) and not _contains_configured_secret(value) else None


def _contains_configured_secret(value: str) -> bool:
    configured_key = os.environ.get("TYPESAFE_API_KEY")
    return bool(configured_key and configured_key in value)


def _safe_label(value: Any, *, maximum: int) -> str | None:
    if not isinstance(value, str) or "\x00" in value:
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    # An API key must never travel through a browser-facing monitor response,
    # even if a faulty test seam or a remote page accidentally reflected it.
    if _contains_configured_secret(compact):
        return "[redacted]"
    return compact[:maximum]


def _safe_public_text(value: Any, *, maximum: int) -> str | None:
    """Keep bounded public evidence while replacing a configured credential."""

    if not isinstance(value, str):
        return None
    text = value.replace("\x00", " ")[:maximum]
    configured_key = os.environ.get("TYPESAFE_API_KEY")
    if configured_key:
        text = text.replace(configured_key, "[redacted]")
    return text or None


def _safe_public_url(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) > 2_048 or "\x00" in value:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    try:
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or _contains_configured_secret(value)
    ):
        return None
    if any(key.casefold() in _SECRET_QUERY_TERMS for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
        return None
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def _safe_choice(value: Any) -> str | None:
    return value if isinstance(value, str) and _CHOICE.fullmatch(value) and not _contains_configured_secret(value) else None


def _safe_event(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    event_type = raw.get("type")
    if event_type not in _EVENT_TYPES:
        return None
    event: dict[str, Any] = {"type": event_type}
    if event_type.startswith("fetch_"):
        request_id = raw.get("request_id")
        stage = raw.get("stage")
        route = _safe_token(raw.get("route"))
        url = _safe_public_url(raw.get("url"))
        if not (isinstance(request_id, str) and _REQUEST_ID.fullmatch(request_id) and stage in _STAGES and route and url):
            return None
        event.update({"request_id": request_id, "stage": stage, "route": route, "url": url})
        if event_type == "fetch_finished":
            final_url = _safe_public_url(raw.get("final_url"))
            if final_url:
                event["final_url"] = final_url
            page_title = _safe_label(raw.get("page_title"), maximum=240)
            if page_title:
                event["page_title"] = page_title
            snippet = _safe_public_text(raw.get("snippet"), maximum=public_fetch.MAX_EVENT_SNIPPET_CHARS)
            if snippet:
                event["snippet"] = snippet
            status = _safe_code(raw.get("status"))
            if status:
                event["status"] = status
            http_status = _nonnegative_int(raw.get("http_status"), 599)
            if http_status is not None and http_status >= 100:
                event["http_status"] = http_status
            elapsed_ms = _finite_number(raw.get("elapsed_ms"))
            if elapsed_ms is not None:
                event["elapsed_ms"] = elapsed_ms
        return event
    if event_type.startswith("jev_choice_"):
        call_id = raw.get("call_id")
        question_count = raw.get("question_count")
        candidate_count = _nonnegative_int(raw.get("candidate_count"), public_fetch.MAX_LINKS)
        if (
            not isinstance(call_id, str)
            or not _REQUEST_ID.fullmatch(call_id)
            or question_count != 1
            or candidate_count is None
        ):
            return None
        event.update({"call_id": call_id, "question_count": 1, "candidate_count": candidate_count})
        if event_type == "jev_choice_started":
            question = _safe_label(raw.get("question"), maximum=360)
            if question:
                event["question"] = question
            raw_summary = raw.get("input_summary")
            if isinstance(raw_summary, Mapping):
                summary: dict[str, Any] = {}
                scope = _safe_token(raw_summary.get("scope"))
                task_summary = _safe_label(raw_summary.get("task_summary"), maximum=120)
                observed_count = _nonnegative_int(raw_summary.get("observed_link_count"), public_fetch.MAX_LINKS)
                structured_count = _nonnegative_int(raw_summary.get("structured_posting_count"), public_fetch.MAX_PAGES)
                if scope:
                    summary["scope"] = scope
                if task_summary:
                    summary["task_summary"] = task_summary
                if observed_count is not None:
                    summary["observed_link_count"] = observed_count
                if structured_count is not None:
                    summary["structured_posting_count"] = structured_count
                raw_links = raw_summary.get("observed_links")
                if isinstance(raw_links, list):
                    links: list[dict[str, str]] = []
                    for raw_link in raw_links[:3]:
                        if not isinstance(raw_link, Mapping):
                            continue
                        link_id = _safe_choice(raw_link.get("id"))
                        label = _safe_label(raw_link.get("label"), maximum=180)
                        url = _safe_public_url(raw_link.get("url"))
                        if link_id and label and url:
                            links.append({"id": link_id, "label": label, "url": url})
                    if links:
                        summary["observed_links"] = links
                if summary:
                    event["input_summary"] = summary
        if event_type == "jev_choice_finished":
            choice = _safe_choice(raw.get("choice"))
            if choice:
                event["choice"] = choice
            status = _safe_code(raw.get("status"))
            if status:
                event["status"] = status
            model = _safe_model(raw.get("model"))
            if model:
                event["model"] = model
            for name in ("input_tokens", "output_tokens"):
                value = raw.get(name)
                if value is None:
                    event[name] = None
                else:
                    parsed = _nonnegative_int(value, 10_000_000)
                    if parsed is not None:
                        event[name] = parsed
            elapsed_ms = _finite_number(raw.get("elapsed_ms"))
            if elapsed_ms is not None:
                event["elapsed_ms"] = elapsed_ms
        return event
    call_id = raw.get("call_id")
    choice = _safe_choice(raw.get("choice"))
    route = _safe_token(raw.get("route"))
    observed_url = _safe_public_url(raw.get("observed_url"))
    fetch_url = _safe_public_url(raw.get("fetch_url"))
    if (
        not isinstance(call_id, str)
        or not _REQUEST_ID.fullmatch(call_id)
        or not choice
        or not route
        or not observed_url
        or not fetch_url
    ):
        return None
    event.update(
        {
            "call_id": call_id,
            "choice": choice,
            "route": route,
            "observed_url": observed_url,
            "fetch_url": fetch_url,
        }
    )
    return event


def _safe_result(raw: Any) -> dict[str, Any]:
    """Project only documented public-fetch output; never echo request/task/errors."""

    if not isinstance(raw, Mapping):
        return {"status": "partial", "roles": [], "routes": [], "incomplete": ["result_unavailable"]}
    status = raw.get("status")
    result: dict[str, Any] = {
        "status": status if status in {"completed", "partial"} else "partial",
        "data_scope": "public_job_evidence_only",
        "roles": [],
        "routes": [],
        "incomplete": [],
    }
    seed_scope = raw.get("seed_scope")
    if isinstance(seed_scope, Sequence) and not isinstance(seed_scope, (str, bytes)):
        result["seed_scope"] = [url for value in seed_scope if (url := _safe_public_url(value))]
    limits = raw.get("limits")
    if isinstance(limits, Mapping):
        safe_limits: dict[str, int] = {}
        for name, maximum in (("max_seed_urls", public_fetch.MAX_SEEDS), ("max_pages", public_fetch.MAX_PAGES), ("pages_fetched", public_fetch.MAX_PAGES), ("max_link_steps", public_fetch.MAX_LINK_STEPS)):
            value = _nonnegative_int(limits.get(name), maximum)
            if value is not None:
                safe_limits[name] = value
        if safe_limits:
            result["limits"] = safe_limits
    timing = raw.get("timing")
    if isinstance(timing, Mapping):
        safe_timing: dict[str, int | float] = {}
        for name in ("elapsed_ms", "parallel_initial_fetches"):
            value = _finite_number(timing.get(name))
            if value is not None:
                safe_timing[name] = value
        if safe_timing:
            result["timing"] = safe_timing
    provider = raw.get("provider")
    if isinstance(provider, Mapping):
        safe_provider: dict[str, Any] = {}
        status_value = _safe_code(provider.get("status"))
        if status_value:
            safe_provider["status"] = status_value
        model = _safe_model(provider.get("model"))
        if model:
            safe_provider["model"] = model
        for name, maximum in (("calls", public_fetch.MAX_LINK_STEPS), ("input_tokens", 10_000_000), ("output_tokens", 10_000_000)):
            value = provider.get(name)
            if value is None and name in {"input_tokens", "output_tokens"}:
                safe_provider[name] = None
            else:
                parsed = _nonnegative_int(value, maximum)
                if parsed is not None:
                    safe_provider[name] = parsed
        if isinstance(provider.get("usage_complete"), bool):
            safe_provider["usage_complete"] = provider["usage_complete"]
        elapsed_ms = _finite_number(provider.get("elapsed_ms"))
        if elapsed_ms is not None:
            safe_provider["elapsed_ms"] = elapsed_ms
        if safe_provider:
            result["provider"] = safe_provider
    for raw_route in raw.get("routes", []) if isinstance(raw.get("routes"), list) else []:
        if not isinstance(raw_route, Mapping):
            continue
        route: dict[str, Any] = {}
        for name in ("stage", "route", "choice"):
            value = _safe_token(raw_route.get(name))
            if value:
                route[name] = value
        status_value = _safe_code(raw_route.get("status"))
        if status_value:
            route["status"] = status_value
        for name in ("seed_url", "fetch_url", "final_url", "observed_url"):
            value = _safe_public_url(raw_route.get(name))
            if value:
                route[name] = value
        http_status = _nonnegative_int(raw_route.get("http_status"), 599)
        if http_status is not None and http_status >= 100:
            route["http_status"] = http_status
        elapsed_ms = _finite_number(raw_route.get("elapsed_ms"))
        if elapsed_ms is not None:
            route["elapsed_ms"] = elapsed_ms
        observed_links = raw_route.get("observed_links")
        if isinstance(observed_links, Mapping):
            route["observed_links"] = {
                name: value
                for name, maximum in (("total", public_fetch.MAX_BODY_BYTES), ("offered", public_fetch.MAX_LINKS), ("omitted", public_fetch.MAX_BODY_BYTES))
                if (value := _nonnegative_int(observed_links.get(name), maximum)) is not None
            }
        if route:
            result["routes"].append(route)
    for raw_role in raw.get("roles", []) if isinstance(raw.get("roles"), list) else []:
        if not isinstance(raw_role, Mapping):
            continue
        role: dict[str, Any] = {}
        for name, maximum in (("title", 240), ("job_id", 160), ("location", 180), ("employment_type", 80), ("listing_scope", 80), ("posting_status", 80), ("open_status", 80)):
            value = _safe_label(raw_role.get(name), maximum=maximum)
            if value:
                role[name] = value
        for name in ("source_url", "job_url", "application_url", "selected_observed_url"):
            value = _safe_public_url(raw_role.get(name))
            if value:
                role[name] = value
        for name in ("source_text_chars",):
            value = _nonnegative_int(raw_role.get(name), public_fetch.MAX_BODY_BYTES)
            if value is not None:
                role[name] = value
        if isinstance(raw_role.get("evidence_truncated"), bool):
            role["evidence_truncated"] = raw_role["evidence_truncated"]
        evidence = _safe_public_text(raw_role.get("evidence"), maximum=700)
        if evidence is not None:
            role["evidence"] = evidence
        source_text = _safe_public_text(raw_role.get("source_text"), maximum=public_fetch.MAX_TEXT_CHARS)
        if source_text is not None:
            role["source_text"] = source_text
        if role:
            result["roles"].append(role)
    incomplete = raw.get("incomplete")
    if isinstance(incomplete, list):
        result["incomplete"] = [value for item in incomplete if (value := _safe_code(item))][:64]
    navigation = raw.get("navigation")
    if isinstance(navigation, Mapping):
        safe_navigation: dict[str, Any] = {}
        remaining = _nonnegative_int(
            navigation.get("remaining_observed_links"), public_fetch.MAX_SEEDS * public_fetch.MAX_LINKS
        )
        if remaining is not None:
            safe_navigation["remaining_observed_links"] = remaining
        if isinstance(navigation.get("budget_exhausted"), bool):
            safe_navigation["budget_exhausted"] = navigation["budget_exhausted"]
        if safe_navigation:
            result["navigation"] = safe_navigation
    return result


class PublicAcquisitionRunRegistry:
    """A small, thread-safe, bounded registry for active public acquisition runs."""

    def __init__(
        self,
        *,
        acquirer_factory: Callable[[], Any] = public_fetch.PublicAcquirer,
        max_runs: int = DEFAULT_MAX_RUNS,
        max_concurrent_runs: int = DEFAULT_MAX_CONCURRENT_RUNS,
        max_events: int = DEFAULT_MAX_EVENTS,
    ) -> None:
        if (
            isinstance(max_runs, bool)
            or not isinstance(max_runs, int)
            or max_runs < 1
            or isinstance(max_concurrent_runs, bool)
            or not isinstance(max_concurrent_runs, int)
            or not 1 <= max_concurrent_runs <= max_runs
            or isinstance(max_events, bool)
            or not isinstance(max_events, int)
            or max_events < 1
        ):
            raise ValueError("invalid_monitor_bounds")
        self._acquirer_factory = acquirer_factory
        self._max_runs = max_runs
        self._max_concurrent_runs = max_concurrent_runs
        self._max_events = max_events
        self._runs: OrderedDict[str, _Run] = OrderedDict()
        self._lock = Lock()

    def start(
        self,
        task: str,
        seed_urls: Sequence[str],
        *,
        max_pages: int = public_fetch.MAX_PAGES,
        timeout_seconds: float = public_fetch.DEFAULT_TIMEOUT_SECONDS,
        use_jev: bool = True,
        detail: bool = False,
    ) -> dict[str, Any]:
        task, seed_urls, max_pages, timeout_seconds, use_jev, detail = public_fetch.validate_public_acquisition_request(
            task,
            seed_urls,
            max_pages=max_pages,
            timeout_seconds=timeout_seconds,
            use_jev=use_jev,
            detail=detail,
        )
        created_at, created_at_epoch_ms = _now()
        run = _Run(
            run_id=uuid4().hex,
            task=task,
            seed_urls=seed_urls,
            max_pages=max_pages,
            timeout_seconds=timeout_seconds,
            use_jev=use_jev,
            detail=detail,
            created_at=created_at,
            created_at_epoch_ms=created_at_epoch_ms,
        )
        with self._lock:
            self._make_room_locked()
            active = sum(item.status in {"queued", "running"} for item in self._runs.values())
            if active >= self._max_concurrent_runs:
                raise public_fetch.PublicFetchError("run_capacity_reached")
            self._runs[run.run_id] = run
        try:
            Thread(target=self._execute, args=(run.run_id,), daemon=True, name=f"public-acquire-{run.run_id[:8]}").start()
        except RuntimeError:
            with self._lock:
                run.status = "failed"
                run.finished_at = _now()[0]
                run.error_code = "acquisition_failed"
                self._append_event_locked(run, {"type": "failed", "error_code": run.error_code})
        return self.snapshot(run.run_id) or {"run_id": run.run_id, "status": "failed"}

    def rerun(self, run_id: str) -> dict[str, Any] | None:
        """Start one new run using only an existing run's private settings.

        The browser never receives the stored task, seeds, or options.  A
        caller gets the normal new-run summary or ``None`` when the requested
        memory-only run has already been evicted.
        """

        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
            return None
        with self._lock:
            previous = self._runs.get(run_id)
            if previous is None:
                return None
            task = previous.task
            seed_urls = previous.seed_urls
            max_pages = previous.max_pages
            timeout_seconds = previous.timeout_seconds
            use_jev = previous.use_jev
            detail = previous.detail
        return self.start(
            task,
            seed_urls,
            max_pages=max_pages,
            timeout_seconds=timeout_seconds,
            use_jev=use_jev,
            detail=detail,
        )

    def snapshot(self, run_id: str, *, after: int = 0) -> dict[str, Any] | None:
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
            return None
        if isinstance(after, bool) or not isinstance(after, int) or after < 0:
            raise public_fetch.PublicFetchError("invalid_cursor")
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return None
            last_event_id = run.next_event_id - 1
            first_event_id = run.events[0]["event_id"] if run.events else run.next_event_id
            if after > last_event_id or (after and after < first_event_id - 1):
                raise public_fetch.PublicFetchError("invalid_cursor")
            response = self._summary_locked(run)
            response["events"] = [dict(event) for event in run.events if event["event_id"] > after]
            response["next_event_id"] = last_event_id
            if run.result is not None:
                response["result"] = dict(run.result)
            if run.error_code is not None:
                response["error_code"] = run.error_code
            return response

    def latest(self, *, after: int = 0) -> dict[str, Any] | None:
        with self._lock:
            run_id = next(reversed(self._runs), None) if self._runs else None
        return self.snapshot(run_id, after=after) if run_id is not None else None

    def list_runs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._summary_locked(run) for run in reversed(self._runs.values())]

    def _make_room_locked(self) -> None:
        while len(self._runs) >= self._max_runs:
            removable = next(
                (run_id for run_id, run in self._runs.items() if run.status in {"completed", "partial", "failed"}),
                None,
            )
            if removable is None:
                raise public_fetch.PublicFetchError("run_capacity_reached")
            self._runs.pop(removable, None)

    def _execute(self, run_id: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return
            run.status = "running"
            run.started_at = _now()[0]
            self._append_event_locked(run, {"type": "run_started"})
        try:
            acquirer = self._acquirer_factory()
            raw_result = acquirer.acquire(
                run.task,
                run.seed_urls,
                max_pages=run.max_pages,
                timeout_seconds=run.timeout_seconds,
                use_jev=run.use_jev,
                detail=run.detail,
                event_callback=lambda event: self._record_event(run_id, event),
            )
            result = _safe_result(raw_result)
            terminal_status = result["status"]
            with self._lock:
                current = self._runs.get(run_id)
                if current is None:
                    return
                current.result = result
                current.status = terminal_status
                current.finished_at = _now()[0]
                self._append_event_locked(current, {"type": "completed", "status": terminal_status})
        except Exception:
            with self._lock:
                current = self._runs.get(run_id)
                if current is None:
                    return
                current.status = "failed"
                current.finished_at = _now()[0]
                current.error_code = "acquisition_failed"
                self._append_event_locked(current, {"type": "failed", "error_code": current.error_code})

    def _record_event(self, run_id: str, raw_event: Mapping[str, Any]) -> None:
        if not isinstance(raw_event, Mapping):
            return
        event = _safe_event(raw_event)
        if event is None:
            return
        with self._lock:
            run = self._runs.get(run_id)
            if run is not None and run.status in {"queued", "running"}:
                self._append_event_locked(run, event)

    def _append_event_locked(self, run: _Run, event: Mapping[str, Any]) -> None:
        timestamp, epoch_ms = _now()
        item = {"event_id": run.next_event_id, "at": timestamp, "at_epoch_ms": epoch_ms, **dict(event)}
        run.next_event_id += 1
        run.events.append(item)
        if len(run.events) > self._max_events:
            del run.events[: len(run.events) - self._max_events]

    @staticmethod
    def _summary_locked(run: _Run) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "status": run.status,
            "created_at": run.created_at,
            "created_at_epoch_ms": run.created_at_epoch_ms,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
        }
