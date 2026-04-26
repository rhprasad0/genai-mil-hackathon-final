# AO Radar Synthetic Data Implementation Plan

A coding-agent-ready plan for generating, validating, and loading the synthetic
fixture corpus that backs the AO Radar pre-decision review demo. This document
is **plan only**: it does not introduce code, but it tells a downstream coding
agent exactly what to build, in what order, and against which validators.

The work in this plan begins **after** the Postgres instance is up and the
migrations from `docs/schema-implementation-plan.md` Phase 1 (tables) and
Phase 2 (constraints/indexes) have been applied. It corresponds to schema plan
Phase 3 (Seed fixtures) and unblocks `docs/application-implementation-plan.md`
Phase 2 (read tools) and onward.

---

## 1. Status, Scope, and Non-Goals

### Status

Forward-looking data plan. No fixtures or loaders have been written yet. The
schema plan owns the tables, enums, CHECKs, and the section 7 corpus shape
(travelers, twelve vouchers, coverage map, volume guidance). This document is
the concrete bridge between the practitioner-derived pain patterns the spec
hints at and the rows that land in Postgres.

### In scope

- A **story-first** authoring workflow: each voucher is specified as a hand-authored
  YAML "story card" before any row is generated.
- A deterministic generator that turns story cards into normalized rows for
  every table named in the schema plan section 5.
- A validator that runs on cards and on generated rows, catching synthetic-marker
  gaps, blocked status values, unsafe wording, FK/coverage holes, and absence of
  required audit events.
- A guarded `reset_demo` loader that deletes canonical seeded rows and reloads
  them in a single transaction.
- A coverage map (schema plan section 7.6) baked into machine-readable metadata.
- Three explicitly designated **hero demo stories** chosen from the twelve
  vouchers, plus brief notes for the remaining nine "supporting" vouchers.
- A post-Postgres runbook a coding agent or demo operator follows from a clean
  schema to a queue full of synthetic packets.

### Non-goals

- Defining tables, enums, CHECKs, or the `data_environment` guard. Those live in
  `docs/schema-implementation-plan.md`.
- Defining MCP tool surface, FastMCP wiring, repository contracts, or boundary
  validators. Those live in `docs/application-implementation-plan.md`.
- Writing real DTS records, real GTCC PANs, real LOAs, real unit names, real
  vendor names, or any piece of real personally identifiable information.
- Producing a retrieval/embedding index or a reasoning component. The seed
  populates `policy_citations` rows as static text only; retrieval design is the
  application layer's concern.
- Auth, deployment automation, observability, or any post-hackathon hardening.

### Hard product constraints (carried from the spec and prior plans)

- Synthetic only. Every `travelers` and `vouchers` row carries
  `data_environment = synthetic_demo`; every dependent row is FK-anchored to
  those synthetic parents and uses synthetic-only markers.
- Story cards and generated text never approve, deny, certify, return, cancel,
  amend, submit, accuse fraud, determine entitlement, determine payability,
  modify amounts, or imply external contact.
- Every seeded scoped write, brief generation, needs-human-review label, and
  the two seeded refusals produce the matching `workflow_events` row in the
  same load transaction.
- The seed routine never writes unless the active DB connection passes the
  synthetic-demo guard in section 11.

---

## 2. Companion Document Map

| Document | Owns | This plan defers to it for |
|---|---|---|
| `docs/spec.md` | Capability spec, OV-1, SSS, action contract, prohibited actions, refusal behavior, controlled vocabularies, acceptance criteria. | Tool names, prohibited actions, controlled review statuses, acceptance criteria. |
| `docs/schema-implementation-plan.md` | Tables, columns, enums, CHECKs, audit-event invariant matrix, the section 7 corpus structure (travelers, twelve vouchers, coverage map, volume guidance), and the section 6.4 unsafe-wording / blocked-status rules. | Every table/column name, every enum value, the canonical scenario list. This plan does **not** redefine them; it only specifies the values that go into them. |
| `docs/application-implementation-plan.md` | Application layout, FastMCP wiring, Lambda handlers, repository contracts, build/deploy handoff. | Where `ops/seed/` plugs in (section 12 of the application plan), and which read tools first need non-empty data (Phase 2 onward). |
| `docs/infra-implementation-plan.md` | Terraform, RDS, VPC, Secrets Manager, Lambdas, API Gateway, and the private `db_ops` Lambda. | The canonical migration/seed execution path. Terraform creates the VPC-attached `db_ops` Lambda; operators invoke it for migrations and seed/reset instead of creating manual AWS resources. |
| This document | Story-card workflow, hero stories, fixture artifact layout, generation/load/validate commands, load order, post-Postgres runbook, acceptance criteria. | — |

If a contradiction surfaces between this plan and a companion document, the
companion document wins for its area, and this plan is updated in the same
change.

---

## 3. Privacy and Authority Boundary Posture

### Fixture privacy concerns are **minimal**

Every row in this corpus is invented whole cloth. There is no real traveler,
no real unit, no real vendor, no real GTCC number, no real LOA string, no real
DTS submission, and no real receipt. There is nothing in this corpus that needs
to be redacted, hashed, anonymized, sampled-down, or held inside a controlled
environment. The corpus can ship in the public repository without a separate
data-handling review.

This does **not** relax ordinary engineering hygiene around operational
artifacts. Do not commit DB secrets, `.env` files, Terraform state, Lambda
probe output containing secret JSON, local connection strings, or private notes
about real people or systems.

This means a coding agent should **not**:

- Spend implementation budget on tokenization, PII scrubbing, or anonymization
  pipelines.
- Build a "real-data preview" mode that loads a different fixture set.
- Add a config switch that toggles between synthetic and non-synthetic.
- Treat the seed corpus as if losing the file is an incident.

### AO authority boundaries remain **critical**

The product the corpus feeds must not approve, deny, certify, return, cancel,
amend, or submit any voucher; must not determine entitlement or payability;
must not characterize anyone as fraudulent, abusive, in misuse, or in
misconduct; and must not contact, notify, or escalate to any external party.
That boundary applies to the **synthetic content as much as to the runtime
code**. The validator in section 13 enforces the boundary on every story card,
every generated narrative field, every seeded draft note, every seeded
clarification request body, and every brief paragraph.

A coding agent will be tempted to make the demo more dramatic by writing a
draft note that says "this looks like fraud" or a finding summary that says
"return this voucher." Both fail the validator and are not how this product
positions itself. The right framing is "anomaly," "documentation gap,"
"policy-risk indicator," "evidence needing closer reviewer attention," and
"needs human review."

### Naming discipline (carried into the validator)

- Traveler `display_name` values use handles such as
  `Demo Traveler Alpha (Synthetic Demo)`. No realistic first/last-name pairs.
  No rank abbreviations attached to names. Role context goes in `role_label`
  only.
- Unit-style strings use clearly fictional handles such as
  `1st Synthetic Logistics Detachment (Demo)`. No real unit, base, command,
  service-component, or installation names.
- Vendor labels carry a `Demo` marker (e.g. `Hotel Coastal Demo`,
  `Air Carrier North Demo`). No real airline, hotel, ride-share, restaurant,
  fuel-station, or merchant names.
- Locations are invented and clearly fictional (e.g. `Coastal Demo City`,
  `Inland Demo Outpost`). No real cities, countries, bases, or installations.
- Funding-reference labels use the `LOA-DEMO-FY26-` prefix.
- Citation `source_identifier` values use the `synthetic_dtmo_checklist_demo_`
  / `synthetic_demo_reference_` prefix. The corpus does **not** quote real DoD
  policy text in this hackathon seed; later pilot work that loads real public
  excerpts must go through an approved reference-corpus review.
