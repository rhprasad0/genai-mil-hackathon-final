"""Policy anchor manifest loading and freshness validation."""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
import json
from pathlib import Path
from typing import Any

from .types import PolicyAnchor, ValidationError


ALLOWED_RETRIEVAL_STATUSES = frozenset({"ok", "mock_static"})
ALLOWED_SOURCE_TYPES = frozenset({"web_guidance", "public_pdf", "static_reference"})


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be an ISO date") from exc


def parse_run_date(value: str | None) -> date:
    if value is None:
        return utc_today()
    return parse_date(value, "run_date")


def _require_string(record: dict[str, Any], field_name: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"anchor missing non-empty {field_name}")
    return value


def _validate_source_url(anchor_id: str, source_url: str) -> None:
    expected = f"mock://anchor/{anchor_id}"
    if source_url != expected:
        raise ValidationError(
            f"anchor {anchor_id} source_url must equal {expected} in mock slice"
        )


def _validate_anchor_record(record: dict[str, Any], run_date: date) -> PolicyAnchor:
    anchor_id = _require_string(record, "anchor_id")
    source_url = _require_string(record, "source_url")
    _validate_source_url(anchor_id, source_url)

    source_type = _require_string(record, "source_type")
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValidationError(f"anchor {anchor_id} has unsupported source_type")

    retrieval_status = _require_string(record, "retrieval_status")
    if retrieval_status not in ALLOWED_RETRIEVAL_STATUSES:
        raise ValidationError(f"anchor {anchor_id} blocked by retrieval_status")

    for required_text in ("specific_policy_point", "quote_or_excerpt", "supported_claim"):
        _require_string(record, required_text)

    checked = parse_date(_require_string(record, "citation_date_checked"), "citation_date_checked")
    window = record.get("freshness_window_days")
    if not isinstance(window, int) or window <= 0:
        raise ValidationError(f"anchor {anchor_id} has invalid freshness_window_days")
    if checked + timedelta(days=window) < run_date:
        raise ValidationError(f"anchor {anchor_id} blocked_pending_anchor_refresh")

    scenario_ids = record.get("scenario_ids")
    if not isinstance(scenario_ids, list) or not all(isinstance(item, str) for item in scenario_ids):
        raise ValidationError(f"anchor {anchor_id} scenario_ids must be strings")

    publication_or_update_date = record.get("publication_or_update_date")
    if publication_or_update_date is not None and not isinstance(publication_or_update_date, str):
        raise ValidationError(f"anchor {anchor_id} publication_or_update_date must be string or null")
    if publication_or_update_date:
        parse_date(publication_or_update_date, "publication_or_update_date")

    return PolicyAnchor(
        anchor_id=anchor_id,
        source_title=_require_string(record, "source_title"),
        issuing_org=_require_string(record, "issuing_org"),
        source_type=source_type,
        source_url=source_url,
        publication_or_update_date=publication_or_update_date,
        citation_date_checked=record["citation_date_checked"],
        retrieval_status=retrieval_status,
        specific_policy_point=record["specific_policy_point"],
        quote_or_excerpt=record["quote_or_excerpt"],
        supported_claim=record["supported_claim"],
        scenario_ids=tuple(scenario_ids),
        scenario_relevance=_require_string(record, "scenario_relevance"),
        expected_safe_behavior=_require_string(record, "expected_safe_behavior"),
        disallowed_behavior=_require_string(record, "disallowed_behavior"),
        freshness_window_days=window,
    )


def load_anchor_manifest(path: str | Path, run_date: date | None = None) -> dict[str, PolicyAnchor]:
    run_date = run_date or utc_today()
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload.get("anchors") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValidationError("anchor manifest must contain an anchors list")

    anchors: dict[str, PolicyAnchor] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValidationError("anchor record must be an object")
        anchor = _validate_anchor_record(record, run_date)
        if anchor.anchor_id in anchors:
            raise ValidationError(f"duplicate anchor_id {anchor.anchor_id}")
        anchors[anchor.anchor_id] = anchor
    if not anchors:
        raise ValidationError("anchor manifest is empty")
    return anchors
