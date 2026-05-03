"""Provider-neutral live-model contracts for Policy Bonfire."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GOOGLE = "google"
PROVIDER_IDS = (PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_GOOGLE)
ALLOWED_PROVIDERS = frozenset(PROVIDER_IDS)
PROVIDER_MODEL_FAMILIES = {
    "openai": "openai_lineage",
    "anthropic": "anthropic_lineage",
    "google": "google_lineage",
}
MODEL_FAMILY_LABELS = PROVIDER_MODEL_FAMILIES
STATUS_COMPLETED_VALID = "completed_valid"
STATUS_PROVIDER_SAFETY_REFUSAL = "provider_safety_refusal"
STATUS_PROVIDER_NO_CANDIDATE = "provider_no_candidate"
STATUS_EXCLUDED_MALFORMED_JSON = "excluded_malformed_json"
STATUS_EXCLUDED_FENCED_JSON = "excluded_fenced_json"
STATUS_EXCLUDED_TRUNCATED = "excluded_truncated"
STATUS_EXCLUDED_SCHEMA_INVALID = "excluded_schema_invalid"
STATUS_PROVIDER_SKIPPED_MISSING_KEY = "provider_skipped_missing_key"
STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE = "provider_skipped_model_unavailable"
STATUS_PROVIDER_SKIPPED_MISSING_RATE = "provider_skipped_missing_rate"
STATUS_BLOCKED_COST_CAP = "blocked_cost_cap"
STATUS_BLOCKED_INPUT_CAP = "blocked_input_cap"
STATUS_TIMEOUT = "timeout"
STATUS_TRANSIENT_ERROR = "transient_error"
STATUS_SANDBOX_UNVERIFIED = "sandbox_unverified"
STATUS_LIVE_CALLS_NOT_ENABLED = "live_calls_not_enabled"

ALLOWED_LIVE_STATUSES = frozenset(
    {
        STATUS_COMPLETED_VALID,
        STATUS_PROVIDER_SAFETY_REFUSAL,
        STATUS_PROVIDER_NO_CANDIDATE,
        STATUS_EXCLUDED_MALFORMED_JSON,
        STATUS_EXCLUDED_FENCED_JSON,
        STATUS_EXCLUDED_TRUNCATED,
        STATUS_EXCLUDED_SCHEMA_INVALID,
        STATUS_PROVIDER_SKIPPED_MISSING_KEY,
        STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE,
        STATUS_PROVIDER_SKIPPED_MISSING_RATE,
        STATUS_BLOCKED_COST_CAP,
        STATUS_BLOCKED_INPUT_CAP,
        STATUS_TIMEOUT,
        STATUS_TRANSIENT_ERROR,
        STATUS_SANDBOX_UNVERIFIED,
        STATUS_LIVE_CALLS_NOT_ENABLED,
    }
)


def decision_envelope_json_schema() -> dict[str, Any]:
    from .decision_schema import build_decision_envelope_schema

    return build_decision_envelope_schema()


@dataclass(frozen=True)
class LiveModelRequest:
    capture_id: str
    scenario_id: str
    scenario_hash: str
    anchor_ids: tuple[str, ...]
    prompt_variant_id: str
    prompt_template_hash: str
    rendered_prompt_hash: str
    trusted_instructions: str
    untrusted_packet_block: str
    decision_schema_version: str
    decision_schema: dict[str, Any]
    max_output_tokens: int = 700
    allowed_evidence_ids: tuple[str, ...] = ()
    temperature: float = 0.0
    seed: int | None = None
    timeout_seconds: int = 30
    cost_cap_context: dict[str, Any] = field(default_factory=dict)
    repetition_id: str = "rep_001"


@dataclass(frozen=True)
class LiveModelResponse:
    status: str
    provider: str
    model_id_exact: str
    model_id_public_label: str
    model_family: str
    latency_ms: int = 0
    usage_input_tokens: int = 0
    usage_output_tokens: int = 0
    usage_estimated: bool = True
    finish_reason: str = "not_provided"
    raw_output_sha256: str | None = None
    parsed_decision_envelope: dict[str, Any] | None = None
    repair_attempted: bool = False
    retry_count: int = 0
    error_code_redacted: str | None = None
    cost_estimate: float = 0.0

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_LIVE_STATUSES:
            raise ValueError(f"unknown live status: {self.status}")
        if self.provider not in PROVIDER_IDS:
            raise ValueError(f"unknown live provider: {self.provider}")
