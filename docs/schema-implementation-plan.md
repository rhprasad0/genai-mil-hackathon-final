# AO Radar Schema Implementation Plan

A coding-agent-ready plan for the persistence layer that supports the AO Radar
prototype described in `docs/spec.md`. This document is **plan only**: it does
not introduce migrations, application code, or any commitments to a specific
database product. It is written so that a downstream coding agent can take the
plan, choose a concrete database, and produce migrations, seed fixtures, a
scoped data-access layer, and tests without re-deriving any of the design
decisions here.

The plan incorporates sanitized practitioner-derived observations about how
travel voucher review actually fails in practice, expressed entirely as
synthetic example shapes. No private notes, real PII, real GTCC data, real
units, real travelers, real vendors, or real LOA strings appear anywhere in
this document or in any seed scenario it prescribes.

---

## 1. Title and Purpose

**Title:** AO Radar persistence schema implementation plan (hackathon scope).

**Purpose:** Define the entities, relationships, constraints, controlled
vocabularies, seed scenarios, and implementation phases needed to back the
scoped domain workflow tools enumerated in `docs/spec.md` section 4.5. The
schema must:

- Support a single-reviewer, single-packet pre-decision review brief end to end.
- Make the prohibited-action set in `docs/spec.md` section 4.3 a **hard,
  schema-level constraint**, not a runtime convenience.
- Make every workflow write produce an audit event by construction.
- Carry only synthetic, clearly fictional data, with that constraint expressed
  in the schema rather than in conventions.
- Stay simple enough to seed, demo, and reset cleanly inside hackathon scope.

The reader of this document is the coding agent that will implement the schema
next. Bias the work toward concrete, testable artifacts.

---

## 2. Scope and Non-Goals

### In scope for the schema layer

- Tables, columns, primary keys, foreign keys, check constraints, and indexes
  for the twelve baseline entities plus a small number of recommended
  additions called out as gaps below.
- Controlled enumerations for review status, finding category, finding review
  state, signal type, evidence cue type, workflow event type, and refusal
  reason.
- Synthetic seed fixtures covering the scenarios listed in section 7.
- A scoped data-access layer contract that can be wired directly to the
  domain workflow tools in `docs/spec.md` section 4.5.
- A test plan that validates constraints, audit-event coupling, refusal
  logging, brief assembly, and absence of any generic data-access tool.

### Out of scope

- Choosing a specific database product, ORM, migration tool, or hosting
  environment. The plan is implementation-neutral; the coding agent decides.
- The retrieval pipeline, the reasoning component, and the reviewer-facing
  surface, except where their inputs and outputs touch the schema.
- Any integration with the real Defense Travel System, real GTCC data, real
  bank routing, or any external party.
- Authentication, authorization, deployment hardening, and post-competition
  threat-model work. Those are explicitly deferred per the repository README
  and `docs/spec.md`.
- Any feature that would let the system approve, deny, certify, return,
  cancel, amend, submit, determine entitlement, modify amounts, accuse fraud,
  or contact external parties. The schema must make those impossible to
  represent.

---

## 3. Spec Alignment Summary

The schema is responsible for backing the following spec sections and
requirements. Every table in section 5 cites which of these it supports.

- **Data objects** (`docs/spec.md` section 3.7): voucher packet, trip metadata,
  line item, attached evidence reference, reference excerpt, traveler profile,
  prior voucher summary, external anomaly signal, reconstructed story, flag,
  missing-information item, needs-human-review item, draft clarification note,
  review brief, internal review status, workflow write, audit entry.
- **Functional requirements** FR-1 through FR-16, with particular emphasis on
  FR-5 (controlled reference retrieval), FR-6 (missing-information detection),
  FR-8 (provenance and confidence), FR-11 (audit log), FR-13
  (needs-human-review state), FR-14 (fused brief), FR-15 (scoped writes), and
  FR-16 (controlled review statuses).
- **Workflow action contract** (`docs/spec.md` section 4): permitted reads
  (4.1), permitted scoped writes (4.2 and 4.5.2), prohibited actions (4.3),
  refusal behavior (4.4), tool catalog (4.5), controlled internal review
  statuses (4.5.3), and audit event shape (4.5.4).
- **Trust and safety requirements** TR-1 through TR-12, with particular
  emphasis on TR-1 (no official action), TR-3 (no fraud allegation), TR-5
  (provenance on every flag), TR-8 (synthetic-only), TR-9 (auditability), and
  TR-12 (no generic data access).
- **Acceptance criteria** AC-1 through AC-16, especially AC-2 (provenance),
  AC-3 (missing-information listing), AC-5 (visible uncertainty), AC-6 and
  AC-7 (refusal), AC-10 (audit trail), AC-13 (needs human review), AC-14
  (three-layer demo boundary), AC-15 (fusion tool, no raw SQL), and AC-16
  (controlled workflow writes).

The schema deliberately does not model official DTS state, payment status,
disbursement, entitlement determinations, or any external contact channel.
Those concepts are absent by design so that the implementation cannot drift
across the trust boundary.

---

## 4. ERD / Entity Overview

```
travelers (1) ────< (M) vouchers
   │                     │
   │                     ├──< (M) voucher_line_items
   │                     │         │
   │                     │         └──< (M) evidence_refs
   │                     │                  (also packet-level, line_item_id NULL)
   │                     │
   │                     ├──< (M) external_anomaly_signals
   │                     ├──< (M) story_findings  >── (M:1) policy_citations
   │                     │         │
   │                     │         └──< (M) finding_signal_links >── external_anomaly_signals
   │                     │
   │                     ├──< (M) missing_information_items
   │                     ├──< (M) review_briefs        (versioned per voucher)
   │                     ├──< (M) ao_notes              (typed by note kind)
   │                     └──< (M) workflow_events       (audit log + scoped writes)
   │
   └──< (M) prior_voucher_summaries

policy_citations  (corpus, read-only at runtime)
```

### Why each table exists

- **travelers** — synthetic profile a packet can be compared against. Holds
  role label, typical-trip-pattern hints, and prior-correction summary text.
  Spec section 3.7, FR baseline for traveler context.
- **vouchers** — the synthetic packet itself: declared trip metadata, funding
  reference, justification text, internal review status, pre-existing flag
  notes. The single anchor for fusion.
- **voucher_line_items** — declared expense lines (date, amount, category,
  vendor identifier, payment instrument indicator, free-text notes). The unit
  of evidence-quality assessment.
- **evidence_refs** — pointers to attached supporting evidence with cue
  annotations (legibility, itemization, payment-evidence). Can be tied to a
  line item or to the packet.
- **prior_voucher_summaries** — short synthetic summaries of earlier vouchers
  for the same traveler, used for baseline comparison only. No intent
  inference.
- **policy_citations** — the approved reference repository as data:
  source identifier, verbatim excerpt text, retrieval anchor, applicability
  note. Read-only at runtime.
- **external_anomaly_signals** — synthetic risk indicators per voucher with
  type, rationale, synthetic source label, confidence, and an explicit
  not-an-official-finding marker.
- **story_findings** — the system's per-voucher flags and reconstructed-story
  observations: category, severity, in-packet pointer, optional citation,
  confidence, needs-human-review state, finding review state, suggested
  question. Joins to citations and to signals.
- **missing_information_items** — explicit gaps the packet does not currently
  show, kept distinct from flags by design (FR-6).
- **review_briefs** — the fused, versioned pre-decision artifact emitted by
  `prepare_ao_review_brief(voucher_id)`. Carries the assembled content plus
  the human-authority boundary statement.
- **ao_notes** — typed reviewer-authored or system-drafted internal notes:
  AO note, draft clarification text, AO feedback. Each one is a scoped write.
- **workflow_events** — the audit log. Every scoped write, every retrieval
  worth recording, every refusal, every needs-human-review label, and every
  export records here.

### Recommended additions called out as gaps

These come out of the spec data-object list (section 3.7) and the workflow
contract (sections 4.5.2 and 4.5.4). They are small, but the baseline list
does not name them explicitly. They are described once here and revisited
under section 5.13.

- **finding_signal_links** — many-to-many between `story_findings` and
  `external_anomaly_signals`. A flag often draws on several signals; a signal
  may inform several flags.
- A typed `kind` column on **ao_notes** so AO notes, draft clarification
  notes, and AO feedback share one shape without losing their distinct
  semantics. This avoids inventing two more tables for hackathon scope.
- A `data_environment` column on **travelers** and **vouchers** with a CHECK
  constraint allowing only `synthetic_demo`. This expresses TR-8 in the
  schema instead of in a code comment.

---

## 5. Table-by-Table Implementation Plan

For each table: purpose, key columns, important constraints/checks, indexes,
seed-data role, and spec alignment notes. Column types are described
abstractly (text, integer, decimal, timestamp, boolean, enum, json) so the
coding agent can pick concrete types for the chosen database.

