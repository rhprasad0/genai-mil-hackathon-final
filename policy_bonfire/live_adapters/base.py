"""Live adapter protocol, test fakes, and provider-normalization helpers."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Protocol

from ..live_contracts import (
    LiveModelRequest,
    LiveModelResponse,
    PROVIDER_MODEL_FAMILIES,
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_PROVIDER_SAFETY_REFUSAL,
    STATUS_TIMEOUT,
    STATUS_TRANSIENT_ERROR,
)


class AdapterTimeoutError(TimeoutError):
    """Redacted adapter timeout signal for offline tests and adapters."""


class AdapterTransientError(RuntimeError):
    """Redacted retryable adapter failure signal for offline tests and adapters."""


class LiveProviderAdapter(Protocol):
    provider: str
    model_id_exact: str
    model_id_public_label: str

    def complete(self, request: LiveModelRequest) -> LiveModelResponse:
        ...


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def elapsed_ms(start_ms: int) -> int:
    return max(0, monotonic_ms() - start_ms)


def get_value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def status_from_finish_reason(finish_reason: str | None) -> str | None:
    if not finish_reason:
        return None
    normalized = finish_reason.strip().lower()
    if normalized in {"length", "max_tokens", "max_output_tokens", "token_limit", "incomplete", "truncated"}:
        return STATUS_EXCLUDED_TRUNCATED
    if normalized in {"safety", "content_filter", "refusal", "blocked", "policy"}:
        return STATUS_PROVIDER_SAFETY_REFUSAL
    return None


def parse_strict_json_object(text: str | None) -> tuple[str, dict[str, Any] | None, str | None]:
    if text is None or text == "":
        return STATUS_EXCLUDED_MALFORMED_JSON, None, text
    stripped = text.strip()
    if stripped.startswith("```") or stripped.startswith("~~~"):
        return STATUS_EXCLUDED_FENCED_JSON, None, text
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return STATUS_EXCLUDED_MALFORMED_JSON, None, text
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return STATUS_EXCLUDED_MALFORMED_JSON, None, text
    if not isinstance(parsed, dict):
        return STATUS_EXCLUDED_MALFORMED_JSON, None, text
    return STATUS_COMPLETED_VALID, parsed, text


def normalized_response(
    *,
    status: str,
    provider: str,
    model_id: str,
    model_label: str,
    model_family: str,
    latency_ms: int,
    usage_input_tokens: int | None,
    usage_output_tokens: int | None,
    finish_reason: str | None,
    raw_text: str | None,
    parsed: dict[str, Any] | None,
) -> LiveModelResponse:
    usage_estimated = usage_input_tokens is None or usage_output_tokens is None
    return LiveModelResponse(
        status=status,
        provider=provider,
        model_id_exact=model_id,
        model_id_public_label=model_label,
        model_family=model_family,
        latency_ms=latency_ms,
        usage_input_tokens=usage_input_tokens if usage_input_tokens is not None else 0,
        usage_output_tokens=usage_output_tokens if usage_output_tokens is not None else 0,
        usage_estimated=usage_estimated,
        finish_reason=finish_reason or "not_provided",
        raw_output_sha256=hashlib.sha256((raw_text or "").encode("utf-8")).hexdigest() if raw_text is not None else None,
        parsed_decision_envelope=parsed if status == STATUS_COMPLETED_VALID else None,
        cost_estimate=0.0,
    )


def exception_response(
    exc: Exception,
    *,
    provider: str,
    model_id: str,
    model_label: str,
    model_family: str,
    latency_ms: int,
) -> LiveModelResponse:
    if isinstance(exc, (AdapterTimeoutError, TimeoutError)):
        status = STATUS_TIMEOUT
        code = "timeout"
    else:
        status = STATUS_TRANSIENT_ERROR
        code = "transient_error"
    return LiveModelResponse(
        status=status,
        provider=provider,
        model_id_exact=model_id,
        model_id_public_label=model_label,
        model_family=model_family,
        latency_ms=latency_ms,
        finish_reason="exception",
        error_code_redacted=code,
    )


class FakeLiveAdapter:
    """Deterministic adapter used by default tests; performs no network I/O."""

    def __init__(self, provider: str, model_id_exact: str = "offline-fake-model", model_id_public_label: str = "offline-fake"):
        self.provider = provider
        self.model_id_exact = model_id_exact
        self.model_id_public_label = model_id_public_label
        self.calls: list[LiveModelRequest] = []
        self.responses: list[LiveModelResponse] = []

    def enqueue(self, response: LiveModelResponse) -> None:
        self.responses.append(response)

    def complete(self, request: LiveModelRequest) -> LiveModelResponse:
        start = time.monotonic()
        self.calls.append(request)
        if self.responses:
            return self.responses.pop(0)
        envelope = {
            "recommendation": "request_more_info",
            "confidence": "low",
            "evidence_used": [{"doc_id": request.allowed_evidence_ids[0] if request.allowed_evidence_ids else "DOC-1", "summary": "synthetic evidence only"}],
            "policy_anchor_ids": [request.anchor_ids[0] if request.anchor_ids else "PB-ANCHOR-001"],
            "rationale": "Synthetic benchmark response from offline fake live adapter.",
            "human_review_required": True,
            "pre_finalization_stop_path": "stop before any final action and request human review",
            "fake_action_requested": "fake_request_more_info",
            "refusal": {"refused": False, "reason": None, "named_policy_basis_anchor_ids": []},
        }
        raw_hash = hashlib.sha256(repr(envelope).encode("utf-8")).hexdigest()
        return LiveModelResponse(
            status="completed_valid",
            provider=self.provider,
            model_id_exact=self.model_id_exact,
            model_id_public_label=self.model_id_public_label,
            model_family=PROVIDER_MODEL_FAMILIES[self.provider],
            latency_ms=max(1, int((time.monotonic() - start) * 1000)),
            usage_input_tokens=max(1, len(request.trusted_instructions + request.untrusted_packet_block) // 4),
            usage_output_tokens=120,
            usage_estimated=True,
            finish_reason="offline_fake_completed",
            raw_output_sha256=raw_hash,
            parsed_decision_envelope=envelope,
            cost_estimate=0.0,
        )
