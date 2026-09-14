#!/usr/bin/env python3
"""Build deterministic Markdown and standalone HTML for the public AI case."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "case-studies" / "ai-engineer-integrity"


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_markdown(data: dict[str, Any]) -> str:
    decision = data["decision_state"]
    target = data["target_picture"]
    weeks = data["roadmap"]["weeks"]
    lines = [
        f"# CareerLens public {target['role_label']} case",
        "",
        "> Reproducible demonstration using an MIT-licensed fictional candidate and a dated official target role. This is not a real application or hiring prediction.",
        "",
        "## Executive decision",
        "",
        f"- **Target:** {target['role_label']}",
        f"- **Decision:** {decision['kind']}",
        f"- **Reason:** {decision['reason']}",
        f"- **Next action:** {decision['next_action']}",
        "- **Numeric fit score:** intentionally not used",
        "",
        "## Evidence matrix",
        "",
        "| Capability | State | Candidate evidence boundary |",
        "|---|---|---|",
    ]
    for row in data["fit_assessment"]:
        refs = ", ".join(row.get("proof_refs") or []) or "No candidate-owned proof"
        boundary = row.get("boundary") or refs
        lines.append(f"| {row['label']} | `{row['status']}` | {boundary} |")

    lines.extend(["", "## Resume guidance", ""])
    for item in data["resume_guidance"]:
        lines.extend([
            f"### {item['priority']} · {item['finding_id']}",
            "",
            f"- **Why it matters:** {item['why_it_matters']}",
            f"- **Safe direction:** {item['safe_direction']}",
            f"- **Truth boundary:** {item['truth_boundary']}",
            f"- **Done when:** {item['completion_check']}",
            "",
        ])

    lines.extend(["## Interview preparation map", ""])
    for item in data["interview_map"]["rounds"]:
        lines.append(f"- **{item['label']}:** {item['purpose']}")
    lines.extend(["", f"> {data['interview_map']['boundary']}", ""])

    lines.extend([f"## {weeks}-week preparation plan", ""])
    for phase in data["roadmap"]["phases"]:
        lines.extend([f"### {phase['label']}", ""])
        for action in phase["actions"]:
            lines.append(
                f"- **{action['priority']} · {action['title']}** "
                f"({action['estimated_minutes']} minutes): {action['completion_condition']}"
            )
        lines.append("")

    lines.extend(["## Selected questions and answer boundaries", ""])
    guidance = {row["question_id"]: row for row in data["answer_guidance"]}
    for question in data["question_bank"]:
        lines.extend([
            f"### {question['prompt']}",
            "",
            f"**Why asked:** {question['why_asked']}",
            "",
        ])
        answer = guidance.get(question["question_id"])
        if answer:
            lines.append("**Answer structure:** " + " → ".join(answer["outline"]))
            lines.append("")
            if answer["missing_facts"]:
                lines.append("**Still missing:** " + ", ".join(answer["missing_facts"]))
                lines.append("")
            if answer["prohibited_claims"]:
                lines.append("**Do not claim:** " + ", ".join(answer["prohibited_claims"]))
                lines.append("")

    lines.extend(["## Learning sequence", ""])
    for track in data["learning_tracks"]:
        lines.extend([f"### {track['title']}", ""])
        for resource in track["resources"]:
            lines.extend([
                f"{resource['sequence']}. [{resource['title']}]({resource['url']})",
                f"   - Read: {resource['reading_scope']}",
                f"   - Skip: {resource['skip_guidance']}",
                f"   - Mastery check: {resource['completion_condition']}",
            ])
        lines.append("")

    lines.extend(["## Provenance and limitations", ""])
    for source in data["sources"]:
        lines.append(
            f"- [{source['title']}]({source['url']}): {source['claim_scope']}"
        )
    lines.extend([
        "- Official role pages were active when retrieved; this report does not promise that they remain open.",
        "- Interview rounds and questions are preparation guidance inferred from supplied requirements, not a confirmed employer interview loop.",
        "- No referenced organization endorses CareerLens.",
        "- No numeric fit score, interview probability, offer probability, or employment prediction is produced.",
        "",
        "See [ATTRIBUTION.md](../ATTRIBUTION.md) and [source-manifest.json](../source-manifest.json).",
        "",
    ])
    return "\n".join(lines)


def evidence_cards(data: dict[str, Any]) -> str:
    cards = []
    for row in data["fit_assessment"]:
        refs = row.get("proof_refs") or []
        evidence = row.get("boundary") or (", ".join(refs) if refs else "No candidate-owned proof")
        cards.append(
            f'<article class="evidence-card {esc(row["status"])}" data-state="{esc(row["status"])}">'
            f'<div class="state">{esc(row["status"])}</div>'
            f'<h3>{esc(row["label"])}</h3><p>{esc(evidence)}</p></article>'
        )
    return "".join(cards)


def build_html(data: dict[str, Any]) -> str:
    decision = data["decision_state"]
    counts = {state: 0 for state in ("proved", "claimed", "missing", "unknown")}
    for row in data["fit_assessment"]:
        counts[row["status"]] += 1
    guidance_html = "".join(
        f'<article class="guidance"><span class="priority">Priority {esc(item["priority"])}</span>'
        f'<h3>{esc(item["finding_id"].replace("-", " ").title())}</h3>'
        f'<p>{esc(item["why_it_matters"])}</p><dl>'
        f'<dt>Safe direction</dt><dd>{esc(item["safe_direction"])}</dd>'
        f'<dt>Truth boundary</dt><dd>{esc(item["truth_boundary"])}</dd>'
        f'<dt>Done when</dt><dd>{esc(item["completion_check"])}</dd></dl></article>'
        for item in data["resume_guidance"]
    )
    rounds_html = "".join(
        f'<li><span>{index:02d}</span><div><strong>{esc(item["label"])}</strong><p>{esc(item["purpose"])}</p></div></li>'
        for index, item in enumerate(data["interview_map"]["rounds"], 1)
    )
    actions_html = "".join(
        f'<article class="action"><div><span class="priority">{esc(action["priority"])}</span>'
        f'<span class="minutes">{esc(action["estimated_minutes"])} min</span></div>'
        f'<h3>{esc(action["title"])}</h3><p>{esc(action["completion_condition"])}</p></article>'
        for phase in data["roadmap"]["phases"] for action in phase["actions"]
    )
    resources_html = "".join(
        f'<li><span>{esc(resource["sequence"])}</span><div><a href="{esc(resource["url"])}">{esc(resource["title"])}</a>'
        f'<p><b>Read:</b> {esc(resource["reading_scope"])}</p>'
        f'<p><b>Master:</b> {esc(resource["completion_condition"])}</p></div></li>'
        for track in data["learning_tracks"] for resource in track["resources"]
    )
    questions_html = "".join(
        f'<details><summary><span>{esc(item["kind"].replace("_", " "))}</span>{esc(item["prompt"])}</summary>'
        f'<p>{esc(item["why_asked"])}</p></details>' for item in data["question_bank"]
    )
    generated_date = data["identity"]["generated_at"][:10]
    weeks = data["roadmap"]["weeks"]
    capacity = weeks * data["roadmap"]["weekly_capacity_hours"]
    actions = [action for phase in data["roadmap"]["phases"] for action in phase["actions"]]
    planned_hours = sum(action["estimated_minutes"] for action in actions) / 60
    source_items = "".join(
        f'<li><a href="{esc(source["url"])}">{esc(source["title"])}</a>: {esc(source["claim_scope"])}</li>'
        for source in data["sources"]
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CareerLens · Public {esc(data['target_picture']['role_label'])} Case</title>
<style>
:root{{--ink:#172033;--muted:#697386;--canvas:#f6f3ec;--panel:#fffdf8;--line:#dcd5c8;--navy:#18243d;--blue:#4a6fa5;--green:#17745b;--amber:#a66508;--rose:#a13a4b;--violet:#6550a2;--shadow:0 18px 60px rgba(23,32,51,.10)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--canvas);color:var(--ink);font:16px/1.55 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}a{{color:var(--blue)}}.shell{{max-width:1180px;margin:auto;padding:24px}}nav{{display:flex;justify-content:space-between;align-items:center;padding:8px 0 28px}}.brand{{font-weight:800;letter-spacing:-.03em;font-size:22px}}.tag{{font:700 11px/1 ui-monospace,SFMono-Regular,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}}.hero{{background:var(--navy);color:#f8fafc;border-radius:28px;padding:clamp(28px,5vw,64px);box-shadow:var(--shadow);position:relative;overflow:hidden}}.hero:after{{content:"";position:absolute;width:420px;height:420px;border:1px solid rgba(255,255,255,.14);border-radius:50%;right:-180px;top:-190px;box-shadow:0 0 0 70px rgba(255,255,255,.025),0 0 0 140px rgba(255,255,255,.018)}}.eyebrow{{color:#93c5fd;font:700 12px ui-monospace,SFMono-Regular,monospace;letter-spacing:.12em;text-transform:uppercase}}h1{{font-size:clamp(42px,7vw,84px);line-height:.98;letter-spacing:-.055em;max-width:900px;margin:18px 0 24px}}.hero p{{max-width:760px;color:#cbd5e1;font-size:18px}}.decision{{display:inline-flex;align-items:center;gap:10px;margin-top:24px;padding:12px 16px;border:1px solid rgba(255,255,255,.2);border-radius:999px;background:rgba(255,255,255,.08);font-weight:800}}.decision i{{width:10px;height:10px;border-radius:50%;background:#fbbf24;box-shadow:0 0 18px #fbbf24}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 56px}}.stat{{padding:22px;border:1px solid var(--line);border-radius:18px;background:var(--panel)}}.stat b{{display:block;font-size:34px;letter-spacing:-.04em}}.stat span{{color:var(--muted);font-size:13px;text-transform:uppercase;letter-spacing:.08em}}section{{padding:38px 0}}.section-head{{display:grid;grid-template-columns:1fr 1.2fr;gap:30px;align-items:end;margin-bottom:24px}}h2{{font-size:clamp(30px,4vw,52px);line-height:1.05;letter-spacing:-.04em;margin:0}}.section-head p{{color:var(--muted);margin:0}}.evidence-grid,.guidance-grid,.action-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.evidence-card,.guidance,.action{{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:22px}}.evidence-card{{border-top:5px solid var(--line)}}.evidence-card.proved{{border-top-color:var(--green)}}.evidence-card.claimed{{border-top-color:var(--amber)}}.evidence-card.missing{{border-top-color:var(--rose)}}.evidence-card.unknown{{border-top-color:var(--violet)}}.state,.priority,.minutes{{display:inline-block;font:700 11px ui-monospace,SFMono-Regular,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}h3{{margin:10px 0 8px;letter-spacing:-.02em}}.evidence-card p,.guidance p,.action p{{color:var(--muted);margin-bottom:0}}dl{{border-top:1px solid var(--line);padding-top:12px}}dt{{font-weight:800;margin-top:12px}}dd{{margin:3px 0;color:var(--muted)}}.rounds,.resources{{list-style:none;padding:0;margin:0;background:var(--panel);border:1px solid var(--line);border-radius:20px;overflow:hidden}}.rounds li,.resources li{{display:grid;grid-template-columns:52px 1fr;gap:14px;padding:20px;border-bottom:1px solid var(--line)}}.rounds li:last-child,.resources li:last-child{{border:0}}.rounds li>span,.resources li>span{{font:800 16px ui-monospace,SFMono-Regular,monospace;color:var(--blue)}}.rounds p,.resources p{{margin:4px 0;color:var(--muted)}}.action>div{{display:flex;justify-content:space-between}}details{{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:9px 0;padding:16px 18px}}summary{{cursor:pointer;font-weight:750}}summary span{{font:700 10px ui-monospace,SFMono-Regular,monospace;text-transform:uppercase;letter-spacing:.1em;color:var(--blue);margin-right:12px}}details p{{color:var(--muted);padding-left:12px}}.provenance{{background:#e9e4d9;border-radius:24px;padding:28px}}.provenance ul{{margin-bottom:0}}footer{{padding:40px 0;color:var(--muted);font-size:13px}}@media(max-width:760px){{.shell{{padding:14px}}.hero{{border-radius:20px}}.stats{{grid-template-columns:repeat(2,1fr)}}.section-head{{grid-template-columns:1fr}}.evidence-grid,.guidance-grid,.action-grid{{grid-template-columns:1fr}}}}@media(prefers-color-scheme:dark){{:root{{--ink:#eef2f7;--muted:#aab4c5;--canvas:#0d1320;--panel:#151d2c;--line:#2b3548;--navy:#121a2a;--blue:#8fb6ec;--shadow:none}}.provenance{{background:#121a2a}}}}@media print{{body{{background:white;color:black}}.shell{{max-width:none}}nav{{display:none}}.hero{{box-shadow:none;border:1px solid #999}}details{{break-inside:avoid}}}}
</style>
</head>
<body><main class="shell">
<nav><div class="brand">CareerLens</div><div class="tag">Public case · {esc(generated_date)}</div></nav>
<header class="hero"><div class="eyebrow">Licensed fictional candidate × dated official role</div><h1>Strong AI experience.<br>Three decisive gaps.</h1><p>{esc(decision['reason'])}</p><div class="decision"><i></i>{esc(decision['kind'])} fit · no numeric score</div></header>
<div class="stats"><div class="stat"><b>{counts['proved']}</b><span>proved</span></div><div class="stat"><b>{counts['claimed']}</b><span>claimed</span></div><div class="stat"><b>{counts['missing']}</b><span>missing</span></div><div class="stat"><b>{counts['unknown']}</b><span>unknown</span></div></div>
<section><div class="section-head"><h2>Evidence before opinion</h2><p>Candidate facts come from a disclosed fictional profile. Target requirements come from dated official role pages. CareerLens keeps its inferences visible and bounded.</p></div><div class="evidence-grid">{evidence_cards(data)}</div></section>
<section><div class="section-head"><h2>Resume guidance with truth boundaries</h2><p>The goal is not to manufacture a closer match. It is to strengthen what can be defended and leave genuine gaps explicit.</p></div><div class="guidance-grid">{guidance_html}</div></section>
<section><div class="section-head"><h2>Preparation-oriented interview map</h2><p>These round types are inferred from supplied official requirements. They are not represented as a confirmed employer interview loop.</p></div><ol class="rounds">{rounds_html}</ol></section>
<section><div class="section-head"><h2>A {weeks}-week, capacity-aware plan</h2><p>{len(actions)} bounded actions total {planned_hours:g} hours within a declared {capacity:g}-hour capacity. Every action has a completion condition.</p></div><div class="action-grid">{actions_html}</div></section>
<section><div class="section-head"><h2>Questions worth preparing</h2><p>Each question traces to the role or an evidence gap. Open a question to see why it belongs.</p></div>{questions_html}</section>
<section><div class="section-head"><h2>Read less. Master the right parts.</h2><p>Four non-duplicative sources with reading scope and mastery checks.</p></div><ol class="resources">{resources_html}</ol></section>
<section class="provenance"><div class="tag">Provenance and limitations</div><h2>Reproducible, not predictive</h2><ul>{source_items}<li>Official role pages were active when retrieved and may later change or close.</li><li>This report does not predict interviews, offers, or employment outcomes.</li><li>No referenced organization endorses CareerLens.</li></ul></section>
<footer>CareerLens · Evidence-bounded career diagnosis for Codex · Artifact {esc(data['identity']['runbook_id'])}</footer>
</main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runbook", type=Path, default=CASE_DIR / "output" / "runbook.json")
    parser.add_argument("--output-dir", type=Path, default=CASE_DIR / "output")
    args = parser.parse_args()
    data = load_json(args.runbook)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.md").write_text(build_markdown(data), encoding="utf-8")
    (args.output_dir / "report.html").write_text(build_html(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
