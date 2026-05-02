"""Scenario card loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .types import (
    ALLOWED_EXPECTED_ACTIONS,
    ExpectedSafeBehavior,
    PolicyAnchor,
    ScenarioCard,
    ValidationError,
    sha256_json,
)


PACKET_DOMAIN = "synthetic_travel_adjudication"
ALLOWED_VARIANT_TYPES = frozenset({"clean_control", "ambiguous_edge", "adversarial_malicious"})
MAX_UNTRUSTED_PACKET_CHARS = 800


def _require_string(record: dict[str, Any], field_name: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"scenario missing non-empty {field_name}")
    return value


def _require_string_list(record: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = record.get(field_name)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValidationError(f"scenario {field_name} must be a non-empty string list")
    return tuple(value)


def evidence_ids_from_facts(facts: dict[str, Any]) -> set[str]:
    documents = facts.get("documents")
    if not isinstance(documents, list):
        return set()
    evidence_ids: set[str] = set()
    for document in documents:
        if isinstance(document, dict) and isinstance(document.get("doc_id"), str):
            evidence_ids.add(document["doc_id"])
    return evidence_ids


def _validate_expected_safe_behavior(record: dict[str, Any]) -> ExpectedSafeBehavior:
    value = record.get("expected_safe_behavior")
    if not isinstance(value, dict):
        raise ValidationError("scenario expected_safe_behavior must be an object")
    primary = value.get("primary_expected_safe_control_action")
    if primary not in ALLOWED_EXPECTED_ACTIONS:
        raise ValidationError("scenario has invalid primary expected safe control action")

    allowed_actions = value.get("allowed_actions")
    disallowed_actions = value.get("disallowed_actions")
    rationale_points = value.get("required_rationale_points")
    for field_name, field_value in (
        ("allowed_actions", allowed_actions),
        ("disallowed_actions", disallowed_actions),
        ("required_rationale_points", rationale_points),
    ):
        if not isinstance(field_value, list) or not all(isinstance(item, str) and item for item in field_value):
            raise ValidationError(f"expected_safe_behavior {field_name} must be a string list")

    return ExpectedSafeBehavior(
        primary_expected_safe_control_action=primary,
        allowed_actions=tuple(allowed_actions),
        disallowed_actions=tuple(disallowed_actions),
        required_rationale_points=tuple(rationale_points),
    )


def validate_scenario_record(
    record: dict[str, Any],
    anchors: dict[str, PolicyAnchor],
) -> ScenarioCard:
    scenario_id = _require_string(record, "scenario_id")
    if record.get("synthetic_notice") is not True:
        raise ValidationError(f"scenario {scenario_id} synthetic_notice must be true")
    if record.get("packet_domain") != PACKET_DOMAIN:
        raise ValidationError(f"scenario {scenario_id} packet_domain is not allowed")
    variant_type = _require_string(record, "variant_type")
    if variant_type not in ALLOWED_VARIANT_TYPES:
        raise ValidationError(f"scenario {scenario_id} variant_type is not allowed")

    policy_anchor_ids = _require_string_list(record, "policy_anchors")
    for anchor_id in policy_anchor_ids:
        if anchor_id not in anchors:
            raise ValidationError(f"scenario {scenario_id} references missing anchor {anchor_id}")

    facts = record.get("facts")
    if not isinstance(facts, dict):
        raise ValidationError(f"scenario {scenario_id} facts must be an object")
    if not evidence_ids_from_facts(facts):
        raise ValidationError(f"scenario {scenario_id} facts must include document evidence")

    untrusted_packet_text = record.get("untrusted_packet_text")
    if not isinstance(untrusted_packet_text, str):
        raise ValidationError(f"scenario {scenario_id} untrusted_packet_text must be a string")
    if len(untrusted_packet_text) > MAX_UNTRUSTED_PACKET_CHARS:
        raise ValidationError(f"scenario {scenario_id} untrusted_packet_text exceeds cap")

    allowed_evidence = _require_string_list(record, "allowed_evidence")
    unknown_allowed = set(allowed_evidence) - evidence_ids_from_facts(facts)
    if unknown_allowed:
        raise ValidationError(f"scenario {scenario_id} allowed_evidence references unknown docs")

    expected = _validate_expected_safe_behavior(record)
    safety_boundary_notes = _require_string(record, "safety_boundary_notes")
    lowered_notes = safety_boundary_notes.lower()
    if "synthetic" not in lowered_notes or "no real" not in lowered_notes:
        raise ValidationError(f"scenario {scenario_id} safety boundary notes are insufficient")

    required_condition = record.get("required_escalation_or_request_info_condition")
    if required_condition is not None and not isinstance(required_condition, str):
        raise ValidationError(f"scenario {scenario_id} required condition must be string or null")

    return ScenarioCard(
        scenario_id=scenario_id,
        title=_require_string(record, "title"),
        version=_require_string(record, "version"),
        synthetic_notice=True,
        packet_domain=PACKET_DOMAIN,
        archetype=_require_string(record, "archetype"),
        variant_type=variant_type,
        policy_anchors=tuple(policy_anchor_ids),
        facts=facts,
        untrusted_packet_text=untrusted_packet_text,
        allowed_evidence=allowed_evidence,
        disallowed_inference=_require_string_list(record, "disallowed_inference"),
        expected_safe_behavior=expected,
        required_escalation_or_request_info_condition=required_condition,
        temptation_or_unsafe_shortcut=_require_string(record, "temptation_or_unsafe_shortcut"),
        expected_failure_labels=tuple(record.get("expected_failure_labels", [])),
        audit_trail_risk=_require_string(record, "audit_trail_risk"),
        human_review_mode_under_test=_require_string(record, "human_review_mode_under_test"),
        article_hook=_require_string(record, "article_hook"),
        public_claim_limit=_require_string(record, "public_claim_limit"),
        safety_boundary_notes=safety_boundary_notes,
        card_hash=sha256_json(record),
        raw=record,
    )


def load_scenario_file(path: str | Path, anchors: dict[str, PolicyAnchor]) -> ScenarioCard:
    with Path(path).open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    if not isinstance(record, dict):
        raise ValidationError("scenario file must contain an object")
    return validate_scenario_record(record, anchors)


def load_scenarios(directory: str | Path, anchors: dict[str, PolicyAnchor]) -> list[ScenarioCard]:
    scenario_paths = sorted(Path(directory).glob("*.json"))
    if not scenario_paths:
        raise ValidationError("no scenario files found")
    scenarios = [load_scenario_file(path, anchors) for path in scenario_paths]
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValidationError("duplicate scenario_id")
    return scenarios
