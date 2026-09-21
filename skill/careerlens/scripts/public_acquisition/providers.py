"""Optional Laya and Jev adapters with one normalized, strict result contract.

Neither adapter writes request content to disk.  The evaluator only accepts
synthetic fixtures, but this boundary is intentionally conservative so a future
personal-mode integration cannot accidentally reuse the P1 reporting path.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import math
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import ProviderAbstention, ProviderResponseError, ProviderUnavailable
from .schema import EvalCase, Question


JEV_SYSTEM_ONE_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class NormalizedAnswer:
    """A provider answer after validating its type-specific invariants."""

    type: str
    choice: str | None = None
    noul: float | None = None
    boolean: bool | None = None
    score: float | None = None
    level: int | None = None
    confidence: float | None = None
    probabilities: Mapping[str, float] | None = None

    def to_report(self) -> dict[str, Any]:
        if self.type == "choice":
            return {
                "type": "choice",
                "choice": self.choice,
                "confidence": self.confidence,
                "probabilities": dict(self.probabilities or {}),
            }
        if self.type == "noul":
            payload: dict[str, Any] = {
                "type": "noul",
                "probability_true": self.noul,
                "boolean": self.boolean if self.noul is None else self.noul >= 0.5,
                "confidence": self.confidence,
            }
            return payload
        return {
            "type": "score",
            "score": self.score,
            "level": self.level,
            "confidence": self.confidence,
            "probabilities": dict(self.probabilities or {}),
        }


@dataclass(frozen=True)
class ProviderOutput:
    """Normalized successful output.  It deliberately has no copy of ``state``."""

    provider: str
    model: str
    answers: Mapping[str, NormalizedAnswer]
    usage: Mapping[str, int | None]
    metadata: Mapping[str, Any]


class TypedDecisionRequest(Protocol):
    """Minimal typed-decision request shape shared by eval and live runtime code.

    This intentionally does not mention synthetic fixture fields such as
    ``expected`` or ``synthetic``.  A live caller can provide the same typed
    question contract without masquerading real input as an ``EvalCase``.
    """

    state: Any
    questions: Mapping[str, Any]
    language: str

    def questions_wire(self) -> Mapping[str, Any]:
        """Return the provider wire representation of the typed questions."""


class DecisionProvider(Protocol):
    """A provider capable of answering every typed decision request."""

    name: str

    def predict(self, case: TypedDecisionRequest) -> ProviderOutput:
        """Return one normalized result or raise a safe provider error."""


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderResponseError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ProviderResponseError(f"{field} must be a finite number")
    return number


def _probability(value: Any, field: str) -> float:
    number = _finite_number(value, field)
    if number < 0.0 or number > 1.0:
        raise ProviderResponseError(f"{field} must be between 0 and 1")
    return number


def _probabilities(raw: Any, expected_keys: set[str], field: str) -> dict[str, float]:
    if not isinstance(raw, dict):
        raise ProviderResponseError(f"{field} must be an object")
    if set(raw) != expected_keys:
        raise ProviderResponseError(
            f"{field} keys must match the question criteria exactly; "
            f"expected {sorted(expected_keys)}, got {sorted(raw)}"
        )
    probabilities = {key: _probability(value, f"{field}.{key}") for key, value in raw.items()}
    total = sum(probabilities.values())
    if abs(total - 1.0) > 0.02:
        raise ProviderResponseError(f"{field} must sum to approximately 1; got {total:.6f}")
    return probabilities


def _argmax_level(probabilities: Mapping[str, float]) -> int:
    # Deterministic low-index tie handling makes the eval reproducible.
    return min(
        (int(key) for key in probabilities),
        key=lambda index: (-probabilities[str(index)], index),
    )


def _validate_answer(question: Question, raw: Any, qid: str) -> NormalizedAnswer:
    if not isinstance(raw, dict):
        raise ProviderResponseError(f"answers.{qid} must be an object")
    if raw.get("type") != question.type:
        raise ProviderResponseError(
            f"answers.{qid}.type must equal question type {question.type!r}"
        )
    if question.type == "choice":
        choice = raw.get("choice")
        if not isinstance(choice, str) or choice not in question.criteria:
            raise ProviderResponseError(f"answers.{qid}.choice must be one of the choice criteria")
        probabilities = _probabilities(
            raw.get("probabilities"), set(question.criteria), f"answers.{qid}.probabilities"
        )
        confidence = _probability(raw.get("confidence"), f"answers.{qid}.confidence")
        if probabilities[choice] + 1e-12 < max(probabilities.values()):
            raise ProviderResponseError(f"answers.{qid}.choice must be an argmax of probabilities")
        return NormalizedAnswer(
            type="choice",
            choice=choice,
            confidence=confidence,
            probabilities=probabilities,
        )
    if question.type == "noul":
        noul = _probability(raw.get("noul"), f"answers.{qid}.noul")
        confidence_raw = raw.get("confidence")
        confidence = (
            _probability(confidence_raw, f"answers.{qid}.confidence")
            if confidence_raw is not None
            else max(noul, 1.0 - noul)
        )
        return NormalizedAnswer(type="noul", noul=noul, confidence=confidence)
    expected_keys = {str(index) for index in range(len(question.criteria))}
    score = _finite_number(raw.get("score"), f"answers.{qid}.score")
    if score < 0.0 or score > len(question.criteria) - 1:
        raise ProviderResponseError(f"answers.{qid}.score is outside the rubric range")
    probabilities = _probabilities(raw.get("probabilities"), expected_keys, f"answers.{qid}.probabilities")
    confidence = _probability(raw.get("confidence"), f"answers.{qid}.confidence")
    legend = raw.get("legend")
    if not isinstance(legend, dict) or set(legend) != expected_keys:
        raise ProviderResponseError(f"answers.{qid}.legend keys must match score levels exactly")
    weighted_score = sum(int(level) * probability for level, probability in probabilities.items())
    if abs(score - weighted_score) > 0.03:
        raise ProviderResponseError(
            f"answers.{qid}.score must match its probability-weighted rubric value"
        )
    return NormalizedAnswer(
        type="score",
        score=score,
        level=_argmax_level(probabilities),
        confidence=confidence,
        probabilities=probabilities,
    )


def normalize_provider_payload(
    provider: str,
    case: TypedDecisionRequest,
    raw: Any,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> ProviderOutput:
    """Validate a raw provider response before its predictions can be scored."""

    if not isinstance(raw, dict):
        raise ProviderResponseError("provider response must be a JSON object")
    model = raw.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ProviderResponseError("provider response requires a non-empty model string")
    raw_answers = raw.get("answers")
    if not isinstance(raw_answers, dict):
        raise ProviderResponseError("provider response requires an answers object")
    if set(raw_answers) != set(case.questions):
        raise ProviderResponseError("provider answer ids must match case question ids exactly")
    answers = {
        qid: _validate_answer(case.questions[qid], raw_answers[qid], qid)
        for qid in case.questions
    }
    raw_usage = raw.get("usage", {})
    if not isinstance(raw_usage, dict):
        raise ProviderResponseError("provider response usage must be an object when supplied")
    usage: dict[str, int | None] = {}
    for key in ("input_tokens", "output_tokens"):
        value = raw_usage.get(key)
        if value is None:
            usage[key] = None
        elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProviderResponseError(f"provider usage.{key} must be a non-negative integer or null")
        else:
            usage[key] = value
    return ProviderOutput(
        provider=provider,
        model=model,
        answers=answers,
        usage=usage,
        metadata=dict(metadata or {}),
    )


class JevHttpProvider:
    """Direct stdlib HTTP adapter for TypeSafe's documented System One endpoint.

    Eval callers use ``TYPESAFE_API_KEY``.  A local runtime may pass an
    ephemeral in-memory credential resolved from the user's keychain; neither
    path accepts a CLI/config-file credential and neither logs request bodies.
    """

    name = "jev"

    def __init__(
        self,
        *,
        model: str = "jev-latest",
        timeout_seconds: float = 30.0,
        opener: Callable[..., Any] | None = None,
        api_key: str | None = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ProviderUnavailable("Jev model must be a non-empty string")
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ProviderUnavailable("Jev timeout must be positive")
        if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()):
            raise ProviderUnavailable("Jev credential must be a non-empty string")
        self.model = model
        self.timeout_seconds = float(timeout_seconds)
        self._opener = opener or urlopen
        self._api_key = api_key

    @staticmethod
    def is_configured() -> bool:
        return bool(os.environ.get("TYPESAFE_API_KEY"))

    def predict(self, case: TypedDecisionRequest) -> ProviderOutput:
        api_key = self._api_key or os.environ.get("TYPESAFE_API_KEY")
        if not api_key:
            raise ProviderUnavailable("Jev requires TYPESAFE_API_KEY in the environment")
        body = json.dumps(
            {
                "state": case.state,
                "model": self.model,
                "questions": case.questions_wire(),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            JEV_SYSTEM_ONE_ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read()
        except HTTPError as error:
            raise ProviderUnavailable(f"Jev HTTP request failed with status {error.code}") from error
        except (URLError, TimeoutError, OSError) as error:
            # Do not stringify the error: a custom transport might include request data in it.
            raise ProviderUnavailable("Jev HTTP request could not be completed") from error
        try:
            decoded = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderResponseError("Jev returned a non-JSON response") from error
        return normalize_provider_payload(
            self.name,
            case,
            decoded,
            metadata={
                "requested_model": self.model,
                "endpoint": JEV_SYSTEM_ONE_ENDPOINT,
                "transport": "https",
            },
        )


def _closed_object(properties: Mapping[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": required,
        "additionalProperties": False,
    }


def openai_decision_schema(case: EvalCase) -> dict[str, Any]:
    """Build a per-case strict JSON schema without asking an LLM for probabilities.

    A generative LLM can supply a typed prediction for the smoke baseline, but
    inventing confidence distributions would make the calibration report less
    honest.  Therefore this schema requests only labels/booleans/ordinal levels.
    """

    answer_properties: dict[str, Any] = {}
    for qid, question in case.questions.items():
        if question.type == "choice":
            answer_properties[qid] = _closed_object(
                {
                    "type": {"type": "string", "enum": ["choice"]},
                    "choice": {"type": "string", "enum": list(question.criteria)},
                },
                ["type", "choice"],
            )
        elif question.type == "noul":
            answer_properties[qid] = _closed_object(
                {
                    "type": {"type": "string", "enum": ["noul"]},
                    "boolean": {"type": "boolean"},
                },
                ["type", "boolean"],
            )
        else:
            answer_properties[qid] = _closed_object(
                {
                    "type": {"type": "string", "enum": ["score"]},
                    "level": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": len(question.criteria) - 1,
                    },
                },
                ["type", "level"],
            )
    return _closed_object(
        {"answers": _closed_object(answer_properties, list(case.questions))},
        ["answers"],
    )


def normalize_openai_decision_payload(
    case: EvalCase,
    raw: Any,
    *,
    model: str,
    usage: Mapping[str, Any] | None,
    metadata: Mapping[str, Any],
) -> ProviderOutput:
    """Strictly normalize the deliberate label-only OpenAI baseline result."""

    if not isinstance(raw, dict) or set(raw) != {"answers"}:
        raise ProviderResponseError("OpenAI structured output must be exactly an answers object")
    raw_answers = raw["answers"]
    if not isinstance(raw_answers, dict) or set(raw_answers) != set(case.questions):
        raise ProviderResponseError("OpenAI answer ids must match case question ids exactly")
    answers: dict[str, NormalizedAnswer] = {}
    for qid, question in case.questions.items():
        answer = raw_answers[qid]
        if not isinstance(answer, dict) or answer.get("type") != question.type:
            raise ProviderResponseError(f"OpenAI answers.{qid} has the wrong typed shape")
        if question.type == "choice":
            if set(answer) != {"type", "choice"}:
                raise ProviderResponseError(f"OpenAI answers.{qid} choice has unsupported keys")
            choice = answer["choice"]
            if not isinstance(choice, str) or choice not in question.criteria:
                raise ProviderResponseError(f"OpenAI answers.{qid}.choice is not a criterion label")
            answers[qid] = NormalizedAnswer(type="choice", choice=choice)
        elif question.type == "noul":
            if set(answer) != {"type", "boolean"} or type(answer["boolean"]) is not bool:
                raise ProviderResponseError(f"OpenAI answers.{qid}.boolean must be a JSON boolean")
            answers[qid] = NormalizedAnswer(type="noul", boolean=answer["boolean"])
        else:
            level = answer.get("level")
            if set(answer) != {"type", "level"} or isinstance(level, bool) or not isinstance(level, int):
                raise ProviderResponseError(f"OpenAI answers.{qid}.level must be an integer")
            if level < 0 or level >= len(question.criteria):
                raise ProviderResponseError(f"OpenAI answers.{qid}.level is outside the score rubric")
            answers[qid] = NormalizedAnswer(type="score", level=level)
    normalized_usage: dict[str, int | None] = {}
    raw_usage = usage or {}
    if not isinstance(raw_usage, Mapping):
        raise ProviderResponseError("OpenAI usage must be an object when supplied")
    for key in ("input_tokens", "output_tokens"):
        value = raw_usage.get(key)
        if value is None:
            normalized_usage[key] = None
        elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProviderResponseError(f"OpenAI usage.{key} must be a non-negative integer or null")
        else:
            normalized_usage[key] = value
    return ProviderOutput(
        provider="openai",
        model=model,
        answers=answers,
        usage=normalized_usage,
        metadata=dict(metadata),
    )


def _openai_output_text(response: Mapping[str, Any]) -> str:
    status = response.get("status")
    if status == "incomplete":
        raise ProviderAbstention("openai_response_incomplete")
    if status in {"failed", "cancelled"}:
        raise ProviderUnavailable("OpenAI response did not complete")
    if status != "completed":
        raise ProviderUnavailable("OpenAI response returned an unexpected status")
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return output_text
    output = response.get("output")
    if not isinstance(output, list):
        raise ProviderResponseError("OpenAI response has no output text")
    texts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "refusal":
                raise ProviderAbstention("openai_model_refusal")
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
    if len(texts) != 1:
        raise ProviderResponseError("OpenAI response did not contain exactly one structured output text")
    return texts[0]


class OpenAIResponsesProvider:
    """OpenAI-compatible label-only LLM baseline over the Responses REST API.

    It sets ``store: false`` and ``truncation: disabled`` on every request.  It
    receives only an explicitly synthetic fixture and never estimates price or
    writes request text, response text, or an API key to an artifact.
    """

    name = "openai"

    def __init__(
        self,
        *,
        model: str,
        timeout_seconds: float = 30.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ProviderUnavailable("OpenAI model must be supplied with --model")
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ProviderUnavailable("OpenAI timeout must be positive")
        self.model = model
        self.timeout_seconds = float(timeout_seconds)
        self._opener = opener or urlopen

    @staticmethod
    def is_configured() -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def predict(self, case: EvalCase) -> ProviderOutput:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ProviderUnavailable("OpenAI requires OPENAI_API_KEY in the environment")
        input_document = json.dumps(
            {"state": case.state, "questions": case.questions_wire()},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        request_body = {
            "model": self.model,
            "instructions": (
                "Make one bounded typed decision for every supplied question. "
                "Return only the schema result. Choice must select a listed label; "
                "noul must be a boolean; score must be an integer rubric level. "
                "Do not claim confidence, evidence, or a reference answer."
            ),
            "input": input_document,
            "store": False,
            "truncation": "disabled",
            "max_output_tokens": 512,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "career_os_typed_answers",
                    "strict": True,
                    "schema": openai_decision_schema(case),
                }
            },
        }
        request = Request(
            OPENAI_RESPONSES_ENDPOINT,
            data=json.dumps(request_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read()
        except HTTPError as error:
            raise ProviderUnavailable(f"OpenAI HTTP request failed with status {error.code}") from error
        except (URLError, TimeoutError, OSError) as error:
            raise ProviderUnavailable("OpenAI HTTP request could not be completed") from error
        try:
            response_document = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderResponseError("OpenAI returned a non-JSON response") from error
        if not isinstance(response_document, dict):
            raise ProviderResponseError("OpenAI response must be a JSON object")
        model = response_document.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ProviderResponseError("OpenAI response requires a non-empty model string")
        output_text = _openai_output_text(response_document)
        try:
            parsed_output = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise ProviderResponseError("OpenAI structured output was not JSON") from error
        return normalize_openai_decision_payload(
            case,
            parsed_output,
            model=model,
            usage=response_document.get("usage"),
            metadata={
                "requested_model": self.model,
                "endpoint": OPENAI_RESPONSES_ENDPOINT,
                "structured_output": "json_schema_strict",
                "response_store": False,
                "truncation": "disabled",
                "calibration": "not_reported_by_label_only_baseline",
            },
        )


def _as_token_ids(tokenizer: Any, text: str) -> list[int]:
    try:
        encoded = tokenizer(text, add_special_tokens=False)
        ids = encoded["input_ids"]
    except Exception as error:  # pragma: no cover - depends on optional runtime behavior
        raise ProviderUnavailable("Laya tokenizer could not tokenize the synthetic input") from error
    if not isinstance(ids, list) or any(isinstance(item, bool) or not isinstance(item, int) for item in ids):
        raise ProviderUnavailable("Laya tokenizer returned an unsupported input_ids shape")
    return ids


def _laya_internal_question(question: Question) -> dict[str, Any]:
    instructions = question.instructions
    if not isinstance(instructions, str):
        instructions = json.dumps(instructions, ensure_ascii=False)
    return {"t": question.type, "ins": instructions, "crit": question.criteria}


def _serialize_laya_state(state: Any) -> str:
    return state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)


def laya_truncation_reason(
    agent: Any,
    case: TypedDecisionRequest,
    render_options: Callable[[dict[str, Any]], list[str]],
) -> str | None:
    """Detect every truncation Laya's runtime would otherwise perform silently.

    This intentionally reads the *loaded agent's* tokenizer and ``cfg``.  It
    does not guess from Laya defaults, so custom checkpoints and runtime config
    are checked against their real context budget before inference.
    """

    cfg = getattr(agent, "cfg", None)
    tokenizer = getattr(agent, "tok", None)
    if not isinstance(cfg, dict) or tokenizer is None:
        raise ProviderUnavailable("installed Laya runtime does not expose cfg and tokenizer for truncation checks")
    max_len = cfg.get("max_len")
    head_max_len = cfg.get("head_max_len")
    if isinstance(max_len, bool) or not isinstance(max_len, int) or max_len <= 0:
        raise ProviderUnavailable("Laya runtime has an invalid max_len")
    if isinstance(head_max_len, bool) or not isinstance(head_max_len, int) or head_max_len <= 0:
        raise ProviderUnavailable("Laya runtime has an invalid head_max_len")
    mask_token = getattr(tokenizer, "mask_token", None)
    mask_token_id = getattr(tokenizer, "mask_token_id", None)
    if not isinstance(mask_token, str) or not isinstance(mask_token_id, int):
        raise ProviderUnavailable("Laya tokenizer does not expose a usable mask token")
    state_text = _serialize_laya_state(case.state).replace(mask_token, " ")
    state_tokens = len(_as_token_ids(tokenizer, state_text))
    for qid, question in case.questions.items():
        qdef = _laya_internal_question(question)
        try:
            options = render_options(qdef)
        except Exception as error:  # pragma: no cover - defensive against changed optional API
            raise ProviderUnavailable("Laya could not render question options") from error
        option_token_lists: list[list[int]] = []
        for option in options:
            option_content = _as_token_ids(tokenizer, " " + option.replace(mask_token, " "))
            # Laya's build_sequence keeps only [:48] of the option text, then
            # prepends one mask marker.  Check that exact boundary, rather than
            # an approximate total sequence length.
            if len(option_content) > 48:
                return (
                    f"laya_input_truncated:q={qid}; option_content_tokens={len(option_content)} "
                    "exceed runtime option limit=48"
                )
            tokens = [mask_token_id] + option_content
            option_token_lists.append(tokens)
        option_total = sum(len(tokens) for tokens in option_token_lists)
        option_budget = head_max_len - option_total
        if option_budget < 16:
            return (
                f"laya_input_truncated:q={qid}; option_tokens={option_total} exceed "
                f"runtime head_max_len={head_max_len}"
            )
        instruction_tokens = len(
            _as_token_ids(
                tokenizer,
                f"{question.type} question: {str(qdef['ins']).replace(mask_token, ' ')}",
            )
        )
        instruction_budget = max(8, option_budget)
        if instruction_tokens > instruction_budget:
            return (
                f"laya_input_truncated:q={qid}; instruction_tokens={instruction_tokens} exceed "
                f"runtime instruction_budget={instruction_budget}"
            )
        # [CLS] header [SEP] option markers/options [SEP] state [SEP]
        fixed_tokens = 1 + instruction_tokens + 1 + option_total + 1
        if fixed_tokens + 1 > max_len:
            return (
                f"laya_input_truncated:q={qid}; question_tokens={fixed_tokens + 1} exceed "
                f"runtime max_len={max_len}"
            )
        state_budget = max_len - fixed_tokens - 1
        if state_tokens > state_budget:
            return (
                f"laya_input_truncated:q={qid}; state_tokens={state_tokens} exceed "
                f"runtime state_budget={state_budget} (max_len={max_len}, head_max_len={head_max_len})"
            )
    return None


class LayaProvider:
    """Optional local Laya adapter.  Import and model loading are lazy."""

    name = "laya"

    def __init__(
        self,
        *,
        model: str | None = None,
        device: str | None = None,
        model_dir: str | Path | None = None,
        max_loaded: int = 1,
    ) -> None:
        # Local checkpoint routing is deliberate.  Set these only when a
        # caller did not already choose a stricter process policy; the Router
        # below is also given explicit local paths and never a Hub identifier.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        try:
            self._laya = importlib.import_module("laya")
            self._common = importlib.import_module("laya.common")
        except ModuleNotFoundError as error:
            raise ProviderUnavailable(
                "Laya is optional and not installed; install the approved Laya dependency before using --provider laya"
            ) from error
        router_cls = getattr(self._laya, "Router", None)
        if router_cls is None:
            raise ProviderUnavailable("installed Laya package does not provide Router")
        if model_dir is None:
            raise ProviderUnavailable(
                "Laya requires an explicit --laya-model-dir with a pinned local checkpoint; "
                "implicit Hub downloads are disabled"
            )
        root = Path(model_dir).expanduser().resolve()
        required = (root, root / "multilingual", root / "typed-decisions")
        if not root.is_dir() or any(
            not (checkpoint / "rl_agent_config.json").is_file()
            or not (checkpoint / "model.safetensors").is_file()
            for checkpoint in required
        ):
            raise ProviderUnavailable(
                "--laya-model-dir must contain pinned root, multilingual, and typed-decisions checkpoints"
            )
        self.model = model
        self.model_dir = root
        if isinstance(max_loaded, bool) or not isinstance(max_loaded, int) or max_loaded < 1:
            raise ProviderUnavailable("Laya max_loaded must be a positive integer")
        # Laya's Router keeps mutable loaded-agent state.  A workspace server
        # retains one provider for warm reuse, so serialize route/load/infer
        # rather than allowing two UI requests to mutate it concurrently.
        self._lock = threading.RLock()
        self._router = router_cls(
            models={
                "english": str(root),
                "multilingual": (str(root), "multilingual"),
                "typed-decisions": (str(root), "typed-decisions"),
            },
            device=device,
            max_loaded=max_loaded,
        )

    def warm(self) -> Mapping[str, Any]:
        """Load the explicit checkpoint without running an inference.

        Call this once at local-server startup if warm latency matters, then
        retain this provider instance and pass it to workspace analysis.  It
        intentionally does not route on user data or make a network request.
        ``typed-decisions`` is the only safe default for this direct warm path;
        callers using automatic routing can simply let the first prediction
        load its routed local checkpoint.
        """

        if not isinstance(self.model, str) or not self.model:
            raise ProviderUnavailable("Laya warm requires an explicit local model variant")
        with self._lock:
            try:
                started = time.perf_counter()
                cold_load = self.model not in self._router.loaded
                agent = self._router.load(self.model)
                load_ms = round((time.perf_counter() - started) * 1000.0, 3)
            except Exception as error:  # pragma: no cover - live optional runtime
                raise ProviderUnavailable("Laya could not warm the selected local checkpoint") from error
            return {
                "provider": self.name,
                "model": self.model,
                "cold_load": cold_load,
                "model_load_ms": load_ms,
                "device": str(getattr(agent, "device", "unknown")),
            }

    def predict(self, case: TypedDecisionRequest) -> ProviderOutput:
        language = getattr(case, "language", None)
        if not isinstance(language, str) or not language:
            raise ProviderUnavailable("Laya requires a request language")
        with self._lock:
            try:
                load_started = time.perf_counter()
                route = self._router.route(
                    case.state,
                    case.questions_wire(),
                    model=self.model,
                    lang=None if language == "auto" else language,
                )
                cold_load = route["model"] not in self._router.loaded
                agent = self._router.load(route["model"])
                load_ms = round((time.perf_counter() - load_started) * 1000.0, 3)
            except Exception as error:  # pragma: no cover - live optional runtime
                raise ProviderUnavailable("Laya could not load the selected local checkpoint") from error
            reason = laya_truncation_reason(agent, case, self._common.render_options)
            if reason is not None:
                raise ProviderAbstention(reason)
            try:
                inference_started = time.perf_counter()
                raw = agent.system_one(case.state, case.questions_wire())
                inference_ms = round((time.perf_counter() - inference_started) * 1000.0, 3)
            except Exception as error:  # pragma: no cover - live optional runtime
                raise ProviderUnavailable("Laya inference could not complete") from error
            runtime_metadata = {
                "requested_model": self.model,
                "routed_model": route.get("model"),
                "routed_repo": route.get("repo"),
                "routing_reason": route.get("reason"),
                "laya_version": getattr(self._laya, "__version__", None),
                "max_len": getattr(agent, "cfg", {}).get("max_len"),
                "head_max_len": getattr(agent, "cfg", {}).get("head_max_len"),
                "device": str(getattr(agent, "device", "unknown")),
                "checkpoint_root": str(self.model_dir),
                "cold_load": cold_load,
                "model_load_ms": load_ms,
                "inference_ms": inference_ms,
            }
            return normalize_provider_payload(self.name, case, raw, metadata=runtime_metadata)


def create_provider(
    name: str,
    *,
    model: str | None = None,
    timeout_seconds: float = 30.0,
    laya_device: str | None = None,
    laya_model_dir: str | Path | None = None,
) -> DecisionProvider:
    """Build one supported provider without hidden fallbacks or cross-provider egress."""

    if name == "jev":
        if not JevHttpProvider.is_configured():
            raise ProviderUnavailable("Jev requires TYPESAFE_API_KEY in the environment")
        return JevHttpProvider(model=model or "jev-latest", timeout_seconds=timeout_seconds)
    if name == "laya":
        return LayaProvider(model=model, device=laya_device, model_dir=laya_model_dir)
    if name == "openai":
        if not OpenAIResponsesProvider.is_configured():
            raise ProviderUnavailable("OpenAI requires OPENAI_API_KEY in the environment")
        if not model:
            raise ProviderUnavailable("OpenAI requires an explicit --model; price is never inferred")
        return OpenAIResponsesProvider(model=model, timeout_seconds=timeout_seconds)
    raise ProviderUnavailable("provider must be one of 'laya', 'jev', or 'openai'")
