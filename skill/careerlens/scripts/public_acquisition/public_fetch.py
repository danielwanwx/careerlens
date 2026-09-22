"""Bounded public-only job evidence acquisition for the local Career OS CLI.

This is intentionally a small read-only adapter for documented Ashby and
Greenhouse HTTPS job-board routes. It never submits forms and keeps results in
memory/stdout. It does not open a database, load candidate material, or start
a server.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import getpass
from html import unescape
from html.parser import HTMLParser
import importlib
import ipaddress
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .errors import ProviderAbstention, ProviderResponseError, ProviderUnavailable
from .providers import JevHttpProvider, NormalizedAnswer, ProviderOutput


MAX_SEEDS = 4
MAX_PAGES = 8
# TypeSafe Choice permits 255 criteria. Two are reserved for stop/follow-up.
MAX_LINKS = 253
MAX_LINK_STEPS = 2
MAX_BODY_BYTES = 900_000
MAX_TEXT_CHARS = 12_000
MAX_EVENT_SNIPPET_CHARS = 700
MAX_TASK_CHARS = 1_200
DEFAULT_TIMEOUT_SECONDS = 8.0
ACTION_PATH_TERMS = frozenset(
    {"apply", "application", "login", "signin", "sign-in", "logout", "signout", "delete", "remove", "submit"}
)
SECRET_QUERY_TERMS = frozenset(
    {"token", "key", "secret", "signature", "sig", "auth", "password", "credential"}
)
_LISTING_PATH_TERMS = frozenset(
    {"career", "careers", "job", "jobs", "listing", "listings", "opening", "openings", "position", "positions", "role", "roles", "search"}
)
_JEV_SKIP_UNVERIFIED_SOURCE = "unverified_source"
_JEV_SKIP_STATUS = "locally_excluded"


class PublicFetchError(ValueError):
    """A public acquisition request is outside this intentionally small contract."""


PublicFetchEventCallback = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class _Page:
    requested_url: str
    final_url: str
    status: int | None
    content_type: str
    body: bytes
    elapsed_ms: float
    error_code: str | None = None


@dataclass(frozen=True)
class _Plan:
    seed_url: str
    fetch_url: str
    route: str
    board: str = ""
    job_id: str = ""


@dataclass(frozen=True)
class _ObservedLink:
    label: str
    observed_url: str
    fetch_url: str
    source_url: str
    route: str
    payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class _JevCandidate:
    """One exact public ATS role link permitted in a Jev Choice request."""

    link: _ObservedLink
    canonical_url: str


@dataclass(frozen=True)
class _JevCandidateSkip:
    """A bounded local explanation for an observed link Jev must not receive."""

    link: _ObservedLink
    reason: str


@dataclass(frozen=True)
class _Question:
    qid: str
    type: str
    instructions: str
    criteria: Mapping[str, str]

    def to_wire(self) -> dict[str, Any]:
        return {"type": self.type, "instructions": self.instructions, "criteria": dict(self.criteria)}


@dataclass(frozen=True)
class _ChoiceRequest:
    state: Mapping[str, Any]
    questions: Mapping[str, _Question]
    language: str = "en"

    def questions_wire(self) -> dict[str, Any]:
        return {name: question.to_wire() for name, question in self.questions.items()}


class _NoRedirect(HTTPRedirectHandler):
    """Make every redirect pass the same public/allowlist validation explicitly."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def _compact(value: Any, limit: int = 400) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.replace("\x00", " ").split())[:limit]


def canonical_public_ats_role_url(value: Any) -> str | None:
    """Return a query-free exact public ATS role URL or ``None``.

    This is a deterministic structural allowlist for the Jev Choice boundary.
    It does not fetch, resolve, or infer a source's authority from its text.
    """

    if not isinstance(value, str) or not value or len(value) > 2_048 or "\x00" in value:
        return None
    try:
        parsed = urlsplit(value)
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
        or any(key.casefold() in SECRET_QUERY_TERMS for key, _ in parse_qsl(parsed.query, keep_blank_values=True))
    ):
        return None
    parts = tuple(part for part in parsed.path.split("/") if part)
    lower_parts = tuple(part.casefold() for part in parts)

    def role_segment(segment: str) -> bool:
        return bool(segment) and segment not in ACTION_PATH_TERMS and segment not in _LISTING_PATH_TERMS

    # Ashby and Lever roles have exactly a board and a job identifier.  Requiring
    # that shape keeps their board roots and their action/listing routes out of
    # the Choice request without relying on page text or source metadata.
    two_part_role = len(parts) == 2 and all(role_segment(part) for part in lower_parts)
    exact = (
        (host == "jobs.ashbyhq.com" and two_part_role)
        or (
            host in {"job-boards.greenhouse.io", "boards.greenhouse.io"}
            and len(parts) == 3
            and role_segment(lower_parts[0])
            and lower_parts[1] == "jobs"
            and parts[2].isdigit()
        )
        or (host in {"jobs.lever.co", "jobs.eu.lever.co"} and two_part_role)
        or (
            host.endswith(".myworkdayjobs.com")
            and len(parts) >= 5
            and lower_parts[-3] == "job"
            and all(role_segment(part) for part in lower_parts[:-3])
            and role_segment(lower_parts[-2])
            and role_segment(lower_parts[-1])
        )
    )
    if not exact:
        return None
    return urlunsplit(("https", host, "/" + "/".join(parts), "", ""))


