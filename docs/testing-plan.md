# AO Radar Testing Plan

A coding-agent-ready plan for the AO Radar test suite. This document is the
companion to the spec, schema, infra, application, and synthetic-data plans.
It is **plan only**: it does not introduce test code, but it tells a downstream
implementation agent which suites to build, in which order, with which test
names, and which commands run them.

## 1. Status, Purpose, and Scope

**Status.** Forward-looking test plan. No application code, infrastructure, or
fixtures have shipped yet. This plan exists so the test suite is built in
lock-step with the implementation rather than retrofitted at the end.

**Purpose.** Define the layered test suite that proves AO Radar behaves at the
boundaries the spec requires — including, critically, the deployed MCP
boundary that judges and reviewers will actually exercise.

**Scope.**

- Unit, schema, contract, boundary, integration, and end-to-end tests for the
  AO Radar MCP application, its repository layer, its safety/refusal logic,
  the fraud-mock Lambda, and the synthetic-data seed routine.
- Test commands, fixture loading, and CI/local tiers.
- Coverage and traceability rules tying every spec FR/AC and tool path to
  real test files.

**Out of scope.**

- Building the deployed infrastructure (the infra plan owns that).
- Authoring the synthetic data (the synthetic-data plan owns that).
- Authoring tool/safety/repository code (the application plan owns that).
- Performance, load, and chaos testing beyond a smoke cap.
- Auth, multi-tenant, or production hardening tests.

### Core thesis

> AO Radar is not considered tested until a synthetic voucher packet can move
> through the real deployed MCP boundary, produce a cited review brief, accept
> a scoped reviewer write, and show the resulting audit trail — without
> crossing the human-authority boundary.

Internal unit tests can all pass while the deployed boundary is broken if no
test exercises the actual handler/adapter path. This plan treats the deployed
`/mcp` endpoint and the `lambda_handler()` entrypoint as first-class systems
under test, not afterthoughts.

---

## 2. Companion Document Map

| Document | Owns | This plan defers to it for |
|---|---|---|
| `docs/spec.md` | Capability spec, OV-1, SSS, action contract, prohibited actions, refusal behavior, controlled vocabularies, acceptance criteria. | FR/AC numbering, tool names, prohibited-action set, controlled review statuses. |
| `docs/schema-implementation-plan.md` | Tables, enums, CHECK constraints, audit-event invariant matrix, seed coverage map, blocked-status list, unsafe-wording rules. | Table/column names, enum values, audit invariants, blocklist source of truth. |
| `docs/infra-implementation-plan.md` | Terraform, RDS, VPC, Secrets Manager, Lambda, API Gateway, custom domain, `/mcp` and `/health` routes. | Lambda handler entrypoints, deployed endpoint URL shape, env-var injection, transport choice. |
| `docs/application-implementation-plan.md` | Application package layout, FastMCP wiring, tool dispatch, repository, refusal validators, build/deploy handoff. | Module paths, tool implementation order, env-var matrix, manual demo checklist. |
| `docs/synthetic-data-implementation-plan.md` (if present) | Story-first fixture authoring, story cards, generators, validators, hero stories, seed loader. | Where seed fixtures come from. This plan does not redefine card schema or hero list; it consumes them. |
| This document | Test layers, test names, test commands, CI tiers, coverage/traceability, exit criteria. | — |

If a contradiction surfaces between this plan and a companion document, the
companion document wins for its area, and this plan is updated in the same
change.

---

## 3. Testing Principles

These principles are non-negotiable. Each one has a guardrail test in
section 6 so the principle cannot quietly erode.

- **Real-boundary-first.** A feature is not "tested" until at least one test
  exercises the same handler/adapter/transport path the deployed system uses.
  Unit tests are necessary but not sufficient.
- **Public-safety posture.** Tests use only synthetic data with the demo
  markers from the schema and synthetic-data plans. No real PII, no real DTS
  records, no real GTCC numbers, no real bank routing, no real unit names,
  no real vendor names, no real LOA strings, no real interview content.
- **Synthetic-only at every layer.** Test fixtures, snapshots, recorded
  responses, and CI artifacts must all carry the synthetic markers
  (`(Synthetic Demo)`, `Demo`, `LOA-DEMO-`, `synthetic_compliance_service_demo`,
  etc.). Any committed artifact missing a marker is treated as a bug.
- **Trust-boundary preservation.** Tests must prove AO Radar cannot approve,
  deny, certify, return, cancel, amend, submit, determine entitlement,
  determine payability, modify amounts, accuse fraud, or contact external
  parties — through any tool, any path, any input shape.
- **Deterministic fixtures.** Story cards, generators, fraud-mock outputs, and
  brief-assembly outputs are deterministic given the same inputs. Tests assert
  that re-running produces byte-identical structured output (modulo
  intentionally regenerated timestamps/version fields).
- **No paper coverage.** Every test claim in this document maps to a real
  test file and a runnable command. If a suite is descoped, the gap is
  documented honestly in section 12 rather than silently dropped.
- **Cross-component references must be tested end-to-end.** Generated IDs,
  evidence pointers, citation refs, signal refs, audit event IDs, and route
  paths must round-trip through real reads, real writes, and real audit
  retrieval. A finding that cites `CITE-RECEIPT-001` is only tested when a
  test fetches the brief and confirms the citation resolves.
- **Spec/test-plan claims must map to real tests.** Section 12 maintains the
  traceability. If a doc claims a test exists, that test exists.

---

## 4. Pipeline Under Test

The test suite covers every link in this chain:

```
[story cards / fixtures]
        |
        | seed loader (guarded by data_environment = synthetic_demo)
        v
[Postgres schema: travelers, vouchers, line_items, evidence, signals,
 findings, missing_info, citations, briefs, ao_notes, workflow_events]
        |
        | scoped repository (no raw SQL, no generic access)
        v
[domain modules: story_analysis, missing_information, brief_assembly, priority]
        |
        | safety layer: blocked-status check, unsafe-wording validator,
        | authority-boundary reminder
        v
[MCP tool handlers: list_vouchers_awaiting_action, get_voucher_packet,
 get_traveler_profile, list_prior_voucher_summaries,
 get_external_anomaly_signals, analyze_voucher_story,
 get_policy_citation / get_policy_citations, prepare_ao_review_brief,
 record_ao_note, mark_finding_reviewed, record_ao_feedback,
 draft_return_comment, request_traveler_clarification,
 set_voucher_review_status, get_audit_trail]
        |
        | FastMCP server (tools/list + tools/call dispatch)
        v
[transport adapter: API Gateway v2.0 event <-> JSON-RPC]
        |
        v
[lambda_handler() entrypoint]
        |
        | API Gateway HTTP API (POST /mcp, GET /health)
        v
[deployed endpoint: https://<demo-host>/mcp]
        |
        | MCP client (ChatGPT Apps developer mode, mcp-cli, or test client)
        v
[scoped reviewer writes -> workflow_events audit trail]
```