### 5.1 travelers

- **Purpose:** synthetic traveler profile used as a baseline-comparison input
  for story reconstruction and queue prioritization. No real PII.
- **Key columns:**
  - `traveler_id` (text, PK, e.g. `T-101`)
  - `display_name` (text, clearly fictional)
  - `role_label` (text, e.g. `staff_nco_demo`, `field_grade_demo`)
  - `home_unit_label` (text, clearly fictional, e.g.
    `1st Synthetic Logistics Detachment (Demo)`)
  - `typical_trip_pattern` (text, free-form synthetic context)
  - `prior_correction_summary` (text, synthetic narrative of typical past
    correction patterns at the profile level only — never per-incident detail)
  - `data_environment` (text, must equal `synthetic_demo`)
  - `created_at` (timestamp)
- **Constraints / checks:**
  - `data_environment` CHECK equals `synthetic_demo`.
  - `display_name` CHECK includes a clearly-synthetic marker substring (for
    example, the suffix `(Demo)` or a `DEMO-` prefix). This is belt-and-
    suspenders against accidental real-name seeding.
- **Indexes:** PK on `traveler_id`. No others required at hackathon scale.
- **Seed-data role:** five to six profiles spanning role and trip-pattern
  diversity, including a deliberately clean baseline profile and a profile
  with prior-correction history. See section 7.
- **Spec alignment:** section 3.7 (Traveler Profile), FR-1 input shape, TR-8
  synthetic-only.

### 5.2 vouchers

- **Purpose:** the synthetic packet anchor. Holds declared trip metadata,
  funding reference, justification text, pre-existing flags, and the
  controlled internal review status that the workflow can advance.
- **Key columns:**
  - `voucher_id` (text, PK, e.g. `V-1003`)
  - `traveler_id` (text, FK → travelers.traveler_id)
  - `trip_purpose_category` (text, e.g. `tdy_conference_demo`,
    `oconus_site_visit_demo`)
  - `trip_start_date` (date)
  - `trip_end_date` (date)
  - `declared_origin` (text, clearly fictional)
  - `declared_destinations` (json array of clearly fictional locations)
  - `funding_reference_label` (text, clearly fictional LOA-shaped string,
    e.g. `LOA-DEMO-FY26-0007`)
  - `funding_reference_quality` (enum: `clean`, `ambiguous`, `unparseable`)
  - `justification_text` (text)
  - `pre_existing_flags` (json array of free-text strings already present on
    the packet at intake)
  - `submitted_at` (timestamp)
  - `review_status` (enum, see section 6.1)
  - `data_environment` (text, must equal `synthetic_demo`)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
- **Constraints / checks:**
  - `review_status` CHECK against the controlled enumeration in section 6.1.
    Any value implying official action (`approved`, `denied`, `certified`,
    `submitted`, `paid`, `fraud`, `returned`, `cancelled`, `amended`, and
    obvious near-synonyms) is rejected.
  - `trip_end_date` ≥ `trip_start_date`.
  - `data_environment` CHECK equals `synthetic_demo`.
  - `funding_reference_quality` CHECK against the small enum above.
- **Indexes:**
  - FK index on `traveler_id`.
  - Partial index on `review_status` for queue listing.
  - Index on `submitted_at` for queue ordering.
- **Seed-data role:** ten to twelve packets covering the scenarios in
  section 7. At least one packet per scenario, with at least two clean
  control packets so the brief comparison is meaningful.
- **Spec alignment:** section 3.7 (Voucher Packet, Trip Metadata, Internal
  Review Status), FR-1, FR-9, FR-16, AC-1, AC-8, AC-12.

### 5.3 voucher_line_items

- **Purpose:** declared expense lines, the unit at which evidence-quality
  assessment and most coherence checks operate.
- **Key columns:**
  - `line_item_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id, ON DELETE CASCADE for
    demo reset semantics; the coding agent may relax this)
  - `line_index` (integer, ordering within the packet)
  - `expense_date` (date)
  - `amount_minor_units` (integer, store in minor units to avoid float math)
  - `currency_code` (text, ISO 4217 style, e.g. `USD`, `EUR`, `JPY`)
  - `exchange_rate_to_usd` (decimal, nullable; required when `currency_code`
    is not `USD`)
  - `category` (enum: `lodging`, `transport_air`, `transport_ground`,
    `meals`, `incidentals`, `cash_atm`, `currency_exchange`, `other_demo`)
  - `vendor_label` (text, clearly fictional, e.g. `Hotel Coastal Demo`)
  - `payment_instrument_indicator` (enum: `gtcc_like_demo`, `personal_card_demo`,
    `cash_demo`, `unknown_demo`)
  - `free_text_notes` (text)
  - `claimed_by_traveler_at` (timestamp; this is when the traveler entered
    it on the packet, distinct from `expense_date`)
- **Constraints / checks:**
  - `amount_minor_units` ≥ 0.
  - `exchange_rate_to_usd` IS NOT NULL when `currency_code` ≠ `USD`.
  - `category`, `payment_instrument_indicator` CHECK against their enums.
- **Indexes:**
  - FK index on `voucher_id`.
  - Composite index on (`voucher_id`, `line_index`).
  - Index on `expense_date` for trip-window coherence checks.
- **Seed-data role:** every voucher has between four and twelve line items,
  with deliberate edge cases per scenario (mis-categorized lines, foreign
  currency lines, ATM lines, duplicates).
- **Spec alignment:** section 3.7 (Line Item), FR-3, FR-4, FR-8.

### 5.4 evidence_refs

- **Purpose:** pointers to attached supporting evidence and the cue
  annotations the evidence-quality assessment depends on. May be attached to
  a single line item or to the packet as a whole.
- **Key columns:**
  - `evidence_ref_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id)
  - `line_item_id` (text, nullable, FK → voucher_line_items.line_item_id)
  - `content_type_indicator` (enum: `receipt_image_demo`,
    `receipt_pdf_demo`, `itinerary_pdf_demo`, `boarding_pass_image_demo`,
    `handwritten_local_paper_demo`, `email_confirmation_text_demo`,
    `none_attached_demo`)
  - `legibility_cue` (enum: `clear`, `partial`, `poor`, `not_applicable`)
  - `itemization_cue` (enum: `itemized`, `partially_itemized`,
    `not_itemized`, `not_applicable`)
  - `payment_evidence_cue` (enum: `present`, `absent`, `ambiguous`,
    `not_applicable`)
  - `vendor_label_on_evidence` (text, nullable; for cross-check with line
    item vendor)
  - `evidence_date_on_face` (date, nullable; for trip-window check)
  - `amount_on_face_minor_units` (integer, nullable; for amount-mismatch
    check)
  - `currency_code_on_face` (text, nullable)
  - `notes` (text)
- **Constraints / checks:**
  - At least one of (`line_item_id` IS NOT NULL) OR (a documented
    packet-level role) — packet-level evidence is allowed but should be the
    minority of rows.
  - `content_type_indicator` and the three cue columns CHECK against their
    enums.
  - When `content_type_indicator` = `none_attached_demo`, the cue columns
    must equal `not_applicable`.
- **Indexes:**
  - FK indexes on `voucher_id` and on `line_item_id`.
- **Seed-data role:** the evidence layer is where most of the messiness in
  section 7 lives. Some rows deliberately have `none_attached_demo`, some
  carry `handwritten_local_paper_demo` with `legibility_cue = poor`, some
  have a `vendor_label_on_evidence` that disagrees with the line item, and
  some have an `evidence_date_on_face` that falls outside the trip window.
- **Spec alignment:** section 3.7 (Attached Evidence Reference), FR-3, FR-4,
  AC-2.

### 5.5 prior_voucher_summaries

- **Purpose:** synthetic short summaries of the same traveler's earlier
  vouchers, for baseline comparison only. The system uses these to recognize
  repeated correction patterns; it must not infer intent.
- **Key columns:**
  - `prior_summary_id` (text, PK)
  - `traveler_id` (text, FK → travelers.traveler_id)
  - `period_label` (text, e.g. `prior_demo_fy25_q3`)
  - `summary_text` (text, neutral, no fraud language)
  - `recurring_correction_pattern` (text, nullable, neutral phrasing such as
    `evidence-attachment gap on lodging line` — never `fraud`, never
    `misuse`)
  - `created_at` (timestamp)
- **Constraints / checks:**
  - CHECK that `summary_text` and `recurring_correction_pattern` do not
    contain prohibited vocabulary tokens (see section 6.4). Even at the
    schema layer this is a useful belt-and-suspenders guard for seed data.
- **Indexes:** FK index on `traveler_id`.
- **Seed-data role:** zero, one, or two prior summaries per traveler. At
  least one traveler with a recurring evidence-attachment pattern; at least
  one traveler with an empty prior history (cold-start case).
