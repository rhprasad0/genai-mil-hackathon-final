-- AO Radar persistence schema: Phase 2 (Postgres 16).
--
-- Implements docs/schema-implementation-plan.md section 6 (enums + blocked
-- status CHECKs) plus the per-table indexes called out in section 5. This
-- migration is forward-only and intentionally separate from 0001 so the
-- table create step is reviewable in isolation.
--
-- Conventions:
--   * Status-like fields get hard CHECKs (section 6.4). Free-text columns do
--     NOT receive a coarse blocked-word CHECK; that is the fixture validator's
--     responsibility (owned by the synthetic-data teammate).
--   * The boundary-text CHECKs on review_briefs and workflow_events test for
--     the keyword + negation presence required by
--     src/ao_radar_mcp/safety/authority_boundary.py. They are intentionally
--     not free-text wording filters; they assert clause coverage only.
--
-- The blocklist applied to vouchers.review_status, story_findings.review_state,
-- and workflow_events.resulting_status mirrors schema plan section 6.4 exactly.
--
-- This file does NOT contain explicit BEGIN/COMMIT; the migration runner wraps
-- each file in a single transaction so file body + schema_migrations insert
-- commit atomically.

-- ===========================================================================
-- travelers
-- ===========================================================================
ALTER TABLE travelers
    ADD CONSTRAINT travelers_data_environment_synthetic_demo
        CHECK (data_environment = 'synthetic_demo');

ALTER TABLE travelers
    ADD CONSTRAINT travelers_display_name_synthetic_marker
        CHECK (
            display_name LIKE '%(Synthetic Demo)%'
            OR display_name LIKE 'DEMO-%'
            OR display_name LIKE 'Demo %'
        );

-- ===========================================================================
-- vouchers
-- ===========================================================================
ALTER TABLE vouchers
    ADD CONSTRAINT vouchers_data_environment_synthetic_demo
        CHECK (data_environment = 'synthetic_demo');

ALTER TABLE vouchers
    ADD CONSTRAINT vouchers_funding_reference_quality_enum
        CHECK (funding_reference_quality IN ('clean', 'ambiguous', 'unparseable'));

ALTER TABLE vouchers
    ADD CONSTRAINT vouchers_trip_dates_ordered
        CHECK (trip_end_date >= trip_start_date);

-- Allowed review_status values, schema plan section 6.1.
ALTER TABLE vouchers
    ADD CONSTRAINT vouchers_review_status_allowed
        CHECK (review_status IN (
            'needs_review',
            'in_review',
            'awaiting_traveler_clarification',
            'ready_for_human_decision',
            'closed_in_demo'
        ));

-- Hard blocklist (schema plan section 6.4). Belt-and-suspenders: the allowed
-- list above already implies rejection of these values; the explicit blocklist
-- preserves intent if the allowed enum is ever extended.
ALTER TABLE vouchers
    ADD CONSTRAINT vouchers_review_status_blocklist
        CHECK (review_status NOT IN (
            'approved', 'approve',
            'denied', 'deny', 'rejected', 'reject',
            'certified', 'certify',
            'submitted', 'submit', 'submitted_to_dts',
            'returned', 'return', 'return_voucher', 'officially_returned',
            'cancelled', 'canceled', 'cancel',
            'amended', 'amend',
            'paid', 'payable', 'nonpayable', 'ready_for_payment', 'payment_ready',
            'fraud', 'fraudulent', 'misuse', 'abuse', 'misconduct',
            'entitled', 'entitlement_determined',
            'escalated_to_investigators', 'notify_command', 'contact_traveler'
        ));

-- ===========================================================================
-- voucher_line_items
-- ===========================================================================
ALTER TABLE voucher_line_items
    ADD CONSTRAINT voucher_line_items_amount_nonneg
        CHECK (amount_minor_units >= 0);

ALTER TABLE voucher_line_items
    ADD CONSTRAINT voucher_line_items_currency_requires_rate
        CHECK (
            currency_code = 'USD'
            OR exchange_rate_to_usd IS NOT NULL
        );

ALTER TABLE voucher_line_items
    ADD CONSTRAINT voucher_line_items_category_enum
        CHECK (category IN (
            'lodging',
            'transport_air',
            'transport_ground',
            'meals',
            'incidentals',
            'cash_atm',
            'currency_exchange',
            'other_demo'
        ));

ALTER TABLE voucher_line_items
    ADD CONSTRAINT voucher_line_items_payment_instrument_enum
        CHECK (payment_instrument_indicator IN (
            'gtcc_like_demo',
            'personal_card_demo',
            'cash_demo',
            'unknown_demo'
        ));