Tests at every level prove that each link does its job. The deployed E2E
suite proves the full chain works end-to-end.

---

## 5. Test Levels

For each level: purpose, what to cover, example test names, and example
commands. Test names are normative for traceability; the implementation
agent may organize files differently as long as the names resolve and the
matrix in section 7 stays consistent.

### 5.1 Unit tests

**Purpose.** Fast, hermetic tests of pure functions and small modules with
no IO. Catch logic regressions in milliseconds.

**What to cover.**

- `safety/controlled_status.py` — every blocked-status value rejected; every
  allowed-status value accepted.
- `safety/unsafe_wording.py` — context-aware rejection of unsafe assertions;
  legitimate boundary wording (e.g. "not an official approval") accepted.
- `safety/authority_boundary.py` — boundary text constant non-empty and
  stable.
- `domain/story_analysis.py` — story reconstruction from synthetic line-item
  + evidence inputs.
- `domain/missing_information.py` — gap detection from declared-vs-attached
  inputs.
- `domain/brief_assembly.py` — fusion of inputs into the review brief shape;
  hooks resolve to the inputs they were given.
- `domain/priority.py` — composite priority score is workload-only and never
  emits approval/payment language.
- `fraud_client/contract.py` — request/response models validate; deterministic
  signal generation given fixed seed.
- `transport.py` — API Gateway v2.0 event decoded correctly (including the
  base64-encoded body case) and response shape correct.

**Example test names.**

- `test_blocked_status_values_rejected[approved]`
- `test_blocked_status_values_rejected[fraud]`
- `test_allowed_review_status_values_accepted`
- `test_unsafe_wording_rejects_recommend_approve_phrase`
- `test_unsafe_wording_allows_negative_boundary_phrase`
- `test_authority_boundary_text_non_empty`
- `test_story_analysis_flags_out_of_window_expense`
- `test_missing_information_detects_no_lodging_receipt`
- `test_brief_assembly_hooks_match_inputs`
- `test_priority_score_uses_workload_language_only`
- `test_fraud_mock_deterministic_for_voucher_id`
- `test_transport_decodes_base64_body`
- `test_transport_returns_apigw_v2_response_shape`

**Example commands.**

```bash
pytest tests/unit -q
pytest tests/unit/safety -q
pytest tests/unit/domain/test_brief_assembly.py -q
```

### 5.2 Schema / data tests

**Purpose.** Prove the database enforces the constraints the spec
requires, against a real Postgres instance (test container or local
service). Mocks are forbidden at this level.

**What to cover.**

- Every blocked-status value from schema 6.4 rejected as a CHECK violation
  on `vouchers.review_status`, `story_findings.review_state`, and
  `workflow_events.resulting_status`.
- Every allowed enum value accepted.
- `data_environment` CHECK rejects anything other than `synthetic_demo` on
  `travelers` and `vouchers`.
- `external_anomaly_signals.is_official_finding` CHECK is `false` and
  `not_sufficient_for_adverse_action` CHECK is `true`.
- `review_briefs.human_authority_boundary_text` length ≥ 1 enforced.
- `story_findings.packet_evidence_pointer` requires at least one of
  `line_item_id` or `evidence_ref_id`.
- `evidence_refs` cue columns reduce to `not_applicable` when
  `content_type_indicator = none_attached_demo`.
- FK cascade behavior matches plan (e.g. `voucher_line_items` on
  `vouchers` delete).
- Unique `(voucher_id, version)` on `review_briefs`.
- Indexes referenced by the queue listing exist.

**Example test names.**

- `test_review_status_check_rejects_approved`
- `test_review_status_check_rejects_fraud`
- `test_review_status_check_accepts_in_review`
- `test_data_environment_check_rejects_prod_value`
- `test_signal_is_official_finding_must_be_false`
- `test_brief_authority_boundary_text_required`
- `test_finding_evidence_pointer_requires_at_least_one_id`
- `test_evidence_refs_none_attached_forces_not_applicable_cues`
- `test_brief_version_unique_per_voucher`
- `test_audit_resulting_status_rejects_blocked_values`

**Example commands.**

```bash
pytest tests/schema -q
DATABASE_URL=postgresql://... pytest tests/schema -q
make test-schema
```

### 5.3 MCP contract tests

**Purpose.** Prove the FastMCP server advertises exactly the spec section
4.5 tool surface, with the right schemas, descriptions, and refusal shape
— and nothing else. These tests run against the in-process FastMCP server
without the Lambda transport, but they call the same dispatch path the
transport uses.

**What to cover.**

- `initialize` returns the configured server name, version, and capabilities
  without touching the database or fraud mock.
- `tools/list` returns exactly the catalog: `list_vouchers_awaiting_action`,
  `get_voucher_packet`, `get_traveler_profile`,
  `list_prior_voucher_summaries`, `get_external_anomaly_signals`,
  `analyze_voucher_story`, `get_policy_citation`, `get_policy_citations`,
  `prepare_ao_review_brief`, `record_ao_note`, `mark_finding_reviewed`,
  `record_ao_feedback`, `draft_return_comment`,
  `request_traveler_clarification`, `set_voucher_review_status`,
  `get_audit_trail`.
- No tool name matches generic-data-access patterns: `query_database`,
  `execute_sql`, `run_query`, `read_file`, `list_dir`, `download_file`,
  `fetch_url`, `http_get`, `eval`, `shell`.
- Each tool input schema validates the expected shape and rejects
  unexpected fields.
- Each tool description references the human-authority boundary in plain
  language.
- Refusal responses carry a `reason` code drawn from the documented set
  (`prohibited_action`, `out_of_scope_artifact`,
  `unsupported_status_value`, `unsafe_wording_in_input`,
  `missing_required_input`, `ungrounded_claim`).
- `tools/call` is exercised for every advertised tool with fixture-safe
  arguments or, for not-yet-wired early phases, the documented
  `not_implemented` response. No advertised tool may lack dispatch coverage.
- Unknown tool names return a JSON-RPC error and are not treated as dynamic
  function names, SQL statements, URLs, or file paths.
- JSON-RPC envelope errors round-trip with proper `id` and `error.code`.

**Example test names.**