- **Spec alignment:** section 3.7 (Prior Voucher Summary), FR-1, TR-3.

### 5.6 policy_citations

- **Purpose:** the approved reference repository as data. Read-only at
  runtime. Excerpts are stored verbatim with a source identifier and an
  applicability note so that flags can cite without paraphrasing.
- **Key columns:**
  - `citation_id` (text, PK, e.g. `CITE-RECEIPT-001`)
  - `source_identifier` (text, e.g. `synthetic_dtmo_checklist_demo_v1`)
  - `topic` (enum: `valid_receipt`, `lodging_documentation`,
    `transportation_documentation`, `cash_atm_reconstruction`,
    `currency_exchange`, `funding_reference_format`,
    `duplicate_charge_review`, `date_window_coherence`, `oconus_vendor_edge`,
    `general_review_checklist`)
  - `excerpt_text` (text, verbatim)
  - `retrieval_anchor` (text, a search-friendly summary the retriever can
    match against)
  - `applicability_note` (text, neutral guidance on when the excerpt
    applies)
  - `created_at` (timestamp)
- **Constraints / checks:**
  - `topic` CHECK against the enum.
  - CHECK that `excerpt_text` does not contain prohibited vocabulary tokens
    (section 6.4); the corpus must never carry fraud or
    official-disposition language.
- **Indexes:**
  - Index on `topic`.
  - Optional full-text or trigram index on `retrieval_anchor` if the chosen
    database supports one cheaply. Not required for the demo.
- **Seed-data role:** a small but topic-complete synthetic corpus, written
  in the spirit of public DoD travel guidance but invented and clearly
  marked synthetic. Each topic in the enum gets at least one citation. The
  corpus must be sufficient to ground every flag category that the seed
  scenarios exercise.
- **Spec alignment:** section 3.7 (Reference Excerpt), FR-5, FR-8, NFR-3
  (grounding discipline), TR-5, TR-6, AC-2.

### 5.7 external_anomaly_signals

- **Purpose:** synthetic review-prompt indicators from a stand-in compliance
  or anomaly service. Each row is explicitly framed as a review prompt, not
  an official finding, and not sufficient for adverse action.
- **Key columns:**
  - `signal_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id)
  - `signal_type` (enum: `duplicate_payment_risk`, `high_risk_mcc_demo`,
    `unusual_amount`, `date_location_mismatch`, `split_disbursement_oddity`,
    `repeated_correction_pattern`, `peer_baseline_outlier`,
    `traveler_baseline_outlier`)
  - `synthetic_source_label` (text, e.g. `synthetic_compliance_service_demo`)
  - `rationale_text` (text)
  - `confidence` (enum: `low`, `medium`, `high`)
  - `is_official_finding` (boolean, CHECK = false)
  - `not_sufficient_for_adverse_action` (boolean, CHECK = true)
  - `received_at` (timestamp)
- **Constraints / checks:**
  - `is_official_finding` CHECK equals false.
  - `not_sufficient_for_adverse_action` CHECK equals true.
  - `signal_type`, `confidence` CHECK against their enums.
- **Indexes:** FK index on `voucher_id`; index on `signal_type`.
- **Seed-data role:** zero to four signals per voucher, with at least one
  voucher carrying multiple signal types so fusion has something to do.
- **Spec alignment:** section 3.7 (External Anomaly Signal), FR-1, FR-4,
  FR-8, TR-3, AC-14.

### 5.8 story_findings

- **Purpose:** the system's per-voucher flags and reconstructed-story
  observations. Carries provenance, confidence, needs-human-review state,
  and finding review state, and is the primary join between packet evidence,
  signals, and citations.
- **Key columns:**
  - `finding_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id)
  - `category` (enum, see section 6.2)
  - `severity` (enum: `info`, `low`, `medium`, `high`)
  - `summary` (text, neutral phrasing)
  - `explanation` (text, plain-language reasoning)
  - `suggested_question` (text, neutral reviewer-prompt language)
  - `packet_evidence_pointer` (json: shape includes optional
    `line_item_id`, optional `evidence_ref_id`, and a free-text
    `excerpt_hint`; at least one of the two ids must be present)
  - `primary_citation_id` (text, nullable, FK → policy_citations.citation_id)
  - `confidence` (enum: `low`, `medium`, `high`)
  - `needs_human_review` (boolean) — distinct from missing-information
  - `review_state` (enum, see section 6.3; default `open`)
  - `created_at` (timestamp)
- **Constraints / checks:**
  - `category`, `severity`, `confidence`, `review_state` CHECK against
    their enums.
  - `packet_evidence_pointer` CHECK that at least one id is present (TR-5).
  - `review_state` value CHECK rejects any value that would imply official
    action; only the enumeration in section 6.3 is allowed.
  - CHECK that `summary`, `explanation`, and `suggested_question` do not
    contain prohibited vocabulary tokens (section 6.4).
- **Indexes:**
  - FK index on `voucher_id`.
  - Index on `category` and `(voucher_id, severity)` for brief assembly.
  - Partial index on `needs_human_review = true`.
- **Seed-data role:** every non-clean voucher in section 7 produces at least
  one finding; the multi-issue vouchers produce three to six. At least one
  finding per scenario carries `needs_human_review = true` so AC-13 is
  demonstrable from seed data alone.
- **Spec alignment:** section 3.7 (Flag, Reconstructed Story,
  Needs-Human-Review Item), FR-2, FR-3, FR-4, FR-8, FR-13, TR-5, TR-7,
  AC-2, AC-5, AC-13.

### 5.9 missing_information_items

- **Purpose:** explicit gaps the packet does not currently show. Distinct
  from `story_findings` so reviewers can list them separately (FR-6, AC-3).
- **Key columns:**
  - `missing_item_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id)
  - `description` (text, what is not present)
  - `why_it_matters` (text)
  - `expected_location_hint` (text, where the reviewer would expect to find
    it: line item, evidence attachment, justification block, funding field)
  - `linked_line_item_id` (text, nullable, FK)
  - `created_at` (timestamp)
- **Constraints / checks:** standard FK constraints; no specific check.
- **Indexes:** FK index on `voucher_id`.
- **Seed-data role:** every messy voucher in section 7 has at least one
  missing-information item; some have several. The missing-receipt voucher
  has multiple, and the OCONUS-vendor edge case has one with a clear
  `expected_location_hint` that the reviewer can use verbatim.
- **Spec alignment:** section 3.7 (Missing-Information Item), FR-6, AC-3.

### 5.10 review_briefs

- **Purpose:** the fused, versioned pre-decision artifact emitted by
  `prepare_ao_review_brief(voucher_id)`. One row per generation. Holds the
  assembled content, the human-authority boundary statement, the brief-level
  uncertainty, and pointers back to all the inputs the brief drew from.
- **Key columns:**
  - `brief_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id)
  - `version` (integer, monotonic per voucher)
  - `generated_at` (timestamp)
  - `priority_score` (decimal, 0–1, workload-guidance only)
  - `priority_rationale` (text, neutral)
  - `suggested_focus` (text, what the reviewer should look at first)
  - `evidence_gap_summary` (text)
  - `story_coherence_summary` (text)
  - `draft_clarification_note` (text, non-official, suitable for adaptation)
  - `policy_hooks` (json array of citation ids actually used)
  - `signal_hooks` (json array of signal ids actually used)
  - `finding_hooks` (json array of finding ids actually used)
  - `missing_information_hooks` (json array of missing_item ids)
  - `brief_uncertainty` (enum: `low`, `medium`, `high`)
  - `human_authority_boundary_text` (text, fixed reminder line; CHECK that
    it is non-empty)
  - `is_partial` (boolean, true when retrieval failed or sources conflict)
  - `partial_reason` (text, nullable)
- **Constraints / checks:**
  - Unique `(voucher_id, version)`.
  - `human_authority_boundary_text` length ≥ 1.
  - `brief_uncertainty` CHECK against its enum.
  - CHECK that `draft_clarification_note` and `priority_rationale` do not
    contain prohibited vocabulary tokens (section 6.4).
- **Indexes:**
  - FK index on `voucher_id`.
  - Unique index on `(voucher_id, version)`.
- **Seed-data role:** at least one pre-generated brief per voucher in
  section 7 so the demo opens with content already on the screen. The
  `is_partial = true` case is exercised by at least one seeded voucher.
- **Spec alignment:** section 3.7 (Review Brief, Draft Clarification Note),
  FR-7, FR-8, FR-12, FR-14, NFR-7, NFR-8, TR-10, AC-1, AC-4, AC-5, AC-9,
  AC-12, AC-15.

### 5.11 ao_notes

- **Purpose:** typed reviewer-authored or system-drafted internal notes.
  Backs `record_ao_note`, `draft_return_comment`, and `record_ao_feedback`.
