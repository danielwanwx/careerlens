#!/usr/bin/env python3
"""Build the deterministic static CareerLens GitHub Pages artifact."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = "/careerlens/"
RUNBOOKS = {
    "ai-engineer-integrity": ROOT / "case-studies/ai-engineer-integrity/output/runbook-demo.html",
    "agentic-llm-platform": ROOT / "case-studies/agentic-llm-platform/output/runbook-demo.html",
}
BUILD_MARKER = ".careerlens-pages-build"
SOCIAL_PREVIEW = ROOT / "assets/launch/social-preview.png"

CASE_METADATA = {
    "ai-engineer-integrity": {
        "title": "AI Engineer Integrity",
        "summary": "A fictional candidate case that shows an evidence-bounded preparation runbook.",
    },
    "agentic-llm-platform": {
        "title": "Agentic LLM Platform",
        "summary": "A synthetic backend and agent-platform case with explicit capability boundaries.",
    },
}

PRIVATE_PERSON_MARKER = "PRIVATE_PERSON_NAME"
PRIVATE_PERSON_PATTERN = re.compile(re.escape(PRIVATE_PERSON_MARKER), re.IGNORECASE)
EMAIL_ADDRESS_PATTERN = re.compile(
    r"(?<![\w.+-])[a-z0-9][a-z0-9._%+-]{0,63}@"
    r"[a-z0-9-]+(?:\.[a-z0-9-]+)+(?![\w.-])",
    re.IGNORECASE,
)
PHONE_NUMBER_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?"
    r"(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]\d{4}(?!\w)"
)
POSIX_HOME_PATH_PATTERN = re.compile(
    r"(?<![\w.-])/(?:users|home)/[^/\s\"'<>]+(?:/|$)",
    re.IGNORECASE,
)
WINDOWS_HOME_PATH_PATTERN = re.compile(
    r"(?<![\w.-])[a-z]:[\\/]+users[\\/]+[^\\/\s\"'<>]+(?:[\\/]|$)",
    re.IGNORECASE,
)
PRIVATE_VOLUME_PATH_PATTERN = re.compile(r"(?<![\w.-])/private(?:/|$)", re.IGNORECASE)
LOCAL_FILE_URL_PATTERN = re.compile(r"file:(?://)?", re.IGNORECASE)
PUBLIC_ROUTE_PATH_PATTERN = re.compile(
    r"/(?:runbook|application-tracker)(?:[/.?#]|$)", re.IGNORECASE
)
RELATIVE_PUBLIC_ROUTE_PATTERN = re.compile(
    r"(?:href|src|action)\s*=\s*[\"']?(?:\.?\.?/)?"
    r"(?:runbook|application-tracker)(?:[/.?#]|[\"']|$)",
    re.IGNORECASE,
)
PUBLIC_TRACKER_DATA_PATH_PATTERN = re.compile(
    r"(?<![\w.-])(?:\.?\.?/)?(?:"
    r"data/application-tracker(?:\.json)?|application-tracker/data(?:\.json)?"
    r")(?![\w.-])",
    re.IGNORECASE,
)
JAVASCRIPT_ESCAPE_PATTERN = re.compile(
    r"\\(?:u(?:([0-9a-f]{4})|\{([0-9a-f]{1,6})\})|x([0-9a-f]{2})|([/\\]))",
    re.IGNORECASE,
)
GITHUB_REPOSITORY_URL = re.compile(
    r"https?://github\.com/[^/?#\s\"'<]+/careerlens(?:/[^\"'<\s]*)?",
    re.IGNORECASE,
)
BINARY_PUBLIC_ARTIFACTS = frozenset(
    {
        Path("media/social-preview.png"),
    }
)


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"required Pages source is missing: {path}")


def normalized_base(base_path: str) -> str:
    stripped = base_path.strip("/")
    return f"/{stripped}/" if stripped else "/"


def workspace_nav(base_path: str, active: str) -> str:
    base = normalized_base(base_path)
    links = (
        ("overview", "Overview", base),
        ("runbook", "Runbook", base + "runbook/"),
        ("tracker", "Tracker", base + "application-tracker/"),
    )
    items = "".join(
        '<a class="cw-nav-link{}" href="{}"{}>{}</a>'.format(
            " active" if key == active else "",
            href,
            ' aria-current="page"' if key == active else "",
            label,
        )
        for key, label, href in links
    )
    return (
        '<header class="cw-topbar"><a class="cw-brand" href="' + base
        + '">CareerLens</a><nav class="cw-nav" aria-label="Career workspace">'
        + items + '</nav><a class="cw-utility" href="https://github.com/">GitHub</a></header>'
    )


def public_nav(base_path: str, active: str) -> str:
    """Return the navigation shared by the public static case-study pages."""
    base = normalized_base(base_path)
    links = (
        ("overview", "Overview", base),
        ("cases", "Case studies", base + "#cases"),
    )
    items = "".join(
        '<a class="cw-nav-link{}" href="{}"{}>{}</a>'.format(
            " active" if key == active else "",
            href,
            ' aria-current="page"' if key == active else "",
            label,
        )
        for key, label, href in links
    )
    return (
        '<header class="cw-topbar"><a class="cw-brand" href="' + base
        + '">CareerLens</a><nav class="cw-nav" aria-label="Public case navigation">'
        + items + '</nav><a class="cw-utility" href="https://github.com/">GitHub</a></header>'
    )


WORKSPACE_CSS = """
.cw-topbar{width:min(1380px,calc(100% - 34px));min-height:68px;margin:auto;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:18px;border-bottom:1px solid #293955;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.cw-brand{color:#eef4ff;text-decoration:none;font-size:18px;font-weight:850;letter-spacing:-.025em}.cw-nav{display:flex;align-items:center;justify-content:initial;min-height:0;gap:5px;padding:5px;border:1px solid #293955;border-radius:12px;background:#101b2ecc}.cw-nav-link{min-height:38px;display:inline-flex;align-items:center;padding:0 13px;border-radius:8px;color:#9aabc5;text-decoration:none;font-size:13px;font-weight:750}.cw-nav-link:hover,.cw-nav-link.active{color:#eef4ff;background:#1b2b45}.cw-nav-link.active{box-shadow:inset 0 -2px #4ed5e8}.cw-utility{justify-self:end;color:#9aabc5;text-decoration:none;font-size:12px}.cw-utility:hover{color:#eef4ff}
@media(max-width:620px){.cw-topbar{grid-template-columns:1fr auto;gap:10px;padding:10px 0}.cw-nav{grid-column:1/-1;grid-row:2;width:100%;justify-content:space-between}.cw-nav-link{flex:1;justify-content:center;padding:0 8px}.cw-utility{grid-column:2;grid-row:1}}
"""


def landing_page(base_path: str = BASE_PATH) -> str:
    base = normalized_base(base_path)
    cards = "".join(
        '<a class="case" href="{}cases/{}/"><span class="tag">Public case</span>'
        "<h2>{}</h2><p>{}</p><strong>Open case study →</strong></a>".format(
            base,
            slug,
            html.escape(str(metadata["title"])),
            html.escape(str(metadata["summary"])),
        )
        for slug, metadata in CASE_METADATA.items()
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Public synthetic CareerLens case studies.">
<title>CareerLens · Public case studies</title>
<style>
:root{{--ink:#eef4ff;--muted:#a7b5ca;--canvas:#08101d;--panel:#101b2e;--line:#293955;--cyan:#4ed5e8;--green:#5ee0a0;--amber:#ffc968}}
{WORKSPACE_CSS}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:radial-gradient(circle at 76% 0,#1b3153 0,transparent 32%),var(--canvas);color:var(--ink);font:16px/1.6 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}}a{{color:inherit}}.shell{{width:min(1120px,calc(100% - 32px));margin:auto}}.hero{{padding:clamp(48px,7vw,84px) 0 34px}}.eyebrow{{color:var(--cyan);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}}h1{{max-width:900px;margin:18px 0 24px;font-size:clamp(44px,7vw,76px);line-height:.98;letter-spacing:-.055em;text-wrap:balance}}.lead{{max-width:760px;color:var(--muted);font-size:clamp(18px,2vw,22px);text-wrap:pretty}}.cases{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;padding-bottom:60px}}.case{{display:flex;min-height:235px;flex-direction:column;padding:26px;border-radius:20px;background:linear-gradient(145deg,#13213a,var(--panel));box-shadow:inset 0 0 0 1px var(--line),0 18px 60px #0003;text-decoration:none;transition:transform 160ms}}.case:hover{{transform:translateY(-3px)}}.case h2{{font-size:28px;line-height:1.1;letter-spacing:-.035em;margin:18px 0 12px}}.case p{{color:var(--muted);margin:0}}.case strong{{margin-top:auto;padding-top:28px;color:var(--cyan)}}.tag{{font-size:11px;color:var(--green);font-weight:800;letter-spacing:.1em;text-transform:uppercase}}footer{{border-top:1px solid var(--line);padding:28px 0 44px;color:var(--muted);font-size:13px}}:focus-visible{{outline:2px solid var(--cyan);outline-offset:4px}}@media(max-width:720px){{.cases{{grid-template-columns:1fr}}.hero{{padding-top:40px}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}.case{{transition:none}}}}
</style>
</head>
<body>
{public_nav(base_path, "overview")}
<div class="shell">
<main>
<section class="hero">
<div class="eyebrow">CareerLens examples</div>
<h1>Public synthetic<br>case studies.</h1>
<p class="lead">These fictional candidate examples demonstrate evidence-bounded preparation workflows with no personal or local data.</p>
</section>
<section id="cases">
<div class="cases">{cards}</div>
</section>
</main>
<footer>CareerLens publishes synthetic product examples only.</footer>
</div>
</body>
</html>
'''


def tracker_page(
    base_path: str = BASE_PATH,
    projection: dict[str, object] | None = None,
) -> str:
    """Return the standalone, read-only application tracker dashboard.

    The page fetches ``data.json`` when served from Pages and also carries the
    same public projection inline as a deterministic fallback.  The fallback
    makes the built page inspectable when opened directly from a local file;
    it contains only the already-sanitized projection.
    """

    base = normalized_base(base_path)
    inline = json.dumps(
        projection or {},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A read-only, evidence-oriented application pipeline dashboard.">
<title>CareerLens · Application Tracker</title>
<style>
__WORKSPACE_CSS__
.cw-topbar{border-bottom-color:#25364c;font-family:"Inter Tight",Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.cw-brand{color:#f4f7fb}.cw-nav{gap:3px;padding:4px;border-color:#25364c;border-radius:4px;background:#0b1422cc}.cw-nav-link{border-radius:3px;color:#9aa9bc}.cw-nav-link:hover,.cw-nav-link.active{color:#f4f7fb;background:#11223a}.cw-nav-link.active{box-shadow:inset 0 -2px #71b8ff}.cw-utility{color:#9aa9bc}.cw-utility:hover{color:#f4f7fb}
:root{--ink:#f4f7fb;--muted:#9aa9bc;--canvas:#050a12;--panel:#0b1422;--panel-2:#11223a;--line:#25364c;--cyan:#71b8ff;--signal:#9bc9f5;--deep:#2d5680;--cool:#72859b;--shadow:0 18px 56px #0008}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;min-width:320px;background-color:var(--canvas);background-image:linear-gradient(#1a2e4412 1px,transparent 1px),linear-gradient(90deg,#1a2e4412 1px,transparent 1px),radial-gradient(circle at 79% 0,#132b4a 0,transparent 36%);background-size:48px 48px,48px 48px,100% 100%;color:var(--ink);font:15px/1.58 "Inter Tight",Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--cyan)}
.shell{width:min(1380px,calc(100% - 34px));margin:auto}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:76px;border-bottom:1px solid var(--line)}
.brand{font-weight:850;letter-spacing:-.025em;color:var(--ink);text-decoration:none;font-size:18px}
.toplinks{display:flex;align-items:center;gap:14px;flex-wrap:wrap;justify-content:flex-end;color:var(--muted);font-size:13px}
.toplinks a{text-decoration:none}
.toplinks a:hover{color:var(--ink)}
.hero{padding:54px 0 30px}
.eyebrow{color:var(--cyan);font-size:11px;font-weight:850;letter-spacing:.13em;text-transform:uppercase}
h1{font-size:clamp(38px,6vw,70px);font-weight:820;line-height:.98;letter-spacing:-.06em;margin:13px 0 15px;max-width:900px;text-wrap:balance}
.lede{max-width:760px;color:var(--muted);font-size:17px;margin:0;text-wrap:pretty}
.meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:19px;color:var(--muted);font-size:12px}
.meta span{padding:5px 9px;border:1px solid var(--line);border-radius:3px;background:#0b1422cc}
.viewbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin:18px 0 14px}
.tabs{display:flex;gap:7px;flex-wrap:wrap}
.tab{min-height:42px;padding:9px 14px;border:1px solid var(--line);border-radius:3px;background:transparent;color:var(--muted);font:inherit;font-weight:750;cursor:pointer}
.tab:hover,.tab[aria-selected="true"]{background:var(--panel-2);color:var(--ink);border-color:#59708e}
.tab[aria-selected="true"]{box-shadow:inset 0 -2px var(--cyan)}
.readonly{color:var(--muted);font-size:12px}
.filters{display:flex;align-items:end;gap:9px;flex-wrap:wrap;padding:14px;border:1px solid var(--line);border-radius:4px;background:#0b1422cc;margin-bottom:20px}
.field{display:flex;flex-direction:column;gap:5px;min-width:145px;flex:1}
.field.search{min-width:240px;flex:2}
.field label{font-size:11px;color:var(--muted);font-weight:750;letter-spacing:.035em}
.field input,.field select{width:100%;min-height:40px;padding:8px 10px;border:1px solid var(--line);border-radius:3px;background:var(--panel);color:var(--ink);font:inherit}
.field input::placeholder{color:#71819a}
.clear{min-height:40px;padding:8px 12px;border:1px solid var(--line);border-radius:3px;background:transparent;color:var(--muted);font:inherit;font-weight:700;cursor:pointer}
.clear:hover{color:var(--ink);border-color:#60718e}
.summary{color:var(--muted);font-size:12px;margin:8px 1px 12px}
.view{display:none}
.view.active{display:block}
.table-wrap{border:1px solid var(--line);border-radius:4px;overflow:auto;background:#0b1422cc;box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;min-width:980px}
th,td{text-align:left;vertical-align:top;padding:14px 13px;border-bottom:1px solid #24334d}
th{color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;background:var(--panel-2)}
tr:last-child td{border-bottom:0}
td.company{font-weight:800;white-space:nowrap}
td.role{min-width:230px}
td.role a{font-weight:750;text-decoration:none}
td.role a:hover{text-decoration:underline}
.sub{color:var(--muted);font-size:12px;margin-top:3px}
.badge{display:inline-flex;align-items:center;min-height:25px;padding:3px 9px;border-radius:3px;background:#172a42;color:var(--muted);font-size:11px;font-weight:800;white-space:nowrap}.badge.submitted{background:#1c4676;color:#d7eaff}.badge.interview{background:#225c9a;color:#e2f0ff}.badge.offer{background:#2f78c8;color:#fff}.badge.closed{background:#1c2633;color:#a7b5c5}.badge.approved,.badge.review{background:#294463;color:#d5e7fa}.badge.verified{background:#1e507f;color:#d3e9ff}.badge.discovered{background:#233249;color:#c7d4e3}
.score{font-variant-numeric:tabular-nums;font-weight:850;color:var(--cyan)}
.mobile-list{display:none}
.empty{padding:45px 24px;border:1px dashed #49617f;border-radius:4px;text-align:center;color:var(--muted);background:#0b142266}
.empty strong{display:block;color:var(--ink);font-size:18px;margin-bottom:5px}
.error{padding:18px;border:1px solid #52759c;border-radius:4px;background:#14263e;color:#dceaff}
.error strong{display:block;margin-bottom:5px}
.board{display:grid;grid-template-columns:repeat(6,minmax(190px,1fr));gap:12px;overflow-x:auto;padding-bottom:6px}
.column{min-height:260px;padding:11px;border:1px solid var(--line);border-radius:4px;background:#0b1422cc}
.column h2{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 10px;font-size:14px;letter-spacing:-.01em}
.column h2 span{display:inline-flex;min-width:23px;justify-content:center;padding:2px 7px;border-radius:999px;background:var(--panel-2);color:var(--muted);font-size:11px}
.role-card{padding:13px;margin:9px 0;border:1px solid var(--line);border-radius:4px;background:linear-gradient(135deg,#0c1727,#08101b);box-shadow:0 7px 24px #0006}
.role-card h3{margin:0 0 5px;font-size:14px;line-height:1.25}
.role-card h3 a{text-decoration:none}.role-card h3 a:hover{text-decoration:underline}
.role-card .sub{margin:0 0 9px}
.card-row{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}
.card-row .badge{font-size:10px}
.card-action{margin-top:9px;color:var(--muted);font-size:11px}
.grid{display:grid;gap:13px}.g4{grid-template-columns:repeat(4,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
.stat{padding:19px;border:1px solid var(--line);border-radius:4px;background:linear-gradient(135deg,#0c1727,#08101b);box-shadow:var(--shadow)}
.stat .value{font-size:32px;line-height:1.05;font-weight:850;color:var(--cyan);font-variant-numeric:tabular-nums}.stat .label{color:var(--muted);font-size:12px;margin-top:7px}.stat .detail{color:var(--muted);font-size:11px;margin-top:4px}
.panel{padding:18px;border:1px solid var(--line);border-radius:4px;background:#0b1422cc;box-shadow:var(--shadow)}
.panel h2{font-size:18px;margin:0 0 13px}.bar-row{display:grid;grid-template-columns:minmax(100px,145px) 1fr 35px;align-items:center;gap:9px;margin:10px 0;color:var(--muted);font-size:12px}.bar{height:6px;border-radius:2px;background:#1a2b40;overflow:hidden}.bar i{display:block;height:100%;min-width:0;border-radius:2px;background:linear-gradient(90deg,#2c679f,var(--cyan))}.legend{margin-top:14px;color:var(--muted);font-size:11px}
.schedule-panel{margin-top:13px}.schedule-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:11px}.schedule-event{padding:14px;border:1px solid var(--line);border-radius:4px;background:linear-gradient(135deg,#0c1727,#08101b)}.schedule-event h3{margin:0 0 4px;font-size:15px;line-height:1.3}.schedule-org{color:var(--cyan);font-weight:750;font-size:12px}.schedule-details{display:grid;gap:3px;margin-top:10px;color:var(--muted);font-size:12px}.schedule-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-top:11px}.event-status{display:inline-flex;align-items:center;min-height:24px;padding:3px 8px;border-radius:3px;background:#225c9a;color:#e2f0ff;font-size:10px;font-weight:800}.event-status.pending{background:#26364a;color:#c6d2df}.event-status.completed{background:#1e507f;color:#d3e9ff}.event-status.cancelled{background:#1c2633;color:#a7b5c5}.event-status.rescheduled{background:#2d5680;color:#deedff}.schedule-next{margin:10px 0 0;color:var(--muted);font-size:11px}
.learning-panel{margin-top:13px}.learning-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}.learning-head h2{margin-bottom:3px}.learning-status{display:inline-flex;align-items:center;min-height:25px;padding:3px 8px;border:1px solid var(--line);border-radius:3px;background:var(--panel-2);color:var(--signal);font-size:10px;font-weight:800;letter-spacing:.035em;text-transform:uppercase}.learning-status.unavailable{color:var(--muted);background:#101a28}.learning-status.no-evidence{color:#c6d2df;background:#1d2a3a}.learning-grid{margin-top:14px}.learning-state-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.learning-state{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border:1px solid var(--line);border-radius:3px;background:#0c1727;color:var(--muted);font-size:12px}.learning-state b{color:var(--ink);font-variant-numeric:tabular-nums}.learning-dimensions{display:flex;flex-wrap:wrap;gap:8px}.learning-dimension{display:flex;align-items:baseline;gap:6px;padding:8px 10px;border:1px solid var(--line);border-radius:3px;background:#0c1727;color:var(--muted);font-size:12px}.learning-dimension b{color:var(--cyan);font-size:15px}.learning-note{margin:14px 0 0;color:var(--muted);font-size:11px}.learning-note strong{color:#cbd6e3}
.operations-panel{margin-top:13px}.operations-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}.operations-head h2{margin-bottom:3px}.operations-status{display:inline-flex;align-items:center;min-height:25px;padding:3px 8px;border:1px solid var(--line);border-radius:3px;background:var(--panel-2);color:var(--signal);font-size:10px;font-weight:800;letter-spacing:.035em;text-transform:uppercase}.operations-status.unavailable{color:var(--muted);background:#101a28}.operations-status.no-runs{color:#c6d2df;background:#1d2a3a}.operations-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}.operations-item{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border:1px solid var(--line);border-radius:3px;background:#0c1727;color:var(--muted);font-size:12px}.operations-item b{color:var(--ink);font-variant-numeric:tabular-nums}.operations-detail{margin:14px 0 0;color:var(--muted);font-size:11px}.operations-detail strong{color:#cbd6e3}
footer{padding:35px 0 48px;margin-top:48px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}
@media(max-width:1120px){.board{grid-template-columns:repeat(6,minmax(205px,1fr))}.g4{grid-template-columns:repeat(2,1fr)}}
@media(max-width:740px){.shell{width:min(100% - 24px,1380px)}.topbar{align-items:flex-start;padding:15px 0}.toplinks{gap:9px;font-size:12px}.hero{padding-top:39px}.lede{font-size:15px}.viewbar{align-items:flex-start;flex-direction:column}.tabs{width:100%}.tab{flex:1}.filters{padding:11px}.field,.field.search{min-width:100%}.clear{width:100%}.table-wrap{display:none}.mobile-list{display:grid;gap:10px}.mobile-list .role-card{margin:0;padding:15px}.role-card .public-note{color:var(--muted);font-size:12px;margin:8px 0 0}.g4,.g2{grid-template-columns:1fr}.bar-row{grid-template-columns:100px 1fr 30px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.tab,.clear{transition:none}}
</style>
</head>
<body>
__WORKSPACE_NAV__
<div class="shell">
<main>
<section class="hero"><div class="eyebrow">Read-only application pipeline</div><h1>Application Tracker</h1><p class="lede">A compact view of the roles in the current hiring pipeline, with the same underlying records across table, board, and summary views.</p><div class="meta"><span id="generated">Last generated: —</span><span id="role-count">Loading roles…</span></div></section>
<div id="load-error" hidden></div>
<section aria-label="Tracker controls">
<div class="viewbar"><div class="tabs" role="tablist" aria-label="Tracker views"><button class="tab" id="tab-overview" role="tab" aria-controls="view-overview" aria-selected="true" data-view="overview">Overview</button><button class="tab" id="tab-all" role="tab" aria-controls="view-all" aria-selected="false" data-view="all">All Applications</button><button class="tab" id="tab-board" role="tab" aria-controls="view-board" aria-selected="false" data-view="board">Board</button><button class="tab" id="tab-stats" role="tab" aria-controls="view-stats" aria-selected="false" data-view="stats">Stats</button><button class="tab" id="tab-learning" role="tab" aria-controls="view-learning" aria-selected="false" data-view="learning">Learning &amp; Diagnosis</button><button class="tab" id="tab-operations" role="tab" aria-controls="view-operations" aria-selected="false" data-view="operations">Pilot Operations</button></div><div class="readonly">Privacy-filtered projection · not editable</div></div>
<div class="filters" id="filters" hidden>
<div class="field search"><label for="search">Search company, role, or location</label><input id="search" type="search" autocomplete="off" placeholder="Try “agent” or “remote”"></div>
<div class="field"><label for="status">Status</label><select id="status"><option value="">All statuses</option></select></div>
<div class="field"><label for="tier">Tier</label><select id="tier"><option value="">All tiers</option></select></div>
<div class="field"><label for="track">Resume track</label><select id="track"><option value="">All tracks</option></select></div>
<div class="field"><label for="sort">Sort</label><select id="sort"><option value="fit">Fit score</option><option value="applied">Application date</option><option value="company">Company</option></select></div>
<button class="clear" id="clear" type="button">Clear filters</button>
</div>
</section>
<div id="summary" class="summary" aria-live="polite"></div>
<section class="view active" id="view-overview" role="tabpanel" aria-labelledby="tab-overview"><div id="overview-content"></div></section>
<section class="view" id="view-all" role="tabpanel" aria-labelledby="tab-all"><div id="all-content"></div></section>
<section class="view" id="view-board" role="tabpanel" aria-labelledby="tab-board"><div id="board-content"></div></section>
<section class="view" id="view-stats" role="tabpanel" aria-labelledby="tab-stats"><div id="stats-content"></div></section>
<section class="view" id="view-learning" role="tabpanel" aria-labelledby="tab-learning"><div id="learning-content"></div></section>
<section class="view" id="view-operations" role="tabpanel" aria-labelledby="tab-operations"><div id="operations-content"></div></section>
</main>
<footer>CareerLens keeps this page read-only and displays only allowlisted tracker information. Verify each opening at its official page before acting.</footer>
</div>
<script id="tracker-data" type="application/json">__INLINE_DATA__</script>
<script>
(() => {
  "use strict";
  const PUBLIC_STATUSES = ["Discovered","Verified","Review","Approved","Submitted","Interview","Offer","Closed"];
  const BOARD_COLUMNS = ["Discovered","Review","Submitted","Interview","Offer","Closed"];
  const LEARNING_STATES = ["needs_check","needs_hint","independent_today","delayed_transfer"];
  const LEARNING_STATE_LABELS = {needs_check:"Needs check",needs_hint:"Needs hint",independent_today:"Independent today",delayed_transfer:"Delayed transfer"};
  const LEARNING_DIMENSION_LABELS = {concepts:"Concepts",causality:"Causality",application:"Application",edges:"Edges",tradeoffs:"Tradeoffs",structure:"Structure",expression:"Expression",retention:"Retention"};
  const PILOT_SOURCES = ["linkedin","indeed","google","greenhouse","ashby","lever","workday","company_careers","wellfound","yc_work_at_a_startup","hacker_news","reddit","substack","lenny"];
  const PILOT_SOURCE_LABELS = {linkedin:"LinkedIn",indeed:"Indeed",google:"Google",greenhouse:"Greenhouse",ashby:"Ashby",lever:"Lever",workday:"Workday",company_careers:"Company careers",wellfound:"Wellfound",yc_work_at_a_startup:"YC Work at a Startup",hacker_news:"Hacker News",reddit:"Reddit",substack:"Substack",lenny:"Lenny"};
  const PILOT_SOURCE_OUTCOMES = ["not_checked","checked","no_results","blocked","error"];
  const PILOT_SOURCE_OUTCOME_LABELS = {not_checked:"Not checked",checked:"Checked",no_results:"No results",blocked:"Blocked",error:"Error"};
  const PILOT_RESULTS = ["completed","partial","blocked","failed"];
  const PILOT_RESULT_LABELS = {completed:"Completed",partial:"Partial",blocked:"Blocked",failed:"Failed"};
  const PILOT_INBOX_STATUSES = ["not_checked","checked","unavailable","failed"];
  const PILOT_INBOX_LABELS = {not_checked:"Not checked",checked:"Checked",unavailable:"Unavailable",failed:"Failed"};
  const PILOT_DECISIONS = ["application","reply","connection","comment","handoff"];
  const PILOT_DECISION_LABELS = {application:"Application",reply:"Reply",connection:"Connection",comment:"Comment",handoff:"Handoff"};
  const PILOT_VERIFICATION_STATUSES = ["not_needed","verified","unverified","failed"];
  const PILOT_TRACKER_STATUSES = ["not_needed","committed","failed"];
  const PILOT_CLEANUP_STATUSES = ["not_needed","completed","failed"];
  const PILOT_EXECUTION_LABELS = {not_needed:"Not needed",verified:"Verified",unverified:"Unverified",committed:"Committed",completed:"Completed",failed:"Failed"};
  const inlineNode = document.getElementById("tracker-data");
  const emptyLearning = () => ({status:"unavailable",updated_at:"",attempts:{total:0,complete:0,incomplete:0},attempt_completion:{complete:0,total:0,percent:null},independent_success:{met:0,total:0,percent:null,unscored:0},section_completion:{complete:0,total:0,percent:null},open_repairs:0,due_repairs:0,open_gaps:0,due_gaps:0,latest_states:{needs_check:0,needs_hint:0,independent_today:0,delayed_transfer:0},dimension_scores:[]});
  const emptyPilotOperations = () => ({status:"unavailable",latest:{completed_at:"",status:""},run_count:0,source_coverage:Object.fromEntries(PILOT_SOURCES.map((key)=>[key,{count:0,latest_outcome:"not_checked",outcome_counts:Object.fromEntries(PILOT_SOURCE_OUTCOMES.map((outcome)=>[outcome,0]))}])),inbox:{latest_status:"not_checked",status_counts:Object.fromEntries(PILOT_INBOX_STATUSES.map((key)=>[key,0])),actionable:0},totals:{discovered:0,verified:0,submitted:0,blocked:0},queue_counts:Object.fromEntries(PILOT_DECISIONS.map((key)=>[key,0])),submission_verification:{latest_status:"not_needed",status_counts:Object.fromEntries(PILOT_VERIFICATION_STATUSES.map((key)=>[key,0]))},tracker_transaction:{latest_status:"not_needed",status_counts:Object.fromEntries(PILOT_TRACKER_STATUSES.map((key)=>[key,0]))},cleanup:{latest_status:"not_needed",status_counts:Object.fromEntries(PILOT_CLEANUP_STATUSES.map((key)=>[key,0]))}});
  const state = {data: {generated_date: "", roles: [], schedule: [], learning: emptyLearning(), pilot_operations: emptyPilotOperations()}, view: "overview", query: "", status: "", tier: "", track: "", sort: "fit", loaded: false};
  const esc = (value) => String(value ?? "").replace(/[&<>\"']/g, (char) => {
    if (char === "&") return "&amp;";
    if (char === "<") return "&lt;";
    if (char === ">") return "&gt;";
    if (char.charCodeAt(0) === 34) return "&quot;";
    return "&#39;";
  });
  const text = (value) => String(value ?? "");
  const natural = (value) => Number.isInteger(value) && value >= 0 ? value : 0;
  const pilotCount = (value) => Number.isSafeInteger(value) && value >= 0 && value <= 1000000000 ? value : 0;
  const percentage = (value) => Number.isInteger(value) && value >= 0 && value <= 100 ? value : null;
  const isoTime = (value) => /^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$/.test(text(value)) ? text(value) : "";
  const localDate = (value) => {
    if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(text(value))) return "—";
    const date = new Date(text(value) + "T00:00:00");
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString(undefined, {year:"numeric", month:"short", day:"numeric"});
  };
  const localDateTime = (value) => {
    const normalized = isoTime(value);
    if (!normalized) return "—";
    const date = new Date(normalized);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString(undefined, {year:"numeric", month:"short", day:"numeric", hour:"numeric", minute:"2-digit"});
  };
  const object = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const normalizeLearning = (value) => {
    const fallback = emptyLearning();
    const source = object(value);
    const status = ["active","no_evidence","unavailable"].includes(source.status) ? source.status : fallback.status;
    const attemptsSource = object(source.attempts);
    const attemptsTotal = natural(attemptsSource.total);
    const attemptsComplete = Math.min(natural(attemptsSource.complete), attemptsTotal);
    const completionSource = object(source.attempt_completion);
    const independentSource = object(source.independent_success);
    const independentTotal = natural(independentSource.total);
    const independentMet = Math.min(natural(independentSource.met), independentTotal);
    const sectionSource = object(source.section_completion);
    const sectionsTotal = natural(sectionSource.total);
    const sectionsComplete = Math.min(natural(sectionSource.complete), sectionsTotal);
    const statesSource = object(source.latest_states);
    const latestStates = Object.fromEntries(LEARNING_STATES.map((key) => [key, natural(statesSource[key])]));
    const byDimension = new Map();
    (Array.isArray(source.dimension_scores) ? source.dimension_scores : []).forEach((item) => {
      const observation = object(item);
      const dimension = text(observation.dimension);
      const score = observation.score;
      const observedAt = isoTime(observation.observed_at);
      if (Object.prototype.hasOwnProperty.call(LEARNING_DIMENSION_LABELS, dimension) && Number.isInteger(score) && score >= 0 && score <= 3 && observedAt) byDimension.set(dimension, {dimension,score,observed_at:observedAt});
    });
    return {
      status,
      updated_at: isoTime(source.updated_at),
      attempts: {total:attemptsTotal,complete:attemptsComplete,incomplete:attemptsTotal - attemptsComplete},
      attempt_completion: {complete:attemptsComplete,total:attemptsTotal,percent:percentage(completionSource.percent)},
      independent_success: {met:independentMet,total:independentTotal,percent:percentage(independentSource.percent),unscored:natural(independentSource.unscored)},
      section_completion: {complete:sectionsComplete,total:sectionsTotal,percent:percentage(sectionSource.percent)},
      open_repairs:natural(source.open_repairs),
      due_repairs:natural(source.due_repairs),
      open_gaps:natural(source.open_gaps),
      due_gaps:natural(source.due_gaps),
      latest_states: latestStates,
      dimension_scores: [...byDimension.values()],
    };
  };
  const normalizePilotOperations = (value) => {
    const fallback = emptyPilotOperations();
    const source = object(value);
    const status = ["available","no_runs","unavailable"].includes(source.status) ? source.status : fallback.status;
    const latestSource = object(source.latest);
    const latestStatus = PILOT_RESULTS.includes(latestSource.status) ? latestSource.status : "";
    const sourceCoverageSource = object(source.source_coverage);
    const sourceCoverage = Object.fromEntries(PILOT_SOURCES.map((key) => {
      const item = object(sourceCoverageSource[key]);
      const outcomeCounts = object(item.outcome_counts);
      return [key, {
        count: pilotCount(item.count),
        latest_outcome: PILOT_SOURCE_OUTCOMES.includes(item.latest_outcome) ? item.latest_outcome : "not_checked",
        outcome_counts: Object.fromEntries(PILOT_SOURCE_OUTCOMES.map((outcome) => [outcome, pilotCount(outcomeCounts[outcome])])),
      }];
    }));
    const inboxSource = object(source.inbox);
    const inboxStatuses = object(inboxSource.status_counts);
    const execution = (value, statuses) => {
      const entry = object(value);
      const statusCounts = object(entry.status_counts);
      return {
        latest_status: statuses.includes(entry.latest_status) ? entry.latest_status : statuses[0],
        status_counts: Object.fromEntries(statuses.map((key) => [key, pilotCount(statusCounts[key])])),
      };
    };
    const totalsSource = object(source.totals);
    const queueSource = object(source.queue_counts);
    return {
      status,
      latest: {completed_at: isoTime(latestSource.completed_at), status: latestStatus},
      run_count: pilotCount(source.run_count),
      source_coverage: sourceCoverage,
      inbox: {
        latest_status: PILOT_INBOX_STATUSES.includes(inboxSource.latest_status) ? inboxSource.latest_status : "not_checked",
        status_counts: Object.fromEntries(PILOT_INBOX_STATUSES.map((key) => [key, pilotCount(inboxStatuses[key])])),
        actionable: pilotCount(inboxSource.actionable),
      },
      totals: Object.fromEntries(["discovered","verified","submitted","blocked"].map((key) => [key, pilotCount(totalsSource[key])])),
      queue_counts: Object.fromEntries(PILOT_DECISIONS.map((key) => [key, pilotCount(queueSource[key])])),
      submission_verification: execution(source.submission_verification, PILOT_VERIFICATION_STATUSES),
      tracker_transaction: execution(source.tracker_transaction, PILOT_TRACKER_STATUSES),
      cleanup: execution(source.cleanup, PILOT_CLEANUP_STATUSES),
    };
  };
  const statusDerivedAction = (status) => ({Discovered:"Verify official role page",Verified:"Review before applying",Review:"Review before applying",Approved:"Prepare application",Submitted:"Monitor recruiter response",Interview:"Prepare for next interview",Offer:"Review offer",Closed:"No action"})[status] || "No action";
  const normalizeRoles = (value) => (Array.isArray(value) ? value : []).map((raw) => {
    const role = object(raw);
    const status = PUBLIC_STATUSES.includes(role.status) ? role.status : "Closed";
    return {...role, status, next_action: statusDerivedAction(status)};
  });
  const statusClass = (value) => text(value).toLowerCase().replace(/\\s+/g, "-");
  const boardStatus = (value) => ["Verified","Review","Approved"].includes(value) ? "Review" : value;
  const optionValues = (field) => [...new Set(state.data.roles.map((role) => text(role[field])).filter(Boolean))].sort((a,b) => a.localeCompare(b));
  const setOptions = (id, values, label) => {
    const select = document.getElementById(id);
    select.innerHTML = `<option value="">${esc(label)}</option>` + values.map((value) => `<option value="${esc(value)}">${esc(value)}</option>`).join("");
  };
  const roleMatches = (role) => {
    const haystack = [role.company, role.role, role.location, role.work_mode, role.tier, role.resume_track, role.status, role.next_action, role.public_note].join(" ").toLowerCase();
    return (!state.query || haystack.includes(state.query)) && (!state.status || role.status === state.status) && (!state.tier || role.tier === state.tier) && (!state.track || role.resume_track === state.track);
  };
  const filtered = () => {
    const rows = state.data.roles.filter(roleMatches).slice();
    rows.sort((a,b) => {
      if (state.sort === "company") return text(a.company).localeCompare(text(b.company)) || text(a.role).localeCompare(text(b.role));
      if (state.sort === "applied") return text(b.applied_date).localeCompare(text(a.applied_date)) || text(a.company).localeCompare(text(b.company));
      return Number(b.fit_score || 0) - Number(a.fit_score || 0) || text(a.company).localeCompare(text(b.company));
    });
    return rows;
  };
  const roleLink = (role) => `<a href="${esc(role.job_url)}" target="_blank" rel="noopener noreferrer">${esc(role.role)}</a>`;
  const badge = (value) => `<span class="badge ${statusClass(value)}">${esc(value)}</span>`;
  const roleCard = (role, compact = false) => `<article class="role-card"><h3>${roleLink(role)}</h3><div class="sub">${esc(role.company)} · ${esc(role.location || "Location not listed")}</div><div class="card-row">${badge(role.status)}<span class="score">${esc(role.fit_score)}/100</span></div>${compact ? `<div class="card-action">${esc(role.next_action || "No action")}</div>` : `<div class="card-action">${esc(role.next_action || "No action")}</div>${role.public_note ? `<div class="public-note">${esc(role.public_note)}</div>` : ""}`}</article>`;
  const empty = (message) => `<div class="empty"><strong>No roles match these filters</strong>${esc(message || "Try clearing one or more filters.")}</div>`;
  const renderAll = (rows) => {
    const target = document.getElementById("all-content");
    if (!rows.length) { target.innerHTML = empty(); return; }
    const table = `<div class="table-wrap"><table><caption class="sr-only">Application tracker roles</caption><thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Location</th><th>Tier</th><th>Fit</th><th>Resume track</th><th>Verified</th><th>Applied</th><th>Next action</th></tr></thead><tbody>${rows.map((role) => `<tr><td class="company">${esc(role.company)}</td><td class="role">${roleLink(role)}${role.public_note ? `<div class="sub">${esc(role.public_note)}</div>` : ""}</td><td>${badge(role.status)}</td><td>${esc(role.location || "—")}<div class="sub">${esc(role.work_mode || "")}</div></td><td>${esc(role.tier || "—")}</td><td><span class="score">${esc(role.fit_score)}</span></td><td>${esc(role.resume_track || "—")}</td><td>${localDate(role.verified_date)}</td><td>${localDate(role.applied_date)}</td><td>${esc(role.next_action || "—")}</td></tr>`).join("")}</tbody></table></div><div class="mobile-list">${rows.map((role) => roleCard(role)).join("")}</div>`;
    target.innerHTML = table;
  };
  const renderBoard = (rows) => {
    const target = document.getElementById("board-content");
    target.innerHTML = `<div class="board">${BOARD_COLUMNS.map((column) => { const cards = rows.filter((role) => boardStatus(role.status) === column); return `<section class="column" aria-labelledby="column-${statusClass(column)}"><h2 id="column-${statusClass(column)}">${esc(column)} <span>${cards.length}</span></h2>${cards.length ? cards.map((role) => roleCard(role, true)).join("") : `<div class="sub">No roles</div>`}</section>`; }).join("")}</div>`;
  };
  const countsFor = (rows, field, values) => values.map((value) => ({label: value, count: rows.filter((role) => role[field] === value).length}));
  const bars = (items, total) => items.map((item) => `<div class="bar-row"><span>${esc(item.label)}</span><span class="bar"><i style="width:${total ? Math.round(item.count / total * 100) : 0}%"></i></span><b>${item.count}</b></div>`).join("");
  const startOfWeek = (value) => { const date = new Date(text(value) + "T00:00:00"); if (Number.isNaN(date.getTime())) return ""; const day = date.getDay() || 7; date.setDate(date.getDate() - day + 1); return date.toISOString().slice(0,10); };
  const renderStats = (rows) => {
    const generated = state.data.generated_date;
    const week = startOfWeek(generated);
    const submitted = rows.filter((role) => Boolean(role.applied_date) || ["Submitted","Interview","Offer"].includes(role.status));
    const applicationsWeek = rows.filter((role) => role.applied_date && (!week || role.applied_date >= week) && (!generated || role.applied_date <= generated)).length;
    const interviews = submitted.filter((role) => ["Interview","Offer"].includes(role.status)).length;
    const responseRate = submitted.length ? Math.round(interviews / submitted.length * 100) : 0;
    const statusCounts = countsFor(rows, "status", PUBLIC_STATUSES);
    const tracks = optionValues("resume_track");
    const trackCounts = countsFor(rows, "resume_track", tracks);
    document.getElementById("stats-content").innerHTML = `<div class="grid g4"><div class="stat"><div class="value">${rows.filter((role) => role.status !== "Closed").length}</div><div class="label">Active roles</div><div class="detail">In the filtered view</div></div><div class="stat"><div class="value">${applicationsWeek}</div><div class="label">Applications this week</div><div class="detail">Week of ${localDate(week)}</div></div><div class="stat"><div class="value">${submitted.length}</div><div class="label">Submitted applications</div><div class="detail">Includes later-stage roles</div></div><div class="stat"><div class="value">${responseRate}%</div><div class="label">Response rate</div><div class="detail">Interview reached ÷ submitted</div></div></div><div class="grid g2" style="margin-top:13px"><section class="panel"><h2>Status distribution</h2>${bars(statusCounts, rows.length) || `<div class="sub">No status data.</div>`}</section><section class="panel"><h2>Resume-track distribution</h2>${bars(trackCounts, rows.length) || `<div class="sub">No resume tracks in this view.</div>`}</section></div><p class="legend">Stats bars and filtered totals use the same rows as the active filters. “Applications this week” uses the tracker generation date as its reference week.</p>`;
  };
  const renderSchedule = () => {
    const events = state.data.schedule;
    if (!events.length) return `<section class="panel schedule-panel"><h2>Scheduled events</h2><div class="sub">No scheduled events are available.</div></section>`;
    return `<section class="panel schedule-panel" aria-labelledby="scheduled-events-title"><h2 id="scheduled-events-title">Scheduled events</h2><div class="schedule-list">${events.map((event) => `<article class="schedule-event"><h3><span class="sr-only">Title: </span>${esc(event.title)}</h3><div class="schedule-org"><span class="sr-only">Organization: </span>${esc(event.organization)}</div><div class="schedule-details"><span><b>Date and time:</b> ${esc(event.datetime)} · ${esc(event.timezone)}</span><span><b>Location:</b> ${esc(event.location)}</span></div><div class="schedule-meta"><span class="event-status ${statusClass(event.status)}"><span class="sr-only">Status: </span>${esc(event.status)}</span></div><p class="schedule-next"><b>Next step:</b> ${esc(event.next_step)}</p></article>`).join("")}</div></section>`;
  };
  const ratio = (numerator, denominator) => denominator ? `${Math.round(numerator / denominator * 100)}%` : "—";
  const learningStatusText = (learning) => ({active:"Evidence available",no_evidence:"No evidence saved",unavailable:"Local source unavailable"})[learning.status] || "Local source unavailable";
  const renderLearningSummary = () => {
    const learning = state.data.learning;
    if (learning.status === "unavailable") return `<section class="panel learning-panel"><div class="learning-head"><div><h2>Learning diagnosis</h2><p class="sub">The local Coach evidence source is unavailable right now.</p></div><span class="learning-status unavailable">Local only</span></div><p class="learning-note">This tracker keeps Coach records local. Start or resume a Coach session to populate a live aggregate summary.</p></section>`;
    if (learning.status === "no_evidence") return `<section class="panel learning-panel"><div class="learning-head"><div><h2>Learning diagnosis</h2><p class="sub">No assessed Coach evidence has been saved yet.</p></div><span class="learning-status no-evidence">No evidence</span></div><p class="learning-note">This space will show coverage and saved assessment signals once there is evidence. It does not treat an unassessed area as a zero.</p></section>`;
    return `<section class="panel learning-panel"><div class="learning-head"><div><h2>Learning diagnosis</h2><p class="sub">Evidence status: ${esc(learningStatusText(learning))} · latest update ${esc(localDateTime(learning.updated_at))}</p></div><span class="learning-status">Local only</span></div><div class="grid g4 learning-grid"><div class="stat"><div class="value">${ratio(learning.attempt_completion.complete, learning.attempt_completion.total)}</div><div class="label">Attempt completion</div><div class="detail">${learning.attempt_completion.complete} complete of ${learning.attempt_completion.total} actual attempts</div></div><div class="stat"><div class="value">${ratio(learning.section_completion.complete, learning.section_completion.total)}</div><div class="label">Section completion</div><div class="detail">${learning.section_completion.complete} current sections complete</div></div><div class="stat"><div class="value">${learning.open_repairs}</div><div class="label">Open repair targets</div><div class="detail">${learning.due_repairs} currently due</div></div><div class="stat"><div class="value">${learning.open_gaps}</div><div class="label">Open debrief gaps</div><div class="detail">${learning.due_gaps} currently due</div></div></div><p class="learning-note">Open <strong>Learning &amp; Diagnosis</strong> for the evidence definitions, current assessment states, and any saved rubric observations.</p></section>`;
  };
  const renderLearning = () => {
    const target = document.getElementById("learning-content");
    const learning = state.data.learning;
    if (learning.status === "unavailable") { target.innerHTML = renderLearningSummary(); return; }
    if (learning.status === "no_evidence") { target.innerHTML = renderLearningSummary(); return; }
    const stateCards = LEARNING_STATES.map((key) => `<div class="learning-state"><span>${esc(LEARNING_STATE_LABELS[key])}</span><b>${learning.latest_states[key]}</b></div>`).join("");
    const dimensionCards = learning.dimension_scores.length ? learning.dimension_scores.map((observation) => `<div class="learning-dimension"><span>${esc(LEARNING_DIMENSION_LABELS[observation.dimension])}</span><b>${observation.score}/3</b><span class="sr-only">Latest observation ${esc(localDateTime(observation.observed_at))}</span></div>`).join("") : `<div class="sub">No anchored rubric scores have been saved yet. Unscored evidence remains valid and is not treated as zero.</div>`;
    const independentDetail = learning.independent_success.total ? `${learning.independent_success.met} met of ${learning.independent_success.total} complete, unhinted attempts with explicit outcomes` : "No complete, unhinted attempts have an explicit outcome yet";
    target.innerHTML = `<section class="panel learning-panel"><div class="learning-head"><div><h2>Learning diagnosis</h2><p class="sub">Evidence status: ${esc(learningStatusText(learning))} · latest saved activity ${esc(localDateTime(learning.updated_at))}</p></div><span class="learning-status">Local only</span></div><div class="grid g4 learning-grid"><div class="stat"><div class="value">${ratio(learning.attempt_completion.complete, learning.attempt_completion.total)}</div><div class="label">Attempt completion</div><div class="detail">${learning.attempt_completion.complete} complete of ${learning.attempt_completion.total} actual attempts</div></div><div class="stat"><div class="value">${ratio(learning.independent_success.met, learning.independent_success.total)}</div><div class="label">Independent success</div><div class="detail">${esc(independentDetail)}${learning.independent_success.unscored ? ` · ${learning.independent_success.unscored} unscored` : ""}</div></div><div class="stat"><div class="value">${ratio(learning.section_completion.complete, learning.section_completion.total)}</div><div class="label">Section completion</div><div class="detail">${learning.section_completion.complete} complete of ${learning.section_completion.total} current sections</div></div><div class="stat"><div class="value">${learning.open_repairs}</div><div class="label">Open repair targets</div><div class="detail">${learning.due_repairs} due now · ${learning.open_gaps} debrief gaps open</div></div></div><div class="grid g2" style="margin-top:13px"><section class="panel"><h2>Current assessment states</h2><div class="learning-state-list">${stateCards}</div><p class="learning-note">Each count uses the latest saved state for an assessed capability. It does not infer a state for unobserved work.</p></section><section class="panel"><h2>Latest observed rubric dimensions</h2><div class="learning-dimensions">${dimensionCards}</div><p class="learning-note">Each score is a saved 0 to 3 observation from one attempt. Scores are shown individually and are never averaged across unrelated tasks.</p></section></div><p class="learning-note"><strong>How to read this:</strong> percentages measure saved evidence coverage and explicit outcomes. They are not mastery, overall interview-readiness, or hiring-probability scores. This local view contains aggregates only, not prompts, answers, topics, repair wording, or contacts.</p></section>`;
  };
  const operationsStatusText = (operations) => ({available:"Receipt aggregate available",no_runs:"No completed run receipts",unavailable:"Local receipt source unavailable"})[operations.status] || "Local receipt source unavailable";
  const executionText = (value) => PILOT_EXECUTION_LABELS[value] || "Not needed";
  const renderPilotOperationsSummary = () => {
    const operations = state.data.pilot_operations;
    if (operations.status === "unavailable") return `<section class="panel operations-panel"><div class="operations-head"><div><h2>Pilot Operations</h2><p class="sub">The local receipt source is unavailable right now.</p></div><span class="operations-status unavailable">Local only</span></div><p class="operations-detail">This tracker shows only fixed aggregate run receipts when the local SQLite source is available.</p></section>`;
    if (operations.status === "no_runs") return `<section class="panel operations-panel"><div class="operations-head"><div><h2>Pilot Operations</h2><p class="sub">No completed run receipts have been saved yet.</p></div><span class="operations-status no-runs">No runs</span></div><p class="operations-detail">Source coverage, inbox states, queue counts, and execution states appear after a bounded receipt is recorded locally.</p></section>`;
    return `<section class="panel operations-panel"><div class="operations-head"><div><h2>Pilot Operations</h2><p class="sub">${esc(operationsStatusText(operations))} · latest run ${esc(PILOT_RESULT_LABELS[operations.latest.status] || "—")} ${esc(localDateTime(operations.latest.completed_at))}</p></div><span class="operations-status">Local only</span></div><div class="grid g4 learning-grid"><div class="stat"><div class="value">${operations.run_count}</div><div class="label">Run receipts</div><div class="detail">Completed local run records</div></div><div class="stat"><div class="value">${operations.totals.submitted}</div><div class="label">Submitted</div><div class="detail">Safe total across receipts</div></div><div class="stat"><div class="value">${operations.inbox.actionable}</div><div class="label">Inbox actionable</div><div class="detail">Latest inbox state: ${esc(PILOT_INBOX_LABELS[operations.inbox.latest_status])}</div></div><div class="stat"><div class="value">${operations.queue_counts.application}</div><div class="label">Application queue</div><div class="detail">Recorded decision count</div></div></div><p class="operations-detail">Open <strong>Pilot Operations</strong> for source coverage, inbox status, decision queues, and verification, tracker, and cleanup execution states.</p></section>`;
  };
  const renderPilotOperations = () => {
    const target = document.getElementById("operations-content");
    const operations = state.data.pilot_operations;
    if (operations.status !== "available") { target.innerHTML = renderPilotOperationsSummary(); return; }
    const sourceItems = PILOT_SOURCES.map((key) => {
      const source = operations.source_coverage[key];
      return `<div class="operations-item"><span>${esc(PILOT_SOURCE_LABELS[key])}</span><span>${esc(PILOT_SOURCE_OUTCOME_LABELS[source.latest_outcome])}</span><b>${source.count}</b></div>`;
    }).join("");
    const queueItems = PILOT_DECISIONS.map((key) => `<div class="operations-item"><span>${esc(PILOT_DECISION_LABELS[key])}</span><b>${operations.queue_counts[key]}</b></div>`).join("");
    const executionItems = [
      ["Submission verification", executionText(operations.submission_verification.latest_status)],
      ["Tracker transaction", executionText(operations.tracker_transaction.latest_status)],
      ["Cleanup", executionText(operations.cleanup.latest_status)],
    ].map(([label, value]) => `<div class="operations-item"><span>${esc(label)}</span><b>${esc(value)}</b></div>`).join("");
    target.innerHTML = `<section class="panel operations-panel"><div class="operations-head"><div><h2>Pilot Operations</h2><p class="sub">Run receipt status: ${esc(PILOT_RESULT_LABELS[operations.latest.status] || "—")} · completed ${esc(localDateTime(operations.latest.completed_at))}</p></div><span class="operations-status">Local only</span></div><div class="grid g4 learning-grid"><div class="stat"><div class="value">${operations.run_count}</div><div class="label">Run receipts</div><div class="detail">Aggregate-only local history</div></div><div class="stat"><div class="value">${operations.totals.discovered}</div><div class="label">Discovered</div><div class="detail">${operations.totals.verified} verified · ${operations.totals.blocked} blocked</div></div><div class="stat"><div class="value">${operations.totals.submitted}</div><div class="label">Submitted</div><div class="detail">Recorded aggregate total</div></div><div class="stat"><div class="value">${operations.inbox.actionable}</div><div class="label">Inbox actionable</div><div class="detail">Latest inbox: ${esc(PILOT_INBOX_LABELS[operations.inbox.latest_status])}</div></div></div><div class="grid g2" style="margin-top:13px"><section class="panel"><h2>Source coverage</h2><div class="operations-list">${sourceItems}</div><p class="operations-detail">Each source shows qualifying-lead counts across receipts. The latest safe outcome is retained locally for each fixed source.</p></section><section class="panel"><h2>Decision queue</h2><div class="operations-list">${queueItems}</div><p class="operations-detail">Counts distinguish application, reply, connection, comment, and handoff decisions without storing any decision text.</p></section></div><div class="grid g2" style="margin-top:13px"><section class="panel"><h2>Inbox</h2><div class="operations-list">${PILOT_INBOX_STATUSES.map((key) => `<div class="operations-item"><span>${esc(PILOT_INBOX_LABELS[key])}</span><b>${operations.inbox.status_counts[key]}</b></div>`).join("")}</div><p class="operations-detail">The latest enum is ${esc(PILOT_INBOX_LABELS[operations.inbox.latest_status])}; unavailable or failed checks are not represented as an empty inbox.</p></section><section class="panel"><h2>Execution state</h2><div class="operations-list">${executionItems}</div><p class="operations-detail">The latest receipt exposes verification, tracker transaction, and cleanup as fixed states only.</p></section></div><p class="operations-detail"><strong>How to read this:</strong> Pilot Operations contains only fixed aggregate receipt data. It excludes roles, identities, contacts, URLs, messages, answers, paths, and resume names.</p></section>`;
  };
  const renderOverview = () => {
    const rows = state.data.roles;
    const active = rows.filter((role) => role.status !== "Closed");
    const submitted = rows.filter((role) => Boolean(role.applied_date) || ["Submitted","Interview","Offer"].includes(role.status));
    const interviews = rows.filter((role) => ["Interview","Offer"].includes(role.status));
    const next = active.slice().sort((a,b) => Number(b.fit_score||0)-Number(a.fit_score||0)).slice(0,4);
    document.getElementById("overview-content").innerHTML = `<div class="grid g4"><div class="stat"><div class="value">${active.length}</div><div class="label">Active roles</div><div class="detail">Still in the working pipeline</div></div><div class="stat"><div class="value">${submitted.length}</div><div class="label">Submitted</div><div class="detail">Applications sent</div></div><div class="stat"><div class="value">${interviews.length}</div><div class="label">Interviews or offers</div><div class="detail">Reached a later stage</div></div><div class="stat"><div class="value">${state.data.roles.length}</div><div class="label">Total tracked</div><div class="detail">Across every status</div></div></div><div class="grid g2" style="margin-top:13px"><section class="panel"><h2>Next actions</h2>${next.length?next.map((role)=>`<div class="bar-row"><b>${esc(role.company)}</b><span>${esc(role.next_action||"No action")}</span><span class="score">${esc(role.fit_score)}</span></div>`).join(""):`<div class="sub">No active roles.</div>`}</section><section class="panel"><h2>Workspace flow</h2><p class="sub">Use <b>All Applications</b> for exact records, <b>Board</b> for stage movement, and <b>Stats</b> for pipeline distribution. Return to <a href="__RUNBOOK__">Runbook</a> for interview preparation.</p></section></div>${renderSchedule()}${renderLearningSummary()}${renderPilotOperationsSummary()}`;
  };
  const render = () => {
    const rows = filtered();
    document.getElementById("summary").textContent = state.loaded ? `Showing ${rows.length} of ${state.data.roles.length} roles` : "Loading roles…";
    renderOverview(); renderAll(rows); renderBoard(rows); renderStats(rows); renderLearning(); renderPilotOperations();
  };
  const showView = (view) => {
    state.view = view;
    document.querySelectorAll(".tab").forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.view === view)));
    document.querySelectorAll(".view").forEach((section) => section.classList.toggle("active", section.id === `view-${view}`));
    document.getElementById("filters").hidden = !["all","board","stats"].includes(view);
  };
  const bind = () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => showView(tab.dataset.view)));
    const controls = [["search","query",(value) => text(value).trim().toLowerCase()], ["status","status",String], ["tier","tier",String], ["track","track",String], ["sort","sort",String]];
    controls.forEach(([id, key, transform]) => { const node = document.getElementById(id); node.addEventListener(id === "search" ? "input" : "change", () => { state[key] = transform(node.value); render(); }); });
    document.getElementById("clear").addEventListener("click", () => { state.query = state.status = state.tier = state.track = ""; state.sort = "fit"; document.getElementById("search").value = ""; ["status","tier","track","sort"].forEach((id) => { document.getElementById(id).value = id === "sort" ? "fit" : ""; }); render(); });
  };
  const normalize = (data) => { const roles = normalizeRoles(Array.isArray(data) ? data : data && Array.isArray(data.roles) ? data.roles : []); const schedule = data && !Array.isArray(data) && Array.isArray(data.schedule) ? data.schedule : []; const learning = data && !Array.isArray(data) ? normalizeLearning(data.learning) : emptyLearning(); const pilotOperations = data && !Array.isArray(data) ? normalizePilotOperations(data.pilot_operations) : emptyPilotOperations(); return {generated_date: data && !Array.isArray(data) ? text(data.generated_date) : "", roles, schedule, learning, pilot_operations: pilotOperations}; };
  const loaded = (data) => { const next = normalize(data); if (state.loaded && JSON.stringify(next) === JSON.stringify(state.data)) return; state.data = next; state.loaded = true; document.getElementById("generated").textContent = `Last generated: ${localDate(state.data.generated_date)}`; document.getElementById("role-count").textContent = `${state.data.roles.length} tracked roles`; setOptions("status", PUBLIC_STATUSES, "All statuses"); setOptions("tier", optionValues("tier"), "All tiers"); setOptions("track", optionValues("resume_track"), "All tracks"); document.getElementById("status").value = state.status; document.getElementById("tier").value = state.tier; document.getElementById("track").value = state.track; render(); };
  const showError = () => { const target = document.getElementById("load-error"); target.hidden = false; target.className = "error"; target.innerHTML = "<strong>Tracker data could not be loaded.</strong><span>Refresh the page or inspect the generated data artifact.</span>"; document.getElementById("role-count").textContent = "Data unavailable"; document.getElementById("summary").textContent = ""; document.getElementById("all-content").innerHTML = ""; document.getElementById("board-content").innerHTML = ""; document.getElementById("stats-content").innerHTML = ""; document.getElementById("learning-content").innerHTML = ""; document.getElementById("operations-content").innerHTML = ""; };
  const refresh = async () => { const response = await fetch("./data.json", {cache:"no-store"}); if (!response.ok) throw new Error("data response"); loaded(await response.json()); };
  const start = async () => { bind(); let fallback = null; try { fallback = JSON.parse(inlineNode.textContent || "{}"); } catch (_) { fallback = null; } try { await refresh(); } catch (_) { if (fallback && (Array.isArray(fallback) || Array.isArray(fallback.roles))) loaded(fallback); else showError(); } window.setInterval(() => { refresh().catch(() => {}); }, 15000); };
  start();
})();
</script>
</body>
</html>
""".replace("__BASE__", base).replace("__RUNBOOK__", base + "runbook/").replace("__INLINE_DATA__", inline).replace("__WORKSPACE_CSS__", WORKSPACE_CSS).replace("__WORKSPACE_NAV__", workspace_nav(base_path, "tracker"))


def integrate_runbook(source: str, base_path: str, *, primary: bool = False) -> str:
    """Add the public case-study shell without changing Runbook internals."""
    if "</style>" not in source or "<body>" not in source:
        raise RuntimeError("Runbook HTML is missing required shell insertion points")
    source = source.replace("</style>", WORKSPACE_CSS + "</style>", 1)
    # Keep the keyword for callers that used the older helper, but Pages no
    # longer emits a primary personal runbook.
    del primary
    return source.replace("<body>", "<body>" + public_nav(base_path, "cases"), 1)


def decode_public_text(text: str) -> str:
    """Normalize common textual encodings before applying Pages privacy guards."""

    def decode_javascript_escape(match: re.Match[str]) -> str:
        hexadecimal = next(
            (group for group in match.groups()[:3] if group is not None), None
        )
        if hexadecimal is not None:
            try:
                return chr(int(hexadecimal, 16))
            except ValueError:
                return match.group(0)
        return match.group(4)

    normalized = text
    for _ in range(3):
        decoded = JAVASCRIPT_ESCAPE_PATTERN.sub(decode_javascript_escape, normalized)
        decoded = html.unescape(unquote(decoded))
        if decoded == normalized:
            break
        normalized = decoded
    return normalized


def assert_public_payload(payload: bytes, *, label: str) -> None:
    """Reject private data and local-only routes from textual Pages artifacts."""
    try:
        normalized = decode_public_text(payload.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"refusing to publish {label}: expected UTF-8 text") from exc

    checks = (
        (PRIVATE_PERSON_PATTERN, "private marker"),
        (EMAIL_ADDRESS_PATTERN, "email address"),
        (PHONE_NUMBER_PATTERN, "phone number"),
        (POSIX_HOME_PATH_PATTERN, "absolute home path"),
        (WINDOWS_HOME_PATH_PATTERN, "Windows absolute home path"),
        (PRIVATE_VOLUME_PATH_PATTERN, "private volume path"),
        (LOCAL_FILE_URL_PATTERN, "local file URL"),
        (PUBLIC_ROUTE_PATH_PATTERN, "local-only tracker or runbook route"),
        (RELATIVE_PUBLIC_ROUTE_PATTERN, "local-only tracker or runbook route"),
        (PUBLIC_TRACKER_DATA_PATH_PATTERN, "local-only tracker data path"),
    )
    for pattern, description in checks:
        if pattern.search(normalized):
            raise RuntimeError(
                f"refusing to publish {label}: contains {description}"
            )


def public_case_page(root: Path, slug: str, source: Path, base_path: str) -> bytes:
    """Load one allowlisted, explicitly fictional case-study page."""
    manifest = root / "case-studies" / slug / "source-manifest.json"
    require_file(source)
    require_file(manifest)
    try:
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid public-case manifest: {manifest}") from exc

    if not isinstance(metadata, dict):
        raise RuntimeError(f"invalid public-case manifest: {manifest}")
    candidate = metadata.get("candidate")
    if (
        metadata.get("case_id") != slug
        or not isinstance(candidate, dict)
        or candidate.get("fictional") is not True
    ):
        raise RuntimeError(
            f"refusing to publish non-fictional or unverified case study: {slug}"
        )

    try:
        source_html = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"invalid public-case HTML: {source}") from exc

    # Citations can point at this repository through an account-specific URL.
    # Keep the public host while dropping any account and repository path.
    source_html = GITHUB_REPOSITORY_URL.sub("https://github.com/", source_html)
    page = integrate_runbook(source_html, base_path)
    payload = page.encode("utf-8")
    assert_public_payload(payload, label=f"case study {slug}")
    return payload


