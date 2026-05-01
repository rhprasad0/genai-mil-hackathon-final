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


def build_decision_envelope_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": DECISION_SCHEMA_VERSION,
        "title": "Policy Bonfire bounded decision envelope",
        "type": "object",
        "additionalProperties": True,
        "required": list(REQUIRED_DECISION_FIELDS),
        "properties": {
            "recommendation": {"type": "string", "enum": sorted(ALLOWED_RECOMMENDATIONS)},
            "confidence": {"type": "string", "enum": sorted(ALLOWED_CONFIDENCE)},
            "evidence_used": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["doc_id"],
                    "properties": {"doc_id": {"type": "string"}, "summary": {"type": "string"}},
                    "additionalProperties": True,
                },
            },
            "policy_anchor_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "rationale": {"type": "string", "maxLength": MAX_RATIONALE_CHARS},
            "human_review_required": {"type": "boolean"},
            "pre_finalization_stop_path": {"type": ["string", "null"]},
            "fake_action_requested": {"type": "string", "enum": sorted(ALLOWED_FAKE_TOOLS)},
            "refusal": {
                "type": "object",
                "required": ["refused", "named_policy_basis_anchor_ids"],
                "properties": {
                    "refused": {"type": "boolean"},
                    "reason": {"type": ["string", "null"]},
                    "named_policy_basis_anchor_ids": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": True,
            },
        },
    }


def decision_envelope_schema() -> dict[str, Any]:
    """Backward-compatible alias used by adapter tests and helpers."""

    return build_decision_envelope_schema()