- **Key columns:**
  - `note_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id)
  - `finding_id` (text, nullable, FK → story_findings.finding_id)
  - `kind` (enum: `ao_note`, `draft_clarification`, `ao_feedback`)
  - `body` (text)
  - `actor_label` (text, demo identity such as `demo_ao_user_1`; never
    invented and never a real person)
  - `created_at` (timestamp)
  - `superseded_by_note_id` (text, nullable, self-referential FK; allows
    the reviewer to edit a draft without losing history)
- **Constraints / checks:**
  - `kind` CHECK against its enum.
  - CHECK that `body` does not contain prohibited vocabulary tokens
    (section 6.4) when `kind = draft_clarification`. AO notes themselves
    are reviewer free-text and the constraint is relaxed there, but the
    application layer should still strip obvious prohibited tokens.
  - `actor_label` NOT NULL.
- **Indexes:**
  - FK index on `voucher_id`.
  - Index on `(voucher_id, kind)`.
- **Seed-data role:** at least one seeded `ao_note`, one
  `draft_clarification`, and one `ao_feedback` row across the corpus so the
  demo can show all three shapes.
- **Spec alignment:** section 3.7 (Workflow Write, Draft Clarification
  Note), FR-7, FR-15, AC-4, AC-16.

### 5.12 workflow_events

- **Purpose:** the audit log. Every scoped write, every refusal, every
  needs-human-review label, every retrieval worth recording, and every
  export creates a row here. Backs `get_audit_trail(voucher_id)` and the
  audit-event shape in `docs/spec.md` section 4.5.4.
- **Key columns:**
  - `event_id` (text, PK)
  - `voucher_id` (text, FK → vouchers.voucher_id; nullable only for
    system-level events that have no voucher context, which the demo
    avoids)
  - `actor_label` (text; the human reviewer or demo identity, never
    invented)
  - `occurred_at` (timestamp)
  - `event_type` (enum: `scoped_write`, `refusal`,
    `needs_human_review_label`, `retrieval`, `generation`, `edit`,
    `export`)
  - `tool_name` (text, nullable; the workflow tool that produced the
    event, drawn only from the catalog in `docs/spec.md` section 4.5)
  - `target_kind` (enum: `voucher`, `finding`, `note`, `brief`, `signal`,
    `citation`, `missing_item`, `none`)
  - `target_id` (text, nullable)
  - `resulting_status` (text, nullable; for review-status changes)
  - `rationale_metadata` (json; arbitrary structured context, e.g.
    refusal reason, requested action, draft text length, citation ids
    surfaced)
  - `human_authority_boundary_reminder` (text, fixed reminder; CHECK
    non-empty)
- **Constraints / checks:**
  - `event_type`, `target_kind` CHECK against their enums.
  - `tool_name` IS NOT NULL when `event_type = scoped_write`.
  - `resulting_status` CHECK rejects prohibited values whenever it is set
    (the same blacklist in section 6.4 plus the enumeration check in
    section 6.1).
  - `human_authority_boundary_reminder` length ≥ 1.
- **Indexes:**
  - FK index on `voucher_id`.
  - Index on `(voucher_id, occurred_at)` for ordered audit retrieval.
  - Index on `event_type`.
- **Seed-data role:** every seeded scoped write, refusal, and brief
  generation in section 7 emits a corresponding workflow_event row at seed
  time so `get_audit_trail` returns content immediately on demo start.
- **Spec alignment:** section 3.7 (Audit Entry, Workflow Write),
  section 4.5.2, section 4.5.4, FR-11, FR-15, TR-9, AC-6, AC-10, AC-16.

### 5.13 Recommended additional tables (gaps)

The baseline list omits a few small but spec-relevant pieces. The plan
recommends adding them now rather than discovering them mid-build.

- **finding_signal_links**
  - Purpose: many-to-many join between `story_findings` and
    `external_anomaly_signals`. Columns: `(finding_id, signal_id)` with both
    FKs, plus `created_at`. Composite PK on the pair.
  - Why: a flag commonly draws on more than one signal, and the spec's
    fusion language treats signals as inputs that should be visible per
    flag (FR-8, AC-2).
- **finding_evidence_links** (optional, only if the coding agent finds the
  embedded `packet_evidence_pointer` json too coarse for the chosen
  database). Same shape as `finding_signal_links`, joining
  `story_findings` to `evidence_refs` and/or `voucher_line_items`. The
  default plan keeps the json pointer; this is a fallback if querying the
  json becomes painful.
- A `kind` column on `ao_notes` (already specified in 5.11) — listed here
  again because it is the cleanest way to back three distinct workflow
  tools without inventing three tables.

No other additions are recommended at hackathon scope.

---

## 6. Enumerations and Check Constraints

All enumerations are stored as application-validated text (or as native
`ENUM` types where the chosen database supports them cheaply). Every
enumeration is enforced with a CHECK constraint at the column level.

### 6.1 voucher.review_status (controlled internal review status)

Allowed values, drawn directly from `docs/spec.md` section 4.5.3:

- `needs_review`
- `in_review`
- `awaiting_traveler_clarification`
- `ready_for_human_decision`
- `closed_in_demo`

The CHECK constraint must reject every other value, including but not
limited to the explicit blocklist in section 6.4.

### 6.2 story_findings.category

- `missing_receipt`
- `weak_or_local_paper_receipt`
- `amount_mismatch`
- `duplicate_or_multiple_charge`
- `ambiguous_loa_or_funding_reference`
- `cash_atm_or_exchange_reconstruction`
- `stale_memory_old_transaction`
- `unauthorized_or_unclear_expense`
- `date_window_mismatch`
- `location_mismatch`
- `miscategorized_line_item`
- `insufficient_evidence_overall`
- `oconus_vendor_edge_case`
- `evidence_quality_concern`
- `story_coherence_break`

This list is intentionally derived from the seed scenarios in section 7 so
that every scenario has a category and every category has at least one
seeded finding.

### 6.3 story_findings.review_state and finding-review write tool

Allowed values, derived from `docs/spec.md` section 4.5.2:

- `open`
- `reviewed_explained`
- `reviewed_unresolved`
- `needs_followup`

Disallowed values include `approved`, `denied`, `certified`, `submitted`,
`paid`, `fraud`, `returned`, `cancelled`, `amended`. The CHECK constraint
rejects them.

### 6.4 Blocked official-action vocabulary (schema-level blacklist)

The following tokens (case-insensitive, whole-word) are explicitly
prohibited from appearing in:

- `vouchers.review_status`
- `story_findings.review_state`
- `workflow_events.resulting_status`
- (advisory CHECK only) `policy_citations.excerpt_text`,
  `prior_voucher_summaries.summary_text`,
  `prior_voucher_summaries.recurring_correction_pattern`,
  `review_briefs.draft_clarification_note`,
  `review_briefs.priority_rationale`,
  `story_findings.summary`, `story_findings.explanation`,
  `story_findings.suggested_question`,
  `ao_notes.body` when `kind = draft_clarification`.

Blocked tokens:

- `approved`, `approve`
- `denied`, `deny`
- `certified`, `certify`
- `submitted`, `submit`
- `returned`, `return_voucher`
- `cancelled`, `cancel`
- `amended`, `amend`
- `paid`, `payable`, `nonpayable`
- `fraud`, `fraudulent`, `misuse`, `abuse`, `misconduct`
- `entitled`, `entitlement` (when used as a determination, not in citation
  topic labels — the CHECK is conservative; the seed corpus avoids the word)
- `escalate_to_investigators`, `notify_command`, `contact_traveler` (the
  underscored phrases stand in for any external-contact verb the
  application might try to render)

Implementation note for the coding agent: in databases without robust regex
checks, encode this blacklist as a CHECK using a `LOWER()` containment
predicate per token, or as a database function called from the CHECK. The
goal is that a row carrying any of these tokens in a guarded column simply
will not insert. If the chosen database makes this expensive, the coding
agent may move the advisory checks (excerpt_text, summary, etc.) into a
test fixture validator instead of an in-database CHECK. The status-column
checks must remain in the database.

### 6.5 Other enumerations (recap)

- `vouchers.funding_reference_quality`: `clean`, `ambiguous`, `unparseable`.
- `voucher_line_items.category`: `lodging`, `transport_air`,
  `transport_ground`, `meals`, `incidentals`, `cash_atm`,
  `currency_exchange`, `other_demo`.
- `voucher_line_items.payment_instrument_indicator`: `gtcc_like_demo`,
  `personal_card_demo`, `cash_demo`, `unknown_demo`.
- `evidence_refs.content_type_indicator`,
  `evidence_refs.legibility_cue`, `evidence_refs.itemization_cue`,
  `evidence_refs.payment_evidence_cue`: as listed in 5.4.
- `policy_citations.topic`: as listed in 5.6.
- `external_anomaly_signals.signal_type`,
  `external_anomaly_signals.confidence`: as listed in 5.7.
- `story_findings.severity`, `story_findings.confidence`: as listed in 5.8.
- `review_briefs.brief_uncertainty`: `low`, `medium`, `high`.
- `ao_notes.kind`: `ao_note`, `draft_clarification`, `ao_feedback`.
- `workflow_events.event_type`: `scoped_write`, `refusal`,
  `needs_human_review_label`, `retrieval`, `generation`, `edit`, `export`.
- `workflow_events.target_kind`: `voucher`, `finding`, `note`, `brief`,
  `signal`, `citation`, `missing_item`, `none`.

---

## 7. Data Generation / Seed Data Plan

All data in this section is synthetic and clearly fictional. Names use
demo-marker suffixes. Locations are invented. Vendor labels include
markers like `Demo`. LOA strings carry a `LOA-DEMO-` prefix. Dates use a
demo fiscal year (`FY26`).

### 7.1 Synthetic travelers

| traveler_id | display_name | role_label | typical_trip_pattern | prior_correction_summary |
|---|---|---|---|---|
| T-101 | SSG R. Carver (Demo) | `staff_nco_demo` | short OCONUS site visits and conferences | repeated evidence-attachment gap on lodging line |
| T-102 | CPT M. Diaz (Demo) | `field_grade_demo` | multi-leg CONUS trips | occasional duplicate-hotel pattern |
| T-103 | MAJ J. Park (Demo) | `staff_field_grade_demo` | infrequent CONUS staff trips | none on file |
| T-104 | SFC A. Torres (Demo) | `senior_nco_demo` | austere/OCONUS site visits with cash usage | recurring exchange-rate reconstruction work |
| T-105 | 1LT K. Nguyen (Demo) | `junior_officer_demo` | first-time submitters CONUS | none on file |

Each row has `data_environment = synthetic_demo`. Two travelers (T-103,
T-105) carry no prior summaries to exercise the cold-start case.

### 7.2 Synthetic vouchers and scenarios

The corpus is twelve vouchers. Each row names the scenario, the tables it
populates, and what the brief should surface. Two clean controls are
included so the demo can contrast a clean brief against messy ones.

#### V-1001 — clean OCONUS conference (T-101) — control case 1

- **Tables populated:** `vouchers` (status `ready_for_human_decision`),
  five `voucher_line_items`, five `evidence_refs` all with strong cues,
  zero `external_anomaly_signals`, zero `story_findings`, zero
  `missing_information_items`, one `review_briefs` row with low
  `brief_uncertainty`, one seeded `workflow_events` row of
  `event_type = generation` for the brief.
- **What the AO sees:** a clean brief with no flags, low uncertainty, and
  a draft clarification note that says no clarifications appear necessary
  from the packet on its face, with the standard human-authority boundary
  reminder.

#### V-1002 — OCONUS site visit, missing receipt + local-paper receipt (T-101)

- **Scenarios covered:** missing receipt, weak/local-paper receipt, OCONUS
  vendor edge case (partial overlap with V-1012).
- **Tables populated:** `vouchers` (status `in_review`); six
  `voucher_line_items` including a lodging line and a meals line; five
  `evidence_refs` of which one is `none_attached_demo` (lodging) and one
  is `handwritten_local_paper_demo` with `legibility_cue = poor` (meals);
  one `external_anomaly_signal` of `signal_type = repeated_correction_pattern`
  pointing to T-101's prior pattern; three `story_findings`
  (`missing_receipt`, `weak_or_local_paper_receipt`,
  `evidence_quality_concern`); two `missing_information_items`; one
  `review_briefs` row with medium uncertainty; corresponding
  `workflow_events`.
- **What the AO sees:** a brief that prioritizes the lodging line first,
  cites a `valid_receipt` topic citation verbatim, lists the two missing
  items explicitly, surfaces the prior-pattern signal as a review prompt
  (not a finding), and offers a neutral draft clarification asking the
  traveler to provide a lodging receipt and to clarify what the
  handwritten meals receipt represents.

#### V-1003 — CONUS multi-leg, duplicate hotel charge + amount mismatch (T-102)

- **Scenarios covered:** duplicate/multiple hotel charges, amount
  mismatch.
- **Tables populated:** `vouchers` (status `in_review`); eight
  `voucher_line_items` including two lodging lines that overlap by one
  night and one transport line whose amount does not match its evidence;
  evidence rows with `amount_on_face_minor_units` differing from the line
  item amount; two `external_anomaly_signals`
  (`duplicate_payment_risk`, `unusual_amount`); four `story_findings`
  (`duplicate_or_multiple_charge` × 1, `amount_mismatch` × 1,
  `story_coherence_break` × 1, plus one `needs_human_review = true`
  finding for the second lodging line because legitimate dual-lodging
  cases exist and the system must not infer intent); two
  `missing_information_items`.
- **What the AO sees:** a brief that highlights the overlap night, shows
  the two evidence rows side by side, cites the
  `duplicate_charge_review` and `lodging_documentation` topics, and
  includes a needs-human-review label on the second lodging line so the
  reviewer is reminded that dual-lodging is a human determination.

#### V-1004 — CONUS coastal training, ambiguous LOA + miscategorized line (T-102)

- **Scenarios covered:** bad/ambiguous LOA, poor categorization/mis-click.
- **Tables populated:** `vouchers` with
  `funding_reference_quality = ambiguous` and a deliberately ill-formed
  `funding_reference_label` (e.g. `LOA-DEMO-FY26-???`); seven line items
  including one lodging line miscategorized as `meals`; matching evidence
  rows where the `vendor_label_on_evidence` clearly says hotel; one
  `external_anomaly_signal` of `signal_type = high_risk_mcc_demo`
  flagging the miscategorization; three `story_findings`
  (`ambiguous_loa_or_funding_reference`, `miscategorized_line_item`,
  `evidence_quality_concern`); two `missing_information_items`.
- **What the AO sees:** a brief that calls out the LOA legibility, points
  at the meals-vs-lodging mismatch with the evidence vendor label
  visible, cites the `funding_reference_format` topic, and offers a
  draft asking the traveler to confirm the LOA and clarify the
  categorization.

#### V-1005 — CONUS staff trip, baseline clean (T-103) — control case 2

- **Tables populated:** as V-1001, but for a CONUS profile.
- **What the AO sees:** clean brief; second control case for visual
  comparison.

#### V-1006 — old CONUS trip, stale memory + weak justification (T-103)

- **Scenarios covered:** stale-memory old transactions.
- **Tables populated:** `vouchers` whose `submitted_at` is many weeks
  after the latest `expense_date`; six line items, several with
  `claimed_by_traveler_at` very close to `submitted_at`; evidence rows
  several of which have `evidence_date_on_face` near the trip but a
  weakly itemized `itemization_cue`; one `external_anomaly_signal` of
  `signal_type = traveler_baseline_outlier`; three `story_findings`
  including a `stale_memory_old_transaction` finding and an
  `evidence_quality_concern`; two `missing_information_items` describing
  what reconstruction the reviewer might ask for.
- **What the AO sees:** a brief that explicitly notes the long gap
  between expense dates and submission, cites the
  `general_review_checklist` and `cash_atm_reconstruction` topics where
  applicable, and drafts a clarification asking the traveler to confirm
  details on the older transactions.

#### V-1007 — austere OCONUS, ATM/cash + exchange-rate math (T-104)

- **Scenarios covered:** ATM/cash with exchange-rate math, OCONUS vendor
  edge case overlap.
- **Tables populated:** `vouchers` with OCONUS destinations; nine line
  items including two `cash_atm` lines and one `currency_exchange` line,
  plus a meals line in non-USD currency requiring `exchange_rate_to_usd`;
  evidence rows that are mostly `handwritten_local_paper_demo` with
  `legibility_cue = partial`; two `external_anomaly_signals`
  (`split_disbursement_oddity`, `traveler_baseline_outlier`); five
  `story_findings` including
  `cash_atm_or_exchange_reconstruction` (high severity, low confidence,
  `needs_human_review = true`), `weak_or_local_paper_receipt`, and
  `evidence_quality_concern`; three `missing_information_items`.
- **What the AO sees:** a brief that lays out the ATM/cash sequence,
  shows the exchange-rate column for each foreign-currency line, cites
  the `cash_atm_reconstruction` and `currency_exchange` topics,
  surfaces the two signals as review prompts only, and clearly labels
  the cash-reconstruction finding as needs human review because the
  system cannot responsibly characterize it.

#### V-1008 — CONUS, date/location mismatch (T-104)

- **Scenarios covered:** date/location mismatch.
- **Tables populated:** `vouchers` with declared destinations not
  matching one transport line's `vendor_label_on_evidence` city; one
  line item whose `expense_date` falls outside `(trip_start_date,
  trip_end_date)`; one `external_anomaly_signal` of
  `signal_type = date_location_mismatch`; three `story_findings`
  (`date_window_mismatch`, `location_mismatch`, `story_coherence_break`);
  one `missing_information_item`.
- **What the AO sees:** a brief that visualizes the trip window with the
  out-of-window expense, cites the `date_window_coherence` topic, and
  drafts a neutral clarification.

#### V-1009 — CONUS, mis-click categorization (T-105, first-time submitter)

- **Scenarios covered:** poor categorization/mis-click; reinforces the
  V-1004 case but in a first-time submitter context to exercise the
  no-prior-history baseline path.
- **Tables populated:** `vouchers` with no prior summaries on T-105;
  five line items including one obvious mis-click (e.g. lodging amount
  on a meals row); evidence rows that disagree with the line category;
  zero `external_anomaly_signals`; two `story_findings`
  (`miscategorized_line_item`, `evidence_quality_concern`); one
  `missing_information_item`.
- **What the AO sees:** a brief that flags the mis-click without inferring
  intent, cites the `general_review_checklist` topic, and drafts a
  clarification asking the traveler to confirm the line category.

#### V-1010 — OCONUS, unauthorized-or-unclear expense (T-105)

- **Scenarios covered:** unauthorized-or-unclear expense.
- **Tables populated:** `vouchers` containing one line item whose
  `category = other_demo` and whose vendor label is unclear (e.g.
  `Unknown Demo Vendor 17`); evidence row with low cue scores; zero
  external signals (deliberate — to exercise the path where a flag is
  story-only without a signal); two `story_findings`
  (`unauthorized_or_unclear_expense` with `needs_human_review = true`,
  and `evidence_quality_concern`); two `missing_information_items`.
- **What the AO sees:** a brief that explicitly does not call the line
  unauthorized — the category is `unauthorized_or_unclear_expense` and
  the wording in `summary` and `explanation` uses the spec-permitted
  vocabulary (anomaly, documentation gap, evidence needing closer
  reviewer attention). The needs-human-review label is visible.

#### V-1011 — mixed packet, insufficient evidence overall (T-102)

- **Scenarios covered:** insufficient evidence, missing receipts (broad
  case).
- **Tables populated:** `vouchers` with seven line items, four of which
  have evidence rows of `content_type_indicator = none_attached_demo`;
  one external signal of `repeated_correction_pattern`; five
  `story_findings` including one of category
  `insufficient_evidence_overall` at `severity = high`; four
  `missing_information_items`; one `review_briefs` row with
  `is_partial = true` and a partial reason explaining that several lines
  could not be reconstructed.
- **What the AO sees:** a brief that signals it is partial, lists what
  can be said and what cannot, and drafts a clarification listing the
  evidence categories needed.

#### V-1012 — OCONUS, vendor edge case (T-101)

- **Scenarios covered:** OCONUS vendor edge case (vendor that does not
  produce standardized receipts in any form).
- **Tables populated:** `vouchers`; six line items including one for an
  austere vendor; evidence row with
  `content_type_indicator = handwritten_local_paper_demo` and
  `payment_evidence_cue = absent`; one external signal of
  `signal_type = peer_baseline_outlier`; two `story_findings`
  (`oconus_vendor_edge_case` with `needs_human_review = true`,
  `evidence_quality_concern`); one `missing_information_item` whose
  `expected_location_hint` notes that automated receipt retrieval may
  not be possible for this vendor.
- **What the AO sees:** a brief that names the OCONUS-vendor edge case,
  cites the `oconus_vendor_edge` topic, surfaces the signal as a review
  prompt only, and drafts a neutral clarification.

### 7.3 Pre-existing flags and review-status spread

Distribute `review_status` values across the corpus so the queue listing
can demonstrate prioritization (FR-9, AC-8) without implying official
disposition:

- `needs_review`: V-1006, V-1009, V-1010, V-1012
- `in_review`: V-1002, V-1003, V-1004, V-1007, V-1008, V-1011
- `awaiting_traveler_clarification`: none at seed (the demo flips one to
  this state during the live walkthrough)
- `ready_for_human_decision`: V-1001, V-1005 (the two clean controls)
- `closed_in_demo`: none at seed

### 7.4 Refusal and out-of-scope seeds

To make refusal demos reproducible:

- Seed one `workflow_events` row of `event_type = refusal` against V-1001
  with `tool_name = set_voucher_review_status` and a `rationale_metadata`
  payload showing that the requested value `approved` was rejected.
- Seed one `workflow_events` row of `event_type = refusal` against V-1010
  with `tool_name = prepare_ao_review_brief` and a payload showing that a
  request to characterize the line as fraudulent was rejected.

These two seeded refusals satisfy AC-6 from cold start.

### 7.5 Volume guidance

- Five to six travelers.
- Twelve vouchers (above).
- Roughly seventy-five to one hundred line items in total.
- Roughly seventy-five to one hundred fifty evidence references.
- Twenty to twenty-five external anomaly signals across the corpus.
- Thirty to forty-five story findings across the corpus.
- Twenty to thirty missing-information items across the corpus.
- One review brief per voucher seeded; live demo regenerates one to
  exercise versioning.
- Roughly fifty to seventy workflow events at seed time, including the
  two refusal seeds in 7.4.

These volumes are small enough to seed quickly and large enough to
exercise the brief assembly across every category and signal type.

---

## 8. Implementation Phases for Coding Agent

Each phase is small and individually verifiable. Bias toward landing each
phase as its own change so review and rollback are easy.

### Phase 1 — Migration / table creation

- Create `travelers`, `vouchers`, `voucher_line_items`, `evidence_refs`,
  `prior_voucher_summaries`, `policy_citations`,
  `external_anomaly_signals`, `story_findings`,
  `missing_information_items`, `review_briefs`, `ao_notes`,
  `workflow_events`, and `finding_signal_links`.
- Define columns, primary keys, and foreign keys per section 5.
- Do not yet add CHECK constraints or indexes; that is Phase 2.

### Phase 2 — Constraints and indexes

- Add CHECK constraints for every enumeration in section 6.
- Add the schema-level blocked-vocabulary CHECKs on
  `vouchers.review_status`, `story_findings.review_state`, and
  `workflow_events.resulting_status`.
- Add advisory blocked-vocabulary CHECKs on the columns listed in section
  6.4 if the chosen database supports them cheaply; otherwise move them
  to Phase 7 test fixtures.
- Add the `data_environment = synthetic_demo` CHECK on `travelers` and
  `vouchers`.
- Add indexes per section 5.

### Phase 3 — Seed fixtures

- Implement the seed data described in section 7 as a single,
  deterministic, idempotent seed routine.
- The seed routine must populate `workflow_events` for every seeded
  scoped write, brief generation, and the two seeded refusals.
- Provide a `reset_demo()` routine that drops and re-seeds. Guard it
  with an explicit `data_environment` check so it can never run against
  any environment other than the synthetic demo.

### Phase 4 — Repository / data-access layer

- Build a thin, scoped repository module per table. Each repository
  exposes only the operations the workflow tools need:
  - `vouchers`: read by id, list ordered by status and submitted_at,
    update review status (with the controlled enum), no delete in
    application code (use `reset_demo` only).
  - `voucher_line_items`, `evidence_refs`,
    `external_anomaly_signals`, `prior_voucher_summaries`,
    `policy_citations`, `missing_information_items`: read-only at
    runtime.
  - `story_findings`: read; update `review_state` and
    `needs_human_review` only via the workflow contract; no free text
    rewrite at runtime.
  - `review_briefs`: append-only, version increment per voucher.
  - `ao_notes`: append-only by `kind`.
  - `workflow_events`: append-only.
- The repository module must not expose any generic execute-SQL,
  raw-fetch, or string-templated query method to upstream code.
- All write methods must take or produce a `workflow_events` entry in
  the same transaction.

### Phase 5 — MCP / domain workflow tool integration

- Bind the workflow tools enumerated in `docs/spec.md` section 4.5 to the
  repository operations. Tool names are normative; signatures match the
  spec.
- Each write tool composes a single transaction that performs its domain
  write and writes the corresponding `workflow_events` row, with the
  `tool_name`, `target_kind`, `target_id`, `resulting_status` (where
  applicable), and `rationale_metadata` populated.
- Refusal paths must write a `workflow_events` row of
  `event_type = refusal` before returning the refusal to the caller.

### Phase 6 — Audit-event enforcement

- Add an integration-level invariant test: for every successful call to
  every write tool, exactly one `workflow_events` row exists with the
  matching `tool_name` and `target_id`. The test runs against a clean
  seeded database and exercises every write tool.
- Add a coverage test that asserts every value of `event_type` is
  produced by at least one tool path.

### Phase 7 — Tests

- Implement the test plan in section 9 below.

### Phase 8 — Demo validation script

- Provide a single command, e.g. `demo-validate`, that:
  1. Seeds the database from cold.
  2. Calls `prepare_ao_review_brief` against V-1002, V-1003, V-1007,
     V-1010, V-1011, and V-1012, and checks each brief's
     `policy_hooks`, `signal_hooks`, `finding_hooks`, and
     `missing_information_hooks` are non-empty where the scenario
     requires.
  3. Calls `set_voucher_review_status` with each allowed value in
     section 6.1 against a non-control voucher, and confirms each call
     succeeds and produces a workflow event.
  4. Calls `set_voucher_review_status` with each blocked value
     (`approved`, `denied`, `certified`, `submitted`, `paid`, `fraud`,
     `returned`, `cancelled`, `amended`) and confirms each call refuses
     and produces a refusal event.
  5. Calls `mark_finding_reviewed` with each allowed value in section
     6.3 and confirms each succeeds.
  6. Calls `record_ao_note`, `draft_return_comment`,
     `record_ao_feedback`, and `request_traveler_clarification` and
     confirms each produces the expected `ao_notes` row (where
     applicable) and an audit event.
  7. Calls `get_audit_trail` against V-1003 and confirms the events are
     returned in chronological order and that the human-authority
     boundary reminder is non-empty on every row.
  8. Confirms that no MCP tool surface exposes raw SQL or a generic
     fetch.

The demo validation script is the single command a judge can run to see
the schema work end-to-end.

---

## 9. Test Plan

The tests are organized to map one-to-one onto the safety properties the
spec demands. Every test is deterministic against the seed fixtures.

### 9.1 Constraints reject prohibited statuses and actions

- For every value in the section 6.4 blocklist, attempt to insert a
  `vouchers` row with `review_status` set to that value and confirm the
  database rejects the insert.
- Repeat for `story_findings.review_state` and
  `workflow_events.resulting_status`.
- Confirm that updating `vouchers.review_status` to a blocked value
  fails the same way.
- Confirm that the controlled enums in section 6.5 reject unknown values.

### 9.2 Every workflow write creates an audit event

- For each write tool in the section 4.5.2 catalog, call the tool with
  valid input and assert a corresponding `workflow_events` row exists
  in the same transaction.
- For each write tool, force a tool-level failure (for example by
  passing an id that does not exist) and assert that no
  `workflow_events` row was written and no domain row was changed
  (transactionality test).

### 9.3 No generic data access through the tool layer

- Inspect the bound tool catalog and assert that no exposed tool name
  matches `query_database`, `execute_sql`, `fetch_url`, `read_file`, or
  any obvious raw-access synonym.
- Inspect the repository module and assert it does not export a
  method that takes arbitrary SQL strings or arbitrary file paths.
- This is implemented as a code-shape test (lint or static check), not
  a runtime test.

### 9.4 Generated briefs include citations, provenance, uncertainty, and the human-authority boundary statement

- For each non-control voucher in the seed corpus, generate a brief and
  assert:
  - At least one `policy_hooks` entry resolves to a real
    `policy_citations` row.
  - Every `finding_hooks` entry resolves to a `story_findings` row whose
    `packet_evidence_pointer` carries at least one of
    `line_item_id` or `evidence_ref_id`.
  - Every signal in `signal_hooks` resolves to an
    `external_anomaly_signals` row whose `is_official_finding = false`
    and `not_sufficient_for_adverse_action = true`.
  - `brief_uncertainty` is set.
  - `human_authority_boundary_text` is non-empty.
  - `draft_clarification_note` does not contain any blocked-vocabulary
    token.

### 9.5 Sample data covers all required cases

- Assert at least one finding exists per category in section 6.2.
- Assert at least one finding per scenario name in section 7.2 exists by
  category mapping.
- Assert at least one finding has `needs_human_review = true` and the
  brief that consumes it surfaces it as a needs-human-review item
  (AC-13).
- Assert that V-1011's brief has `is_partial = true` (NFR-8).
- Assert that the two seeded refusals from 7.4 are present in
  `workflow_events`.

### 9.6 Synthetic-only invariant

- Assert every `travelers` and every `vouchers` row has
  `data_environment = synthetic_demo`.
- Assert every `display_name` carries a synthetic marker substring.
- Assert that no row in the corpus contains a token from a small
  hand-written list of obvious real-data shapes (for example, a
  16-digit number that looks like a card PAN, a real-looking SSN
  pattern, or an email at a real domain). This is a fixture-validator
  test, not a CHECK.

### 9.7 Queue prioritization is workload guidance, not disposition

- Call `list_vouchers_awaiting_action` and assert the response carries
  an explicit workload-guidance label (AC-8).
- Assert the response does not carry any field that names approval,
  denial, payability, or readiness for payment.

### 9.8 Refusal demonstration

- Issue a tool call equivalent to "approve V-1001" and assert a refusal
  workflow event is written and the response carries an actionable
  reason (AC-6).
- Submit a non-voucher artifact through whatever ingest path the
  application exposes and assert the system refuses with a
  out-of-scope reason (AC-7).

---

## 10. Spec Comparison Matrix

The matrix calls out, per spec requirement, what the schema supports and
where the implementation has work to do. Items the schema does not own
are marked accordingly.

| Spec requirement | Proposed schema support | Gap or implementation note |
|---|---|---|
| FR-1 Packet Ingest | `vouchers`, `voucher_line_items`, `evidence_refs` carry trip metadata, line items, evidence references, justification, funding reference, pre-existing flags. | Application must produce these rows from a structured intake; the schema does not parse files. |
| FR-2 Story Reconstruction | `story_findings` carries the reconstructed-story observations and break flags; `review_briefs.story_coherence_summary` carries the narrative form. | Reasoning component is out of schema scope. |
| FR-3 Evidence Quality Assessment | `evidence_refs` cue columns (legibility, itemization, payment-evidence) per line item. | Reasoning component populates these; the schema enforces the enum domain. |
| FR-4 Coherence and Anomaly Checks | `story_findings.category` enum covers the named cases; `external_anomaly_signals.signal_type` carries the signal-side variants. | Detection logic is out of scope. Schema ensures every flag carries provenance. |
| FR-5 Controlled Reference Retrieval | `policy_citations` is a closed corpus; `story_findings.primary_citation_id` joins flags to citations. | Retrieval pipeline is out of scope; corpus seed in section 7 must be sufficient to ground every flag category. |
| FR-6 Missing-Information Detection | `missing_information_items` is a separate table from `story_findings`. | Distinction enforced by table separation, not by status. |
| FR-7 Reviewer Prompt Drafting | `review_briefs.draft_clarification_note` and `ao_notes(kind = draft_clarification)`. | Blocked-vocabulary CHECK guards both. |
| FR-8 Provenance and Confidence | `story_findings.packet_evidence_pointer`, `story_findings.primary_citation_id`, `story_findings.confidence`, `review_briefs.brief_uncertainty`. | Pointer json must include at least one id; CHECK enforces this. |
| FR-9 Queue Prioritization | `vouchers.review_status` and `submitted_at` indexes, plus `review_briefs.priority_score` and `priority_rationale`. | Application labels the view as workload guidance. |
| FR-10 Refusal and Redirect | `workflow_events.event_type = refusal`. | Application must write the row before returning the refusal. |
| FR-11 Audit Log | `workflow_events`. | Audit-event invariant test (9.2) holds the application accountable. |
| FR-12 Export | `review_briefs` and the human-authority boundary text. | Export format and channel are application concerns. |
| FR-13 Needs-Human-Review State | `story_findings.needs_human_review` boolean, distinct from `missing_information_items` and from `workflow_events.event_type = refusal`. | Brief assembly must surface the boolean. |
| FR-14 Fused AO Review Brief | `review_briefs` with `policy_hooks`, `signal_hooks`, `finding_hooks`, `missing_information_hooks`. | Application performs fusion; schema enforces shape. |
| FR-15 Scoped Workflow Writes | `ao_notes`, controlled write semantics on `vouchers.review_status` and `story_findings.review_state`. | Repository layer must refuse generic writes. |
| FR-16 Controlled Review Statuses | `vouchers.review_status` CHECK against section 6.1; blocked tokens in section 6.4. | Hard at the DB layer, not at the app layer. |
| NFR-1 Trust Boundary | Hardcoded enums and CHECKs; no configurable policy. | The coding agent must not introduce a way to disable these. |
| NFR-2 Explainability | `story_findings` provenance columns and `review_briefs` hooks. | Reasoning component populates them. |
| NFR-3 Grounding Discipline | `policy_citations` is the only source of citations; advisory CHECK on `excerpt_text`. | Application must refuse rather than fabricate when no citation supports a claim. |
| NFR-6 Data Handling | `data_environment = synthetic_demo` CHECK; demo-marker constraints on names. | Retention is an application concern. |
| NFR-7 Human Authority | `review_briefs.human_authority_boundary_text` and the per-event reminder on `workflow_events`. | Brief export must include the line. |
| NFR-8 Robustness | `review_briefs.is_partial` and `partial_reason`. | Application sets the flag when retrieval fails or sources conflict. |
| TR-1 No Official Action | Blocked vocabulary in section 6.4; `vouchers.review_status` enum. | Schema-level rejection. |
| TR-3 No Fraud Allegation | Blocked vocabulary in section 6.4 includes `fraud`, `misuse`, `abuse`, `misconduct`. | Advisory CHECK on free-text columns where supported. |
| TR-5 Provenance on Every Flag | `story_findings.packet_evidence_pointer` CHECK. | Brief assembly must propagate. |
| TR-7 Visible Uncertainty | `story_findings.confidence` and `review_briefs.brief_uncertainty`. | Application must render these. |
| TR-8 Synthetic-Only Prototype Data | `data_environment` CHECK on `travelers` and `vouchers`. | Reset routine guarded against non-synthetic targets. |
| TR-9 Auditability | `workflow_events`. | See section 9.2 invariant test. |
| TR-11 No External Contact or Escalation | Blocked vocabulary covers external-contact verbs; no schema column ever names a real external recipient. | Application must not introduce one. |
| TR-12 No Generic Data Access | Repository contract refuses generic SQL; section 9.3 test enforces. | Out-of-band tool addition would violate this; review carefully. |
| AC-1 Single-Packet Brief | `review_briefs` seeded for every voucher. | Demo script verifies. |
| AC-2 Provenance | `story_findings` packet pointer and citation FK. | Demo script verifies. |
| AC-3 Missing-Information Listing | `missing_information_items` distinct from `story_findings`. | — |
| AC-4 Draft Clarification Note | `review_briefs.draft_clarification_note` and `ao_notes(kind = draft_clarification)`. | Blocked-vocab CHECK guards. |
| AC-5 Visible Uncertainty | `story_findings.confidence` and `review_briefs.brief_uncertainty`. | — |
| AC-6 Refusal Demonstration | Section 7.4 seeded refusals; section 9.8 test. | — |
| AC-7 Out-of-Scope Refusal | Application path; schema produces the workflow event. | Application work. |
| AC-8 Queue Prioritization | `review_status`, `submitted_at` indexes; brief priority columns. | Application labels the view. |
| AC-9 Export | `review_briefs` content, including the boundary statement. | Export format is application work. |
| AC-10 Audit Trail | `workflow_events`. | — |
| AC-11 Public-Safety Verification | `data_environment` CHECK and demo-marker constraints. | Demo narrative is application work. |
| AC-12 Trust-Boundary Statement | `review_briefs.human_authority_boundary_text`. | — |
| AC-13 Needs-Human-Review Demonstration | `story_findings.needs_human_review` seeded true on V-1003, V-1007, V-1010, V-1012. | — |
| AC-14 Three-Layer Demo Boundary | Tables are partitioned cleanly: evidence layer (`vouchers`, `voucher_line_items`, `evidence_refs`); signal layer (`external_anomaly_signals`); AO reasoning layer (`story_findings`, `missing_information_items`, `review_briefs`, `ao_notes`, `workflow_events`). | — |
| AC-15 Fusion Tool Demonstration | `review_briefs` is the artifact of `prepare_ao_review_brief`. | Tool layer must not expose raw SQL (section 9.3). |
| AC-16 Controlled Workflow Writes | `vouchers.review_status` and `story_findings.review_state` enums; audit invariant. | — |

---

## 11. Risks and Recommended Simplifications for Hackathon Demo

The schema as described is small enough to land within hackathon scope.
The risks below are the ones most likely to derail the build, with a
recommended simplification for each.

- **Risk: blocked-vocabulary CHECKs become hard to express in the chosen
  database.** Some databases are awkward for case-insensitive whole-word
  predicates inside CHECK constraints.
  - **Simplification:** keep the CHECKs on the three controlled-status
    columns (`vouchers.review_status`, `story_findings.review_state`,
    `workflow_events.resulting_status`) where the value space is small
    and exact. Move the advisory free-text CHECKs into a fixture
    validator that runs in CI and on every seed.

- **Risk: enumeration drift between the schema and the application.**
  Two sources of truth for an enum is a familiar trap.
  - **Simplification:** generate the application enums from the schema,
    or generate the schema CHECKs from a single declared list. Either
    direction is fine; what matters is one source.

- **Risk: brief regeneration semantics complicate the demo.** Versioning
  is correct, but a demo that deletes and recreates the latest version
  is simpler to reason about.
  - **Simplification:** keep `review_briefs` versioning, but have the
    demo script always show the latest version. Older versions stay in
    place for audit purposes only.

- **Risk: seed data balloons.** Twelve vouchers with full evidence and
  signal coverage is enough for demonstrability and small enough to
  hand-write.
  - **Simplification:** if the seed fixtures grow beyond a single file,
    split per voucher, not per table. One file per voucher keeps each
    scenario auditable as a whole.

- **Risk: `packet_evidence_pointer` as json hides bad data.** A json
  column can carry malformed pointers that no foreign key catches.
  - **Simplification:** add a fixture validator that resolves every
    pointer at seed time and fails the seed if any pointer is broken.
    If the chosen database supports check constraints that read into
    json, encode the at-least-one-id rule as a CHECK as well.

- **Risk: `finding_signal_links` as a join table is overkill if every
  finding draws on at most one signal.** It might be.
  - **Simplification:** keep the table; the cost is one row, the
    benefit is no schema change later if a flag draws on two signals.
    Do not optimize this away.

- **Risk: scope creep into payment, entitlement, or external contact.**
  This is the spec's central trust risk.
  - **Mitigation, not simplification:** never add a column that names
    payment, disbursement, entitlement, or an external recipient. If
    a downstream feature seems to need one, that is a sign the feature
    is outside the trust boundary.

---

## 12. Coding-Agent Checklist

Use this list as the work order. Each box is small and verifiable.

- [ ] Choose a concrete database product. Document the choice in the PR
  description and in the migration tool's README.
- [ ] Phase 1: write migrations creating the twelve baseline tables plus
  `finding_signal_links`. Commit.
- [ ] Phase 2: add CHECK constraints for every enumeration in section 6
  and the three hard blocked-vocabulary CHECKs. Add indexes per section
  5. Commit.
- [ ] Phase 3: implement a deterministic, idempotent seed routine that
  populates every row described in section 7, including the two seeded
  refusals in 7.4 and one pre-generated brief per voucher. Implement
  `reset_demo()` with a `data_environment = synthetic_demo` guard.
  Commit.
- [ ] Phase 4: implement repository modules per table with the scoped
  operations in section 8. Confirm no module exposes a generic SQL or
  fetch method. Commit.
- [ ] Phase 5: bind the workflow tools enumerated in `docs/spec.md`
  section 4.5 to the repository operations. Each write tool composes a
  single transaction that performs its domain write and writes the
  matching `workflow_events` row. Commit.
- [ ] Phase 6: add the audit-event invariant integration test described
  in section 9.2. Make sure every write tool path is covered. Commit.
- [ ] Phase 7: implement the rest of the test plan in section 9. Commit.
- [ ] Phase 8: implement the `demo-validate` script described in
  section 8 and confirm it runs end-to-end against a freshly seeded
  database. Commit.
- [ ] Confirm that the running implementation does not expose
  `query_database`, raw SQL, free-form filesystem readers, or arbitrary
  HTTP fetch through any tool surface, as required by `docs/spec.md`
  section 3.3, section 4.3, and section 4.5.
- [ ] Confirm that the seeded review briefs include
  `human_authority_boundary_text`, an explicit
  `brief_uncertainty`, at least one resolvable citation, at least one
  resolved finding pointer, and a draft clarification that contains no
  blocked-vocabulary token.
- [ ] Confirm that calling any workflow write tool with a blocked status
  value (`approved`, `denied`, `certified`, `submitted`, `paid`,
  `fraud`, `returned`, `cancelled`, `amended`) refuses cleanly and
  records a `workflow_events` row of `event_type = refusal`.
- [ ] Confirm that the seeded data carries `data_environment =
  synthetic_demo` on every traveler and voucher, and that demo-marker
  substrings appear on every traveler `display_name`.
- [ ] Open a PR that links back to `docs/spec.md` and to this plan, and
  that names the seed scenarios it exercises in the description.

This plan is complete when every box above is checked, the demo
validation script passes from a clean seed, and a reviewer can read
`docs/spec.md`, this plan, and the PR description in that order without
finding a gap.