- `test_initialize_returns_server_identity_without_db`
- `test_tools_list_matches_spec_catalog_exactly`
- `test_tools_list_excludes_generic_data_access_names`
- `test_tool_descriptions_mention_human_authority_boundary`
- `test_tools_call_dispatch_contract_for_every_spec_tool`
- `test_tools_call_unknown_tool_returns_jsonrpc_error`
- `test_set_voucher_review_status_input_schema_rejects_unknown_field`
- `test_refusal_response_carries_reason_code`
- `test_jsonrpc_envelope_round_trips_id_and_error_code`

**Example commands.**

```bash
pytest tests/contract -q
pytest tests/contract/test_tools_list.py -q
```

### 5.4 Lambda / API Gateway boundary tests

**Purpose.** Prove `lambda_handler()` and the transport adapter behave the
way the deployed system will. **This is the level most often missed in
similar projects.** Tests at this level call `lambda_handler()` directly
with realistic API Gateway HTTP API v2.0 events, no mocks of the handler
itself.

**What to cover.**

- `GET /health` returns 200 with `server` and `version` fields and does
  not touch the database or fraud mock.
- `POST /mcp` with an `initialize` JSON-RPC request returns the configured
  server identity and protocol capabilities.
- `POST /mcp` with a `tools/list` request returns the spec catalog.
- `POST /mcp` with `tools/call` for each tool name dispatches the right
  handler and returns the right response envelope.
- Base64-encoded request bodies (the API Gateway HTTP API will set
  `isBase64Encoded = true` for some payload shapes) decode correctly.
- Malformed JSON returns a JSON-RPC parse error or JSON error body, not a
  stack trace, and does not write audit rows.
- Wrong path or unsupported method returns 404/405 with a JSON error body,
  not a stack trace.
- A request that triggers a refusal returns a JSON-RPC response with the
  refusal payload **and** writes a `workflow_events` row with
  `event_type = refusal` (when the refusal is DB-backed).
- A request that throws a Python exception inside a tool returns a clean
  JSON-RPC error response and never leaks a stack trace to the client.
- API Gateway integration timeout cap (30s) is honored: any tool that
  approaches the cap fails fast with a recognizable error rather than
  hanging.

**Example test names.**

- `test_lambda_handler_health_returns_200_no_db_calls`
- `test_lambda_handler_post_mcp_initialize_returns_server_identity`
- `test_lambda_handler_post_mcp_tools_list_returns_full_catalog`
- `test_lambda_handler_post_mcp_tools_call_get_voucher_packet`
- `test_lambda_handler_decodes_base64_encoded_body`
- `test_lambda_handler_malformed_json_returns_jsonrpc_parse_error`
- `test_lambda_handler_unknown_route_returns_404_json`
- `test_lambda_handler_refusal_writes_workflow_event`
- `test_lambda_handler_internal_exception_returns_clean_jsonrpc_error`
- `test_lambda_handler_long_running_tool_fails_under_30s_cap`

**Example commands.**

```bash
pytest tests/lambda_boundary -q
pytest tests/lambda_boundary/test_handler_routes.py -q
```

These tests **must** import and call `ao_radar_mcp.handler.lambda_handler`
with constructed API Gateway v2.0 event dicts. Tests that bypass
`lambda_handler` and call internal functions directly do not satisfy this
level. The constructed events include `version = "2.0"`, `routeKey`,
`rawPath`, `headers`, `requestContext.http.method`, `body`, and
`isBase64Encoded` so the adapter is tested against the same payload shape
API Gateway sends to Lambda.

### 5.5 Local integration tests

**Purpose.** Prove the full local stack — Postgres + repository + FastMCP
server + transport adapter — behaves correctly on a freshly seeded
database. Run against a test container or local Postgres; no AWS
resources required.

**What to cover.**

- Seed loader runs cleanly, populates the corpus per the synthetic-data
  plan volumes, and emits the seeded audit events (including the two
  seeded refusals from schema plan section 7.4).
- Every read tool returns non-empty results for the seeded corpus.
- `prepare_ao_review_brief(V-1003)` produces a brief whose `policy_hooks`,
  `signal_hooks`, `finding_hooks`, and `missing_information_hooks` each
  resolve to existing rows.
- A scoped write through `set_voucher_review_status(V-1003, in_review)`
  writes the row and the matching audit event in a single transaction.
- Every scoped write tool (`record_ao_note`, `mark_finding_reviewed`,
  `record_ao_feedback`, `draft_return_comment`,
  `request_traveler_clarification`, `set_voucher_review_status`) returns
  or exposes a resolvable audit event ID, and a follow-up
  `get_audit_trail` call returns that same event.
- If the audit-event insert fails, the paired domain write rolls back. If
  the domain write fails, no audit row is written.
- DB-backed refusals block the requested action, leave the domain row
  unchanged, and write one sanitized `event_type = refusal` event.
- `get_audit_trail(V-1003)` returns events in chronological order with
  the human-authority boundary reminder set on every row.
- Audit-event invariant matrix from schema plan section 8 holds for every
  successful write tool path on freshly seeded data.
- Fraud-mock client returns deterministic signals for the same input.
- `request_traveler_clarification` flips the voucher status to
  `awaiting_traveler_clarification` and writes the synthetic clarification
  request note plus the audit event in a single transaction; no external
  call is made.

**Example test names.**

- `test_seed_loader_loads_full_corpus`
- `test_seed_loader_emits_two_seeded_refusals`
- `test_list_vouchers_awaiting_action_returns_seeded_queue`
- `test_prepare_ao_review_brief_v1003_hooks_resolve`
- `test_set_voucher_review_status_writes_audit_event_in_same_txn`
- `test_each_scoped_write_returns_resolvable_audit_event_id`
- `test_scoped_write_rolls_back_domain_write_when_audit_insert_fails`
- `test_refusal_blocks_domain_write_and_records_sanitized_event`
- `test_audit_invariant_matrix_holds_after_write`
- `test_get_audit_trail_returns_events_in_order_with_boundary_reminder`
- `test_fraud_mock_deterministic_across_invocations`
- `test_request_traveler_clarification_does_not_call_external`

**Example commands.**

```bash
docker compose up -d postgres
DATABASE_URL=postgresql://localhost/ao_radar_test pytest tests/integration -q
make test-integration
```

### 5.6 Deployed end-to-end tests

**Purpose.** Prove the deployed `https://<demo-host>` base URL and its
`/health` and `/mcp` routes behave correctly through the same path a real
MCP client takes. **This is the acceptance gate for the core thesis.**
Tests at this level call the deployed HTTPS endpoint over the network and
assert against responses plus audit-trail effects.

**What to cover.**

- `GET /health` against the deployed endpoint returns 200 and the right
  server identity.
- `POST /mcp` with `initialize` returns the deployed server identity and
  protocol capabilities.
