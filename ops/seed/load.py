"""Loader CLI for the AO Radar seed.

Connects to Postgres via ``DATABASE_URL`` (developer path) or via a DB secret
JSON loaded from AWS Secrets Manager (``DB_SECRET_ARN``; ``db_ops`` Lambda
path). Refuses to write unless every connection-guard condition in
synthetic-data plan section 11 is satisfied.

Reset is exposed only as ``--reset`` and as the ``ops.seed.reset`` wrapper;
neither is exposed as an MCP tool.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ops.seed.constants import (
    DATA_ENVIRONMENT,
    TRAVELER_IDS,
    VOUCHER_IDS,
)
from ops.seed.generators.corpus import Corpus, build_corpus, seed_root
from ops.seed.validate import _validate_full

_LOAD_ORDER: tuple[str, ...] = (
    "policy_citations",
    "travelers",
    "prior_voucher_summaries",
    "vouchers",
    "voucher_line_items",
    "evidence_refs",
    "external_anomaly_signals",
    "story_findings",
    "finding_signal_links",
    "missing_information_items",
    "review_briefs",
    "ao_notes",
    "workflow_events",
)

_DELETE_ORDER: tuple[str, ...] = tuple(reversed(_LOAD_ORDER))


def _resolve_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    secret_arn = os.environ.get("DB_SECRET_ARN")
    if not secret_arn:
        return None
    try:
        import boto3  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required to resolve DB_SECRET_ARN; install ao-radar[mcp]"
        ) from exc
    client = boto3.client("secretsmanager")
    resp = client.get_secret_value(SecretId=secret_arn)
    blob = json.loads(resp["SecretString"])
    user = blob["username"]
    password = blob["password"]
    host = blob["host"]
    port = blob.get("port", 5432)
    database = blob["dbname"]
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _check_connection_guard(conn: Any) -> None:
    # 1. DEMO_DATA_ENVIRONMENT must equal synthetic_demo.
    env = os.environ.get("DEMO_DATA_ENVIRONMENT")
    if env != DATA_ENVIRONMENT:
        raise RuntimeError(
            f"connection guard failed: DEMO_DATA_ENVIRONMENT={env!r}, expected "
            f"{DATA_ENVIRONMENT!r}"
        )
    with conn.cursor() as cur:
        # 2. CHECK constraints exist on travelers + vouchers.
        cur.execute(
            """
            SELECT conname FROM pg_constraint
            WHERE conname IN (
                'travelers_data_environment_synthetic_demo',
                'vouchers_data_environment_synthetic_demo'
            )
            """
        )
        names = {row[0] for row in cur.fetchall()}
        missing = {
            "travelers_data_environment_synthetic_demo",
            "vouchers_data_environment_synthetic_demo",
        } - names
        if missing:
            raise RuntimeError(
                f"connection guard failed: missing data_environment CHECKs: "
                f"{sorted(missing)}"
            )
        # 3. Every existing travelers/vouchers row has data_environment=synthetic_demo.
        for table in ("travelers", "vouchers"):
            cur.execute(
                f"SELECT COUNT(*) FROM {table} WHERE data_environment <> %s",
                (DATA_ENVIRONMENT,),
            )
            (count,) = cur.fetchone()
            if count:
                raise RuntimeError(
                    f"connection guard failed: {table} contains {count} rows with "
                    f"data_environment != {DATA_ENVIRONMENT!r}"
                )


def _delete_seeded(conn: Any) -> None:
    """Delete only the canonical seeded IDs and dependents in reverse order."""

    voucher_set = list(VOUCHER_IDS)
    traveler_set = list(TRAVELER_IDS)
    with conn.cursor() as cur:
        # workflow_events keyed by voucher_id.
        cur.execute(
            "DELETE FROM workflow_events WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM ao_notes WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM review_briefs WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM missing_information_items WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            """
            DELETE FROM finding_signal_links WHERE finding_id IN (
                SELECT finding_id FROM story_findings WHERE voucher_id = ANY(%s)
            )
            """,
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM story_findings WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM external_anomaly_signals WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM evidence_refs WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM voucher_line_items WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM vouchers WHERE voucher_id = ANY(%s)",
            (voucher_set,),
        )
        cur.execute(
            "DELETE FROM prior_voucher_summaries WHERE traveler_id = ANY(%s)",
            (traveler_set,),
        )
        cur.execute(
            "DELETE FROM travelers WHERE traveler_id = ANY(%s)",
            (traveler_set,),
        )
        # policy_citations: only delete the canonical seeded ones.
        cur.execute(
            """
            DELETE FROM policy_citations WHERE source_identifier IN (
                'synthetic_dtmo_checklist_demo_v1',
                'synthetic_demo_reference_v1'
            )
            """
        )


_INSERT_SQL: dict[str, str] = {
    "policy_citations": """
        INSERT INTO policy_citations
            (citation_id, source_identifier, topic, excerpt_text, retrieval_anchor,
             applicability_note, created_at)
        VALUES
            (%(citation_id)s, %(source_identifier)s, %(topic)s, %(excerpt_text)s,
             %(retrieval_anchor)s, %(applicability_note)s, %(created_at)s)
    """,
    "travelers": """
        INSERT INTO travelers
            (traveler_id, display_name, role_label, home_unit_label,
             typical_trip_pattern, prior_correction_summary, data_environment, created_at)
        VALUES
            (%(traveler_id)s, %(display_name)s, %(role_label)s, %(home_unit_label)s,
             %(typical_trip_pattern)s, %(prior_correction_summary)s, %(data_environment)s,
             %(created_at)s)
    """,
    "prior_voucher_summaries": """
        INSERT INTO prior_voucher_summaries
            (prior_summary_id, traveler_id, period_label, summary_text,
             recurring_correction_pattern, created_at)
        VALUES
            (%(prior_summary_id)s, %(traveler_id)s, %(period_label)s, %(summary_text)s,
             %(recurring_correction_pattern)s, %(created_at)s)
    """,
    "vouchers": """
        INSERT INTO vouchers
            (voucher_id, traveler_id, trip_purpose_category, trip_start_date,
             trip_end_date, declared_origin, declared_destinations,
             funding_reference_label, funding_reference_quality, justification_text,
             pre_existing_flags, demo_packet_submitted_at, review_status,
             data_environment, created_at, updated_at)
        VALUES
            (%(voucher_id)s, %(traveler_id)s, %(trip_purpose_category)s, %(trip_start_date)s,
             %(trip_end_date)s, %(declared_origin)s, %(declared_destinations)s::jsonb,
             %(funding_reference_label)s, %(funding_reference_quality)s, %(justification_text)s,
             %(pre_existing_flags)s::jsonb, %(demo_packet_submitted_at)s, %(review_status)s,
             %(data_environment)s, %(created_at)s, %(updated_at)s)
    """,
    "voucher_line_items": """
        INSERT INTO voucher_line_items
            (line_item_id, voucher_id, line_index, expense_date, amount_minor_units,
             currency_code, exchange_rate_to_usd, category, vendor_label,
             payment_instrument_indicator, free_text_notes, claimed_by_traveler_at)
        VALUES
            (%(line_item_id)s, %(voucher_id)s, %(line_index)s, %(expense_date)s,
             %(amount_minor_units)s, %(currency_code)s, %(exchange_rate_to_usd)s,
             %(category)s, %(vendor_label)s, %(payment_instrument_indicator)s,
             %(free_text_notes)s, %(claimed_by_traveler_at)s)
    """,
    "evidence_refs": """
        INSERT INTO evidence_refs
            (evidence_ref_id, voucher_id, line_item_id, packet_level_role,
             content_type_indicator, legibility_cue, itemization_cue, payment_evidence_cue,
             vendor_label_on_evidence, evidence_date_on_face, amount_on_face_minor_units,
             currency_code_on_face, notes)
        VALUES
            (%(evidence_ref_id)s, %(voucher_id)s, %(line_item_id)s, %(packet_level_role)s,
             %(content_type_indicator)s, %(legibility_cue)s, %(itemization_cue)s,
             %(payment_evidence_cue)s, %(vendor_label_on_evidence)s,
             %(evidence_date_on_face)s, %(amount_on_face_minor_units)s,
             %(currency_code_on_face)s, %(notes)s)
    """,
    "external_anomaly_signals": """
        INSERT INTO external_anomaly_signals
            (signal_id, voucher_id, signal_key, signal_type, synthetic_source_label,
             rationale_text, confidence, is_official_finding,
             not_sufficient_for_adverse_action, received_at)
        VALUES
            (%(signal_id)s, %(voucher_id)s, %(signal_key)s, %(signal_type)s,
             %(synthetic_source_label)s, %(rationale_text)s, %(confidence)s,
             %(is_official_finding)s, %(not_sufficient_for_adverse_action)s,
             %(received_at)s)
    """,
    "story_findings": """
        INSERT INTO story_findings
            (finding_id, voucher_id, category, severity, summary, explanation,
             suggested_question, packet_evidence_pointer, primary_citation_id,
             confidence, needs_human_review, review_state, created_at)
        VALUES
            (%(finding_id)s, %(voucher_id)s, %(category)s, %(severity)s, %(summary)s,
             %(explanation)s, %(suggested_question)s, %(packet_evidence_pointer)s::jsonb,
             %(primary_citation_id)s, %(confidence)s, %(needs_human_review)s,
             %(review_state)s, %(created_at)s)
    """,
    "finding_signal_links": """
        INSERT INTO finding_signal_links (finding_id, signal_id, created_at)
        VALUES (%(finding_id)s, %(signal_id)s, %(created_at)s)
    """,
    "missing_information_items": """
        INSERT INTO missing_information_items
            (missing_item_id, voucher_id, description, why_it_matters,
             expected_location_hint, linked_line_item_id, created_at)
        VALUES
            (%(missing_item_id)s, %(voucher_id)s, %(description)s, %(why_it_matters)s,
             %(expected_location_hint)s, %(linked_line_item_id)s, %(created_at)s)
    """,
    "review_briefs": """
        INSERT INTO review_briefs
            (brief_id, voucher_id, version, generated_at, priority_score,
             priority_rationale, suggested_focus, evidence_gap_summary,
             story_coherence_summary, draft_clarification_note, policy_hooks,
             signal_hooks, finding_hooks, missing_information_hooks,
             brief_uncertainty, human_authority_boundary_text, is_partial,
             partial_reason)
        VALUES
            (%(brief_id)s, %(voucher_id)s, %(version)s, %(generated_at)s,
             %(priority_score)s, %(priority_rationale)s, %(suggested_focus)s,
             %(evidence_gap_summary)s, %(story_coherence_summary)s,
             %(draft_clarification_note)s, %(policy_hooks)s::jsonb,
             %(signal_hooks)s::jsonb, %(finding_hooks)s::jsonb,
             %(missing_information_hooks)s::jsonb, %(brief_uncertainty)s,
             %(human_authority_boundary_text)s, %(is_partial)s, %(partial_reason)s)
    """,
    "ao_notes": """
        INSERT INTO ao_notes
            (note_id, voucher_id, finding_id, kind, body, actor_label, created_at,
             superseded_by_note_id)
        VALUES
            (%(note_id)s, %(voucher_id)s, %(finding_id)s, %(kind)s, %(body)s,
             %(actor_label)s, %(created_at)s, %(superseded_by_note_id)s)
    """,
    "workflow_events": """
        INSERT INTO workflow_events
            (event_id, voucher_id, actor_label, occurred_at, event_type, tool_name,
             target_kind, target_id, resulting_status, rationale_metadata,
             human_authority_boundary_reminder)
        VALUES
            (%(event_id)s, %(voucher_id)s, %(actor_label)s, %(occurred_at)s,
             %(event_type)s, %(tool_name)s, %(target_kind)s, %(target_id)s,
             %(resulting_status)s, %(rationale_metadata)s::jsonb,
             %(human_authority_boundary_reminder)s)
    """,
}


def _row_for_insert(table: str, row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    # Encode JSON-bearing columns.
    if table == "vouchers":
        out["declared_destinations"] = json.dumps(row.get("declared_destinations", []))
        out["pre_existing_flags"] = json.dumps(row.get("pre_existing_flags", []))
    if table == "story_findings":
        out["packet_evidence_pointer"] = json.dumps(row.get("packet_evidence_pointer", {}))
    if table == "review_briefs":
        for col in ("policy_hooks", "signal_hooks", "finding_hooks", "missing_information_hooks"):
            out[col] = json.dumps(row.get(col, []))
    if table == "workflow_events":
        out["rationale_metadata"] = json.dumps(row.get("rationale_metadata") or {})
    return out


def _insert_corpus(conn: Any, corpus: Corpus) -> None:
    bundles = {
        "policy_citations": corpus.policy_citations,
        "travelers": corpus.travelers,
        "prior_voucher_summaries": corpus.prior_voucher_summaries,
        "vouchers": corpus.vouchers,
        "voucher_line_items": corpus.voucher_line_items,
        "evidence_refs": corpus.evidence_refs,
        "external_anomaly_signals": corpus.external_anomaly_signals,
        "story_findings": corpus.story_findings,
        "finding_signal_links": corpus.finding_signal_links,
        "missing_information_items": corpus.missing_information_items,
        "review_briefs": corpus.review_briefs,
        "ao_notes": corpus.ao_notes,
        "workflow_events": corpus.workflow_events,
    }
    with conn.cursor() as cur:
        for table in _LOAD_ORDER:
            sql = _INSERT_SQL[table]
            for row in bundles[table]:
                cur.execute(sql, _row_for_insert(table, row))


def run_load(reset: bool, seed_dir: Path | None = None) -> None:
    seed_dir = seed_dir or seed_root()
    # Pure validators first.
    _validate_full(seed_dir)
    corpus = build_corpus(seed_dir)
    url = _resolve_database_url()
    if not url:
        raise RuntimeError(
            "load requires DATABASE_URL or DB_SECRET_ARN to be set"
        )
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for load; install ao-radar[mcp]"
        ) from exc

    conn = psycopg.connect(url)
    try:
        with conn:  # transaction
            _check_connection_guard(conn)
            if reset:
                _delete_seeded(conn)
            _insert_corpus(conn, corpus)
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops.seed.load")
    parser.add_argument("--reset", action="store_true",
                        help="delete only canonical seeded IDs before insert")
    parser.add_argument("--seed-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        run_load(reset=args.reset, seed_dir=args.seed_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