-- ===========================================================================
-- evidence_refs
-- ===========================================================================
ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_packet_or_line_item
        CHECK (
            line_item_id IS NOT NULL
            OR packet_level_role IS NOT NULL
        );

ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_packet_level_role_enum
        CHECK (
            packet_level_role IS NULL
            OR packet_level_role IN (
                'trip_itinerary',
                'authorization_snapshot',
                'packet_justification',
                'funding_reference_attachment',
                'none_attached_summary'
            )
        );

ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_content_type_enum
        CHECK (content_type_indicator IN (
            'receipt_image_demo',
            'receipt_pdf_demo',
            'itinerary_pdf_demo',
            'boarding_pass_image_demo',
            'handwritten_local_paper_demo',
            'email_confirmation_text_demo',
            'none_attached_demo'
        ));

ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_legibility_cue_enum
        CHECK (legibility_cue IN ('clear', 'partial', 'poor', 'not_applicable'));

ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_itemization_cue_enum
        CHECK (itemization_cue IN (
            'itemized', 'partially_itemized', 'not_itemized', 'not_applicable'
        ));

ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_payment_evidence_cue_enum
        CHECK (payment_evidence_cue IN ('present', 'absent', 'ambiguous', 'not_applicable'));

-- When content_type_indicator = none_attached_demo, every cue must be
-- not_applicable (schema plan section 5.4).
ALTER TABLE evidence_refs
    ADD CONSTRAINT evidence_refs_none_attached_forces_na_cues
        CHECK (
            content_type_indicator <> 'none_attached_demo'
            OR (
                legibility_cue = 'not_applicable'
                AND itemization_cue = 'not_applicable'
                AND payment_evidence_cue = 'not_applicable'
            )
        );

-- ===========================================================================
-- policy_citations
-- ===========================================================================
ALTER TABLE policy_citations
    ADD CONSTRAINT policy_citations_topic_enum
        CHECK (topic IN (
            'valid_receipt',
            'lodging_documentation',
            'transportation_documentation',
            'cash_atm_reconstruction',
            'currency_exchange',
            'funding_reference_format',
            'duplicate_charge_review',
            'date_window_coherence',
            'oconus_vendor_edge',
            'general_review_checklist'
        ));

ALTER TABLE policy_citations
    ADD CONSTRAINT policy_citations_synthetic_source_prefix
        CHECK (
            source_identifier LIKE 'synthetic_dtmo_checklist_demo_%'
            OR source_identifier LIKE 'synthetic_demo_reference_%'
        );

-- ===========================================================================
-- external_anomaly_signals
-- ===========================================================================
ALTER TABLE external_anomaly_signals
    ADD CONSTRAINT external_anomaly_signals_signal_type_enum
        CHECK (signal_type IN (
            'duplicate_payment_risk',
            'high_risk_mcc_demo',
            'unusual_amount',
            'date_location_mismatch',
            'split_disbursement_oddity',
            'repeated_correction_pattern',
            'peer_baseline_outlier',
            'traveler_baseline_outlier'
        ));

ALTER TABLE external_anomaly_signals
    ADD CONSTRAINT external_anomaly_signals_confidence_enum
        CHECK (confidence IN ('low', 'medium', 'high'));

ALTER TABLE external_anomaly_signals
    ADD CONSTRAINT external_anomaly_signals_not_official_finding
        CHECK (is_official_finding = FALSE);

ALTER TABLE external_anomaly_signals
    ADD CONSTRAINT external_anomaly_signals_not_sufficient_for_adverse
        CHECK (not_sufficient_for_adverse_action = TRUE);

-- ===========================================================================
-- story_findings
-- ===========================================================================
ALTER TABLE story_findings
    ADD CONSTRAINT story_findings_category_enum
        CHECK (category IN (
            'missing_receipt',
            'weak_or_local_paper_receipt',
            'amount_mismatch',
            'duplicate_or_multiple_charge',
            'ambiguous_loa_or_funding_reference',
            'cash_atm_or_exchange_reconstruction',
            'stale_memory_old_transaction',
            'forced_audit_receipt_review',
            'paperwork_or_math_inconsistency',
            'unclear_or_possibly_unjustified_expense',
            'date_window_mismatch',
            'location_mismatch',
            'miscategorized_line_item',
            'insufficient_evidence_overall',
            'oconus_vendor_edge_case',
            'evidence_quality_concern',
            'story_coherence_break'
        ));

ALTER TABLE story_findings
    ADD CONSTRAINT story_findings_severity_enum
        CHECK (severity IN ('info', 'low', 'medium', 'high'));

ALTER TABLE story_findings
    ADD CONSTRAINT story_findings_confidence_enum
        CHECK (confidence IN ('low', 'medium', 'high'));

