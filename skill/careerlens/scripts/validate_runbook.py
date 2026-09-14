#!/usr/bin/env python3
"""Validate personalized_runbook.v1 using only the Python standard library."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
REQUIRED = {
    "identity", "input_status", "target_picture", "candidate_picture",
    "fit_assessment", "decision_state", "resume_guidance", "target_portfolio",
    "strategy", "interview_map", "learning_tracks", "question_bank",
    "answer_guidance", "roadmap", "application_experiment", "sources", "quality",
}
FIT_STATES = {"proved", "claimed", "missing", "unknown"}
SOURCE_CLASSES = {
    "candidate_owned", "official", "primary_technical", "government",
    "university", "established_learning", "community", "unknown",
}
PRIORITIES = {"A", "B", "C"}
SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|password|bearer\s+[a-z0-9._-]{12,}|token\s*[:=]\s*[a-z0-9._-]{12,})")
PRIVATE_RE = re.compile(r"(?:/Users/|/home/|[A-Z]:\\Users\\|-----BEGIN [A-Z ]+PRIVATE KEY-----)")


def validate(data: Any, *, strict: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return _receipt(["artifact must be a JSON object"], warnings)
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append("missing required sections: " + ", ".join(missing))
    identity = _object(data.get("identity"))
    if identity.get("schema_version") != "personalized_runbook.v1":
        errors.append("identity.schema_version must be personalized_runbook.v1")
    for index, row in enumerate(_list(data.get("fit_assessment"))):
        if not isinstance(row, dict) or row.get("status") not in FIT_STATES:
            errors.append(f"fit_assessment[{index}].status is invalid")
            continue
        if row.get("status") in {"proved", "claimed"}:
            refs = [str(item) for item in _list(row.get("proof_refs"))]
            if not refs or any(not item.startswith("candidate:") for item in refs):
                errors.append(f"fit_assessment[{index}] requires candidate-owned proof_refs")
    decision = _object(data.get("decision_state"))
    if decision.get("kind") == "input_gate":
        if decision.get("show_numeric_score") is not False or decision.get("score") is not None:
            errors.append("input_gate must not display a numeric score")
        if _object(data.get("quality")).get("export_ready") is True:
            errors.append("input_gate cannot be export_ready")
    full_runbook = _object(data.get("quality")).get("runbook_depth") == "dynamic_full"
    if full_runbook:
        for section in ("module_selection", "selection_methodology"):
            if section not in data:
                errors.append(f"dynamic_full runbook missing {section}")
    for index, module in enumerate(_list(data.get("module_selection"))):
        if not isinstance(module, dict):
            errors.append(f"module_selection[{index}] must be an object")
            continue
        for field in ("module_id", "state", "reason", "confidence"):
            if not str(module.get(field) or "").strip():
                errors.append(f"module_selection[{index}] missing {field}")
        if module.get("state") not in {"enabled", "deferred", "suppressed"}:
            errors.append(f"module_selection[{index}].state is invalid")
        if not _list(module.get("evidence_refs")):
            errors.append(f"module_selection[{index}] requires evidence_refs")
    methodology = _object(data.get("selection_methodology"))
    if full_runbook:
        for field in ("question_factors", "resource_factors", "plan_factors"):
            if not _list(methodology.get(field)):
                errors.append(f"selection_methodology.{field} must not be empty")
    resources = _resources(data)
    urls: set[str] = set()
    for resource_id, resource in resources:
        url = str(resource.get("url") or "")
        if not url.startswith("https://"):
            errors.append(f"resource {resource_id} must use an HTTPS URL")
        if url in urls:
            errors.append(f"duplicate resource URL: {url}")
        urls.add(url)
        if resource.get("source_class") not in SOURCE_CLASSES:
            errors.append(f"resource {resource_id} has invalid source_class")
        fields = ["reading_scope", "skip_guidance", "completion_condition", "verification_state"]
        if full_runbook:
            fields.extend(["candidate_starting_state", "resource_role", "assigned_output"])
        for field in fields:
            if not str(resource.get(field) or "").strip():
                errors.append(f"resource {resource_id} missing {field}")
        if full_runbook and float(resource.get("estimated_minutes") or 0) <= 0:
            errors.append(f"resource {resource_id} requires positive estimated_minutes")
        if full_runbook and not _list(resource.get("mapped_question_ids")):
            errors.append(f"resource {resource_id} requires mapped_question_ids")
    for index, source in enumerate(_list(data.get("sources"))):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        if source.get("source_class") not in SOURCE_CLASSES:
            errors.append(f"sources[{index}] has invalid source_class")
        if not str(source.get("url") or "").startswith("https://"):
            errors.append(f"sources[{index}] must use an HTTPS URL")
        if not isinstance(source.get("freshness"), dict):
            errors.append(f"sources[{index}] requires freshness metadata")
    actions = _actions(data)
    for action_id, action in actions:
        priority = str(action.get("priority") or "")
        if priority not in PRIORITIES:
            errors.append(f"action {action_id} has invalid priority")
        if priority == "A" and not _list(action.get("linked_refs")):
            errors.append(f"Priority A action {action_id} requires linked_refs")
        if not str(action.get("completion_condition") or "").strip():
            errors.append(f"action {action_id} missing completion_condition")
        for field in (("artifact", "exit_gate") if full_runbook else ()):
            if not str(action.get(field) or "").strip():
                errors.append(f"action {action_id} missing {field}")
    for index, question in enumerate(_list(data.get("question_bank"))):
        if not isinstance(question, dict):
            errors.append(f"question_bank[{index}] must be an object")
            continue
        fields = ["question_id", "prompt"]
        if full_runbook:
            fields.extend(["selection_reason", "priority", "confidence", "completion_standard"])
        for field in fields:
            if not str(question.get(field) or "").strip():
                errors.append(f"question_bank[{index}] missing {field}")
        if full_runbook and (not _list(question.get("mapped_rounds")) or not _list(question.get("mapped_requirements"))):
            errors.append(f"question_bank[{index}] requires round and requirement mappings")
    roadmap = _object(data.get("roadmap"))
    capacity_minutes = float(roadmap.get("weekly_capacity_hours") or 0) * 60 * int(roadmap.get("weeks") or 0)
    planned_minutes = sum(float(action.get("estimated_minutes") or 0) for _, action in actions)
    if planned_minutes > capacity_minutes:
        errors.append("roadmap planned minutes exceed declared capacity")
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if SECRET_RE.search(serialized):
        errors.append("artifact contains a secret-like value")
    if PRIVATE_RE.search(serialized):
        errors.append("artifact contains a local path or private key marker")
    quality = _object(data.get("quality"))
    if quality.get("source_safe") is not True:
        errors.append("quality.source_safe must be true")
    if strict and warnings:
        errors.extend("strict: " + item for item in warnings)
    receipt = _receipt(errors, warnings)
    receipt.update({"resource_count": len(resources), "action_count": len(actions), "planned_minutes": planned_minutes, "capacity_minutes": capacity_minutes})
    return receipt


def _resources(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    result = []
    for track in _list(data.get("learning_tracks")):
        if not isinstance(track, dict):
            continue
        for index, item in enumerate(_list(track.get("resources"))):
            if isinstance(item, dict):
                result.append((str(item.get("resource_id") or f"resource-{index}"), item))
    return result


def _actions(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    result = []
    for phase in _list(_object(data.get("roadmap")).get("phases")):
        if not isinstance(phase, dict):
            continue
        for index, item in enumerate(_list(phase.get("actions"))):
            if isinstance(item, dict):
                result.append((str(item.get("action_id") or f"action-{index}"), item))
    return result


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _receipt(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {"validator_version": "career_runbook_validator.v1", "valid": not errors, "source_safe": not any("secret" in item or "private" in item or "local path" in item for item in errors), "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 2
    receipt = validate(data, strict=args.strict)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
