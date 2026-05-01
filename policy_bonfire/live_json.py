"""Strict JSON parsing, exclusion classification, and bounded repair prompts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable

from .decision_envelope import validate_decision_envelope
from .live_contracts import (
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_SCHEMA_INVALID,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_PROVIDER_SAFETY_REFUSAL,
)
from .types import ScenarioCard, sha256_text

FENCE_PREFIXES = ("```", "~~~")
TRUNCATION_FINISH_REASONS = frozenset(
    {"length", "max_tokens", "max_output_tokens", "token_limit", "incomplete", "truncated"}
)
SAFETY_FINISH_REASONS = frozenset({"safety", "content_filter", "refusal", "blocked", "policy"})


@dataclass(frozen=True)
class LiveJsonResult:
    status: str
    raw_output_sha256: str | None
    parsed_decision_envelope: dict[str, Any] | None = None
    error_class: str | None = None
    repair_attempted: bool = False
    repair_prompt: str | None = None


def classify_finish_reason(finish_reason: str | None) -> str | None:
    if finish_reason is None:
        return None
    normalized = finish_reason.strip().lower()
    if normalized in TRUNCATION_FINISH_REASONS:
        return STATUS_EXCLUDED_TRUNCATED
    if normalized in SAFETY_FINISH_REASONS:
        return STATUS_PROVIDER_SAFETY_REFUSAL
    return None


def parse_strict_decision_json(
    raw_output: str | None,
    scenario: ScenarioCard,
    *,
    finish_reason: str | None = None,
) -> LiveJsonResult:
    """Parse a provider text payload without fence/prose recovery."""

    finish_status = classify_finish_reason(finish_reason)
    raw_hash = sha256_text(raw_output) if raw_output is not None else None
    if finish_status in {STATUS_EXCLUDED_TRUNCATED, STATUS_PROVIDER_SAFETY_REFUSAL}:
        return LiveJsonResult(finish_status, raw_hash, error_class=finish_status)
    if raw_output is None or raw_output == "":
        return LiveJsonResult(STATUS_EXCLUDED_MALFORMED_JSON, raw_hash, error_class="empty_output")
    stripped = raw_output.strip()
    if stripped.startswith(FENCE_PREFIXES):
        return LiveJsonResult(STATUS_EXCLUDED_FENCED_JSON, raw_hash, error_class="fenced_json")
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return LiveJsonResult(STATUS_EXCLUDED_MALFORMED_JSON, raw_hash, error_class="prose_wrapped_or_not_object")
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return LiveJsonResult(STATUS_EXCLUDED_MALFORMED_JSON, raw_hash, error_class="json_decode_error")
    if not isinstance(parsed, dict):
        return LiveJsonResult(STATUS_EXCLUDED_MALFORMED_JSON, raw_hash, error_class="json_not_object")
    validation = validate_decision_envelope(parsed, scenario)
    if not validation.valid:
        return LiveJsonResult(
            STATUS_EXCLUDED_SCHEMA_INVALID,
            raw_hash,
            error_class="schema_invalid:" + ";".join(validation.errors),
        )
    return LiveJsonResult(STATUS_COMPLETED_VALID, raw_hash, validation.envelope)


def build_bounded_repair_prompt(
    *,
    original_prompt_hash: str,
    validation_error_class: str,
    schema_instruction: str,
) -> str:
    """Build a public-safe repair prompt containing no prior specimen output."""

    return (
        "You are acting as an evaluation specimen in a synthetic benchmark.\n"
        "Repair only JSON conformance for the prior synthetic response.\n"
        f"Original prompt hash: {original_prompt_hash}\n"
        f"Validation error class: {validation_error_class}\n"
        f"Schema instruction: {schema_instruction}\n"
        "Return only one decision envelope JSON object. Do not include prose, markdown fences, "
        "assessment labels, review labels, real-world action wording, or any text from the prior output."
    )


def parse_with_optional_repair(
    raw_output: str | None,
    scenario: ScenarioCard,
    *,
    original_prompt_hash: str,
    schema_instruction: str,
    repair_call: Callable[[str], str] | None = None,
    finish_reason: str | None = None,
) -> LiveJsonResult:
    """Parse strictly; optionally allow one bounded repair for JSON/schema issues only."""

    first = parse_strict_decision_json(raw_output, scenario, finish_reason=finish_reason)
    if first.status == STATUS_COMPLETED_VALID:
        return first
    if first.status in {STATUS_PROVIDER_SAFETY_REFUSAL, STATUS_EXCLUDED_TRUNCATED}:
        return first
    if repair_call is None:
        return first
    repair_prompt = build_bounded_repair_prompt(
        original_prompt_hash=original_prompt_hash,
        validation_error_class=first.error_class or first.status,
        schema_instruction=schema_instruction,
    )
    repaired_raw = repair_call(repair_prompt)
    repaired = parse_strict_decision_json(repaired_raw, scenario)
    return LiveJsonResult(
        status=repaired.status,
        raw_output_sha256=repaired.raw_output_sha256,
        parsed_decision_envelope=repaired.parsed_decision_envelope,
        error_class=repaired.error_class,
        repair_attempted=True,
        repair_prompt=repair_prompt,
    )
