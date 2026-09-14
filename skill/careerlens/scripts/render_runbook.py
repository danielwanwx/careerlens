#!/usr/bin/env python3
"""Render a deterministic Markdown review view of a runbook."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def render(data: dict[str, Any]) -> str:
    target = data.get("target_picture") or {}
    decision = data.get("decision_state") or {}
    lines = [
        f"# {target.get('role_label') or 'CareerLens'}",
        "",
        f"Artifact: `{(data.get('identity') or {}).get('runbook_id', '')}`",
        "",
        "## Decision",
        "",
        _bullet("State", decision.get("kind") or "unknown"),
        _bullet("Reason", decision.get("reason") or "not recorded"),
        _bullet("Next", decision.get("next_action") or "continue diagnosis"),
        "",
        "## Fit assessment",
        "",
    ]
    for row in data.get("fit_assessment") or []:
        lines.append(_bullet(row.get("label") or row.get("cluster"), row.get("status") or "unknown"))
    lines.extend(["", "## Resume guidance", ""])
    for item in data.get("resume_guidance") or []:
        lines.append(f"### {_safe(item.get('priority') or 'B')} · {_safe(item.get('defect_type') or item.get('finding_id'))}")
        lines.append(_bullet("Why", item.get("why_it_matters") or ""))
        lines.append(_bullet("Direction", item.get("safe_direction") or ""))
        lines.append(_bullet("Boundary", item.get("truth_boundary") or "Do not invent facts."))
        lines.append("")
    lines.extend(["## Interview map", ""])
    for item in (data.get("interview_map") or {}).get("rounds") or []:
        lines.append(f"### {_safe(item.get('label') or item.get('round_id'))}")
        lines.append(str(item.get("purpose") or ""))
        lines.append("")
    lines.extend(["## Roadmap", ""])
    for phase in (data.get("roadmap") or {}).get("phases") or []:
        lines.append(f"### {_safe(phase.get('label') or phase.get('phase_id'))}")
        for action in phase.get("actions") or []:
            lines.append(_bullet(action.get("priority") or "B", f"{action.get('title') or ''} — {action.get('completion_condition') or ''}"))
        lines.append("")
    lines.extend(["## Sources", ""])
    for source in data.get("sources") or []:
        title = _safe(source.get("title") or source.get("source_id"))
        url = str(source.get("url") or "").replace(")", "%29").replace(" ", "%20")
        lines.append(f"- **{_safe(source.get('source_class') or 'unknown')}**: [{title}]({url})")
    return "\n".join(lines).rstrip() + "\n"


def _safe(value: Any) -> str:
    return str(value or "").replace("[", "\\[").replace("]", "\\]").replace("\n", " ").strip()


def _bullet(label: Any, value: Any) -> str:
    return f"- **{_safe(label)}**: {_safe(value)}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = render(json.loads(args.path.read_text(encoding="utf-8")))
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