def _prefilter_jev_candidates(
    observed: Sequence[_ObservedLink],
) -> tuple[list[_JevCandidate], list[_JevCandidateSkip]]:
    """Keep only exact public ATS roles before a Jev request is constructed."""

    candidates: list[_JevCandidate] = []
    skipped: list[_JevCandidateSkip] = []
    for link in observed:
        canonical_url = canonical_public_ats_role_url(link.observed_url)
        if canonical_url is None:
            skipped.append(_JevCandidateSkip(link, _JEV_SKIP_UNVERIFIED_SOURCE))
            continue
        candidates.append(_JevCandidate(link, canonical_url))
    return candidates, skipped


def _emit_event(callback: PublicFetchEventCallback | None, event: Mapping[str, Any]) -> None:
    """Best-effort observability seam that can never alter acquisition work.

    The monitor owns timestamping, retention, and output sanitization.  This
    small seam deliberately emits only operational facts already produced by
    the bounded public acquisition path.
    """

    if callback is None:
        return
    try:
        callback(dict(event))
    except Exception:
        # A UI observer must never make an otherwise read-only acquisition fail.
        return


def _safe_url(value: Any, allowed_hosts: set[str] | None = None, *, navigation: bool = False) -> str:
    """Validate HTTPS, public DNS, no credentials/secrets, and this run's host scope.

    The Research Engine's guard is used when installed.  Its DNS-to-connect
    interval remains a documented local-CLI residual; this adapter is never
    exposed as a remotely callable URL-fetch API.
    """

    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError as error:
        raise PublicFetchError("url_invalid") from error
    try:
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as error:
        raise PublicFetchError("url_rejected") from error
    if parsed.scheme.lower() != "https" or not host or parsed.username or parsed.password:
        raise PublicFetchError("url_rejected")
    if port not in (None, 443):
        raise PublicFetchError("url_rejected")
    if any(term in {key.casefold() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)} for term in SECRET_QUERY_TERMS):
        raise PublicFetchError("url_rejected")
    if navigation and any(part.casefold() in ACTION_PATH_TERMS for part in parsed.path.split("/") if part):
        raise PublicFetchError("url_rejected")
    if allowed_hosts is not None and host not in allowed_hosts:
        raise PublicFetchError("url_outside_allowlist")
    _research_engine_validate(urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, "")))
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def _research_engine_validate(url: str) -> None:
    """Reuse Research Engine URL validation when available; retain safe fallback."""

    try:
        from .workspace import RESEARCH_ENGINE_ROOT

        root = Path(RESEARCH_ENGINE_ROOT)
        source = root / "src"
        import_root = str(source if source.is_dir() else root)
        if import_root not in sys.path and Path(import_root).is_dir():
            sys.path.insert(0, import_root)
        validator = importlib.import_module("research_engine.connectors.web").validate_public_url
    except (ImportError, AttributeError, OSError):
        validator = None
    if validator is not None:
        try:
            validator(url)
        except ValueError as error:
            raise PublicFetchError("url_not_public") from error
        return
    host = urlsplit(url).hostname or ""
    try:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        addresses = [ipaddress.ip_address(record[4][0]) for record in records]
    except (OSError, ValueError) as error:
        raise PublicFetchError("url_not_public") from error
    if not addresses or any(not address.is_global for address in addresses):
        raise PublicFetchError("url_not_public")


def _display_url(value: Any) -> str:
    """A syntactically safe public URL retained as evidence, never fetched."""

    try:
        return _safe_url(value, navigation=False)
    except PublicFetchError:
        return ""