-- Allowed review_state, schema plan section 6.3.
ALTER TABLE story_findings
    ADD CONSTRAINT story_findings_review_state_allowed
        CHECK (review_state IN (
            'open',
            'reviewed_explained',
            'reviewed_unresolved',
            'needs_followup'
        ));

-- Schema plan section 6.4 blocklist.
ALTER TABLE story_findings
    ADD CONSTRAINT story_findings_review_state_blocklist
        CHECK (review_state NOT IN (
            'approved', 'approve',
            'denied', 'deny', 'rejected', 'reject',
            'certified', 'certify',
            'submitted', 'submit', 'submitted_to_dts',
            'returned', 'return', 'return_voucher', 'officially_returned',
            'cancelled', 'canceled', 'cancel',
            'amended', 'amend',
            'paid', 'payable', 'nonpayable', 'ready_for_payment', 'payment_ready',
            'fraud', 'fraudulent', 'misuse', 'abuse', 'misconduct',
            'entitled', 'entitlement_determined',
            'escalated_to_investigators', 'notify_command', 'contact_traveler'
        ));

-- packet_evidence_pointer must include at least one of line_item_id or
-- evidence_ref_id (TR-5; schema plan section 5.8).
ALTER TABLE story_findings
    ADD CONSTRAINT story_findings_packet_pointer_has_id
        CHECK (
            (packet_evidence_pointer ? 'line_item_id'
                AND jsonb_typeof(packet_evidence_pointer -> 'line_item_id') = 'string')
            OR (packet_evidence_pointer ? 'evidence_ref_id'
                AND jsonb_typeof(packet_evidence_pointer -> 'evidence_ref_id') = 'string')
        );

-- ===========================================================================
-- review_briefs
-- ===========================================================================
ALTER TABLE review_briefs
    ADD CONSTRAINT review_briefs_voucher_version_unique
        UNIQUE (voucher_id, version);

ALTER TABLE review_briefs
    ADD CONSTRAINT review_briefs_brief_uncertainty_enum
        CHECK (brief_uncertainty IN ('low', 'medium', 'high'));

