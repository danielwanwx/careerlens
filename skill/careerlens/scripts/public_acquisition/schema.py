"""Strict, dependency-free schema handling for synthetic evaluation fixtures.

The evaluator never accepts a fixture unless it explicitly says ``synthetic: true``.
That keeps the P1 report format safe to use in a repository or a demo without
turning a model run over personal material into a durable artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Mapping

from .errors import SchemaValidationError


QUESTION_TYPES = frozenset({"choice", "noul", "score"})
FIXTURE_METADATA_FIELDS = frozenset(
    {"rationale", "split", "template_family", "label_status", "provenance", "pending_adjudication"}
)


def _where(line_number: int | None) -> str:
    return f"line {line_number}: " if line_number is not None else ""


def _fail(message: str, line_number: int | None = None) -> None:
    raise SchemaValidationError(f"{_where(line_number)}{message}")


def _is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _require_object(value: Any, field: str, line_number: int | None) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{field} must be an object", line_number)
    return value


def _require_nonempty_string(value: Any, field: str, line_number: int | None) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{field} must be a non-empty string", line_number)
    return value


def _require_json_instruction(value: Any, field: str, line_number: int | None) -> Any:
    if not isinstance(value, (str, dict, list)) or not _is_json_value(value):
        _fail(f"{field} must be a string, object, or array JSON value", line_number)
    if isinstance(value, str) and not value.strip():
        _fail(f"{field} must not be an empty string", line_number)
    return value


@dataclass(frozen=True)
class Question:
    """One typed, atomic System One question."""

    qid: str
    type: str
    instructions: Any
    criteria: Any | None

    def to_wire(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type, "instructions": self.instructions}
        if self.criteria is not None:
            payload["criteria"] = self.criteria
        return payload


@dataclass(frozen=True)
class ExpectedAnswer:
    """A fixture reference label, intentionally separate from a model prediction."""

    type: str
    value: str | bool | int

    def to_report(self) -> dict[str, Any]:
        if self.type == "choice":
            return {"label": self.value}
        if self.type == "noul":
            return {"boolean": self.value}
        return {"level": self.value}


@dataclass(frozen=True)
class EvalCase:
    """A validated, synthetic-only evaluation fixture row."""

    case_id: str
    task_kind: str
    language: str
    state: Any
    questions: Mapping[str, Question]
    expected: Mapping[str, ExpectedAnswer]
    metadata: Mapping[str, Any]

    def questions_wire(self) -> dict[str, dict[str, Any]]:
        return {qid: question.to_wire() for qid, question in self.questions.items()}


def _parse_question(
    qid: str, raw: Any, line_number: int | None
) -> Question:
    question = _require_object(raw, f"questions.{qid}", line_number)
    allowed = {"type", "instructions", "criteria"}
    unknown = set(question) - allowed
    if unknown:
        _fail(f"questions.{qid} has unsupported keys: {sorted(unknown)}", line_number)
    if set(question) - {"type", "instructions", "criteria"}:
        _fail(f"questions.{qid} has unsupported keys", line_number)
    if "type" not in question or "instructions" not in question:
        _fail(f"questions.{qid} requires type and instructions", line_number)
    qtype = question["type"]
    if qtype not in QUESTION_TYPES:
        _fail(f"questions.{qid}.type must be one of {sorted(QUESTION_TYPES)}", line_number)
    instructions = _require_json_instruction(question["instructions"], f"questions.{qid}.instructions", line_number)
    has_criteria = "criteria" in question
    criteria = question.get("criteria")
    if qtype == "choice":
        if not has_criteria or not isinstance(criteria, dict) or not criteria:
            _fail(f"questions.{qid}.criteria must be a non-empty object for choice", line_number)
        if len(criteria) > 255:
            _fail(f"questions.{qid}.criteria may contain at most 255 choice labels", line_number)
        if any(not isinstance(label, str) or not label.strip() for label in criteria):
            _fail(f"questions.{qid}.criteria labels must be non-empty strings", line_number)
        if not all(_is_json_value(value) for value in criteria.values()):
            _fail(f"questions.{qid}.criteria must contain JSON values", line_number)
    elif qtype == "score":
        if not has_criteria or not isinstance(criteria, list) or len(criteria) < 2:
            _fail(f"questions.{qid}.criteria must be an ordered list of at least two levels for score", line_number)
        if len(criteria) > 10:
            _fail(f"questions.{qid}.criteria may contain at most 10 score levels", line_number)
        if not all(_is_json_value(value) and value is not None for value in criteria):
            _fail(f"questions.{qid}.criteria must contain non-null JSON levels", line_number)
    else:
        if has_criteria:
            if not isinstance(criteria, dict) or set(criteria) - {"true", "false"}:
                _fail(f"questions.{qid}.criteria for noul may only define true/false", line_number)
            if not all(_is_json_value(value) for value in criteria.values()):
                _fail(f"questions.{qid}.criteria must contain JSON values", line_number)
    return Question(qid=qid, type=qtype, instructions=instructions, criteria=criteria)


def _parse_expected(
    qid: str, raw: Any, question: Question, line_number: int | None
) -> ExpectedAnswer:
    if question.type == "choice":
        # The frozen P1 fixture contract uses a scalar label.  Accepting the
        # explicit wrapper as well keeps early hand-authored fixtures usable.
        label = raw.get("label") if isinstance(raw, dict) and set(raw) == {"label"} else raw
        if not isinstance(label, str) or label not in question.criteria:
            _fail(f"expected.{qid}.label must be one of the choice criteria", line_number)
        return ExpectedAnswer(type="choice", value=label)
    if question.type == "noul":
        value = raw.get("boolean") if isinstance(raw, dict) and set(raw) == {"boolean"} else raw
        if type(value) is not bool:
            _fail(f"expected.{qid}.boolean must be a JSON boolean", line_number)
        return ExpectedAnswer(type="noul", value=value)
    level = raw.get("level") if isinstance(raw, dict) and set(raw) == {"level"} else raw
    if isinstance(level, bool):
        _fail(f"expected.{qid}.level must be an integer index or exact criteria label", line_number)
    if isinstance(level, int):
        if level < 0 or level >= len(question.criteria):
            _fail(f"expected.{qid}.level index is outside the score criteria", line_number)
        return ExpectedAnswer(type="score", value=level)
    if isinstance(level, str):
        matches = [index for index, criterion in enumerate(question.criteria) if criterion == level]
        if len(matches) != 1:
            _fail(
                f"expected.{qid}.level string must match exactly one score criteria entry",
                line_number,
            )
        return ExpectedAnswer(type="score", value=matches[0])
    _fail(f"expected.{qid}.level must be an integer index or exact criteria label", line_number)


def parse_case(raw: Any, *, line_number: int | None = None) -> EvalCase:
    """Validate one JSONL case against the frozen P1 interface."""

    row = _require_object(raw, "case", line_number)
    required = {"case_id", "task_kind", "language", "state", "questions", "expected", "synthetic"}
    allowed = required | FIXTURE_METADATA_FIELDS
    unknown = set(row) - allowed
    missing = required - set(row)
    if unknown:
        _fail(f"case has unsupported keys: {sorted(unknown)}", line_number)
    if missing:
        _fail(f"case is missing required keys: {sorted(missing)}", line_number)
    if row["synthetic"] is not True:
        _fail("synthetic must be literal true; non-synthetic data is rejected", line_number)
    case_id = _require_nonempty_string(row["case_id"], "case_id", line_number)
    task_kind = _require_nonempty_string(row["task_kind"], "task_kind", line_number)
    language = _require_nonempty_string(row["language"], "language", line_number)
    if not isinstance(row["state"], (str, dict, list)) or not _is_json_value(row["state"]):
        _fail("state must be a string, object, or array JSON value", line_number)
    questions_raw = _require_object(row["questions"], "questions", line_number)
    if not questions_raw:
        _fail("questions must not be empty", line_number)
    questions: dict[str, Question] = {}
    for qid, question_raw in questions_raw.items():
        if not isinstance(qid, str) or not qid.strip():
            _fail("question ids must be non-empty strings", line_number)
        questions[qid] = _parse_question(qid, question_raw, line_number)
    expected_raw = _require_object(row["expected"], "expected", line_number)
    if set(expected_raw) != set(questions):
        _fail("expected question ids must match questions exactly", line_number)
    expected = {
        qid: _parse_expected(qid, expected_raw[qid], questions[qid], line_number)
        for qid in questions
    }
    metadata: dict[str, Any] = {}
    for field in FIXTURE_METADATA_FIELDS:
        if field not in row:
            continue
        value = row[field]
        if not _is_json_value(value):
            _fail(f"{field} must be JSON serializable", line_number)
        if field in {"rationale", "split", "template_family", "label_status"}:
            _require_nonempty_string(value, field, line_number)
        metadata[field] = value
    return EvalCase(
        case_id=case_id,
        task_kind=task_kind,
        language=language,
        state=row["state"],
        questions=questions,
        expected=expected,
        metadata=metadata,
    )


def load_cases(path: str | Path) -> list[EvalCase]:
    """Load a non-empty JSONL file and reject duplicate case ids."""

    input_path = Path(path)
    cases: list[EvalCase] = []
    seen: set[str] = set()
    try:
        with input_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError as error:
                    _fail(f"invalid JSON: {error.msg}", line_number)
                case = parse_case(raw, line_number=line_number)
                if case.case_id in seen:
                    _fail(f"duplicate case_id {case.case_id!r}", line_number)
                seen.add(case.case_id)
                cases.append(case)
    except OSError as error:
        raise SchemaValidationError(f"cannot read cases file {input_path}: {error.strerror or error}") from error
    if not cases:
        raise SchemaValidationError("cases file contains no non-empty JSONL rows")
    return cases


def score_level_index(question: Question, expected: ExpectedAnswer) -> int:
    """Return the normalized ordinal fixture target for a validated score question."""

    if question.type != "score" or expected.type != "score" or not isinstance(expected.value, int):
        raise ValueError("score_level_index requires a validated score question and expected answer")
    return expected.value
