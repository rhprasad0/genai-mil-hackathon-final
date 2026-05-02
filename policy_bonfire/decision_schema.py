"""JSON schema for the bounded Policy Bonfire decision envelope."""

from __future__ import annotations

from typing import Any

from .decision_envelope import ALLOWED_CONFIDENCE, ALLOWED_RECOMMENDATIONS, MAX_RATIONALE_CHARS
from .fake_tools import ALLOWED_FAKE_TOOLS

DECISION_SCHEMA_VERSION = "policy-bonfire-decision-envelope-v1"
REQUIRED_DECISION_FIELDS = (
    "recommendation",
    "confidence",
    "evidence_used",
    "policy_anchor_ids",
    "rationale",
    "human_review_required",
    "pre_finalization_stop_path",
    "fake_action_requested",
    "refusal",
)


def build_decision_envelope_schema(
    *,
    allowed_policy_anchor_ids: tuple[str, ...] | list[str] = (),
    allowed_evidence_ids: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Build the decision schema, optionally narrowed to scenario citable IDs.

    Provider-native structured outputs prevent malformed envelopes, but free-form
    citation strings can still become fake policy IDs. For live-shaped requests,
    callers pass the scenario's allowed evidence and policy IDs so the model is
    constrained to citable units before local validation gets the final vote.
    """

    evidence_doc_id_schema: dict[str, Any] = {"type": "string"}
    if allowed_evidence_ids:
        evidence_doc_id_schema["enum"] = sorted(set(allowed_evidence_ids))

    policy_anchor_schema: dict[str, Any] = {"type": "string"}
    if allowed_policy_anchor_ids:
        policy_anchor_schema["enum"] = sorted(set(allowed_policy_anchor_ids))

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": DECISION_SCHEMA_VERSION,
        "title": "Policy Bonfire bounded decision envelope",
        "type": "object",
        "additionalProperties": False,
        "required": list(REQUIRED_DECISION_FIELDS),
        "properties": {
            "recommendation": {"type": "string", "enum": sorted(ALLOWED_RECOMMENDATIONS)},
            "confidence": {"type": "string", "enum": sorted(ALLOWED_CONFIDENCE)},
            "evidence_used": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["doc_id", "summary"],
                    "properties": {"doc_id": evidence_doc_id_schema, "summary": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            "policy_anchor_ids": {"type": "array", "items": policy_anchor_schema, "minItems": 1},
            "rationale": {"type": "string", "maxLength": MAX_RATIONALE_CHARS},
            "human_review_required": {"type": "boolean"},
            "pre_finalization_stop_path": {"type": ["string", "null"]},
            "fake_action_requested": {"type": "string", "enum": sorted(ALLOWED_FAKE_TOOLS)},
            "refusal": {
                "type": "object",
                "required": ["refused", "reason", "named_policy_basis_anchor_ids"],
                "properties": {
                    "refused": {"type": "boolean"},
                    "reason": {"type": ["string", "null"]},
                    "named_policy_basis_anchor_ids": {"type": "array", "items": policy_anchor_schema},
                },
                "additionalProperties": False,
            },
        },
    }


def decision_envelope_schema(
    *,
    allowed_policy_anchor_ids: tuple[str, ...] | list[str] = (),
    allowed_evidence_ids: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Backward-compatible alias used by adapter tests and helpers."""

    return build_decision_envelope_schema(
        allowed_policy_anchor_ids=allowed_policy_anchor_ids,
        allowed_evidence_ids=allowed_evidence_ids,
    )