-- Boundary text CHECK: must contain each required action verb plus a negation
-- marker. Mirrors src/ao_radar_mcp/safety/authority_boundary.py and schema
-- plan section 6.6 (which permits longer approved variants that still cover
-- every clause).
ALTER TABLE review_briefs
    ADD CONSTRAINT review_briefs_boundary_text_clauses
        CHECK (
            POSITION('approve' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('deny' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('certify' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('return' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('cancel' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('amend' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('submit' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('entitlement' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('payability' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('fraud' IN LOWER(human_authority_boundary_text)) > 0
            AND POSITION('external' IN LOWER(human_authority_boundary_text)) > 0
            AND (
                POSITION('not' IN LOWER(human_authority_boundary_text)) > 0
                OR POSITION('no ' IN LOWER(human_authority_boundary_text)) > 0
            )
        );

-- ===========================================================================
-- ao_notes
-- ===========================================================================
ALTER TABLE ao_notes
    ADD CONSTRAINT ao_notes_kind_enum
        CHECK (kind IN (
            'ao_note',
            'draft_clarification',
            'synthetic_clarification_request',
            'ao_feedback'
        ));

-- ===========================================================================
-- workflow_events
-- ===========================================================================
ALTER TABLE workflow_events
    ADD CONSTRAINT workflow_events_event_type_enum
        CHECK (event_type IN (
            'scoped_write',
            'refusal',
            'needs_human_review_label',
            'retrieval',
            'generation',
            'edit',
            'export'
        ));

ALTER TABLE workflow_events
    ADD CONSTRAINT workflow_events_target_kind_enum
        CHECK (target_kind IN (
            'voucher', 'finding', 'note', 'brief', 'signal',
            'citation', 'missing_item', 'none'
        ));

ALTER TABLE workflow_events
    ADD CONSTRAINT workflow_events_scoped_write_requires_tool
        CHECK (
            event_type <> 'scoped_write'
            OR tool_name IS NOT NULL
        );

-- resulting_status, when set, must be a value from either the voucher allowed
-- list (section 6.1) or the finding-review allowed list (section 6.3).
ALTER TABLE workflow_events
    ADD CONSTRAINT workflow_events_resulting_status_allowed
        CHECK (
            resulting_status IS NULL
            OR resulting_status IN (
                -- vouchers.review_status (section 6.1)
                'needs_review',
                'in_review',
                'awaiting_traveler_clarification',
                'ready_for_human_decision',
                'closed_in_demo',
                -- story_findings.review_state (section 6.3)
                'open',
                'reviewed_explained',
                'reviewed_unresolved',
                'needs_followup'
            )
        );

-- Schema plan section 6.4 blocklist applied independently.
ALTER TABLE workflow_events
    ADD CONSTRAINT workflow_events_resulting_status_blocklist
        CHECK (
            resulting_status IS NULL
            OR resulting_status NOT IN (
                'approved', 'approve',
                'denied', 'deny', 'rejected', 'reject',
                'certified', 'certify',
                'submitted', 'submit', 'submitted_to_dts',
                'returned', 'return', 'return_voucher', 'officially_returned',
                'cancelled', 'canceled', 'cancel',
                'amended', 'amend',
                'paid', 'payable', 'nonpayable', 'ready_for_payment', 'payment_ready',
                'fraud', 'fraudulent', 'misuse', 'abuse', 'misconduct',
                'entitled', 'entitlement_determined',
                'escalated_to_investigators', 'notify_command', 'contact_traveler'
            )
        );

-- Boundary reminder must contain each required clause + a negation marker.
ALTER TABLE workflow_events
    ADD CONSTRAINT workflow_events_boundary_reminder_clauses
        CHECK (
            POSITION('approve' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('deny' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('certify' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('return' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('cancel' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('amend' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('submit' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('entitlement' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('payability' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('fraud' IN LOWER(human_authority_boundary_reminder)) > 0
            AND POSITION('external' IN LOWER(human_authority_boundary_reminder)) > 0
            AND (
                POSITION('not' IN LOWER(human_authority_boundary_reminder)) > 0
                OR POSITION('no ' IN LOWER(human_authority_boundary_reminder)) > 0
            )
        );

-- ===========================================================================
-- Indexes
-- ===========================================================================

-- travelers: only PK index needed at hackathon scale.

-- prior_voucher_summaries
CREATE INDEX prior_voucher_summaries_traveler_id_idx
    ON prior_voucher_summaries (traveler_id);

-- vouchers
CREATE INDEX vouchers_traveler_id_idx
    ON vouchers (traveler_id);

CREATE INDEX vouchers_review_status_open_idx
    ON vouchers (review_status)
    WHERE review_status IN (
        'needs_review',
        'in_review',
        'awaiting_traveler_clarification',
        'ready_for_human_decision'
    );

CREATE INDEX vouchers_demo_packet_submitted_at_idx
    ON vouchers (demo_packet_submitted_at);

-- voucher_line_items
CREATE INDEX voucher_line_items_voucher_id_idx
    ON voucher_line_items (voucher_id);

CREATE UNIQUE INDEX voucher_line_items_voucher_line_index_uidx
    ON voucher_line_items (voucher_id, line_index);

CREATE INDEX voucher_line_items_expense_date_idx
    ON voucher_line_items (expense_date);

-- evidence_refs
CREATE INDEX evidence_refs_voucher_id_idx
    ON evidence_refs (voucher_id);

CREATE INDEX evidence_refs_line_item_id_idx
    ON evidence_refs (line_item_id);

-- policy_citations
CREATE INDEX policy_citations_topic_idx
    ON policy_citations (topic);

-- external_anomaly_signals
CREATE INDEX external_anomaly_signals_voucher_id_idx
    ON external_anomaly_signals (voucher_id);

CREATE INDEX external_anomaly_signals_signal_type_idx
    ON external_anomaly_signals (signal_type);

CREATE UNIQUE INDEX external_anomaly_signals_voucher_signal_key_uidx
    ON external_anomaly_signals (voucher_id, signal_key);

-- story_findings
CREATE INDEX story_findings_voucher_id_idx
    ON story_findings (voucher_id);

CREATE INDEX story_findings_category_idx
    ON story_findings (category);

CREATE INDEX story_findings_voucher_severity_idx
    ON story_findings (voucher_id, severity);

CREATE INDEX story_findings_needs_human_review_idx
    ON story_findings (voucher_id)
    WHERE needs_human_review = TRUE;

-- missing_information_items
CREATE INDEX missing_information_items_voucher_id_idx
    ON missing_information_items (voucher_id);

-- review_briefs
CREATE INDEX review_briefs_voucher_id_idx
    ON review_briefs (voucher_id);

-- ao_notes
CREATE INDEX ao_notes_voucher_id_idx
    ON ao_notes (voucher_id);

CREATE INDEX ao_notes_voucher_kind_idx
    ON ao_notes (voucher_id, kind);

-- workflow_events
CREATE INDEX workflow_events_voucher_id_idx
    ON workflow_events (voucher_id);

CREATE INDEX workflow_events_voucher_occurred_at_idx
    ON workflow_events (voucher_id, occurred_at);

CREATE INDEX workflow_events_event_type_idx
    ON workflow_events (event_type);