- Email addresses, phone numbers, GTCC PANs, SSN-shaped strings, and bank
  routing numbers do not appear anywhere in the corpus.

The validator has a small block-list and a small allow-list (synthetic markers)
that backstop these conventions automatically; see section 13.

---

## 4. Story-First Workflow Discipline

A coding agent should write the **story** before the **rows**.

The reason: a brief is only useful when the reviewer can see *why* this packet
is on screen and *what they should look at*. When fixtures are generated
field-up — pick a vendor, pick an amount, pick a category, pick a signal — the
result is plausible but undirected: nothing fuses, nothing prioritizes, the
draft clarification has nothing to say. The brief becomes a list of disconnected
flags.

Story-first inverts that. Each voucher begins as a single YAML card describing:

1. **Pain pattern(s)** the voucher exists to demonstrate.
2. **AO-facing experience** when the brief opens (what the reviewer sees first,
   what citation appears, what draft note appears, what needs-human-review
   label appears).
3. **Story narrative** in two or three plain sentences (the reconstructed trip
   and where it breaks).
4. **Required signals, findings, missing items, and citations** the brief must
   surface to make 1–3 land.
5. **Concrete line items, evidence rows, prior-summary text, and pre-existing
   flags** that justify each signal/finding/missing item.

The generator reads the card top-down: the line items and evidence rows exist
because the findings need them; the findings exist because the brief needs
them; the brief exists because the AO-facing experience demands it. A coding
agent who reverses this order will produce noise.

The schema plan section 7.2 gives one paragraph per voucher describing exactly
this — that paragraph is the seed of the story card and should be copied into
each card's `narrative` field as the starting point, not paraphrased away.

---

## 5. Pain Pattern → Story → Fixture Bridge

The twelve pain patterns are sanitized practitioner-derived observations about
how voucher review actually fails in practice. They are stated abstractly so
the corpus can demonstrate them with invented detail. Each pattern below maps
to one or more voucher IDs (the same mapping appears in schema plan section
7.6, which is the authoritative source).

| Pain pattern (interview-derived, sanitized) | Story moment in the brief | Voucher(s) | Primary tables exercised |
|---|---|---|---|
| Forced-audit receipt review where the reviewer must inspect a categorization plus the receipt evidence in tandem. | Brief opens on the miscategorized line with the evidence vendor label visible side-by-side. | V-1004 | `vouchers.pre_existing_flags`, `voucher_line_items.category`, `evidence_refs.vendor_label_on_evidence` |
| Lodging or other line with no attached receipt at all. | "No lodging receipt attached" appears as a missing-information item, not as a finding allegation. | V-1002, V-1011 | `evidence_refs.content_type_indicator = none_attached_demo`, `missing_information_items` |
| Weak or local-paper receipt that is hard to read. | Finding category `weak_or_local_paper_receipt` with `legibility_cue = poor` evidence shown verbatim. | V-1002, V-1007, V-1012 | `evidence_refs.content_type_indicator = handwritten_local_paper_demo`, `legibility_cue` |
| LOA / funding-pot label that is ambiguous or unparseable. | Finding `ambiguous_loa_or_funding_reference` with the literal string surfaced; citation hits the `funding_reference_format` topic. | V-1004 | `vouchers.funding_reference_quality = ambiguous`, `policy_citations.topic = funding_reference_format` |
| Stale memory: a packet submitted weeks after the trip with thin reconstruction. | Brief explicitly notes the gap between expense dates and `demo_packet_submitted_at`. | V-1006 | `vouchers.demo_packet_submitted_at`, `voucher_line_items.claimed_by_traveler_at` |
| Mis-click categorization or paperwork math that does not reconcile. | Finding `paperwork_or_math_inconsistency` with the receipt subtotal/tax/claimed amount visible. | V-1004, V-1009 | `voucher_line_items.amount_minor_units`, `evidence_refs.amount_on_face_minor_units` |
| Amount on the line item does not match the amount on the receipt. | Finding `amount_mismatch` with side-by-side amounts. | V-1003 | `voucher_line_items.amount_minor_units` vs `evidence_refs.amount_on_face_minor_units` |
| Two hotel charges that overlap by one or more nights. | Finding `duplicate_or_multiple_charge` plus a needs-human-review label on the second lodging line because dual-lodging is a human determination. | V-1003 | Two `voucher_line_items` rows with overlapping `expense_date`s; `story_findings.needs_human_review = true` |
| Cash/ATM and currency-exchange reconstruction. | Brief lays out the ATM sequence, shows `exchange_rate_to_usd` per foreign-currency line, surfaces signals as review prompts only. | V-1007 | `voucher_line_items.category = cash_atm`/`currency_exchange`, `exchange_rate_to_usd`, `external_anomaly_signals` |
| Missing dates, overlapping details, or strange numbers. | Brief visualizes the trip window with the out-of-window expense and labels the unusual number for reviewer reconstruction. | V-1008 | `voucher_line_items.expense_date` outside `vouchers.trip_*`, `evidence_refs.evidence_date_on_face IS NULL` |
| OCONUS vendor that does not produce standardized receipts. | Finding `oconus_vendor_edge_case` with `needs_human_review = true`; missing-information item notes that automated retrieval may not be possible. | V-1007, V-1012 | `evidence_refs.payment_evidence_cue = absent`, `missing_information_items.expected_location_hint` |
| Unclear or possibly unjustified expense, where the responsible move is to ask, not to allege. | Finding `unclear_or_possibly_unjustified_expense` with `needs_human_review = true`; brief explicitly does not say unauthorized / nonpayable / fraudulent. | V-1010 | `voucher_line_items.category = other_demo`, `story_findings.needs_human_review = true`, brief vocabulary check |

The validator in section 13 walks the schema plan section 7.6 coverage map and
asserts each row resolves to at least one voucher, one finding, one provenance
pointer, and either a citation or an explicit needs-human-review reason.
Do not store interviewee names or raw interview notes in the fixture metadata;
the public artifact records only these sanitized pain-pattern labels.

---

## 6. Three Hero Demo Stories

Three vouchers are designated as **hero demo stories**. The hero set is curated
so a five-minute walkthrough can demonstrate the bread-and-butter case, the
multi-issue fusion case, and the authority-boundary case in that order, without
having to swap context.

### Hero 1 — V-1002: "The lodging receipt isn't attached, and the meals receipt is a slip of paper."

- **Why it's a hero:** every reviewer recognizes this in five seconds. Missing
  receipt + weak local-paper receipt is an immediately legible review burden,
  and the brief has somewhere obvious to start.
- **What the AO sees first:** the lodging line, with a missing-information item
  saying "no lodging receipt attached" and a citation to the
  `valid_receipt` topic. The meals line surfaces second with the
  `weak_or_local_paper_receipt` finding and the synthetic local-paper evidence
  cue visible.
- **Boundary moment:** the prior-pattern signal on T-101 is shown as a review
  prompt, not as a finding or as evidence of intent.
- **Demo beats:** open the queue → V-1002 is high-priority → the brief shows
  two clear findings, two missing-information items, one cited excerpt, one
  prior-pattern signal labeled as a review prompt → reviewer adapts the draft
  clarification note → reviewer flips the status to
  `awaiting_traveler_clarification` and the audit trail shows the scoped write
  with the boundary reminder attached.

### Hero 2 — V-1003: "Two hotels overlap one night. The transport amount doesn't match its receipt."

- **Why it's a hero:** layered fusion. Two findings of different categories,
  two signals, and a needs-human-review label reminds the reviewer that
  dual-lodging is a legitimate possibility the system will not infer away.
- **What the AO sees first:** the side-by-side comparison of the two lodging
  rows with the overlapping night highlighted, plus the side-by-side
  comparison of the transport line amount against the receipt amount.
