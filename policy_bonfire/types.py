"""Shared types and deterministic helpers for the mock-only harness."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


MOCK_ONLY_BANNER = "> MOCK ONLY — NOT FOR PUBLICATION. Synthetic lab. Deterministic fixture, not a model. No real models, real vouchers, real claimants, real payments, real fraud accusations, or official action. Do not quote, screenshot, or share any portion of this bundle as evidence of model behavior."
CSV_MOCK_ONLY_BANNER = "# MOCK ONLY — NOT FOR PUBLICATION. Synthetic lab. Deterministic fixture, not a model. No real models, real vouchers, real claimants, real payments, real fraud accusations, or official action. Do not quote, screenshot, or share any portion of this bundle as evidence of model behavior."

MODEL_FAMILY = "mock_specimen"
MODEL_ID_PUBLIC_LABEL = "mock-specimen-v1"
COMPARISON_LABEL = "mock_only"

ALLOWED_EXPECTED_ACTIONS = frozenset(
    {
        "SAFE_APPROVE",
        "SAFE_DENY",
        "REQUEST_INFO",
        "ESCALATE",
        "REFUSE_UNSUPPORTED_ACTION",
        "NO_FINAL_ACTION",
    }
)


class ValidationError(ValueError):
    """Raised when public-safe harness data fails validation."""


def normalize_text(value: str) -> str:
    """Normalize text for stable hashing and template comparison."""

    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if value.startswith("\ufeff"):
        value = value[1:]
    lines = [line.rstrip() for line in value.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def sha256_text(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def stable_json(data: Any) -> str:
    return normalize_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def sha256_json(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicyAnchor:
    anchor_id: str
    source_title: str
    issuing_org: str
    source_type: str
    source_url: str
    publication_or_update_date: str | None
    citation_date_checked: str
    retrieval_status: str
    specific_policy_point: str
    quote_or_excerpt: str
    supported_claim: str
    scenario_ids: tuple[str, ...]
    scenario_relevance: str
    expected_safe_behavior: str
    disallowed_behavior: str
    freshness_window_days: int


@dataclass(frozen=True)
class ExpectedSafeBehavior:
    primary_expected_safe_control_action: str
    allowed_actions: tuple[str, ...]
    disallowed_actions: tuple[str, ...]
    required_rationale_points: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioCard:
    scenario_id: str
    title: str
    version: str
    synthetic_notice: bool
    packet_domain: str
    archetype: str
    variant_type: str
    policy_anchors: tuple[str, ...]
    facts: dict[str, Any]
    untrusted_packet_text: str
    allowed_evidence: tuple[str, ...]
    disallowed_inference: tuple[str, ...]
    expected_safe_behavior: ExpectedSafeBehavior
    required_escalation_or_request_info_condition: str | None
    temptation_or_unsafe_shortcut: str
    expected_failure_labels: tuple[str, ...]
    audit_trail_risk: str
    human_review_mode_under_test: str
    article_hook: str
    safety_boundary_notes: str
    card_hash: str
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class PromptVariant:
    prompt_variant_id: str
    pilot_use: bool
    intended_pressure: str
    expected_failure_modes: tuple[str, ...]
    public_claim_limits: str
    prompt_template: str
    prompt_version: str
    prompt_template_hash: str


@dataclass(frozen=True)
class PromptRenderResult:
    rendered_prompt: str
    rendered_prompt_hash: str
    escape_report: dict[str, Any]


@dataclass(frozen=True)
class EnvelopeValidationResult:
    valid: bool
    envelope: dict[str, Any]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    truncation_applied: bool


@dataclass(frozen=True)
class ScrubFinding:
    finding_class: str
    count: int
    sha256_of_match_prefix: str
    artifact_path: str
    byte_offset: int


@dataclass(frozen=True)
class ScrubResult:
    status: str
    findings: tuple[ScrubFinding, ...]
    checked_artifacts: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "passed"
