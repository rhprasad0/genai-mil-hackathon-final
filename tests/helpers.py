from __future__ import annotations

import copy
import json
from pathlib import Path

from policy_bonfire.anchors import load_anchor_manifest
from policy_bonfire.fake_tools import dispatch_fake_tool
from policy_bonfire.mock_specimen import load_canned_envelopes, lookup_envelope
from policy_bonfire.prompts import load_prompt_variants, render_prompt
from policy_bonfire.scenarios import load_scenarios
from policy_bonfire.decision_envelope import validate_decision_envelope
from policy_bonfire.evaluator import evaluate_run


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_all(run_date=None):
    anchors = load_anchor_manifest(DATA_DIR / "policy_anchors" / "mock_v1_anchors.json", run_date=run_date)
    scenarios = load_scenarios(DATA_DIR / "scenarios", anchors)
    prompts = load_prompt_variants(DATA_DIR / "prompts" / "pilot_variants.json")
    canned = load_canned_envelopes(DATA_DIR / "mock_outputs" / "canned_envelopes.json", scenarios, prompts)
    return anchors, scenarios, prompts, canned


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def mutable_anchor_payload():
    return copy.deepcopy(read_json(DATA_DIR / "policy_anchors" / "mock_v1_anchors.json"))


def mutable_scenario_payload(name="pb_scen_001_clean_packet.json"):
    return copy.deepcopy(read_json(DATA_DIR / "scenarios" / name))


def evaluator_matrix():
    _, scenarios, prompts, canned = load_all()
    scenario_map = {scenario.scenario_id: scenario for scenario in scenarios}
    rows = {}
    for scenario in scenarios:
        for prompt in prompts:
            envelope = lookup_envelope(canned, scenario.scenario_id, prompt.prompt_variant_id)
            validation = validate_decision_envelope(envelope, scenario)
            run_id = f"run-{scenario.scenario_id}-{prompt.prompt_variant_id}"
            fake_call = dispatch_fake_tool(run_id, validation.envelope, scenario)
            render = render_prompt(prompt, scenario)
            run_record = {
                "run_id": run_id,
                "scenario_id": scenario.scenario_id,
                "prompt_variant_id": prompt.prompt_variant_id,
                "prompt_template_hash": render.rendered_prompt_hash,
            }
            result = evaluate_run(run_record, scenario_map[scenario.scenario_id], validation.envelope, validation, fake_call)
            rows[(scenario.scenario_id, prompt.prompt_variant_id)] = result
    return rows
