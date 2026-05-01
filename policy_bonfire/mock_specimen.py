"""Pure table lookup for canned mock specimen envelopes."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .decision_envelope import validate_decision_envelope
from .types import MOCK_ONLY_BANNER, PromptVariant, ScenarioCard, ValidationError


def load_canned_envelopes(
    path: str | Path,
    scenarios: list[ScenarioCard],
    prompt_variants: list[PromptVariant],
) -> dict[tuple[str, str], dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValidationError("canned envelopes file must be an object")
    if payload.get("_mock_only_notice") != MOCK_ONLY_BANNER:
        raise ValidationError("canned envelopes missing mock-only notice")
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise ValidationError("canned envelopes entries must be an object")

    scenario_map = {scenario.scenario_id: scenario for scenario in scenarios}
    prompt_ids = [variant.prompt_variant_id for variant in prompt_variants]
    if set(entries.keys()) != set(scenario_map.keys()):
        raise ValidationError("canned envelopes scenario keys do not match loaded scenarios")

    table: dict[tuple[str, str], dict[str, Any]] = {}
    for scenario_id, by_prompt in entries.items():
        if not isinstance(by_prompt, dict) or set(by_prompt.keys()) != set(prompt_ids):
            raise ValidationError(f"canned envelopes prompt keys mismatch for {scenario_id}")
        for prompt_id in prompt_ids:
            envelope = by_prompt[prompt_id]
            result = validate_decision_envelope(envelope, scenario_map[scenario_id])
            if not result.valid:
                raise ValidationError(
                    f"canned envelope invalid for {scenario_id}/{prompt_id}: {', '.join(result.errors)}"
                )
            table[(scenario_id, prompt_id)] = envelope
    if len(table) != len(scenarios) * len(prompt_variants):
        raise ValidationError("canned envelopes must contain exactly one entry per scenario and prompt")
    return table


def lookup_envelope(
    table: dict[tuple[str, str], dict[str, Any]],
    scenario_id: str,
    prompt_variant_id: str,
) -> dict[str, Any]:
    try:
        return copy.deepcopy(table[(scenario_id, prompt_variant_id)])
    except KeyError as exc:
        raise ValidationError(f"missing canned envelope for {scenario_id}/{prompt_variant_id}") from exc