def _fetch(url: str, allowed_hosts: set[str], timeout: float) -> _Page:
    started = time.perf_counter()
    current = url
    opener = build_opener(_NoRedirect())
    for _ in range(4):
        try:
            current = _safe_url(current, allowed_hosts, navigation=True)
            request = Request(
                current,
                headers={
                    "User-Agent": "career-os-public-fetch/0.1",
                    "Accept": "application/json,text/html;q=0.9,text/plain;q=0.5",
                },
                method="GET",
            )
            with opener.open(request, timeout=timeout) as response:
                body = response.read(MAX_BODY_BYTES + 1)
                if len(body) > MAX_BODY_BYTES:
                    return _Page(current, current, _status(response), "", b"", _elapsed(started), "body_limit")
                return _Page(
                    current,
                    _safe_url(response.geturl() or current, allowed_hosts, navigation=True),
                    _status(response),
                    str(response.headers.get_content_type() or "").lower(),
                    body,
                    _elapsed(started),
                )
        except HTTPError as error:
            location = error.headers.get("Location") if error.headers else None
            if error.code in {301, 302, 303, 307, 308} and location:
                try:
                    current = _safe_url(urljoin(current, location), allowed_hosts, navigation=True)
                    continue
                except PublicFetchError as validation_error:
                    return _Page(url, current, error.code, "", b"", _elapsed(started), str(validation_error))
            return _Page(url, current, error.code, "", b"", _elapsed(started), "http_error")
        except PublicFetchError as error:
            return _Page(url, current, None, "", b"", _elapsed(started), str(error))
        except (URLError, OSError, TimeoutError):
            return _Page(url, current, None, "", b"", _elapsed(started), "transport_error")
    return _Page(url, current, None, "", b"", _elapsed(started), "redirect_limit")


def _status(response: Any) -> int | None:
    try:
        return int(getattr(response, "status", response.getcode()))
    except (TypeError, ValueError, AttributeError):
        return None


