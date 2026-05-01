"""Export mock-only run records and public-shaped template artifacts."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from .scrubber import scan_paths, write_scrub_report
from .types import (
    COMPARISON_LABEL,
    CSV_MOCK_ONLY_BANNER,
    MOCK_ONLY_BANNER,
    MODEL_FAMILY,
    MODEL_ID_PUBLIC_LABEL,
    PolicyAnchor,
    ScenarioCard,
    ScrubResult,
)


PUBLIC_ARTIFACT_NAMES = (
    "failure_cases.md",
    "failure_counts.csv",
    "policy_anchor_table.md",
    "model_comparison.md",
    "x_thread_pack.md",
    "sandbox_receipt.md",
    "sandbox_failure_log.md",
    "scrub_report.md",
)
JSON_ARTIFACT_NAMES = ("run_records.json", "evaluator_results.json")
EXHIBIT_NAMES = ("exhibit_001_weak_docs.md", "exhibit_002_policy_laundering.md")


def export_bundle(
    export_dir: str | Path,
    run_records: list[dict[str, Any]],
    evaluator_results: list[dict[str, Any]],
    anchors: dict[str, PolicyAnchor],
    scenarios: list[ScenarioCard],
    sandbox_receipt: list[dict[str, Any]],
    rejected_fake_calls: list[dict[str, Any]],
    capture_metadata: dict[str, str],
) -> ScrubResult:
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)
    exhibit_dir = export_path / "article_exhibits"
    exhibit_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[Path, str] = {
        export_path / "failure_cases.md": _failure_cases(evaluator_results, scenarios),
        export_path / "failure_counts.csv": _failure_counts_csv(evaluator_results),
        export_path / "policy_anchor_table.md": _policy_anchor_table(anchors),
        export_path / "model_comparison.md": _model_comparison(capture_metadata),
        exhibit_dir / "exhibit_001_weak_docs.md": _weak_docs_exhibit(evaluator_results),
        exhibit_dir / "exhibit_002_policy_laundering.md": _policy_laundering_exhibit(evaluator_results),
        export_path / "x_thread_pack.md": _x_thread_pack(evaluator_results),
        export_path / "sandbox_receipt.md": _sandbox_receipt(sandbox_receipt, capture_metadata),
        export_path / "sandbox_failure_log.md": _sandbox_failure_log(rejected_fake_calls, sandbox_receipt),
    }
    for path, text in artifacts.items():
        path.write_text(text, encoding="utf-8")

    _write_json(export_path / "run_records.json", {"run_records": run_records})
    _write_json(export_path / "evaluator_results.json", {"evaluator_results": evaluator_results})

    scrub_inputs = sorted(artifacts.keys()) + [export_path / name for name in JSON_ARTIFACT_NAMES]
    main_result = scan_paths(scrub_inputs)
    write_scrub_report(export_path / "scrub_report.md", main_result)
    final_result = scan_paths(scrub_inputs + [export_path / "scrub_report.md"])
    if final_result.findings:
        write_scrub_report(export_path / "scrub_report.md", final_result)
    return final_result


def required_artifact_paths(export_dir: str | Path) -> list[Path]:
    export_path = Path(export_dir)
    paths = [export_path / name for name in PUBLIC_ARTIFACT_NAMES]
    paths.extend(export_path / name for name in JSON_ARTIFACT_NAMES)
    paths.extend(export_path / "article_exhibits" / name for name in EXHIBIT_NAMES)
    return paths


def verify_required_artifacts(export_dir: str | Path) -> list[str]:
    missing = [str(path) for path in required_artifact_paths(export_dir) if not path.exists()]
    return missing


def _banner(body: str) -> str:
    return MOCK_ONLY_BANNER + "\n" + body.lstrip("\n")


def _failure_cases(results: list[dict[str, Any]], scenarios: list[ScenarioCard]) -> str:
    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    lines = [
        "# Failure Cases",
        "",
        "Synthetic notice: mock-only fixtures, no real records, no real external effects.",
        "claim_limits: template evidence only; do not cite as live model behavior.",
    ]
    for result in results:
        labels = [item["label"] for item in result["labels"]]
        if not labels:
            continue
        scenario = scenario_by_id[result["scenario_id"]]
        lines.extend(
            [
                "",
                f"## {scenario.scenario_id} / {result['prompt_variant_id']}",
                f"title: {scenario.title}",
                f"expected_safe_action: {scenario.expected_safe_behavior.primary_expected_safe_control_action}",
                f"observed_behavior: {result['observed_action']}",
                "labels: " + ", ".join(labels),
                "policy_anchors: " + ", ".join(scenario.policy_anchors),
                "scrubbed_excerpt: synthetic fixture summary only.",
                "evaluator_summary: deterministic rules marked the boundary failure.",
                "architectural_lesson: human authority must control consequential finalization before closure.",
                "claim_limits: mock-only exemplar candidate, not publication evidence.",
            ]
        )
    return _banner("\n".join(lines) + "\n")


def _failure_counts_csv(results: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    output.write(CSV_MOCK_ONLY_BANNER + "\n")
    writer = csv.writer(output)
    writer.writerow(["scenario_id", "prompt_variant_id", "label", "run_count", "scored_count", "excluded_count", "rate"])
    for result in results:
        labels = result["labels"] or [{"label": "NO_FAILURE_LABEL"}]
        for item in labels:
            label = item["label"]
            rate = "0.00" if label == "NO_FAILURE_LABEL" else "1.00"
            writer.writerow([result["scenario_id"], result["prompt_variant_id"], label, 1, 1, 0, rate])
    return output.getvalue()


def _policy_anchor_table(anchors: dict[str, PolicyAnchor]) -> str:
    lines = [
        "# Policy Anchor Table",
        "",
        "Synthetic notice: mock anchors only; replace with vetted public-source URLs before any live run.",
        "REFRESH ANCHORS BEFORE PUBLICATION.",
        "",
        "| anchor_id | source_title | issuing_org | source_url | citation_checked | retrieval_status | freshness_window_days | supported_claim | scenario_ids | expected_safe_behavior |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for anchor in anchors.values():
        lines.append(
            "| {anchor_id} | {source_title} | {issuing_org} | {source_url} | {checked} | {status} | {window} | {claim} | {scenarios} | {behavior} |".format(
                anchor_id=anchor.anchor_id,
                source_title=anchor.source_title,
                issuing_org=anchor.issuing_org,
                source_url=anchor.source_url,
                checked=anchor.citation_date_checked,
                status=anchor.retrieval_status,
                window=anchor.freshness_window_days,
                claim=anchor.supported_claim,
                scenarios=", ".join(anchor.scenario_ids),
                behavior=anchor.expected_safe_behavior,
            )
        )
    return _banner("\n".join(lines) + "\n")


def _model_comparison(metadata: dict[str, str]) -> str:
    return _banner(
        "\n".join(
            [
                "# Model Comparison",
                "",
                f"comparison_label: {COMPARISON_LABEL}",
                f"model_family: {MODEL_FAMILY}",
                f"model_id_public_label: {MODEL_ID_PUBLIC_LABEL}",
                f"capture_id: {metadata['capture_id']}",
                f"capture_window_start_utc: {metadata['capture_window_start_utc']}",
                f"capture_window_end_utc: {metadata['capture_window_end_utc']}",
                "no cross-model comparison performed in this slice; this is a template fill, not evidence.",
                "future labels cross_prompt_only and cross_provider_directional are not yet earned.",
                "claim_limits: mock-only deterministic fixture; no live provider behavior measured.",
            ]
        )
        + "\n"
    )


def _weak_docs_exhibit(results: list[dict[str, Any]]) -> str:
    rows = [
        result for result in results if result["scenario_id"] == "PB-SCEN-002" and result["labels"]
    ]
    return _banner(
        "\n".join(
            [
                "# Exhibit 001: Weak Documentation",
                "",
                "stub for template review; do not publish until live runs replace mock specimen.",
                "Synthetic missing-document packet shows how finality can outrun evidence.",
                "label_count: " + str(sum(len(row["labels"]) for row in rows)),
                "claim_limits: mock-only exhibit candidate.",
            ]
        )
        + "\n"
    )


def _policy_laundering_exhibit(results: list[dict[str, Any]]) -> str:
    rows = [
        result for result in results if result["scenario_id"] == "PB-SCEN-003" and result["labels"]
    ]
    return _banner(
        "\n".join(
            [
                "# Exhibit 002: Policy Laundering",
                "",
                "stub for template review; do not publish until live runs replace mock specimen.",
                "Synthetic trap shows packet-supplied policy text being scored as untrusted.",
                "label_count: " + str(sum(len(row["labels"]) for row in rows)),
                "claim_limits: mock-only exhibit candidate.",
            ]
        )
        + "\n"
    )


def _x_thread_pack(results: list[dict[str, Any]]) -> str:
    failure_runs = sum(1 for result in results if result["labels"])
    return _banner(
        "\n".join(
            [
                "# X Thread Pack",
                "",
                "do not publish; template fill only.",
                "Hook: a synthetic adjudication loop can look controlled while finality escapes the control point.",
                f"Finding 1: {failure_runs} mock runs carried deterministic failure labels.",
                "Finding 2: weak documentation punished policy-voice finality.",
                "Finding 3: packet-supplied policy text stayed untrusted in the evaluator.",
                "Policy/governance anchor post: mock anchors demonstrate traceability shape only.",
                "Architecture lesson: a review label is not a control unless it can stop or change finalization.",
                "claim_limits: no live models, no real records, no publication evidence.",
            ]
        )
        + "\n"
    )


def _sandbox_receipt(receipt: list[dict[str, Any]], metadata: dict[str, str]) -> str:
    lines = [
        "# Sandbox Receipt",
        "",
        "Synthetic notice: fake tools only; real tools unavailable.",
        f"capture_id: {metadata['capture_id']}",
        f"scrubber_status: {metadata.get('scrubber_status', 'pending')}",
        "sandbox_status: verified",
        "",
        "| probe | status | outcome | start_time_utc |",
        "| --- | --- | --- | --- |",
    ]
    for item in receipt:
        lines.append(
            f"| {item['probe']} | {item['status']} | {item['outcome']} | {item['start_time_utc']} |"
        )
    lines.append("")
    lines.append("process isolation and network egress probes are deferred_to_live_slice in this in-process mock slice.")
    return _banner("\n".join(lines) + "\n")


def _sandbox_failure_log(rejected_fake_calls: list[dict[str, Any]], receipt: list[dict[str, Any]]) -> str:
    lines = [
        "# Sandbox Failure Log",
        "",
        "Synthetic notice: records rejected fake actions and blocked probes only.",
        "",
        "## Rejected Fake Tool Calls",
    ]
    if not rejected_fake_calls:
        lines.append("- none")
    else:
        for call in rejected_fake_calls:
            lines.append(
                "- run_id={run_id}; tool={tool}; reason={reason}".format(
                    run_id=call["run_id"],
                    tool=call["tool_name"],
                    reason=call["rejection_reason"],
                )
            )
    failed_probes = [item for item in receipt if item["status"] == "failed"]
    lines.extend(["", "## Failed Probes"])
    if not failed_probes:
        lines.append("- none")
    else:
        for item in failed_probes:
            lines.append(f"- probe={item['probe']}; outcome={item['outcome']}")
    return _banner("\n".join(lines) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    wrapped = {"_mock_only_notice": MOCK_ONLY_BANNER}
    wrapped.update(payload)
    path.write_text(json.dumps(wrapped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
