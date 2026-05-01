"""Prompt variant inventory and trusted/untrusted rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .types import PromptRenderResult, PromptVariant, ScenarioCard, ValidationError, sha256_text, stable_json


EXPECTED_PROMPT_VARIANTS = (
    "cautious_baseline",
    "policy_voice_specimen",
    "decorative_hitl_specimen",
)

TRUSTED_DELIMITERS = (
    "<HARNESS_INSTRUCTIONS>",
    "</HARNESS_INSTRUCTIONS>",
    "<UNTRUSTED_PACKET>",
    "</UNTRUSTED_PACKET>",
)

BLOCKED_PROMPT_TERMS = ("dts", "dod", "cdao", "deploy", "payment")


def _require_string(record: dict[str, Any], field_name: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"prompt variant missing non-empty {field_name}")
    return value


def load_prompt_variants(path: str | Path) -> list[PromptVariant]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload.get("variants") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValidationError("prompt inventory must contain variants list")

    variants: list[PromptVariant] = []
    seen: set[str] = set()
    intended_pressures: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValidationError("prompt variant must be an object")
        variant_id = _require_string(record, "prompt_variant_id")
        if variant_id not in EXPECTED_PROMPT_VARIANTS:
            raise ValidationError(f"unexpected prompt variant {variant_id}")
        if variant_id in seen:
            raise ValidationError(f"duplicate prompt variant {variant_id}")
        if record.get("pilot_use") is not True:
            raise ValidationError(f"prompt variant {variant_id} pilot_use must be true")
        template = _require_string(record, "prompt_template")
        lowered = template.lower()
        if any(term in lowered for term in BLOCKED_PROMPT_TERMS):
            raise ValidationError(f"prompt variant {variant_id} contains blocked operational wording")
        stored_hash = _require_string(record, "prompt_template_hash")
        actual_hash = sha256_text(template)
        if stored_hash != actual_hash:
            raise ValidationError(f"prompt variant {variant_id} template hash mismatch")
        expected_modes = record.get("expected_failure_modes")
        if not isinstance(expected_modes, list) or not all(isinstance(item, str) for item in expected_modes):
            raise ValidationError(f"prompt variant {variant_id} expected_failure_modes must be strings")
        pressure = _require_string(record, "intended_pressure")
        intended_pressures.add(pressure)
        variants.append(
            PromptVariant(
                prompt_variant_id=variant_id,
                pilot_use=True,
                intended_pressure=pressure,
                expected_failure_modes=tuple(expected_modes),
                public_claim_limits=_require_string(record, "public_claim_limits"),
                prompt_template=template,
                prompt_version=_require_string(record, "prompt_version"),
                prompt_template_hash=stored_hash,
            )
        )
        seen.add(variant_id)

    if tuple(variant.prompt_variant_id for variant in variants) != EXPECTED_PROMPT_VARIANTS:
        raise ValidationError("prompt inventory must contain exactly the three V1 variants in order")
    if len(intended_pressures) != len(variants):
        raise ValidationError("prompt variant intended_pressure strings must be distinct")
    return variants


def escape_untrusted_packet_text(value: str) -> tuple[str, dict[str, Any]]:
    escaped = value.replace("<", "\\u003c").replace(">", "\\u003e")
    return escaped, {
        "strategy": "angle_brackets_to_literal_unicode_escape",
        "substitutions": len(value) - len(value.replace("<", "")) + len(value) - len(value.replace(">", "")),
    }


def render_prompt(variant: PromptVariant, scenario: ScenarioCard) -> PromptRenderResult:
    escaped_packet, escape_report = escape_untrusted_packet_text(scenario.untrusted_packet_text)
    values = {
        "prompt_variant_id": variant.prompt_variant_id,
        "prompt_version": variant.prompt_version,
        "intended_pressure": variant.intended_pressure,
        "scenario_id": scenario.scenario_id,
        "scenario_title": scenario.title,
        "expected_action": scenario.expected_safe_behavior.primary_expected_safe_control_action,
        "policy_anchor_ids": ", ".join(scenario.policy_anchors),
        "allowed_actions": ", ".join(scenario.expected_safe_behavior.allowed_actions),
        "allowed_evidence": ", ".join(scenario.allowed_evidence),
        "facts_json": stable_json(scenario.facts).strip(),
        "untrusted_packet_text": escaped_packet,
    }
    rendered = variant.prompt_template.format(**values)
    _validate_rendered_prompt(rendered)
    return PromptRenderResult(
        rendered_prompt=rendered,
        rendered_prompt_hash=sha256_text(rendered),
        escape_report=escape_report,
    )


def _validate_rendered_prompt(rendered: str) -> None:
    if rendered.count("<HARNESS_INSTRUCTIONS>") != 1:
        raise ValidationError("rendered prompt must contain exactly one trusted start delimiter")
    if rendered.count("</HARNESS_INSTRUCTIONS>") != 1:
        raise ValidationError("rendered prompt must contain exactly one trusted end delimiter")
    if rendered.count("<UNTRUSTED_PACKET>") != 1:
        raise ValidationError("rendered prompt must contain exactly one untrusted start delimiter")
    if rendered.count("</UNTRUSTED_PACKET>") != 1:
        raise ValidationError("rendered prompt must contain exactly one untrusted end delimiter")
    if rendered.index("<HARNESS_INSTRUCTIONS>") > rendered.index("<UNTRUSTED_PACKET>"):
        raise ValidationError("trusted instructions must precede untrusted packet")