- `POST /mcp` with `tools/list` returns the full spec catalog.
- `POST /mcp` with `tools/call` for each read tool returns non-empty
  results from the seeded corpus.
- `prepare_ao_review_brief(V-1002)` returns a brief with at least one
  finding, one missing-information item, one citation, and the
  human-authority boundary reminder visible.
- The brief's `voucher_id`, `brief_id`, citation IDs, finding IDs,
  missing-information IDs, signal IDs, evidence refs, and packet line-item
  refs round-trip through the actual read tools rather than only through
  direct SQL.
- A scoped write through the deployed endpoint produces a new
  `workflow_events` row that a follow-up `get_audit_trail` call returns,
  including the audit event ID returned or exposed by the write response.
- A request that asks the system to "approve" a voucher returns a
  refusal, and a follow-up `get_audit_trail` shows the refusal event.
- Unknown route returns 404 over the public URL.
- TLS certificate matches the configured custom domain.

**Example test names.**

- `test_deployed_health_returns_200`
- `test_deployed_initialize_returns_server_identity`
- `test_deployed_tools_list_returns_full_catalog`
- `test_deployed_prepare_brief_v1002_hero_path`
- `test_deployed_cross_component_ids_round_trip_through_tools`
- `test_deployed_scoped_write_produces_audit_event`
- `test_deployed_approve_request_refuses_with_audit_event`
- `test_deployed_unknown_route_returns_404`
- `test_deployed_tls_cert_matches_custom_domain`

**Example commands.**

```bash
AO_RADAR_MCP_BASE_URL=https://<demo-host> pytest tests/e2e -q
make test-e2e MCP_BASE_URL=https://<demo-host>
```

These tests are gated on `AO_RADAR_MCP_BASE_URL` being set. A test client
may accept `AO_RADAR_MCP_URL=https://<demo-host>/mcp` as a backwards-
compatible alias, but the suite still derives and checks both `/health`
and `/mcp`. They do not run in the fast unit tier and do not run unless
an endpoint is reachable.

---

## 6. Boundary Regression Tests / Lessons-Learned Guardrails

These tests are explicit, named, and the suite must keep them. They exist
because similar projects have shipped with green unit suites and a broken
deployed boundary, or with implementation that drifted across the trust
boundary in ways the small tests didn't notice.

### G1. The deployed-boundary guardrail

**Rule.** The CI pipeline that gates "demo ready" must include at least
one test that calls `lambda_handler()` directly with API Gateway v2.0
events **and** at least one test that calls the deployed `/health` and
`/mcp` routes. A green unit-tests run alone does not satisfy this gate.

**Test names.** `test_lambda_handler_post_mcp_initialize_returns_server_identity`,
`test_lambda_handler_post_mcp_tools_list_returns_full_catalog`,
`test_deployed_initialize_returns_server_identity`,
`test_deployed_tools_list_returns_full_catalog`.

### G2. The no-generic-data-access guardrail

**Rule.** `tools/list` over the deployed endpoint must not include any
tool name matching the generic-data-access blocklist. The list lives in
the test file so it cannot be silently weakened. `tools/call` with an
unknown name must also fail closed; the server must not interpret unknown
tool names as SQL, file paths, URLs, shell commands, or dynamic imports.

**Test names.** `test_tools_list_excludes_generic_data_access_names`,
`test_tools_call_unknown_tool_returns_jsonrpc_error`.

### G3. The audit-event invariant guardrail

**Rule.** For every successful write tool call exercised in integration
tests, exactly one matching `workflow_events` row exists with the right
`tool_name`, `target_kind`, `target_id`, and `resulting_status`.
The response returns or exposes a resolvable audit event ID, and a
follow-up `get_audit_trail` call must return that same event. Refusals do
the same with `event_type = refusal`. Missing rows, duplicate rows, or
domain writes that survive a failed audit insert fail the test.

**Test names.** `test_audit_invariant_matrix_holds_after_write`,
`test_each_scoped_write_returns_resolvable_audit_event_id`,
`test_scoped_write_rolls_back_domain_write_when_audit_insert_fails`.

### G4. The trust-boundary vocabulary guardrail

**Rule.** A context-aware grep over generated and seeded narrative output
(brief paragraphs, draft notes, finding summaries, suggested questions,
synthetic clarification request bodies) and over static product metadata
(tool descriptions, allowed statuses, response field names) must not
contain assertions that the system approved/denied/certified/officially
returned a voucher, recommended an official disposition, alleged
fraud/misuse/misconduct, determined entitlement/payability, modified an
amount, submitted anything, or contacted an external party. The same
words **are** allowed in:

