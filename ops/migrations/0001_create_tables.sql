-- AO Radar persistence schema: Phase 1 (Postgres 16).
--
-- Implements docs/schema-implementation-plan.md section 5.
-- This migration creates tables, primary keys, foreign keys, NOT NULL columns,
-- and default timestamps. CHECK constraints and indexes land in 0002.
--
-- The schema deliberately omits dts_status, payment_status, disbursement_status,
-- certification_status, paid_amount, and any other column that could imply
-- official action, payability, or external contact (docs/spec.md sections 3.3,
-- 4.3 and docs/schema-implementation-plan.md sections 2 and 6.4).
--
-- This file does NOT contain explicit BEGIN/COMMIT; the migration runner
-- wraps each file in a single transaction so file body + schema_migrations
-- insert commit atomically.

-- ---------------------------------------------------------------------------
-- schema_migrations: idempotency tracking for ops/scripts/run_migrations.py.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- policy_citations: read-only synthetic demo reference corpus.
-- ---------------------------------------------------------------------------
CREATE TABLE policy_citations (
    citation_id         TEXT PRIMARY KEY,
    source_identifier   TEXT NOT NULL,
    topic               TEXT NOT NULL,
    excerpt_text        TEXT NOT NULL,
    retrieval_anchor    TEXT NOT NULL,
    applicability_note  TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- travelers: synthetic profile (no real PII; demo markers required).
-- ---------------------------------------------------------------------------
CREATE TABLE travelers (
    traveler_id              TEXT PRIMARY KEY,
    display_name             TEXT NOT NULL,
    role_label               TEXT NOT NULL,
    home_unit_label          TEXT NOT NULL,
    typical_trip_pattern     TEXT NOT NULL,
    prior_correction_summary TEXT NOT NULL,
    data_environment         TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- prior_voucher_summaries: synthetic per-traveler baseline summaries.
-- ---------------------------------------------------------------------------
CREATE TABLE prior_voucher_summaries (
    prior_summary_id             TEXT PRIMARY KEY,
    traveler_id                  TEXT NOT NULL REFERENCES travelers(traveler_id),
    period_label                 TEXT NOT NULL,
    summary_text                 TEXT NOT NULL,
    recurring_correction_pattern TEXT,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- vouchers: synthetic packet anchor. No official-state columns.
-- ---------------------------------------------------------------------------
CREATE TABLE vouchers (
    voucher_id                 TEXT PRIMARY KEY,
    traveler_id                TEXT NOT NULL REFERENCES travelers(traveler_id),
    trip_purpose_category      TEXT NOT NULL,
    trip_start_date            DATE NOT NULL,
    trip_end_date              DATE NOT NULL,
    declared_origin            TEXT NOT NULL,
    declared_destinations      JSONB NOT NULL,
    funding_reference_label    TEXT NOT NULL,
    funding_reference_quality  TEXT NOT NULL,
    justification_text         TEXT NOT NULL,
    pre_existing_flags         JSONB NOT NULL DEFAULT '[]'::JSONB,
    demo_packet_submitted_at   TIMESTAMPTZ NOT NULL,
    review_status              TEXT NOT NULL,
    data_environment           TEXT NOT NULL,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- voucher_line_items: declared expense lines (claimed amounts only).
-- ---------------------------------------------------------------------------
CREATE TABLE voucher_line_items (
    line_item_id                 TEXT PRIMARY KEY,
    voucher_id                   TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    line_index                   INTEGER NOT NULL,
    expense_date                 DATE NOT NULL,
    amount_minor_units           BIGINT NOT NULL,
    currency_code                TEXT NOT NULL,
    exchange_rate_to_usd         NUMERIC(20, 10),
    category                     TEXT NOT NULL,
    vendor_label                 TEXT NOT NULL,
    payment_instrument_indicator TEXT NOT NULL,
    free_text_notes              TEXT NOT NULL DEFAULT '',
    claimed_by_traveler_at       TIMESTAMPTZ NOT NULL
);

-- ---------------------------------------------------------------------------
-- evidence_refs: pointers to attached evidence (line-item or packet-level).
-- ---------------------------------------------------------------------------
CREATE TABLE evidence_refs (
    evidence_ref_id           TEXT PRIMARY KEY,
    voucher_id                TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    line_item_id              TEXT REFERENCES voucher_line_items(line_item_id) ON DELETE CASCADE,
    packet_level_role         TEXT,
    content_type_indicator    TEXT NOT NULL,
    legibility_cue            TEXT NOT NULL,
    itemization_cue           TEXT NOT NULL,
    payment_evidence_cue      TEXT NOT NULL,
    vendor_label_on_evidence  TEXT,
    evidence_date_on_face     DATE,
    amount_on_face_minor_units BIGINT,
    currency_code_on_face     TEXT,
    notes                     TEXT NOT NULL DEFAULT ''
);

-- ---------------------------------------------------------------------------
-- external_anomaly_signals: synthetic review-prompt indicators per voucher.
-- Each row is explicitly NOT an official finding and NOT sufficient for
-- adverse action (docs/spec.md FR-4, AC-14; schema plan section 5.7).
-- ---------------------------------------------------------------------------
CREATE TABLE external_anomaly_signals (
    signal_id                          TEXT PRIMARY KEY,
    voucher_id                         TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    signal_key                         TEXT NOT NULL,
    signal_type                        TEXT NOT NULL,
    synthetic_source_label             TEXT NOT NULL,
    rationale_text                     TEXT NOT NULL,
    confidence                         TEXT NOT NULL,
    is_official_finding                BOOLEAN NOT NULL DEFAULT FALSE,
    not_sufficient_for_adverse_action  BOOLEAN NOT NULL DEFAULT TRUE,
    received_at                        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- story_findings: per-voucher flags / reconstructed-story observations.
-- packet_evidence_pointer is JSONB; the at-least-one-id rule is enforced in
-- migration 0002.
-- ---------------------------------------------------------------------------
CREATE TABLE story_findings (
    finding_id              TEXT PRIMARY KEY,
    voucher_id              TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    category                TEXT NOT NULL,
    severity                TEXT NOT NULL,
    summary                 TEXT NOT NULL,
    explanation             TEXT NOT NULL,
    suggested_question      TEXT NOT NULL,
    packet_evidence_pointer JSONB NOT NULL,
    primary_citation_id     TEXT REFERENCES policy_citations(citation_id),
    confidence              TEXT NOT NULL,
    needs_human_review      BOOLEAN NOT NULL DEFAULT FALSE,
    review_state            TEXT NOT NULL DEFAULT 'open',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- finding_signal_links: many-to-many between story_findings and signals.
-- ---------------------------------------------------------------------------
CREATE TABLE finding_signal_links (
    finding_id  TEXT NOT NULL REFERENCES story_findings(finding_id) ON DELETE CASCADE,
    signal_id   TEXT NOT NULL REFERENCES external_anomaly_signals(signal_id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (finding_id, signal_id)
);

-- ---------------------------------------------------------------------------
-- missing_information_items: explicit gaps; distinct from story_findings.
-- ---------------------------------------------------------------------------
CREATE TABLE missing_information_items (
    missing_item_id          TEXT PRIMARY KEY,
    voucher_id               TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    description              TEXT NOT NULL,
    why_it_matters           TEXT NOT NULL,
    expected_location_hint   TEXT NOT NULL,
    linked_line_item_id      TEXT REFERENCES voucher_line_items(line_item_id) ON DELETE SET NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- review_briefs: fused, versioned pre-decision artifact.
-- ---------------------------------------------------------------------------
CREATE TABLE review_briefs (
    brief_id                       TEXT PRIMARY KEY,
    voucher_id                     TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    version                        INTEGER NOT NULL,
    generated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    priority_score                 NUMERIC(6, 4) NOT NULL,
    priority_rationale             TEXT NOT NULL,
    suggested_focus                TEXT NOT NULL,
    evidence_gap_summary           TEXT NOT NULL,
    story_coherence_summary        TEXT NOT NULL,
    draft_clarification_note       TEXT NOT NULL,
    policy_hooks                   JSONB NOT NULL DEFAULT '[]'::JSONB,
    signal_hooks                   JSONB NOT NULL DEFAULT '[]'::JSONB,
    finding_hooks                  JSONB NOT NULL DEFAULT '[]'::JSONB,
    missing_information_hooks      JSONB NOT NULL DEFAULT '[]'::JSONB,
    brief_uncertainty              TEXT NOT NULL,
    human_authority_boundary_text  TEXT NOT NULL,
    is_partial                     BOOLEAN NOT NULL DEFAULT FALSE,
    partial_reason                 TEXT
);

-- ---------------------------------------------------------------------------
-- ao_notes: typed reviewer-authored or system-drafted internal notes.
-- ---------------------------------------------------------------------------
CREATE TABLE ao_notes (
    note_id              TEXT PRIMARY KEY,
    voucher_id           TEXT NOT NULL REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    finding_id           TEXT REFERENCES story_findings(finding_id) ON DELETE SET NULL,
    kind                 TEXT NOT NULL,
    body                 TEXT NOT NULL,
    actor_label          TEXT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    superseded_by_note_id TEXT REFERENCES ao_notes(note_id)
);

-- ---------------------------------------------------------------------------
-- workflow_events: audit log. Every scoped write/refusal/needs-review label/
-- export creates a row here (docs/spec.md sections 4.5.2, 4.5.4).
-- ---------------------------------------------------------------------------
CREATE TABLE workflow_events (
    event_id                            TEXT PRIMARY KEY,
    voucher_id                          TEXT REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    actor_label                         TEXT NOT NULL,
    occurred_at                         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type                          TEXT NOT NULL,
    tool_name                           TEXT,
    target_kind                         TEXT NOT NULL,
    target_id                           TEXT,
    resulting_status                    TEXT,
    rationale_metadata                  JSONB NOT NULL DEFAULT '{}'::JSONB,
    human_authority_boundary_reminder   TEXT NOT NULL
);