def _elapsed(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


class _Html(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.text: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._skip = 0
        self._in_title = False
        self._href = ""
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
        elif tag == "a" and self._href:
            self.links.append((self._href, _compact(" ".join(self._link_text), 180)))
            self._href = ""

    def handle_data(self, data: str) -> None:
        value = " ".join(data.replace("\x00", " ").split())
        if not value or self._skip:
            return
        self.text.append(value)
        if self._in_title:
            self.title = _compact(f"{self.title} {value}", 240)
        if self._href:
            self._link_text.append(value)


def _html_page(page: _Page) -> tuple[str, str, list[tuple[str, str]]]:
    decoded = page.body.decode("utf-8", errors="replace")
    parser = _Html()
    try:
        parser.feed(decoded)
    except Exception:
        pass
    return parser.title or "Untitled public page", _compact(" ".join(parser.text), MAX_TEXT_CHARS), parser.links


def _event_page_preview(page: _Page) -> tuple[str, str]:
    """Return a small visible-page preview for the browser monitor.

    This deliberately extracts text rather than returning raw HTML or a raw
    ATS JSON document.  It is observational only: acquisition and final
    evidence processing continue to use the original bounded response.
    """

    if page.error_code or not page.body:
        return "", ""
    payload = _json_page(page)
    if isinstance(payload, Mapping):
        values: list[str] = []

        def add(value: Any, limit: int = 180) -> None:
            compact = _compact(value, limit)
            if compact and compact not in values:
                values.append(compact)

        add(payload.get("title"))
        location = payload.get("location")
        if isinstance(location, Mapping):
            add(location.get("name"))
        else:
            add(location)
        for field in ("content", "descriptionPlain", "descriptionHtml"):
            excerpt, _source_chars, _truncated = _evidence_text(payload.get(field))
            add(excerpt, 360)
        jobs = payload.get("jobs")
        if isinstance(jobs, list):
            for job in jobs[:3]:
                if isinstance(job, Mapping):
                    add(job.get("title"))
                    nested_location = job.get("location")
                    if isinstance(nested_location, Mapping):
                        add(nested_location.get("name"))
        return (values[0] if values else "Public ATS response", _compact(" · ".join(values), MAX_EVENT_SNIPPET_CHARS))
    title, visible_text, _links = _html_page(page)
    return _compact(title, 240), _compact(visible_text, MAX_EVENT_SNIPPET_CHARS)


def _evidence_text(value: Any) -> tuple[str, int, bool]:
    """Return a compact visible excerpt plus honest source coverage facts."""

    raw = unescape(str(value or "")).replace("\x00", " ")
    parser = _Html()
    try:
        parser.feed(raw)
    except Exception:
        pass
    text = " ".join((parser.text or [raw])).strip()
    source_chars = len(text)
    return text[:700], source_chars, source_chars > 700


def _full_evidence_text(value: Any) -> str:
    raw = unescape(str(value or "")).replace("\x00", " ")
    parser = _Html()
    try:
        parser.feed(raw)
    except Exception:
        pass
    return " ".join((parser.text or [raw])).strip()[:MAX_TEXT_CHARS]


def _json_page(page: _Page) -> Any:
    if "json" not in page.content_type:
        return None
    try:
        return json.loads(page.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _ats_plan(seed: str) -> _Plan:
    parsed = urlsplit(seed)
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host == "jobs.ashbyhq.com" and parts:
        board = parts[0]
        route = "ashby_exact_api" if len(parts) >= 2 else "ashby_board_api"
        return _Plan(seed, f"https://api.ashbyhq.com/posting-api/job-board/{quote(board)}", route, board)
    if host in {"job-boards.greenhouse.io", "boards.greenhouse.io"} and parts:
        board = parts[0]
        if len(parts) >= 3 and parts[1] == "jobs" and parts[2].isdigit():
            return _Plan(
                seed,
                f"https://boards-api.greenhouse.io/v1/boards/{quote(board)}/jobs/{quote(parts[2])}",
                "greenhouse_exact_api",
                board,
                parts[2],
            )
        return _Plan(
            seed,
            f"https://boards-api.greenhouse.io/v1/boards/{quote(board)}/jobs",
            "greenhouse_board_api",
            board,
        )
    return _Plan(seed, seed, "seed_page")


def _allowed_hosts(seeds: Sequence[str]) -> set[str]:
    hosts = {urlsplit(seed).hostname or "" for seed in seeds}
    for seed in seeds:
        host = urlsplit(seed).hostname or ""
        if host == "jobs.ashbyhq.com":
            hosts.add("api.ashbyhq.com")
        if host in {"job-boards.greenhouse.io", "boards.greenhouse.io"}:
            hosts.add("boards-api.greenhouse.io")
    return {host.lower() for host in hosts if host}


def validate_public_acquisition_request(
    task: Any,
    seed_urls: Any,
    *,
    max_pages: Any = MAX_PAGES,
    timeout_seconds: Any = DEFAULT_TIMEOUT_SECONDS,
    use_jev: Any = True,
    detail: Any = False,
) -> tuple[str, tuple[str, ...], int, float, bool, bool]:
    """Validate the complete public-only request before any worker starts.

    This is intentionally public so the loopback monitor can reject malformed,
    non-ATS, private, or oversized requests synchronously rather than queueing
    them for later failure.  It preserves the existing public-fetch ceilings.
    """

    if (
        not isinstance(task, str)
        or not task.strip()
        or len(task) > MAX_TASK_CHARS
        or "\x00" in task
        or isinstance(seed_urls, (str, bytes))
        or not isinstance(seed_urls, Sequence)
        or not seed_urls
        or len(seed_urls) > MAX_SEEDS
        or isinstance(max_pages, bool)
        or not isinstance(max_pages, int)
        or not 1 <= max_pages <= MAX_PAGES
        or isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or not 0 < float(timeout_seconds) <= 30
        or type(use_jev) is not bool
        or type(detail) is not bool
    ):
        raise PublicFetchError("invalid_input")
    compact_task = _compact(task, MAX_TASK_CHARS)
    if not compact_task:
        raise PublicFetchError("invalid_input")
    raw_seeds = tuple(_safe_url(value, navigation=True) for value in seed_urls)
    if len(set(raw_seeds)) != len(raw_seeds):
        raise PublicFetchError("duplicate_seed_url")
    if any(_ats_plan(seed).route == "seed_page" for seed in raw_seeds):
        raise PublicFetchError("official_ats_seed_required")
    return compact_task, raw_seeds, max_pages, float(timeout_seconds), use_jev, detail


def _canonical(value: str) -> str:
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.path.rstrip("/"), "", ""))


def _ashby_role(
    job: Mapping[str, Any], *, source_url: str, selected_url: str = "", detail: bool = False
) -> dict[str, Any] | None:
    job_url = _display_url(job.get("jobUrl"))
    apply_url = _display_url(job.get("applyUrl"))
    title = _compact(job.get("title"), 240)
    job_id = urlsplit(job_url).path.rstrip("/").split("/")[-1] if job_url else ""
    if not (title and job_id and apply_url):
        return None
    evidence, source_text_chars, evidence_truncated = _evidence_text(job.get("descriptionPlain"))
    result = {
        "title": title,
        "job_id": job_id,
        "source_url": source_url,
        "job_url": job_url,
        "application_url": apply_url,
        "location": _compact(job.get("location"), 180),
        "employment_type": _compact(job.get("employmentType"), 80),
        "listing_scope": "listed" if job.get("isListed") is True else "direct_link_only_or_unspecified",
        "posting_status": "structured_posting_observed",
        "open_status": "unverified",
        "evidence": evidence,
        "source_text_chars": source_text_chars,
        "evidence_truncated": evidence_truncated,
        "selected_observed_url": selected_url or None,
    }
    if detail:
        result["source_text"] = _full_evidence_text(job.get("descriptionPlain"))
    return result


def _greenhouse_role(
    job: Mapping[str, Any], *, source_url: str, selected_url: str = "", detail: bool = False
) -> dict[str, Any] | None:
    title = _compact(job.get("title"), 240)
    job_id = str(job.get("id") or "")
    application_url = _display_url(job.get("absolute_url"))
    if not (title and job_id and application_url):
        return None
    location = job.get("location")
    evidence, source_text_chars, evidence_truncated = _evidence_text(job.get("content"))
    result = {
        "title": title,
        "job_id": job_id,
        "source_url": source_url,
        "job_url": application_url,
        "application_url": application_url,
        "location": _compact(location.get("name") if isinstance(location, Mapping) else "", 180),
        "employment_type": "",
        "listing_scope": "public_job_board",
        "posting_status": "structured_posting_observed",
        "open_status": "unverified",
        "evidence": evidence,
        "source_text_chars": source_text_chars,
        "evidence_truncated": evidence_truncated,
        "selected_observed_url": selected_url or None,
    }
    if detail:
        result["source_text"] = _full_evidence_text(job.get("content"))
    return result


def _links_from_plan(plan: _Plan, page: _Page, allowed_hosts: set[str]) -> tuple[list[_ObservedLink], int]:
    payload = _json_page(page)
    output: list[_ObservedLink] = []
    if plan.route == "greenhouse_board_api" and isinstance(payload, Mapping):
        jobs = payload.get("jobs")
        if isinstance(jobs, list):
            total = len(jobs)
            for job in jobs[:MAX_LINKS]:
                if not isinstance(job, Mapping) or not str(job.get("id") or "").isdigit():
                    continue
                observed = _display_url(job.get("absolute_url"))
                if not observed:
                    continue
                job_id = str(job["id"])
                output.append(
                    _ObservedLink(
                        _compact(job.get("title"), 180) or f"Greenhouse job {job_id}",
                        observed,
                        f"https://boards-api.greenhouse.io/v1/boards/{quote(plan.board)}/jobs/{quote(job_id)}",
                        page.final_url,
                        "greenhouse_selected_job_api",
                        dict(job),
                    )
                )
    elif plan.route == "ashby_board_api" and isinstance(payload, Mapping):
        jobs = payload.get("jobs")
        if isinstance(jobs, list):
            total = len(jobs)
            for job in jobs[:MAX_LINKS]:
                if isinstance(job, Mapping):
                    observed = _display_url(job.get("jobUrl"))
                    if observed:
                        output.append(
                            _ObservedLink(
                                _compact(job.get("title"), 180) or "Ashby job",
                                observed,
                                observed,
                                page.final_url,
                                "ashby_selected_job_page",
                                dict(job),
                            )
                        )
    elif plan.route == "seed_page":
        _, _, links = _html_page(page)
        total = len(links)
        for href, label in links[:MAX_LINKS]:
            try:
                target = _safe_url(urljoin(page.final_url, href), allowed_hosts, navigation=True)
            except PublicFetchError:
                continue
            output.append(_ObservedLink(label or target, target, target, page.final_url, "selected_observed_page"))
    return output, locals().get("total", 0)


def _macos_keychain_jev_credential() -> str | None:
    """Best-effort standalone fallback for a locally configured Jev key.

    Vendored public-fetch callers do not need the Career OS workspace module.
    This mirrors the current-user Keychain lookup without retaining, logging, or
    exposing the credential.  It is a no-op on hosts without macOS's security
    command.
    """

    if sys.platform != "darwin":
        return None
    try:
        import pwd

        current_user = pwd.getpwuid(os.getuid()).pw_name
    except (ImportError, KeyError, OSError):
        try:
            current_user = getpass.getuser()
        except (KeyError, OSError):
            return None
    try:
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-a",
                current_user,
                "-s",
                "typesafe-ai-jev",
                "-w",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    credential = result.stdout.strip()
    return credential or None


def _jev_credential() -> str | None:
    """Resolve an in-memory credential without requiring the workspace module."""

    environment_key = os.environ.get("TYPESAFE_API_KEY")
    if environment_key:
        return environment_key
    try:
        from .workspace import _keychain_jev_credential
    except (ImportError, AttributeError):
        _keychain_jev_credential = None
    if _keychain_jev_credential is not None:
        try:
            credential = _keychain_jev_credential()
        except Exception:
            credential = None
        if credential:
            return credential
    return _macos_keychain_jev_credential()


def _provider(timeout: float) -> JevHttpProvider | None:
    try:
        credential = _jev_credential()
        if not credential:
            return None
        # The direct endpoint is fixed in JevHttpProvider.  Refuse redirects so
        # Authorization can never be replayed to another host.
        return JevHttpProvider(
            model="jev-1.13.0",
            timeout_seconds=timeout,
            api_key=credential,
            opener=build_opener(_NoRedirect()).open,
        )
    except (ProviderUnavailable, OSError):
        return None


def _choose(
    provider: Any,
    task: str,
    candidates: Sequence[_JevCandidate],
    known_roles: Sequence[Mapping[str, Any]],
) -> tuple[str | None, dict[str, Any]]:
    criteria = {
        f"link_{index}": f"Observed exact public ATS role {index}: {candidate.link.label}"
        for index, candidate in enumerate(candidates)
    }
    criteria["done"] = "Stop within the visited seed scope; this is not a claim of global job coverage."
    criteria["needs_followup"] = "No observed link can safely answer the task; retain incomplete evidence."
    request = _ChoiceRequest(
        state={
            "data_scope": "public_job_evidence_only",
            "task": task,
            "observed_links": [
                {
                    "id": f"link_{index}",
                    "label": _compact(item.link.label, 180),
                    "url": item.canonical_url,
                }
                for index, item in enumerate(candidates)
            ],
            "retrieved_structured_posting_count": len(known_roles),
            "policy": {
                "select_only_canonical_public_ats_role": True,
                "no_forms_or_submission": True,
            },
        },
        questions={
            "next_link": _Question(
                "next_link",
                "choice",
                "Choose one next observed public role link relevant to the task, or done/needs_followup. "
                "Do not infer that any job is open and do not choose an unlisted action.",
                criteria,
            )
        },
    )
    started = time.perf_counter()
    try:
        output: ProviderOutput = provider.predict(request)
        answer: NormalizedAnswer = output.answers["next_link"]
        return answer.choice, {
            "status": "ok",
            "model": _compact(output.model, 120),
            "calls": 1,
            "input_tokens": output.usage.get("input_tokens"),
            "output_tokens": output.usage.get("output_tokens"),
            "elapsed_ms": _elapsed(started),
        }
    except (ProviderAbstention, ProviderUnavailable, ProviderResponseError, KeyError):
        return None, {"status": "unavailable", "calls": 1, "input_tokens": None, "output_tokens": None, "elapsed_ms": _elapsed(started)}
    except Exception:
        return None, {"status": "error", "calls": 1, "input_tokens": None, "output_tokens": None, "elapsed_ms": _elapsed(started)}


def _choice_event_summary(
    candidates: Sequence[_JevCandidate], known_roles: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Project the actual Choice prompt/input into a safe, bounded event.

    The stored task itself remains private to the in-memory run.  The monitor
    receives the fixed question and a count/short preview of the public input,
    not the full task or the full evidence sent to Jev.
    """

    return {
        "question": (
            "Choose one next observed public role link relevant to the task, or done/needs_followup. "
            "Do not infer that any job is open and do not choose an unlisted action."
        ),
        "input_summary": {
            "scope": "public_job_evidence_only",
            "task_summary": "stored_public_task",
            "observed_link_count": len(candidates),
            "structured_posting_count": len(known_roles),
            "observed_links": [
                {
                    "id": f"link_{index}",
                    "label": _compact(candidate.link.label, 180),
                    "url": candidate.canonical_url,
                }
                for index, candidate in enumerate(candidates[:3])
            ],
        },
    }


class PublicAcquirer:
    """One bounded vertical slice, with injectable fetch/provider seams for tests."""

    def __init__(
        self,
        *,
        fetcher: Callable[[str, set[str], float], _Page] | None = None,
        jev_provider: Any | None = None,
    ) -> None:
        self._fetcher = fetcher or _fetch
        self._jev_provider = jev_provider

    def _fetch_with_events(
        self,
        plan: _Plan,
        allowed_hosts: set[str],
        timeout_seconds: float,
        *,
        request_id: str,
        stage: str,
        event_callback: PublicFetchEventCallback | None,
    ) -> _Page:
        """Fetch one already-validated public route and expose its real interval."""

        _emit_event(
            event_callback,
            {
                "type": "fetch_started",
                "request_id": request_id,
                "stage": stage,
                "route": plan.route,
                "url": plan.fetch_url,
            },
        )
        try:
            page = self._fetcher(plan.fetch_url, allowed_hosts, timeout_seconds)
        except Exception:
            page = _Page(plan.fetch_url, plan.fetch_url, None, "", b"", 0.0, "transport_error")
        page_title, snippet = _event_page_preview(page)
        _emit_event(
            event_callback,
            {
                "type": "fetch_finished",
                "request_id": request_id,
                "stage": stage,
                "route": plan.route,
                "url": page.requested_url,
                "final_url": page.final_url,
                "http_status": page.status,
                "elapsed_ms": page.elapsed_ms,
                "status": "fetched" if page.error_code is None else page.error_code,
                "page_title": page_title,
                "snippet": snippet,
            },
        )
        return page

    def acquire(
        self,
        task: str,
        seed_urls: Sequence[str],
        *,
        max_pages: int = MAX_PAGES,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        use_jev: bool = True,
        detail: bool = False,
        event_callback: PublicFetchEventCallback | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        task, raw_seeds, max_pages, timeout_seconds, use_jev, detail = validate_public_acquisition_request(
            task,
            seed_urls,
            max_pages=max_pages,
            timeout_seconds=timeout_seconds,
            use_jev=use_jev,
            detail=detail,
        )
        allowed = _allowed_hosts(raw_seeds)
        plans = [_ats_plan(seed) for seed in raw_seeds][:max_pages]
        pages: list[tuple[_Plan, _Page]] = []

        def fetch_initial(index: int, plan: _Plan) -> tuple[_Plan, _Page]:
            return (
                plan,
                self._fetch_with_events(
                    plan,
                    allowed,
                    timeout_seconds,
                    request_id=f"http-{index + 1}",
                    stage="initial_parallel_fetch",
                    event_callback=event_callback,
                ),
            )

        with ThreadPoolExecutor(max_workers=min(4, len(plans))) as pool:
            futures = {pool.submit(fetch_initial, index, plan): plan for index, plan in enumerate(plans)}
            for future in as_completed(futures):
                plan = futures[future]
                try:
                    pages.append(future.result())
                except Exception:
                    pages.append((plan, _Page(plan.fetch_url, plan.fetch_url, None, "", b"", 0.0, "transport_error")))
        pages.sort(key=lambda item: plans.index(item[0]))
        routes: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        observed: list[_ObservedLink] = []
        incomplete: list[str] = ["scope_is_selected_seed_urls_not_global_job_coverage", "opening_status_not_verified"]
        if len(raw_seeds) > len(plans):
            incomplete.append("max_pages_prevented_some_seed_fetches")
        for plan, page in pages:
            routes.append(
                {
                    "stage": "initial_parallel_fetch",
                    "route": plan.route,
                    "seed_url": plan.seed_url,
                    "fetch_url": page.requested_url,
                    "final_url": page.final_url,
                    "http_status": page.status,
                    "elapsed_ms": page.elapsed_ms,
                    "status": "fetched" if page.error_code is None else page.error_code,
                }
            )
            payload = _json_page(page)
            if page.error_code:
                incomplete.append(f"{plan.route}:{page.error_code}")
                continue
            if plan.route == "greenhouse_exact_api" and isinstance(payload, Mapping):
                role = (
                    _greenhouse_role(payload, source_url=page.final_url, detail=detail)
                    if str(payload.get("id") or "") == plan.job_id
                    else None
                )
                if role:
                    evidence.append(role)
                else:
                    incomplete.append("greenhouse_exact_identity_incomplete")
            elif plan.route == "ashby_exact_api" and isinstance(payload, Mapping):
                jobs = payload.get("jobs")
                matched = next(
                    (
                        job for job in jobs
                        if isinstance(job, Mapping) and _canonical(_display_url(job.get("jobUrl"))) == _canonical(plan.seed_url)
                    ),
                    None,
                ) if isinstance(jobs, list) else None
                role = _ashby_role(matched, source_url=page.final_url, detail=detail) if isinstance(matched, Mapping) else None
                if role:
                    evidence.append(role)
                else:
                    incomplete.append("ashby_exact_identity_incomplete")
            page_links, observed_total = _links_from_plan(plan, page, allowed)
            observed.extend(page_links)
            routes[-1]["observed_links"] = {"total": observed_total, "offered": len(page_links), "omitted": max(0, observed_total - len(page_links))}
            if observed_total > len(page_links):
                incomplete.append("observed_links_capped")
        provider = self._jev_provider if self._jev_provider is not None else (_provider(timeout_seconds) if use_jev else None)
        provider_state: dict[str, Any] = {
            "status": "not_requested" if not use_jev else ("ready" if provider else "unavailable"),
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "usage_complete": True,
        }
        visited = {item.fetch_url for item in plans}
        emitted_local_skips: set[tuple[str, str, str]] = set()
        for step in range(MAX_LINK_STEPS):
            available = [item for item in observed if item.fetch_url not in visited]
            candidates, locally_skipped = _prefilter_jev_candidates(available)
            for skipped in locally_skipped:
                identity = (skipped.link.observed_url, skipped.link.fetch_url, skipped.reason)
                if identity in emitted_local_skips:
                    continue
                emitted_local_skips.add(identity)
                event: dict[str, Any] = {
                    "type": "jev_candidate_skipped",
                    "status": _JEV_SKIP_STATUS,
                    "reason": skipped.reason,
                    "route": skipped.link.route,
                }
                event["observed_url"] = skipped.link.observed_url
                _emit_event(event_callback, event)
            if locally_skipped:
                incomplete.append("jev_candidates_locally_excluded")
            eligible_count = len(candidates)
            candidates = candidates[:MAX_LINKS]
            if len(candidates) < eligible_count:
                incomplete.append("remaining_observed_links_not_offered_to_jev")
            if not candidates or len(pages) >= max_pages:
                break
            if provider is None:
                incomplete.append("jev_unavailable_observed_links_not_traversed")
                break
            call_id = f"jev-{step + 1}"
            _emit_event(
                event_callback,
                {
                    "type": "jev_choice_started",
                    "call_id": call_id,
                    "question_count": 1,
                    "candidate_count": len(candidates),
                    **_choice_event_summary(candidates, evidence),
                },
            )
            choice, usage = _choose(provider, task, candidates, evidence)
            _emit_event(
                event_callback,
                {
                    "type": "jev_choice_finished",
                    "call_id": call_id,
                    "question_count": 1,
                    "candidate_count": len(candidates),
                    "choice": choice,
                    "status": usage.get("status"),
                    "model": usage.get("model"),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "elapsed_ms": usage.get("elapsed_ms"),
                },
            )
            provider_state.update({key: usage[key] for key in ("status", "model") if key in usage})
            provider_state["calls"] += usage["calls"]
            for token_field in ("input_tokens", "output_tokens"):
                token_value = usage[token_field]
                if token_value is None:
                    provider_state[token_field] = None
                    provider_state["usage_complete"] = False
                elif provider_state[token_field] is not None:
                    provider_state[token_field] += token_value
            provider_state["elapsed_ms"] = round((provider_state.get("elapsed_ms") or 0) + usage["elapsed_ms"], 3)
            if choice in {"done", "needs_followup"}:
                routes.append({"stage": "jev_choice", "choice": choice, "remaining_observed_links": len(available)})
                incomplete.append("jev_stopped_before_global_coverage")
                break
            if not choice or not choice.startswith("link_"):
                incomplete.append("jev_choice_unavailable")
                break
            try:
                selected = candidates[int(choice.removeprefix("link_"))].link
            except (ValueError, IndexError):
                incomplete.append("jev_choice_invalid")
                break
            selected_plan = _Plan(selected.source_url, selected.fetch_url, selected.route)
            _emit_event(
                event_callback,
                {
                    "type": "selected_link",
                    "call_id": call_id,
                    "choice": choice,
                    "route": selected.route,
                    "observed_url": selected.observed_url,
                    "fetch_url": selected.fetch_url,
                },
            )
            page = self._fetch_with_events(
                selected_plan,
                allowed,
                timeout_seconds,
                request_id=f"http-selected-{step + 1}",
                stage="jev_selected_observed_link",
                event_callback=event_callback,
            )
            pages.append((selected_plan, page))
            visited.add(selected.fetch_url)
            routes.append(
                {
                    "stage": "jev_selected_observed_link",
                    "choice": choice,
                    "observed_url": selected.observed_url,
                    "fetch_url": selected.fetch_url,
                    "route": selected.route,
                    "http_status": page.status,
                    "elapsed_ms": page.elapsed_ms,
                    "status": "fetched" if page.error_code is None else page.error_code,
                }
            )
            payload = _json_page(page)
            role = (
                _greenhouse_role(payload, source_url=page.final_url, selected_url=selected.observed_url, detail=detail)
                if (
                    page.error_code is None
                    and selected.route == "greenhouse_selected_job_api"
                    and isinstance(payload, Mapping)
                    and str(payload.get("id") or "") == str((selected.payload or {}).get("id") or "")
                )
                else _ashby_role(selected.payload or {}, source_url=selected.source_url, selected_url=selected.observed_url, detail=detail)
                if page.error_code is None and selected.route == "ashby_selected_job_page"
                else None
            )
            if role:
                evidence.append(role)
            else:
                incomplete.append("selected_link_not_structured_posting")
        deduped = {f"{item['job_id']}\\0{item['title']}": item for item in evidence}
        evidence = list(deduped.values())
        if not evidence:
            incomplete.append("no_structured_posting_with_job_id_title_and_application_url")
        remaining_observed = [item for item in observed if item.fetch_url not in visited]
        budget_exhausted = bool(
            remaining_observed
            and (len(pages) >= max_pages or provider_state["calls"] >= MAX_LINK_STEPS)
        )
        if remaining_observed:
            incomplete.append("remaining_observed_links_not_traversed")
        if budget_exhausted:
            incomplete.append("navigation_budget_exhausted")
        if provider_state["calls"] == 0 and not observed:
            provider_state["status"] = "not_needed"
        return {
            "status": "completed" if evidence and len(incomplete) == 2 else "partial",
            "data_scope": "public_job_evidence_only",
            "task": task,
            "seed_scope": raw_seeds,
            "limits": {"max_seed_urls": MAX_SEEDS, "max_pages": max_pages, "pages_fetched": len(pages), "max_link_steps": MAX_LINK_STEPS},
            "timing": {"elapsed_ms": _elapsed(started), "parallel_initial_fetches": len(plans)},
            "provider": provider_state,
            "navigation": {
                "remaining_observed_links": len(remaining_observed),
                "budget_exhausted": budget_exhausted,
            },
            "routes": routes,
            "roles": evidence,
            "incomplete": list(dict.fromkeys(incomplete)),
            "security": {
                "https_only": True,
                "allowlisted_hosts": sorted(allowed),
                "forms_clicks_login_post_private_urls": "not_used",
                "dns_to_connect_toc_tou_residual": "loopback_only_local_monitor; not a public-network fetch service",
                "upstream_jev_browser": "disabled_not_embedded",
            },
        }


def acquire_public_jobs(
    task: str,
    seed_urls: Sequence[str],
    *,
    max_pages: int = MAX_PAGES,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    use_jev: bool = True,
    detail: bool = False,
    event_callback: PublicFetchEventCallback | None = None,
) -> dict[str, Any]:
    return PublicAcquirer().acquire(
        task,
        seed_urls,
        max_pages=max_pages,
        timeout_seconds=timeout_seconds,
        use_jev=use_jev,
        detail=detail,
        event_callback=event_callback,
    )