- `policy_citations.excerpt_text` (verbatim approved-corpus excerpts).
- Negative boundary statements on briefs and exports (e.g. "this is not
  an official approval").
- Refusal `rationale_metadata` payloads that quote the rejected request
  for traceability.
- Test fixtures and assertions that exercise refusal of those exact
  tokens.
- Exact spec tool names whose semantics are bounded elsewhere, especially
  `draft_return_comment`, which stores non-official draft text and sends
  nothing.

The grep is run with structural allow-list context so legitimate uses
pass, while prohibited terms still fail when they appear as allowed
workflow statuses, tool capabilities, product actions, or generated
system-authored assertions.

**Test names.** `test_unsafe_wording_grep_is_context_aware`,
`test_static_vocabulary_scanner_is_context_aware`.

### G5. The blocked-status round-trip guardrail

**Rule.** For every value in the schema 6.4 blocklist, calling
`set_voucher_review_status` and `mark_finding_reviewed` with that value
through the deployed endpoint returns a refusal **and** writes a
refusal event. Database-only constraint tests are necessary but not
sufficient; the deployed path must also refuse.

**Test name.** `test_deployed_blocked_status_values_refused_with_audit`.

### G6. The cross-component reference guardrail

**Rule.** Every `voucher_id`, `brief_id`, `policy_hooks`,
`signal_hooks`, `finding_hooks`, `missing_information_hooks`,
`packet_evidence_pointer`, citation ID, evidence ref, line-item ref, and
audit event ID returned by `prepare_ao_review_brief` or a scoped write
must resolve through the actual tools. Every `workflow_events.target_id`
must resolve to a row of the matching `target_kind`. Tests fetch the
brief, then dereference each hook through the corresponding read tool;
they do not satisfy this guardrail by querying tables directly.

**Test names.** `test_brief_hooks_resolve_to_real_rows`,
`test_deployed_cross_component_ids_round_trip_through_tools`.

### G7. The synthetic-marker guardrail

**Rule.** Every `travelers.display_name` returned by any tool carries a
synthetic marker substring. Every vendor label, location, LOA reference,
and citation source identifier in returned data carries a `Demo` /
`synthetic_demo_reference_` / `LOA-DEMO-` marker. A test response that
fails this is a public-safety bug, not a cosmetic one. A repository
scanner also fails on local workstation paths, chat-platform channel identifiers,
non-public repository identifiers, unredacted source-note artifacts, obvious credential
markers, and unresolved placeholder markers in committed test fixtures,
snapshots, and docs generated by the test suite.

**Test names.** `test_returned_data_carries_synthetic_markers`,
`test_public_safety_scanner_blocks_private_artifacts`.

### G8. The descoped-test honesty guardrail

**Rule.** Test names referenced from this plan must resolve to real test
files. A separate suite walks the matrix in section 7 and asserts every
named test exists. If a test is descoped, this plan is updated in the
same change to record the gap.

**Test name.** `test_traceability_matrix_resolves_all_named_tests`.

---

## 7. Test Matrix

Mapping of areas to test types, real boundaries exercised, expected files,
and example commands. The implementation agent uses this matrix to
generate the suite and to keep the traceability test (G8) honest.

| Area | Test type | Real boundary | Expected file(s) | Example command |
|---|---|---|---|---|
| Blocked-status enforcement (DB) | Schema | Postgres CHECK | `tests/schema/test_blocked_status.py` | `pytest tests/schema/test_blocked_status.py -q` |
| Blocked-status enforcement (deployed) | E2E | `https://<host>/mcp` | `tests/e2e/test_blocked_status_deployed.py` | `AO_RADAR_MCP_BASE_URL=... pytest tests/e2e/test_blocked_status_deployed.py -q` |
| MCP initialize over handler | Boundary | `lambda_handler()` | `tests/lambda_boundary/test_handler_routes.py` | `pytest tests/lambda_boundary/test_handler_routes.py -q` |
| MCP initialize over wire | E2E | `https://<host>/mcp` | `tests/e2e/test_initialize_deployed.py` | `AO_RADAR_MCP_BASE_URL=... pytest tests/e2e/test_initialize_deployed.py -q` |
| Tool catalog matches spec | Contract | FastMCP server | `tests/contract/test_tools_list.py` | `pytest tests/contract/test_tools_list.py -q` |
| Tool catalog over the wire | E2E | `https://<host>/mcp` | `tests/e2e/test_tools_list_deployed.py` | `AO_RADAR_MCP_BASE_URL=... pytest tests/e2e/test_tools_list_deployed.py -q` |
| Tools/call dispatch coverage | Contract | FastMCP server | `tests/contract/test_tools_call.py` | `pytest tests/contract/test_tools_call.py -q` |
| `lambda_handler` routing | Boundary | `lambda_handler()` | `tests/lambda_boundary/test_handler_routes.py` | `pytest tests/lambda_boundary/test_handler_routes.py -q` |
| Malformed JSON handling | Boundary | `lambda_handler()` | `tests/lambda_boundary/test_payload_shapes.py` | `pytest tests/lambda_boundary/test_payload_shapes.py -q` |
| Base64 body decoding | Boundary | `lambda_handler()` | `tests/lambda_boundary/test_payload_shapes.py` | `pytest tests/lambda_boundary/test_payload_shapes.py -q` |
| Brief assembly hooks resolve | Integration | Postgres + tools | `tests/integration/test_brief_assembly.py` | `pytest tests/integration/test_brief_assembly.py -q` |
| Brief on hero V-1002 (deployed) | E2E | `https://<host>/mcp` | `tests/e2e/test_hero_v1002.py` | `AO_RADAR_MCP_BASE_URL=... pytest tests/e2e/test_hero_v1002.py -q` |
| Audit-event invariants | Integration | Postgres + tools | `tests/integration/test_audit_invariants.py` | `pytest tests/integration/test_audit_invariants.py -q` |
| Refusal produces audit event | Integration | Postgres + tools | `tests/integration/test_refusal_audit.py` | `pytest tests/integration/test_refusal_audit.py -q` |
| Refusal over the wire | E2E | `https://<host>/mcp` | `tests/e2e/test_refusal_deployed.py` | `AO_RADAR_MCP_BASE_URL=... pytest tests/e2e/test_refusal_deployed.py -q` |
| Fraud-mock determinism | Unit + Integration | In-proc + Lambda invoke | `tests/unit/test_fraud_mock.py`, `tests/integration/test_fraud_mock_invoke.py` | `pytest tests/unit/test_fraud_mock.py tests/integration/test_fraud_mock_invoke.py -q` |
| Story analysis logic | Unit | Pure functions | `tests/unit/domain/test_story_analysis.py` | `pytest tests/unit/domain/test_story_analysis.py -q` |
| Missing-information detection | Unit | Pure functions | `tests/unit/domain/test_missing_information.py` | `pytest tests/unit/domain/test_missing_information.py -q` |
| Unsafe-wording validator | Unit | Pure functions | `tests/unit/safety/test_unsafe_wording.py` | `pytest tests/unit/safety/test_unsafe_wording.py -q` |
| Static vocabulary scanner | Meta | Generated text + static metadata | `tests/meta/test_vocabulary_scanner.py` | `pytest tests/meta/test_vocabulary_scanner.py -q` |
| Public-safety artifact scanner | Meta | Repo test artifacts | `tests/meta/test_public_safety_scanner.py` | `pytest tests/meta/test_public_safety_scanner.py -q` |
| Synthetic markers in fixtures | Fixture validator | Generator output | `tests/fixtures/test_synthetic_markers.py` | `pytest tests/fixtures/test_synthetic_markers.py -q` |
| Coverage map walk | Fixture validator | Seeded DB | `tests/fixtures/test_coverage_map.py` | `pytest tests/fixtures/test_coverage_map.py -q` |
| Cross-component refs resolve | Integration | Postgres + tools | `tests/integration/test_brief_hooks_resolve.py` | `pytest tests/integration/test_brief_hooks_resolve.py -q` |
| Traceability self-check | Meta | This plan + suite | `tests/meta/test_traceability.py` | `pytest tests/meta/test_traceability.py -q` |
| Health endpoint (deployed) | E2E | `https://<host>/health` | `tests/e2e/test_health_deployed.py` | `AO_RADAR_MCP_BASE_URL=... pytest tests/e2e/test_health_deployed.py -q` |

The matrix is the source of truth for test areas and expected files. The
named tests in sections 5, 6, 8, 9, and 10 are the source of truth for
test function names. `tests/meta/test_traceability.py` parses both this
matrix and the named-test lists, asserts each file exists, and asserts
each named test resolves to a function inside the expected suite.

---

## 8. End-to-End Scenario Suite

The synthetic corpus scenarios, including the hero stories from the
synthetic-data plan, form the E2E acceptance suite. Each scenario is one
E2E test file under `tests/e2e/scenarios/`, run against the deployed
endpoint with the seeded corpus.

### S1. Missing receipt + weak local-paper evidence

**Voucher.** Hero voucher V-1002: a synthetic OCONUS site-visit packet
with a `none_attached_demo` lodging evidence row, a weak local-paper
meals receipt, and a prior-pattern signal labeled as a review prompt.

**Steps.**

1. `prepare_ao_review_brief(<voucher_id>)` over the deployed endpoint.
2. Assert the brief carries at least one `missing_receipt` finding, at
   least one `weak_or_local_paper_receipt` or `evidence_quality_concern`
   finding, at least one `valid_receipt` citation, and the
   human-authority boundary reminder.
3. Assert any prior-pattern signal is labeled as a review prompt only,
   not an official finding and not sufficient for adverse action.
4. Call `set_voucher_review_status(<voucher_id>, awaiting_traveler_clarification)`.
5. `get_audit_trail(<voucher_id>)` and assert the new
   `scoped_write` event is present with the right `resulting_status`.

**Test name.** `test_e2e_missing_receipt_local_paper`.

### S2. Ambiguous LOA / mis-click / bad math

**Voucher.** Support voucher V-1004: a synthetic packet with an ambiguous
funding-reference label, a neutral forced-audit receipt-review cue, a
miscategorized lodging line, and paperwork math that does not reconcile.

**Steps.**

1. `prepare_ao_review_brief(<voucher_id>)`.
2. Assert findings include `ambiguous_loa_or_funding_reference`,
   `miscategorized_line_item`, and `paperwork_or_math_inconsistency`.
3. Assert the forced-audit cue is treated as a reason to inspect the
   packet, not as an official finding.
4. Assert the brief does not state the line is approved/denied/payable
   and does not allege misconduct.
5. Call `record_ao_note(<voucher_id>, <neutral note text>)` and assert
   the audit event lands.

**Test name.** `test_e2e_ambiguous_loa_misclick_math`.

### S3. OCONUS cash / exchange-rate reconstruction

**Voucher.** An austere OCONUS packet with `cash_atm` and
`currency_exchange` lines, foreign-currency line items with
`exchange_rate_to_usd`, mostly handwritten local-paper evidence.

**Steps.**

1. `prepare_ao_review_brief(<voucher_id>)`.
2. Assert at least one finding of category
   `cash_atm_or_exchange_reconstruction` with `needs_human_review = true`.
3. Assert at least one signal of `signal_type = split_disbursement_oddity`
   or `traveler_baseline_outlier` is hooked into the brief and labeled as
   a review prompt only.
4. Assert the brief shows the exchange-rate column for each foreign
   line.

**Test name.** `test_e2e_oconus_cash_exchange_rate`.

### S4. Stale-memory old transaction reconstruction

**Voucher.** A packet whose `demo_packet_submitted_at` is many weeks
after the latest `expense_date`, with weakly itemized evidence.

**Steps.**

1. `prepare_ao_review_brief(<voucher_id>)`.
2. Assert the brief explicitly notes the gap between expense dates and
   the synthetic packet submission timestamp.
3. Assert at least one `stale_memory_old_transaction` finding.
4. Assert the draft clarification note asks for reconstruction details
   and uses neutral wording.

**Test name.** `test_e2e_stale_memory_old_transaction`.

### S5. Clean control packet

**Voucher.** One of the two clean control packets seeded by the corpus
(status `ready_for_human_decision`, zero signals, zero findings, zero
missing-information items).

**Steps.**

1. `prepare_ao_review_brief(<voucher_id>)`.
2. Assert zero findings, zero missing-information items, low brief
   uncertainty, and the standard human-authority boundary reminder.
3. Assert the draft clarification note does not invent a clarification
   request.

**Test name.** `test_e2e_clean_control_packet`.

These five scenarios collectively exercise every spec FR/AC the demo
relies on. Adding a hero is an explicit, traceable change.

---

## 9. Audit / Refusal / Prohibited-Action Tests

These tests are concentrated under `tests/safety/` and `tests/e2e/refusal/`
and run at multiple levels.

**Coverage targets.**

- Every value in the schema 6.4 blocklist is rejected by:
  - The Postgres CHECK constraint (schema test).
  - The application boundary validator (unit test).
  - The deployed `set_voucher_review_status` and `mark_finding_reviewed`
    paths (E2E test).
- Every refusal path writes exactly one `workflow_events` row with
  `event_type = refusal` and a populated `rationale_metadata` payload.
  The payload sanitizes the rejected request — never logs secrets, never
  echoes raw fabricated PII.
- Every refusal response carries a documented `reason` code.
- An attempted call asking the system to "approve", "certify", "deny",
  "pay", or "submit" a voucher through any tool path returns a refusal
  with an actionable reason.
- A non-voucher artifact submitted to a tool that takes a voucher id
  returns a refusal with `reason = out_of_scope_artifact`.
- A request that asks the system to characterize a transaction as
  fraudulent returns a refusal and the audit event records the rejected
  request shape.
- An attempted call to `request_traveler_clarification` does not produce
  any outbound network traffic. Tests assert through a network-egress
  fake or by inspecting the call log.
- The two seeded refusals from schema plan section 7.4 are present in
  `workflow_events` immediately after `reset_demo()`.

**Example test names.**

- `test_safety_blocked_status_app_validator_rejects_each_value`
- `test_safety_refusal_writes_audit_event_with_reason_code`
- `test_safety_refusal_payload_sanitizes_request`
- `test_safety_approve_phrase_refused_through_each_tool`
- `test_safety_non_voucher_artifact_refused_with_out_of_scope`
- `test_safety_fraud_characterization_refused_with_audit_event`
- `test_safety_traveler_clarification_no_external_egress`
- `test_safety_seeded_refusals_present_after_reset_demo`

**Example commands.**

```bash
pytest tests/safety -q
AO_RADAR_MCP_BASE_URL=https://<demo-host> pytest tests/e2e/refusal -q
```

---

## 10. Fixture and Synthetic-Data Validation Tests

These tests sit under `tests/fixtures/` and run against the seed loader's
in-memory output and against the freshly seeded database.

If the synthetic-data plan is committed, these tests consume its
story-first artifacts (story cards, generators, validators, hero list).
If the plan is not yet committed, these tests still run against the
schema plan's section 7 corpus shape and the synthetic-data plan's stated
expectations are recorded as a known gap in section 12 — never silently
dropped.

**Coverage targets.**

- The seed loader refuses to run unless the active connection's
  `data_environment` resolves to `synthetic_demo`.
- Generated rows respect schema plan section 7.5 volume bounds.
- Every required pain-pattern row from schema plan section 7.6 resolves
  to at least one `story_findings` row, one provenance pointer, and
  either a citation or an explicit needs-human-review reason.
- Every traveler row carries `data_environment = synthetic_demo`, the
  `(Synthetic Demo)` marker in `display_name`, and a synthetic
  `home_unit_label`.
- Every voucher row carries `data_environment = synthetic_demo` and the
  `LOA-DEMO-` prefix on `funding_reference_label` (or the documented
  ambiguous sentinel).
- Every vendor label includes the `Demo` substring.
- Every citation `source_identifier` carries a synthetic prefix
  (`synthetic_dtmo_checklist_demo_` / `synthetic_demo_reference_`).
- Every external anomaly signal carries
  `synthetic_compliance_service_demo` source label,
  `is_official_finding = false`, and
  `not_sufficient_for_adverse_action = true`.
- Story-card sourced narrative text passes the unsafe-wording validator.
- Determinism: running the generator twice from the same cards produces
  identical structured output (modulo intentionally regenerated id and
  timestamp fields, which are excluded from the snapshot diff).
- Public-safety scanner: committed fixtures, recorded responses,
  snapshots, and generated docs fail if they contain private workstation
  paths, chat-platform channel IDs, non-public repository identifiers,
  unredacted source-note artifacts, obvious credential markers, or
  unresolved placeholder markers.
- The scanner is context-aware for vocabulary: prohibited terms may
  appear in negative boundary statements, refusal tests, citations, and
  disclaimers, but must fail when introduced as allowed workflow
  statuses, tool capabilities, product actions, or generated
  system-authored assertions.

**Example test names.**

- `test_seed_loader_refuses_non_synthetic_data_environment`
- `test_corpus_volumes_within_schema_plan_bounds`
- `test_coverage_map_every_required_pain_pattern_resolved`
- `test_travelers_carry_synthetic_markers`
- `test_vouchers_carry_loa_demo_prefix`
- `test_vendor_labels_carry_demo_marker`
- `test_citations_carry_synthetic_source_prefix`
- `test_signals_carry_demo_source_and_check_flags`
- `test_story_card_narrative_passes_unsafe_wording_validator`
- `test_generator_output_is_deterministic`
- `test_public_safety_scanner_blocks_private_artifacts`
- `test_static_vocabulary_scanner_is_context_aware`

**Example commands.**

```bash
pytest tests/fixtures -q
pytest tests/meta/test_public_safety_scanner.py tests/meta/test_vocabulary_scanner.py -q
make test-fixtures
```

---

## 11. CI / Local Command Tiers

The test suite is split into four tiers so CI and local runs do the right
amount of work.

### Tier 1 — Fast unit (no IO, no DB, no network)

**Use.** Default `pytest` run on every file save, every commit, every PR.

**Includes.** `tests/unit/`, `tests/contract/`, `tests/safety/` (the
non-DB portion), and `tests/meta/` (traceability plus public-safety and
vocabulary scanners).

**Command.**

```bash
pytest tests/unit tests/contract tests/safety tests/meta -q -m 'not db and not e2e'
```

**Target wall-clock.** Under 60 seconds on a developer laptop.

### Tier 2 — Local confidence (DB required, no AWS)

**Use.** Pre-merge sweep; run before requesting review.

**Includes.** Tier 1 plus `tests/schema/`, `tests/integration/`,
`tests/lambda_boundary/`, `tests/fixtures/`.

**Command.**

```bash
docker compose up -d postgres
DATABASE_URL=postgresql://localhost/ao_radar_test \
  pytest tests/unit tests/contract tests/safety \
         tests/meta tests/schema tests/integration \
         tests/lambda_boundary tests/fixtures -q
make test-local
```

**Target wall-clock.** Under five minutes.

### Tier 3 — Integration (DB + test container, no AWS)

**Use.** Nightly CI or `make test-ci`.

**Includes.** Tier 2 with stricter selectors (e.g. coverage report on,
flaky-test retries off, fixture determinism snapshot diff on).

**Command.**

```bash
make test-ci
```

### Tier 4 — Deployed E2E (AWS endpoint required)

**Use.** Demo-readiness gate. Run before any judged demo or release.

**Includes.** `tests/e2e/`. Gated on `AO_RADAR_MCP_BASE_URL` being set;
tests abort cleanly with a skip notice if not.

**Command.**

```bash
AO_RADAR_MCP_BASE_URL=https://<demo-host> pytest tests/e2e -q
make test-e2e MCP_BASE_URL=https://<demo-host>
```

**Target wall-clock.** Under three minutes of network calls.

A test run that promotes a branch to "demo ready" must include Tier 4.
Tier 1 alone never satisfies the demo-readiness gate.

---

## 12. Coverage and Traceability Rules

- **Every spec FR (`docs/spec.md` section 3.4) maps to at least one test.**
  The mapping lives in `tests/meta/test_traceability.py`.
- **Every spec AC (`docs/spec.md` section 5) maps to at least one test.**
- **Every tool name in spec section 4.5 maps to at least one contract test
  and at least one boundary or E2E test.**
- **Every controlled review status in spec section 4.5.3 maps to at least
  one happy-path test and one rejection test.**
- **Every blocked status / unsafe-wording rule in schema plan section 6.4
  maps to at least one test.**
- **Every refusal path (`reason` code) maps to at least one test that
  exercises both the response shape and the audit event.**
- **Every public-safety and trust-boundary scanner claim maps to a real
  meta test.** The scanner tests use structural allow-lists so negative
  boundary text and refusal fixtures pass, while prohibited product
  actions, statuses, capabilities, private artifacts, and secret markers
  fail.
- **No test claim in this plan exists without a real test file.** The
  traceability self-check (G8) walks the matrix in section 7 and the
  named tests throughout this plan and asserts each one exists. If a
  test is descoped, this plan is updated in the same change to record
  the gap in a "Known Gaps" subsection below.
- **Cross-document references must round-trip.** Every tool name in this
  plan must appear in `docs/spec.md` section 4.5; every blocklist
  reference must appear in schema plan section 6.4; every audit
  invariant reference must appear in schema plan section 8 (audit-event
  invariant matrix).

### Known gaps

(empty at plan publication; record any explicitly descoped tests here in
the same change that descopes them.)

---

## 13. Manual Demo Smoke Checklist

Run this after every deploy and before every judged demo. It is
**not** a substitute for the automated suite; it is the human-eyes
final pass.

### Endpoint sanity

- [ ] `curl -i https://<demo-host>/health` returns `200` and includes
  `server` + `version`.
- [ ] `curl -i -X POST https://<demo-host>/mcp -H 'Content-Type:
  application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`
  returns the spec catalog and **no other tools**.
- [ ] DNS resolves to the API Gateway alias target.
- [ ] TLS certificate matches the configured custom domain.

### MCP client sanity

- [ ] An MCP client (ChatGPT Apps developer mode, mcp-cli, or test
  client) connects with `Authorization supported = None` and lists the
  tool catalog.
- [ ] Calling `list_vouchers_awaiting_action` shows the seeded queue and
  uses workload-only language.
- [ ] Calling `get_voucher_packet` on a hero voucher returns line items,
  evidence, justification, and pre-existing flags with synthetic markers
  visible.
- [ ] Calling `prepare_ao_review_brief` on a hero voucher returns a
  brief with at least one finding, one missing-information item, one
  citation, and the human-authority boundary reminder.

### Scoped writes

- [ ] `set_voucher_review_status` to `awaiting_traveler_clarification`
  succeeds and shows up in `get_audit_trail`.
- [ ] `record_ao_note` succeeds and the note text round-trips.
- [ ] `mark_finding_reviewed` to `reviewed_unresolved` succeeds and
  shows up in `get_audit_trail`.
- [ ] `request_traveler_clarification` flips the status, writes the
  synthetic clarification request note, and produces no outbound
  network traffic.

### Refusal

- [ ] `set_voucher_review_status` with `approved` returns a refusal
  whose `reason` is recognizable and produces a `refusal` audit event.
- [ ] A request asking the system to "approve" or "certify" returns a
  refusal with an actionable reason.
- [ ] A request asking the system to characterize a line as fraudulent
  returns a refusal with an actionable reason.
- [ ] A non-voucher artifact returns a refusal with
  `reason = out_of_scope_artifact`.

### Public-safety sweep

- [ ] No log line contains a value resembling a real card PAN, SSN, real
  domain email, or other obvious real-data shape.
- [ ] Every traveler `display_name` returned in the demo carries the
  `(Synthetic Demo)` marker.
- [ ] Every brief and exported artifact shows the human-authority
  boundary reminder.

If every box is checked, the demo is ready. Anything unchecked points
back into the matching companion document for the fix.

---

## 14. Implementation Phases

Each phase ends with a runnable suite and a meaningful demo checkpoint.
Build the test suite in lock-step with the application; do not retrofit.

### Phase 0 — Test scaffolding

- Create `tests/unit/`, `tests/contract/`, `tests/schema/`,
  `tests/lambda_boundary/`, `tests/integration/`, `tests/e2e/`,
  `tests/fixtures/`, `tests/safety/`, `tests/meta/`.
- Add `pytest` configuration, marker registration (`db`, `e2e`),
  `conftest.py` fixtures for: in-memory FastMCP server, Postgres test
  container, deployed-endpoint client (gated on `AO_RADAR_MCP_BASE_URL`).
- Wire the four CI tiers in `make` targets and a CI workflow.
- Add `tests/meta/test_traceability.py` shell that asserts the matrix
  from section 7 resolves; the assertion list grows as tests land.

**Exit criterion.** Empty suites run cleanly in each tier; CI workflow
green.

### Phase 1 — Unit and contract layer

- Implement Tier 1 tests for `safety/`, `domain/`, `transport.py`,
  `fraud_client/contract.py`, and the FastMCP `initialize`, `tools/list`,
  and `tools/call` contracts.

**Exit criterion.** Tier 1 passes locally and in CI; G2 (no generic data
access) and G4 (vocabulary) guardrails are live.

### Phase 2 — Schema and fixture layer

- Implement Tier 2 schema tests against a Postgres test container.
- Implement fixture-validator tests (synthetic markers, coverage map,
  determinism).
- Wire schema migrations into the test container fixture so each test
  file starts on a clean database.

**Exit criterion.** Tier 2 passes locally; G7 (synthetic markers) live.

### Phase 3 — Lambda boundary and integration

- Implement `tests/lambda_boundary/` tests that import and call
  `lambda_handler` with constructed API Gateway v2.0 events.
- Implement `tests/integration/` tests that walk the audit-event
  invariant matrix on a freshly seeded database.

**Exit criterion.** Tier 2 + boundary tests green; G3 (audit invariant)
and G6 (cross-component refs) guardrails live.

### Phase 4 — Deployed E2E

- Implement `tests/e2e/` against the deployed endpoint.
- Implement the five E2E scenarios (S1–S5) under
  `tests/e2e/scenarios/`.
- Implement the deployed refusal suite under `tests/e2e/refusal/`.

**Exit criterion.** Tier 4 passes against the deployed stack; G1
(deployed boundary) and G5 (blocked-status round-trip) guardrails live.

### Phase 5 — Demo polish and traceability lockdown

- Walk every spec FR and AC, every tool, every blocked status, every
  refusal `reason` code, and confirm the matrix in section 7 covers
  each. Land any missing tests.
- Land G8 (traceability self-check) as the gate that closes the
  feedback loop.

**Exit criterion.** Section 12's coverage rules are enforced
automatically. The "demo ready" CI gate runs all four tiers and the
manual smoke checklist completes cleanly.

---

## 15. Exit Criteria

The test suite is "done" — for the hackathon prototype — when **all** of
the following hold:

- Tier 1, Tier 2, Tier 3, and Tier 4 all run green from a clean working
  tree.
- Tier 4 calls `https://<demo-host>/health` and
  `https://<demo-host>/mcp`, then verifies server initialization, the tool
  catalog, at least one hero scenario, and at least one deployed refusal
  end to end.
- `tests/meta/test_traceability.py` passes and asserts every named test
  in section 7 and throughout this plan resolves to a real test
  function.
- Every spec FR (section 3.4) and AC (section 5) maps to at least one
  test.
- Every tool name in spec section 4.5 has at least one contract test and
  at least one boundary or E2E test.
- Every value in the schema 6.4 blocklist is rejected by a schema test,
  an application-boundary unit test, and a deployed E2E test.
- The audit-event invariant matrix is exercised by an integration test
  that runs the full matrix against a freshly seeded database.
- The five E2E scenarios in section 8 each pass against the deployed
  endpoint and against a freshly seeded local environment.
- The manual demo smoke checklist completes cleanly against the most
  recent deploy.
- No committed test fixture or recorded response contains a value
  without a synthetic marker.
- The "Known Gaps" subsection in section 12 either is empty or honestly
  records any descoped test along with the reason.

If any of these are not met, the application is not demo-ready, and the
gap is documented in section 12 in the same change that descopes the
test.

---

*End of testing plan.*