def public_artifacts(root: Path, base_path: str) -> dict[Path, bytes]:
    """Assemble and validate every Pages artifact before replacing output."""
    if set(RUNBOOKS) != set(CASE_METADATA):
        raise RuntimeError("public case metadata must exactly match the Pages allowlist")

    artifacts: dict[Path, bytes] = {
        Path(BUILD_MARKER): b"CareerLens Pages build\n",
        Path(".nojekyll"): b"",
        Path("index.html"): landing_page(base_path).encode("utf-8"),
    }
    for relative, source in (
        (Path("media/social-preview.png"), root / SOCIAL_PREVIEW.relative_to(ROOT)),
    ):
        require_file(source)
        try:
            artifacts[relative] = source.read_bytes()
        except OSError as exc:
            raise RuntimeError(f"unable to read public Pages media: {source}") from exc

    for slug, path in RUNBOOKS.items():
        source = root / path.relative_to(ROOT)
        artifacts[Path("cases") / slug / "index.html"] = public_case_page(
            root, slug, source, base_path
        )

    for relative, payload in artifacts.items():
        if relative not in BINARY_PUBLIC_ARTIFACTS:
            assert_public_payload(payload, label=str(relative))
    return artifacts


def build(output_dir: Path, *, root: Path = ROOT, base_path: str = BASE_PATH) -> None:
    artifacts = public_artifacts(root, base_path)

    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"Pages output is not a directory: {output_dir}")
    if output_dir.exists() and any(output_dir.iterdir()) and not (output_dir / BUILD_MARKER).is_file():
        raise RuntimeError(
            f"refusing to replace an unmarked non-empty directory: {output_dir}"
        )
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for relative, payload in sorted(artifacts.items(), key=lambda item: item[0].as_posix()):
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist/pages")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base-path", default=BASE_PATH)
    args = parser.parse_args()
    build(args.output, root=args.root, base_path=args.base_path)
    print(html.escape(str(args.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