- **Boundary moment:** the overlap is surfaced as a duplicate/multiple-charge
  review surface, but the brief does **not** conclude that the second lodging
  line is an improper duplicate. The second lodging line carries
  `needs_human_review = true` because the system cannot tell whether
  dual-lodging was contemplated for the trip.
- **Demo beats:** open V-1003 → the brief surfaces overlap and amount mismatch
  with citations to `duplicate_charge_review` and `lodging_documentation` →
  the needs-human-review label is visible and explained → reviewer marks the
  finding `reviewed_unresolved` (not `approved`, not `denied`) and the audit
  trail captures the scoped write.

### Hero 3 — V-1010: "This expense is unclear, and the system will not say it is unauthorized."

- **Why it's a hero:** the authority-boundary case. This is the moment the
  audience watches for, and the moment the brief's vocabulary discipline
  matters most.
- **What the AO sees first:** a single line item with `category = other_demo`,
  an unclear vendor label, and weak evidence cues. The finding category is
  `unclear_or_possibly_unjustified_expense` and the wording is anchored in
  the spec-permitted vocabulary ("anomaly," "documentation gap," "evidence
  needing closer reviewer attention").
- **Boundary moment:** the demo deliberately tries to push the system into a
  fraud allegation by issuing a tool call that asks the system to characterize
  the line as fraudulent. The seeded refusal in section 7.4 of the schema
  plan satisfies this from cold start; the live demo can repeat the call to
  show the live refusal too.
- **Demo beats:** open V-1010 → the brief uses neutral vocabulary throughout →
  the needs-human-review label is visible → the audit trail shows the seeded
  refusal of the fraud-characterization request and (if the live attempt is
  made) a fresh refusal event with an actionable reason.

The remaining nine vouchers (V-1001, V-1004 through V-1009, V-1011, V-1012) are
**supporting** vouchers. They make the queue feel real, exercise every category
and signal type, and are loaded by the same seed routine as the hero set. They
are not the focus of the live walkthrough but should be inspectable on demand.

---

## 7. Twelve-Voucher Corpus

The full twelve-voucher corpus is defined in `docs/schema-implementation-plan.md`
section 7.2. **This plan does not restate the corpus**; it commits to honoring
the scenario, required findings, missing-information shape, review-status
spread, and volume bounds. A coding agent's job is to translate each voucher
paragraph into a story card (section 10) and a deterministic generator output
(section 11).

For convenience, the table below maps voucher IDs to traveler, trip flavor,
hero/supporting role, and the schema-plan-required review-status
distribution from section 7.3. Anything beyond this table comes from the
schema plan.

| Voucher | Traveler | Trip flavor | Role | Seeded `review_status` |
|---|---|---|---|---|
| V-1001 | T-101 | OCONUS conference (clean control 1) | Supporting | `ready_for_human_decision` |
| V-1002 | T-101 | OCONUS site visit, missing + weak receipt | **Hero 1** | `in_review` |
| V-1003 | T-102 | CONUS multi-leg, duplicate hotel + amount mismatch | **Hero 2** | `in_review` |
| V-1004 | T-102 | CONUS coastal training, forced-audit + LOA + miscategorization | Supporting | `in_review` |
| V-1005 | T-103 | CONUS staff trip (clean control 2) | Supporting | `ready_for_human_decision` |
| V-1006 | T-103 | Old CONUS trip, stale memory + weak justification | Supporting | `needs_review` |
| V-1007 | T-104 | Austere OCONUS, ATM/cash + exchange-rate | Supporting | `in_review` |
| V-1008 | T-104 | CONUS, missing dates + overlapping details | Supporting | `in_review` |
| V-1009 | T-105 | CONUS, mis-click categorization + bad math (first-time submitter) | Supporting | `needs_review` |
| V-1010 | T-105 | OCONUS, unclear or possibly unjustified expense | **Hero 3** | `needs_review` |
| V-1011 | T-102 | Mixed packet, insufficient evidence overall (`is_partial = true` brief) | Supporting | `in_review` |
| V-1012 | T-101 | OCONUS, vendor edge case | Supporting | `needs_review` |

Volumes per schema plan section 7.5 (the generator must hit these ranges):

| Entity | Range across the corpus |
|---|---|
| `travelers` | 5–6 |
| `vouchers` | 12 |
| `voucher_line_items` | 75–100 |
| `evidence_refs` | 75–150 |
| `external_anomaly_signals` | 20–25 |
| `story_findings` | 35–50 |
| `missing_information_items` | 20–30 |
| `review_briefs` | 12 (one per voucher; live demo regenerates one to exercise versioning) |
| `ao_notes` | At least one per `kind` value (`ao_note`, `draft_clarification`, `synthetic_clarification_request`, `ao_feedback`) |
| `workflow_events` | 50–70, including the two seeded refusals from schema plan section 7.4 |

The signal counts named in schema plan section 7.2 are required **anchor**
signals, not the complete signal budget. To satisfy the schema plan section 7.5
volume range without inventing unsupported noise, generate 20 total
`external_anomaly_signals` with this distribution:

| Voucher | Signal count | Required signal types |
|---|---:|---|
| V-1001 | 0 | none |
| V-1002 | 2 | `repeated_correction_pattern`, `traveler_baseline_outlier` |
| V-1003 | 2 | `duplicate_payment_risk`, `unusual_amount` |
| V-1004 | 3 | `high_risk_mcc_demo`, `repeated_correction_pattern`, `unusual_amount` |
| V-1005 | 0 | none |
| V-1006 | 2 | `traveler_baseline_outlier`, `date_location_mismatch` |
| V-1007 | 4 | `split_disbursement_oddity`, `traveler_baseline_outlier`, `unusual_amount`, `peer_baseline_outlier` |
| V-1008 | 3 | `date_location_mismatch`, `unusual_amount`, `peer_baseline_outlier` |
| V-1009 | 0 | none; this stays a no-prior-history, story/evidence-only case |
| V-1010 | 0 | none; this stays an authority-boundary, story-only case |
| V-1011 | 2 | `repeated_correction_pattern`, `traveler_baseline_outlier` |
| V-1012 | 2 | `peer_baseline_outlier`, `high_risk_mcc_demo` |

Every signal remains a review prompt with `is_official_finding = false` and
`not_sufficient_for_adverse_action = true`; no signal may create a new finding
unless the card already has the evidence/citation/story support for it.
If schema plan section 7.2 is later edited to make per-voucher signal counts
exact rather than minimum anchors, update this table in the same change so the
volume target and story cards stay consistent.

### External signal IDs and fraud-mock ownership

The seed generator owns the canonical deterministic signal inventory for the
demo. For every signal row:

- `signal_key` is deterministic within the voucher, formatted as
  `<signal_type>:<scenario_slug>:<ordinal>`, for example
  `duplicate_payment_risk:lodging_overlap:01`.
- `signal_id` is derived from the voucher and key, formatted as
  `SIG-<voucher_id>-<slugified_signal_key>`.
- `(voucher_id, signal_key)` is unique and is the idempotence key used by the
  loader, repository, and fraud-mock integration.

The fraud-mock Lambda must mirror the seeded deterministic signals when asked
for a seeded voucher, using the same `signal_key` values, or supplement only a
missing deterministic demo signal that the seed did not already persist. It
must not create a duplicate for an existing `(voucher_id, signal_key)`.
Repository upsert logic treats a unique-key conflict as a successful replay
and returns the already stored row.

---

## 8. Synthetic Identity Conventions

These are the exact value patterns the generator emits. The validator (section
13) uses the same patterns.

- **`travelers.traveler_id`:** `T-101`, `T-102`, `T-103`, `T-104`, `T-105`.
- **`travelers.display_name`:** `Demo Traveler {Alpha|Bravo|Charlie|Delta|Echo} (Synthetic Demo)`.
- **`travelers.role_label`:** one of `staff_nco_demo`, `field_grade_demo`,
  `staff_field_grade_demo`, `senior_nco_demo`, `junior_officer_demo`.
- **`travelers.home_unit_label`:** `{Nth} Synthetic {Logistics|Support|Training}
  Detachment (Demo)`.
- **`vouchers.voucher_id`:** `V-1001` through `V-1012`.
- **`vouchers.declared_origin` / `declared_destinations`:** invented coastal /
  inland / outpost names (e.g. `Coastal Demo City`, `Inland Demo Outpost`,
  `Northern Demo Garrison`). Mark every location with the literal substring
  `Demo`.
- **`vouchers.funding_reference_label`:** `LOA-DEMO-FY26-####`. The
  V-1004 ambiguous case uses `LOA-DEMO-FY26-???` or the literal sentinel
  `FUND-POT-DEMO-AMBIG`.
- **`voucher_line_items.vendor_label`:** `{Hotel|Air Carrier|Ground Transport
  |Eatery|Cash ATM Provider|Currency Exchange Booth} {Geo} Demo` where `Geo` is
  one of the invented locations above.
- **`voucher_line_items.currency_code`:** `USD` for CONUS lines; synthetic
  OCONUS demo lines may use common ISO-style display codes such as `EUR` or
  `JPY`, or the ISO testing code `XTS`, with `exchange_rate_to_usd` populated.
  Do not pair any currency with a real city, country, base, or vendor.
- **`evidence_refs.vendor_label_on_evidence`:** matches `vendor_label` for
  consistent rows; deliberately diverges for the V-1004 miscategorization case.
- **`policy_citations.citation_id`:** `CITE-{TOPIC}-###` (e.g.
  `CITE-RECEIPT-001`, `CITE-LOA-002`).
- **`policy_citations.source_identifier`:** `synthetic_dtmo_checklist_demo_v1`
  or `synthetic_demo_reference_v1`. The text is short, neutral, and clearly
  marked as synthetic.
- **`external_anomaly_signals.synthetic_source_label`:**
  `synthetic_compliance_service_demo`.
- **`external_anomaly_signals.signal_key`:**
  `<signal_type>:<scenario_slug>:<ordinal>`, stable across the seed generator
  and the fraud-mock Lambda.
- **`external_anomaly_signals.signal_id`:**
  `SIG-<voucher_id>-<slugified_signal_key>`, derived from `signal_key`.
- **`ao_notes.actor_label`:** `demo_ao_user_1` (the seeded demo identity).
- **`workflow_events.actor_label`:** the same `demo_ao_user_1` for seeded
  reviewer-side events; `synthetic_demo_seed` for system-side events created at
  load time.
- **`workflow_events.human_authority_boundary_reminder`:** the exact canonical
  string from schema plan section 6.6 and
  `src/ao_radar_mcp/safety/authority_boundary.py`. If the seed package lands
  before the application package, define the string once in
  `ops/seed/constants.py` and have the application import or copy that exact
  value when its safety module is created.
- **Dates:** all dates fall inside `FY26` (2025-10-01 through 2026-09-30) so the
  corpus is internally consistent. The V-1006 stale-memory case uses
  `expense_date` values weeks before `demo_packet_submitted_at`, all still
  inside FY26.

The validator rejects any row whose value pattern violates the above.

---

## 9. Seed Artifact Layout under `ops/seed/`

The application plan section 4 reserves `ops/seed/` for this work. The
recommended layout is below; a coding agent may rename files without changing
the boundaries, but the **categories** are load-bearing.

```
ops/
  seed/
    __init__.py
    cards/                          # source of truth: one YAML per voucher
      V-1001.yaml
      V-1002.yaml
      V-1003.yaml
      V-1004.yaml
      V-1005.yaml
      V-1006.yaml
      V-1007.yaml
      V-1008.yaml
      V-1009.yaml
      V-1010.yaml
      V-1011.yaml
      V-1012.yaml
    travelers.yaml                  # five traveler rows
    prior_summaries.yaml            # zero/one/two summaries per traveler
    citations.yaml                  # policy_citations corpus
    coverage_map.yaml               # machine-readable schema plan § 7.6
    refusal_seeds.yaml              # the two seeded refusals (§ 7.4)
    generators/
      __init__.py
      cards.py                      # YAML card loader + schema validation
      travelers.py                  # travelers + prior_voucher_summaries rows
      citations.py                  # policy_citations rows
      vouchers.py                   # vouchers + line_items + evidence_refs
      signals.py                    # external_anomaly_signals + finding_signal_links
      findings.py                   # story_findings + missing_information_items
      briefs.py                     # review_briefs + ao_notes
      events.py                     # workflow_events for every seeded write
      determinism.py                # fixed seed + UUID/timestamp helpers
    validators/
      __init__.py
      synthetic_markers.py          # display names, vendor markers, LOA prefix
      blocked_status.py             # mirrors schema § 6.4 blocklist
      unsafe_wording.py             # context-aware text check (mirrors § 6.4)
      coverage.py                   # walks coverage_map.yaml
      audit_invariants.py           # walks schema § 8 audit-event matrix
      fk_and_volume.py              # FK presence and § 7.5 volume bounds
    validate.py                     # CLI entrypoint for pure validation
    load.py                         # main entrypoint: validate then load
    reset.py                        # guarded reset_demo()
    snapshot.py                     # optional: write JSON snapshots for diffing
    snapshots/                      # generated; gitignored by default except
                                    # README.md explaining local refresh/compare
```

Notes on the layout:

- `cards/` and the four root YAML files (`travelers.yaml`,
  `prior_summaries.yaml`, `citations.yaml`, `coverage_map.yaml`,
  `refusal_seeds.yaml`) are the **only** files a human edits to change demo
  content. Everything in `generators/` and `validators/` is logic.
- The generator never invents narrative content beyond what the cards specify.
  It may derive deterministic IDs, timestamps, hook arrays, and fixed constants
  from explicit card fields and this plan. If a card is silent on a narrative
  field, evidence cue, citation, missing item, signal rationale, or finding
  text the schema/demo requires, generation fails loudly rather than filling in
  prose.
- The loader is the only path that talks to Postgres. Generators run pure
  in-memory and are unit-testable without the database.
- `snapshots/` exists for local determinism checks. Snapshots are not the
  source of truth, are gitignored by default, and never feed the loader. If a
  later team chooses to commit golden snapshots, make that an explicit review
  decision rather than an accidental generated-file commit.

---

## 10. Story Card Schema

Each card under `ops/seed/cards/` is a YAML document with the structure below.
This is illustrative; the loader uses a Pydantic model (or equivalent) so the
schema is enforced at load time.

```yaml
# ops/seed/cards/V-1003.yaml
voucher_id: V-1003
traveler_id: T-102
hero: true
hero_position: 2
narrative: |
  CONUS multi-leg trip. Two hotel line items overlap by one night and a
  transport line's claimed amount differs from its receipt amount. The brief
  surfaces the overlap and the amount mismatch, but the second lodging line
  carries needs_human_review because dual-lodging can be legitimate and the
  system does not infer intent.
pain_patterns:
  - amount_mismatch
  - duplicate_or_multiple_charge
expected_ao_experience:
  first_focus: lodging_overlap_side_by_side
  required_citations:
    - duplicate_charge_review
    - lodging_documentation
  required_signals:
    - duplicate_payment_risk
    - unusual_amount
  required_findings:
    - duplicate_or_multiple_charge
    - amount_mismatch
    - story_coherence_break
  required_labels:
    - needs_human_review_on_second_lodging
  required_missing_information_items: 2
  brief_uncertainty: medium
  is_partial: false
voucher:
  trip_purpose_category: tdy_conference_demo
  trip_start_date: 2026-02-09
  trip_end_date: 2026-02-13
  declared_origin: Inland Demo Garrison
  declared_destinations:
    - Coastal Demo City
    - Northern Demo Outpost
  funding_reference_label: LOA-DEMO-FY26-0042
  funding_reference_quality: clean
  justification_text: |
    Multi-leg coordination visit between Coastal Demo City and Northern Demo
    Outpost. Synthetic demo packet — not a real trip.
  pre_existing_flags: []
  demo_packet_submitted_at: 2026-02-18T15:04:00Z
  review_status: in_review
line_items:
  - line_index: 1
    expense_date: 2026-02-09
    amount_minor_units: 18900
    currency_code: USD
    category: lodging
    vendor_label: Hotel Coastal Demo
    payment_instrument_indicator: gtcc_like_demo
    evidence_refs:
      - content_type_indicator: receipt_pdf_demo
        legibility_cue: clear
        itemization_cue: itemized
        payment_evidence_cue: present
        vendor_label_on_evidence: Hotel Coastal Demo
        evidence_date_on_face: 2026-02-09
        amount_on_face_minor_units: 18900
        currency_code_on_face: USD
  - line_index: 2
    expense_date: 2026-02-10
    amount_minor_units: 21500
    currency_code: USD
    category: lodging
    vendor_label: Hotel Coastal Demo Annex
    payment_instrument_indicator: gtcc_like_demo
    free_text_notes: |
      Second lodging line that overlaps Feb 10 with line_index 1. Dual-lodging
      remains a human determination; do not call this duplicate without
      reviewer judgment.
    evidence_refs:
      - content_type_indicator: receipt_pdf_demo
        legibility_cue: clear
        itemization_cue: itemized
        payment_evidence_cue: present
        vendor_label_on_evidence: Hotel Coastal Demo Annex
        evidence_date_on_face: 2026-02-10
        amount_on_face_minor_units: 21500
        currency_code_on_face: USD
  # ...remaining six line items, including the transport line whose
  # amount_minor_units differs from amount_on_face_minor_units...
external_anomaly_signals:
  - signal_type: duplicate_payment_risk
    confidence: medium
    rationale_text: |
      Two lodging-line charges within the trip window overlap on Feb 10. Demo
      signal only — not an official finding.
  - signal_type: unusual_amount
    confidence: low
    rationale_text: |
      One transport line's claimed amount differs from its synthetic receipt
      amount by more than the demo tolerance. Review prompt only.
findings:
  - category: duplicate_or_multiple_charge
    severity: medium
    confidence: medium
    needs_human_review: false
    summary: |
      Two lodging rows overlap on Feb 10 and need side-by-side review.
    explanation: |
      The packet contains two lodging charges on the same synthetic trip night.
      This is a duplicate/multiple-charge review surface only; it is not a
      conclusion that either line is improper.
    suggested_question: |
      Do the two lodging rows describe separate stays for the same night, or
      should the packet include more context about the overlap?
    primary_citation_id: CITE-DUP-001
    packet_evidence_pointer:
      line_item_id: V-1003-LI-2
      excerpt_hint: lodging line 2 overlaps Feb 10
    signal_links:
      - duplicate_payment_risk
  - category: amount_mismatch
    severity: medium
    confidence: high
    needs_human_review: false
    summary: |
      The transport line's claimed amount differs from the receipt amount.
    explanation: |
      The claimed transport amount and the amount visible on the synthetic
      receipt do not reconcile on their face.
    suggested_question: |
      Could the traveler confirm the transport amount and provide the
      breakdown if the receipt total has changed?
    primary_citation_id: CITE-AMT-001
    packet_evidence_pointer:
      line_item_id: V-1003-LI-5
      evidence_ref_id: V-1003-LI-5-EV-1
      excerpt_hint: claim 240.00 vs receipt 218.00
    signal_links:
      - unusual_amount
  - category: story_coherence_break
    severity: low
    confidence: medium
    needs_human_review: false
    summary: |
      The trip narrative does not yet explain the lodging overlap.
    explanation: |
      The declared trip sequence explains most dates, but Feb 10 has two
      lodging rows without enough narrative context for reconstruction.
    suggested_question: |
      Could the traveler clarify the trip leg covering the second lodging
      night?
    primary_citation_id: CITE-CHECKLIST-001
    packet_evidence_pointer:
      line_item_id: V-1003-LI-2
      excerpt_hint: trip narrative does not yet account for second lodging
  - category: story_coherence_break
    severity: low
    confidence: low
    needs_human_review: true
    summary: |
      Dual-lodging authority cannot be inferred from the packet.
    explanation: |
      Dual-lodging can be legitimate, but the synthetic packet does not show
      enough context for the system to characterize the second lodging line.
    suggested_question: |
      Was dual-lodging authorized for the Feb 10 leg, or is one of these
      lines an inadvertent duplicate?
    packet_evidence_pointer:
      line_item_id: V-1003-LI-2
      excerpt_hint: needs_human_review on second lodging line
missing_information_items:
  - description: |
      No itinerary attachment for the trip leg covering the second lodging
      night.
    why_it_matters: |
      Without the leg itinerary, the reviewer cannot confirm whether dual
      lodging was contemplated for this trip.
    expected_location_hint: itinerary attachment on the packet
  - description: |
      No supporting note from the traveler explaining the transport amount
      difference.
    why_it_matters: |
      A short reconciliation note would let the reviewer close the
      amount_mismatch finding without further outreach.
    expected_location_hint: justification block or line free_text_notes
brief:
  priority_score: 0.74
  priority_rationale: |
    Multiple findings of medium severity with at least one needs_human_review
    label; review-difficulty signal is moderate. Workload guidance only.
  suggested_focus: |
    Open the two lodging lines side by side first, then the transport line.
  evidence_gap_summary: |
    Itinerary leg coverage and transport-amount reconciliation are missing.
  story_coherence_summary: |
    Trip narrative covers Feb 9 and Feb 11–13 cleanly; Feb 10 carries two
    lodging lines that may or may not be intentional dual-lodging.
  draft_clarification_note: |
    Could you confirm whether dual-lodging was authorized for the Feb 10 leg
    of this trip, and share the receipt or note that supports the transport
    amount on Feb 12? Synthetic demo draft — not an official communication.
  brief_uncertainty: medium
  is_partial: false
ao_notes:
  - kind: ao_note
    body: |
      Holding for clarification on the Feb 10 lodging overlap before
      requesting any further evidence.
seeded_workflow_events: []  # standard generation/scoped_write events are
                            # produced automatically by the generator; only
                            # one-off events such as the section 7.4 refusals
                            # are listed explicitly here.
```

The card schema is intentionally verbose. The verbosity makes the demo easy to
adjust by editing one file, and the validator can be strict because the inputs
are explicit.

`travelers.yaml`, `prior_summaries.yaml`, `citations.yaml`, `coverage_map.yaml`,
and `refusal_seeds.yaml` follow analogous shapes; their contents come from the
schema plan sections 7.1 and 5.6 (citations corpus must cover every flag
category exercised in the cards) and 7.4 (refusal seeds).

---

## 11. Deterministic Generation, Loading, and Validation Commands

All commands run from the repository root. The `ops.seed` package is importable
once the application's `pyproject.toml` (per application plan Phase 0) is in
place.

### Commands

| Command | Purpose | Touches DB? | Idempotent? |
|---|---|---|---|
| `python -m ops.seed.validate --cards-only` | Loads every YAML, validates against the card schema, runs the synthetic-marker / blocked-status / unsafe-wording validators on raw text. | No | Yes |
| `python -m ops.seed.snapshot --out /tmp/ao-radar-seed-a` | Runs the generators in memory and writes JSON snapshots to the requested directory so a coding agent can compare two runs. | No | Yes |
| `python -m ops.seed.validate` | Runs the cards-only validation, then runs the generators in memory and runs the FK/coverage/audit-invariant/volume validators against the in-memory rows. | No | Yes |
| `python -m ops.seed.load --reset` | Proves the connection is the synthetic demo target, runs the full validator, opens a transaction, deletes seeded rows in dependency order, inserts the generated corpus in load order (section 12), commits. | Yes | Yes (intended to be re-runnable from cold) |
| `python -m ops.seed.load` | Same as above without the reset/delete step; fails if the database already has rows for any seeded entity. Use this for the first ever load against a freshly migrated database. | Yes | No (single-use on an empty DB) |
| `python -m ops.seed.reset` | Convenience wrapper: same as `python -m ops.seed.load --reset`. Exists because `reset_demo` is the name in the application plan section 12. | Yes | Yes |

Every command exits non-zero on failure with a structured error pointing to the
specific card, row, or invariant that failed.

Local commands are for unit/integration development. The deployed hackathon
path is the Terraform-managed `db_ops` Lambda. It receives an operation payload
such as `{"operation":"migrate"}`, `{"operation":"seed"}`, or
`{"operation":"seed","reset":true}` and runs the same migration or seed code
inside the VPC with `DB_SECRET_ARN` and `DEMO_DATA_ENVIRONMENT=synthetic_demo`
injected by Terraform. Do not create ad hoc probe, migration, or seed Lambdas
outside Terraform.

### DB connection guard for load/reset

`load`, `load --reset`, and `reset` fail closed unless all of these are true:

- `DEMO_DATA_ENVIRONMENT` is exactly `synthetic_demo`.
- The expected `data_environment = synthetic_demo` CHECK constraints exist on
  `travelers` and `vouchers`.
- Existing rows in `travelers` and `vouchers`, if any, all have
  `data_environment = synthetic_demo`.
- Reset deletes only the canonical seeded IDs (`T-101` through `T-105`,
  `V-1001` through `V-1012`, and dependent rows reachable from those parents),
  not arbitrary tables or unconstrained rowsets.

Do not implement a flag that bypasses this guard, and do not expose reset as an
MCP tool.

### Determinism rules

- The generator imports a single fixed seed string, e.g.
  `_SEED = "ao-radar-synthetic-v1"`, used only through deterministic helpers
  in `generators/determinism.py`.
- Prefer SHA-256-derived integers, stable sorting, and deterministic ID
  formatting over Python's process-global `random` state or `uuid4()`.
- All `created_at`, `updated_at`, and `received_at` timestamps are derived
  deterministically from the card's declared dates; nothing reads "now."
- All primary keys (e.g. `V-1003-LI-2`, `V-1003-LI-5-EV-1`,
  `V-1003-FND-1`) are derived from card structure, not from random UUIDs. The
  generator helper in `generators/determinism.py` owns the formatting rules.
- The seed routine produces the same output across cold starts, across
  Python minor versions, and across machines. The proof is a two-directory
  compare:
  ```bash
  python -m ops.seed.snapshot --out /tmp/ao-radar-seed-a
  python -m ops.seed.snapshot --out /tmp/ao-radar-seed-b
  diff -ru /tmp/ao-radar-seed-a /tmp/ao-radar-seed-b
  ```

### Validator inventory

The validator package under `ops/seed/validators/` contains the following
checks, each runnable in isolation:

- `synthetic_markers.py` — every `display_name` contains `(Synthetic Demo)` or
  a `DEMO-` prefix; every `vendor_label` and `vendor_label_on_evidence`
  contains `Demo`; every `home_unit_label` contains `Demo`; every
  `funding_reference_label` matches `^LOA-DEMO-FY26-` or the
  `FUND-POT-DEMO-AMBIG` sentinel; every traveler/voucher row has
  `data_environment = synthetic_demo`.
- `blocked_status.py` — mirrors schema plan section 6.4. Asserts no
  `vouchers.review_status`, no `story_findings.review_state`, and no
  `workflow_events.resulting_status` value matches the blocklist; runs the
  same check on every card field that resolves to those columns.
- `unsafe_wording.py` — context-aware text check (schema plan section 6.4)
  applied to every narrative field generated for storage:
  `vouchers.justification_text`, `voucher_line_items.free_text_notes`,
  `prior_voucher_summaries.summary_text` and `recurring_correction_pattern`,
  `external_anomaly_signals.rationale_text`,
  `story_findings.summary` / `explanation` / `suggested_question`,
  `missing_information_items.description` / `why_it_matters`,
  `review_briefs.priority_rationale` / `suggested_focus` /
  `evidence_gap_summary` / `story_coherence_summary` /
  `draft_clarification_note`, `ao_notes.body`. Policy-citation `excerpt_text`
  is excluded because the section 6.4 split is intentional; it gets a softer
  marker check that requires a `synthetic_dtmo_checklist_demo_` or
  `synthetic_demo_reference_` source label.
  `workflow_events.rationale_metadata` may store a rejected requested value
  such as `approved` or `fraudulent` for traceability, but the validator must
  ensure it is typed as rejected input and not presented as system-authored
  narrative.
- `authority_boundary.py` — asserts every seeded brief/export/event boundary
  field equals the schema plan section 6.6 canonical string and contains the
  required no approve, deny, certify, return, cancel, amend, submit,
  entitlement, payability, fraud, and external-contact clauses.
- `signal_keys.py` — asserts every `external_anomaly_signals` row has a
  deterministic `signal_key`, that `(voucher_id, signal_key)` is unique, and
  that the generated `signal_id` matches the key formatting rule in section 8.
- `coverage.py` — walks `coverage_map.yaml` and asserts every required
  practitioner case resolves to at least one voucher with at least one
  `story_findings` row, at least one `packet_evidence_pointer`, and either a
  resolvable `primary_citation_id` or an explicit `needs_human_review = true`
  reason.
- `audit_invariants.py` — walks the schema plan section 8 audit-event invariant
  matrix and asserts every seeded scoped write, every seeded brief generation,
  every seeded `needs_human_review = true` finding, and the two seeded refusals
  produce the matching `workflow_events` row in the generator output.
- `fk_and_volume.py` — every FK in the generated rowset resolves; row counts
  fall inside the schema plan section 7.5 ranges; every `evidence_refs` row
  has either a `line_item_id` or a `packet_level_role`; `is_partial = true`
  appears on at least one brief (V-1011); the spread of seeded `review_status`
  values matches schema plan section 7.3.

Failure messages from any validator point at a specific card path and field so
a coding agent can fix the source without spelunking through the generator.

---

## 12. Load Order

Loading happens inside a single transaction. The order respects every FK in
the schema and lets the validator catch dangling references before insert.

1. `policy_citations` — no FKs.
2. `travelers` — no FKs.
3. `prior_voucher_summaries` — FK to `travelers`.
4. `vouchers` — FK to `travelers`.
5. `voucher_line_items` — FK to `vouchers`.
6. `evidence_refs` — FK to `vouchers`, optional FK to `voucher_line_items`.
7. `external_anomaly_signals` — FK to `vouchers`.
8. `story_findings` — FK to `vouchers`, optional FK to `policy_citations`.
9. `finding_signal_links` — FKs to `story_findings` and
   `external_anomaly_signals`.
10. `missing_information_items` — FK to `vouchers`, optional FK to
    `voucher_line_items`.
11. `review_briefs` — FK to `vouchers`; `policy_hooks`, `signal_hooks`,
    `finding_hooks`, and `missing_information_hooks` reference rows from steps
    1, 7, 8, and 10 respectively. The generator asserts every hook resolves to
    a real row before insert.
12. `ao_notes` — FK to `vouchers`, optional FK to `story_findings`.
13. `workflow_events` — FK to `vouchers`, optional FKs by `target_kind` to
    `story_findings`, `ao_notes`, `review_briefs`,
    `external_anomaly_signals`, `policy_citations`, or
    `missing_information_items` according to the enum value. Inserted last so
    every `target_id` it references already exists.

The reset path deletes only the canonical seeded IDs and their dependent rows
in **reverse** order:
`workflow_events`, then `ao_notes`, then `review_briefs`, then
`missing_information_items`, then `finding_signal_links`, then
`story_findings`, then `external_anomaly_signals`, then `evidence_refs`, then
`voucher_line_items`, then `vouchers`, then `prior_voucher_summaries`, then
`travelers`, then `policy_citations`. The reset and reload happen inside the
same transaction so a partial reset can never leave the database half-populated.

---

## 13. Validators (what runs and when)

The pure validator stack runs on the in-memory generator output before the
loader opens a write transaction. Anything the database CHECK can also catch is
caught here first so the failure message is human-readable. When a DB
connection is available, the loader adds a short rollback-only schema preflight
after the connection guard and before deleting or inserting seeded rows. The
schema-level CHECKs (schema plan sections 6.1, 6.3, 6.4, 6.5) remain the
**source of truth**: the validator mirrors the schema's rules, never broadens
them, and never relaxes them.

The validator stack runs in this order; the first failure aborts the load:

1. `generators/cards.py` via `validate.py` — every YAML parses against the
   card Pydantic schema.
2. `synthetic_markers.py`.
3. `blocked_status.py`.
4. `unsafe_wording.py`.
5. The generators run end-to-end in memory.
6. `fk_and_volume.py`.
7. `coverage.py`.
8. `audit_invariants.py`.
9. When a database connection is available (`load`, `load --reset`, or an
   explicit future `--db-checks` option), the schema plan section 6.4 status
   CHECKs are spot-checked inside a rollback-only transaction by attempting one
   blocked value per status-like field and asserting the database rejects each
   write. The pure `python -m ops.seed.validate` command does not touch the DB.

Once the pure validator stack and any DB preflight pass, the loader opens the
write transaction in section 12 and inserts.

---

## 14. Post-Postgres Runbook

A coding agent (or demo operator) follows this runbook end-to-end once the
infra plan and the schema plan migrations are in place. Each step is small,
explicit, and verifiable.

1. **Confirm prerequisites.**
   - Infra plan Phase 2 is applied; RDS is reachable from the
     Terraform-managed, VPC-attached `db_ops` Lambda.
   - `DB_SECRET_ARN` and `DEMO_DATA_ENVIRONMENT=synthetic_demo` are exported
     in the `db_ops` Lambda environment.
   - Schema plan Phase 1 (tables) and Phase 2 (constraints/indexes) have been
     applied through the `db_ops` migration operation, which calls
     `ops/scripts/run_migrations.py`.

2. **Sanity-check the schema.**
   - Confirm the `data_environment = synthetic_demo` CHECK exists on
     `travelers` and `vouchers`.
   - Confirm `vouchers.review_status` rejects `approved` (a one-row insert
     attempt is the cheapest test).
   - Confirm the database is empty for every seeded table.

3. **Validate the cards in isolation.**
   ```
   python -m ops.seed.validate --cards-only
   ```
   Fix any card-level errors before continuing.

4. **Snapshot for determinism.**
   ```
   python -m ops.seed.snapshot --out /tmp/ao-radar-seed-a
   python -m ops.seed.snapshot --out /tmp/ao-radar-seed-b
   diff -ru /tmp/ao-radar-seed-a /tmp/ao-radar-seed-b
   ```
   The diff should be empty. A non-empty diff means the generator is not
   deterministic; fix the generator before touching the database.

5. **Run the full validator (no DB writes).**
   ```
   python -m ops.seed.validate
   ```
   This runs every pure validator step in section 13 against the in-memory
   generator output.

6. **Load the corpus.**
   - First-ever load against a freshly migrated database, through `db_ops`:
     ```
     aws lambda invoke --function-name ao-radar-db-ops \
       --payload '{"operation":"seed"}' \
       --cli-binary-format raw-in-base64-out /tmp/ao-radar-seed.json
     ```
   - Subsequent loads (or re-loads after a card edit), through `db_ops`:
     ```
     aws lambda invoke --function-name ao-radar-db-ops \
       --payload '{"operation":"seed","reset":true}' \
       --cli-binary-format raw-in-base64-out /tmp/ao-radar-seed.json
     ```
   The loader runs the connection guard in section 11, runs the validator stack
   one final time, performs the DB preflight, then runs the inserts in section
   12 order.

7. **Spot-check the loaded data.**
   - `SELECT count(*) FROM travelers` returns 5.
   - `SELECT count(*) FROM vouchers` returns 12.
   - `SELECT count(*) FROM voucher_line_items` falls within 75–100.
   - `SELECT count(*) FROM evidence_refs` falls within 75–150.
   - `SELECT count(*) FROM external_anomaly_signals` falls within 20–25.
   - `SELECT count(*) FROM story_findings` falls within 35–50.
   - `SELECT count(*) FROM missing_information_items` falls within 20–30.
   - `SELECT count(*) FROM review_briefs` returns 12.
   - `SELECT count(*) FROM workflow_events WHERE event_type = 'refusal'`
     returns at least 2 (the seeded refusals from schema plan section 7.4).
   - `SELECT count(*) FROM workflow_events WHERE event_type = 'generation'`
     returns at least 12 (one per seeded brief).
   - `SELECT count(*) FROM review_briefs WHERE is_partial` returns at least 1.
   - `SELECT human_authority_boundary_reminder FROM workflow_events
     WHERE coalesce(human_authority_boundary_reminder, '') = ''` returns no
     rows.

8. **Hand off to the application plan Phase 2.**
   Read tools (`list_vouchers_awaiting_action`, `get_voucher_packet`,
   `get_traveler_profile`, `list_prior_voucher_summaries`,
   `get_policy_citation`) should now return non-empty results immediately on
   first call.

9. **(Optional) Pre-demo regeneration.**
   Before the live walkthrough, re-run the `db_ops` seed operation with
   `reset = true` so the demo opens against a known clean state. Do not add a
   cockpit-facing reset tool.

If any spot-check in step 7 fails, the validator should have caught it earlier;
treat the failure as a validator gap and fix the validator before re-running
the loader.

---

## 15. Implementation Phases

Each phase ends in a small, individually verifiable deliverable. The
phases align with schema plan Phase 3 and unblock application plan Phase 2.

### Phase A — Card schema + first card

- Land the `ops/seed/cards/V-1001.yaml` clean control with the full card
  schema represented.
- Land the Pydantic card model and the `cards-only` validator command.
- **Exit criterion:** `python -m ops.seed.validate --cards-only` passes
  on a single-card corpus.

### Phase B — Generators and snapshot

- Implement every generator under `ops/seed/generators/`.
- Implement `python -m ops.seed.snapshot --out <dir>` for local
  determinism checks. Do not commit generated snapshots unless the team
  deliberately chooses a golden-snapshot workflow.
- **Exit criterion:** the snapshot output is byte-stable across two runs in
  the same checkout.

### Phase C — Full validator stack

- Implement every validator under `ops/seed/validators/`.
- Implement `python -m ops.seed.validate` (cards + in-memory rows).
- **Exit criterion:** the validator passes on the V-1001 single-card corpus
  and explains exactly which check fails when V-1001 is intentionally broken
  (e.g. by removing the `(Synthetic Demo)` marker).

### Phase D — Twelve-voucher cards

- Add cards V-1002 through V-1012, the five travelers, the prior summaries,
  the citations corpus, the coverage map, and the two refusal seeds.
- **Exit criterion:** `python -m ops.seed.validate` passes on the full
  twelve-voucher corpus.

### Phase E — Loader and reset

- Implement `python -m ops.seed.load`, `python -m ops.seed.load --reset`,
  and `python -m ops.seed.reset` against a real Postgres connection.
- The loader runs the full validator stack one more time before opening the
  transaction.
- The reset path uses the section 11 DB connection guard and deletes only
  canonical seeded IDs plus dependent rows.
- **Exit criterion:** every spot-check in section 14 step 7 passes.

### Phase F — Application read-tool integration

- Coordinate with application plan Phase 2: confirm
  `list_vouchers_awaiting_action`, `get_voucher_packet`,
  `get_traveler_profile`, `list_prior_voucher_summaries`, and
  `get_policy_citation` / `get_policy_citations` return non-empty rows for
  the seeded corpus.
- **Exit criterion:** the application plan section 13 read-path checklist
  passes against the seeded database.

### Phase G — Hero-story dry runs

- Walk through each hero demo story end-to-end (V-1002 → V-1003 → V-1010),
  using the same MCP cockpit the live demo will use.
- Confirm the seeded refusals appear in the audit trail for V-1001 and
  V-1010, and that issuing a fresh refusal-eligible request also produces a
  `workflow_events` row.
- **Exit criterion:** every hero story renders the expected first focus,
  citations, signals, findings, missing-information items, draft note, and
  needs-human-review label without any further card edits.

---

## 16. Acceptance Criteria / Definition of Done

The synthetic data layer is "done for the demo" when **every** item below is
true. A coding agent should treat this as the checklist for sign-off.

### Authoring discipline

- [ ] Twelve story cards exist under `ops/seed/cards/`, one per voucher in
      schema plan section 7.2.
- [ ] V-1002, V-1003, and V-1010 carry `hero: true` with `hero_position` set.
- [ ] Every card's `narrative` is plain English in two or three sentences and
      uses neutral vocabulary.

### Synthetic posture

- [ ] Every traveler `display_name` carries `(Synthetic Demo)` or a `DEMO-`
      prefix.
- [ ] Every vendor label carries the `Demo` substring.
- [ ] Every funding reference matches `LOA-DEMO-FY26-` (with the explicit
      `FUND-POT-DEMO-AMBIG` sentinel only on V-1004).
- [ ] Every `travelers.data_environment` and `vouchers.data_environment` value
      is `synthetic_demo`.
- [ ] No row contains a token matching the validator block-list (16-digit
      card-PAN-shape, SSN-shape, real-domain email, real bank-routing-shape).

### Coverage

- [ ] The schema plan section 7.6 coverage map resolves: every required
      practitioner case maps to at least one voucher with at least one finding,
      at least one provenance pointer, and either a citation or a
      needs-human-review reason.
- [ ] At least one `story_findings` row per category in schema plan section
      6.2 exists in the corpus.
- [ ] At least one `external_anomaly_signals.signal_type` value of each enum
      member exists across the corpus; V-1001, V-1005, V-1009, and V-1010 may
      still have zero signals as prescribed by schema plan section 7.2.
- [ ] Every signal has a deterministic `signal_key`; `(voucher_id,
      signal_key)` is unique; fraud-mock supplements replay or fill missing
      deterministic keys without duplicates.
- [ ] V-1011's brief has `is_partial = true`.
- [ ] Both seeded refusals from schema plan section 7.4 are present in
      `workflow_events`.

### Audit invariants

- [ ] Every seeded scoped write produces exactly one matching
      `workflow_events` row (schema plan section 8 audit invariant matrix).
- [ ] Every seeded brief produces a `generation` event referencing the
      `brief_id`.
- [ ] Every `story_findings` row with `needs_human_review = true` has a
      matching `needs_human_review_label` event.
- [ ] Every `workflow_events` row has a non-empty
      `human_authority_boundary_reminder` equal to the schema plan section 6.6
      canonical string.

### Authority boundary

- [ ] No card field, no generated text, and no seeded note contains an
      assertion that a voucher is approved, denied, certified, returned,
      cancelled, amended, submitted, payable, nonpayable, or ready for
      payment.
- [ ] No card field, no generated text, and no seeded note alleges fraud,
      misuse, abuse, or misconduct against any traveler, vendor, or
      transaction.
- [ ] No seeded `request_traveler_clarification` body implies a real traveler
      was contacted.

### Determinism and reproducibility

- [ ] Two runs of `python -m ops.seed.snapshot --out <dir>` produce
      byte-identical output when compared with `diff -ru`.
- [ ] `python -m ops.seed.load --reset` is safely re-runnable; running it
      twice produces the same row counts and the same content.
- [ ] The loader fails closed if any section 11 DB connection guard condition
      is not satisfied.

### Volumes

- [ ] Row counts for every seeded entity fall inside the schema plan section
      7.5 ranges.
- [ ] The seeded `review_status` distribution matches schema plan section
      7.3.

### Application handoff

- [ ] Application plan section 13 read-path manual checks pass against the
      seeded database without further card edits.
- [ ] Each of the three hero demo stories renders the expected first focus,
      citations, signals, findings, missing-information items, draft note,
      and needs-human-review label end-to-end.

When every box is checked, the synthetic data layer is demo-ready and the
remainder of the application plan can proceed.

---

## 17. Open Questions and Deferred Work

### Open questions

- Should story cards live as YAML (proposed) or as TOML for tighter typing?
  YAML wins on readability of the long narrative blocks; TOML wins on
  unambiguous types. Default is YAML; revisit only if YAML's typing causes
  validator pain.
- Should the loader run through the Terraform-managed `db_ops` Lambda or a
  developer-side script? Resolved for hackathon scope: `db_ops` is canonical
  for deployed migration/seed/reset. Developer-side scripts remain local test
  conveniences only.
- Should `policy_citations.excerpt_text` carry short synthetic excerpts
  (default), or should the seed leave the excerpt empty and have the
  application populate it from a separate retrieval-side corpus loader?
  Default is "short synthetic excerpts" so the read tools have something to
  return immediately. The application plan may swap to a richer corpus later
  only after approved reference-corpus review; real DoD/JTR/DTMO excerpts are
  not loaded for the hackathon build.
- Should the demo regenerate one brief at runtime to exercise versioning
  (schema plan section 5.10), and which voucher? Default is V-1003 because
  the dual-lodging needs-human-review label is a natural narrative beat the
  reviewer might iterate on.
- Should the seed include an `ao_notes(kind = synthetic_clarification_request)`
  row at seed time, or should the demo create it live from the cockpit?
  Schema plan section 5.11 wants at least one of every `kind` value seeded;
  the live demo can still create another to show the workflow.

### Deferred work

- Loading real public DTMO/JTR excerpts as `policy_citations` entries. Out of
  scope for the hackathon seed; gated on an approved reference-corpus review.
- Generating image fixtures for `evidence_refs` (PDF/PNG synthetic receipts).
  The current schema treats `evidence_refs` rows as cue annotations only; if
  later work wants to render synthetic receipt images for the cockpit, that
  belongs in a separate plan and must keep every image clearly marked as
  synthetic.
- A larger corpus (50+ vouchers) for evaluation work. Twelve is the right
  number for a five-minute demo; a labeled evaluation set is a Pilot-phase
  artifact per spec section 1.7.
- Locale variations and accessibility considerations on the rendered brief.
  Out of scope for the seed; that is a cockpit/UI concern.

---

*End of synthetic data implementation plan.*
