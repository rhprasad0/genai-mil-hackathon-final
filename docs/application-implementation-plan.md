# AO Radar Application Implementation Plan

A coding-agent-ready implementation plan for the Python/FastMCP Lambda
application that exposes the AO Radar pre-decision review workflow over the
Postgres persistence layer and the fraud-mock Lambda described in the
companion infrastructure plan. This document is **plan only**: it does not
introduce code, but it tells a downstream coding agent exactly what to build
and in what order.

The implementation must remain public-safe at every step. No secrets, no real
PII, no real DTS records, no real Government Travel Charge Card data, and no
real bank routing data appear here or in any artifact this plan prescribes.
Examples are synthetic and clearly fictional.

---

## 1. Status, Scope, and Non-Goals

### Status

Forward-looking application plan. No application code has been written yet.
The companion infrastructure plan is forward-looking as well; the schema plan
is forward-looking. This document is the canonical specification a coding
agent follows to stand up the AO Radar MCP application that runs in Lambda
behind the API Gateway endpoint described in
`docs/infra-implementation-plan.md`.

### In scope

- A Python application packaged for AWS Lambda that serves the AO Radar MCP
  tool surface defined in `docs/spec.md` section 4.5.
- A FastMCP-based MCP server bound to that tool surface, exposed through API
  Gateway HTTP API on `POST /mcp` and `GET /health`.
- A scoped Postgres data-access layer built on the schema in
  `docs/schema-implementation-plan.md`.
- A separate Python Lambda that mocks the synthetic external anomaly signal
  service. The MCP Lambda invokes this mock through the AWS SDK.
- An audit invariant: every scoped workflow write records a
  `workflow_events` row in the same transaction as the domain write; every
  DB-backed refusal records a sanitized `workflow_events` row before the
  response returns.
- Refusal and boundary validators that enforce the trust boundary at the
  application layer in addition to the schema layer.
- Build and deploy handoff to Terraform: zip artifacts, environment
  variables, and migration entry points.

### Non-goals

- Detailed synthetic data / seed scenario design. That lives in
  `docs/synthetic-data-implementation-plan.md`. This plan defines only the
  application contracts needed to consume synthetic data; it does not
  enumerate voucher narratives, persona names, or per-scenario fraud-mock
  recipes.
- Formal test plans, TDD plans, or coverage targets. A short manual demo
  verification checklist is in section 13; that is not a test plan.
- Choosing or implementing a reviewer-facing UI. The reviewer cockpit is
  ChatGPT (or another MCP-capable assistant) configured against the public
  endpoint; no custom UI ships in this plan.
- Auth, multi-tenant scoping, observability platforms, deploy pipelines, or
  anything outside the hackathon demo loop.
- Any feature that would let the application approve, deny, certify, return,
  cancel, amend, submit, determine entitlement, modify amounts, accuse fraud,
  or contact external parties.

### Hard product constraints (carried from the spec)

- The model can move the review workflow forward; it cannot move money.
- Tools are scoped domain workflow tools only. No raw SQL, no arbitrary
  filesystem, no arbitrary HTTP fetch is exposed through MCP.
- Review-facing generated artifacts and scoped write/refusal responses that
  represent workflow state include or point to the human-authority boundary
  reminder. Low-level liveness responses and MCP protocol metadata do not
  need to repeat the full reminder.
- Hackathon reference retrieval uses the synthetic demo reference corpus only.
  The application must not load real DoD, JTR, DTMO, checklist, or
  government-system excerpts unless later approved corpus-review work changes
  the scope.

---

## 2. Companion Document Map

This plan is the application layer. The other three documents are load-bearing
and should be read first.

| Document | Owns | This plan defers to it for |
|---|---|---|
| `docs/spec.md` | Capability spec, OV-1, SSS, action contract, prohibited actions, refusal behavior, controlled vocabularies, acceptance criteria. | Tool names, prohibited actions, controlled review statuses, acceptance criteria. This plan does not redefine them. |
| `docs/infra-implementation-plan.md` | AWS infrastructure: VPC, RDS, Lambdas, API Gateway, custom domain, Secrets Manager, IAM, networking. | Lambda runtime, env-var injection, zip artifact paths, RDS endpoint, secret ARN, fraud-mock Lambda function name, API Gateway routes. |
| `docs/schema-implementation-plan.md` | Postgres schema: tables, enums, CHECK constraints, audit invariants, fixture-validator expectations. | Table/column names, enum values, blocked-status values, repository contracts, audit-event invariant matrix. |
| This document | Application layout, FastMCP wiring, Lambda handlers, tool dispatch order, refusal validators, build/deploy handoff. | — |

If a contradiction surfaces between this plan and one of the three companion
documents, the companion document wins for its area, and this plan should be
edited to match in the same change.

---

## 3. Target Application Architecture

```
ChatGPT.com / ChatGPT Apps developer mode (or any MCP-capable cockpit)
        │  HTTPS, no auth (per infra plan)
        ▼
API Gateway HTTP API
        │  AWS_PROXY (payload v2.0)
        ▼
MCP Lambda  (Python, FastMCP)
        │
        ├── POST /mcp   → FastMCP request handler (JSON-RPC over Streamable HTTP)
        └── GET  /health → liveness probe
        │
        │  scoped repository module (no generic SQL)
        ▼
Postgres (RDS, private subnets, schema per schema plan)
        │
        │  AWS SDK Lambda Invoke (synchronous)
        ▼
Fraud-mock Lambda  (Python, deterministic, synthetic)
```

Key invariants enforced by this architecture:

- The MCP Lambda is the only public runtime workflow path that talks to
  Postgres. Migration or probe utilities may connect only through the
  private-network patterns allowed by the infra plan.
- The fraud-mock Lambda is the only runtime generator of synthetic external
  anomaly signals beyond any persisted synthetic fixtures. The application
  never reaches outside this loop for anomaly data.
- The default API Gateway routes are exactly `POST /mcp` and `GET /health`.
  No generic, exploratory, or admin routes are added; `GET /sse` remains an
  infra-gated fallback only if Streamable HTTP fails.
- Streamable HTTP is the default MCP transport; SSE is opt-in and gated on
  the infra plan's `enable_sse_route` switch.

---

## 4. Recommended Python Package Layout

The Lambda zip is built from a single repository. Two Lambdas, one repo. The
shape below is recommended; the coding agent may adjust file names without
changing the boundaries.

```
src/
  ao_radar_mcp/                  # MCP Lambda package
    __init__.py
    handler.py                   # Lambda entrypoint (API GW → FastMCP)
    config.py                    # env-var loading, no secret values
    logging_setup.py             # structured logging
    server.py                    # FastMCP server, tool registration
    transport.py                 # API GW v2 ↔ FastMCP request/response adapter
    tools/                       # one module per spec § 4.5 tool
      __init__.py
      list_vouchers.py
      get_voucher_packet.py
      get_traveler_profile.py
      list_prior_voucher_summaries.py
      get_external_anomaly_signals.py
      analyze_voucher_story.py
      get_policy_citation.py
      get_policy_citations.py
      prepare_ao_review_brief.py
      export_review_brief.py
      record_ao_note.py
      mark_finding_reviewed.py
      record_ao_feedback.py
      draft_return_comment.py
      request_traveler_clarification.py
      set_voucher_review_status.py
      get_audit_trail.py
    repository/                  # scoped data-access layer (see § 8)
      __init__.py
      connection.py              # connection pool, secret fetch
      vouchers.py
      line_items.py
      evidence.py
      travelers.py
      prior_summaries.py
      citations.py
      signals.py
      findings.py
      missing_information.py
      briefs.py
      ao_notes.py
      workflow_events.py
    domain/                      # pure domain logic, no IO
      __init__.py
      brief_assembly.py          # prepare_ao_review_brief composition
      story_analysis.py          # story coherence helpers
      missing_information.py     # gap detection helpers
      priority.py                # workload-guidance scoring
    safety/                      # boundary / refusal layer (see § 11)
      __init__.py
      controlled_status.py       # blocked-value checks for status fields
      unsafe_wording.py          # context-aware wording validator
      authority_boundary.py      # boundary reminder text constant
    fraud_client/                # fraud-mock invocation, no other network IO
      __init__.py
      client.py                  # boto3 lambda invoke wrapper
      contract.py                # request/response shape models

  ao_radar_fraud_mock/           # fraud-mock Lambda package
    __init__.py
    handler.py                   # Lambda entrypoint
    deterministic.py             # synthetic signal generation per voucher_id

  ao_radar_db_ops/               # private migration/seed Lambda package
    __init__.py
    handler.py                   # Lambda entrypoint for migrate/seed/reset
    operations.py                # calls ops/scripts and ops/seed safely

ops/
  migrations/                    # Postgres migrations (per schema plan)
  seed/                          # synthetic seed routine (separate plan)
  build/                         # zip packaging scripts
    build_mcp_zip.sh
    build_fraud_zip.sh
    build_db_ops_zip.sh
  scripts/
    run_migrations.py            # idempotent migration runner

infra/                           # Terraform (per infra plan)
```

Notes on the layout:

- `tools/` is one module per spec section 4.5 tool. Keeping each tool small
  and isolated makes the audit-event invariant easy to enforce.
- `domain/` holds pure logic with no database or network IO. This makes the
  brief assembly directly inspectable.
- `safety/` is the only place the prohibited-vocabulary and blocked-status
  rules live in code. Tools call into it; the schema enforces the same rules
  independently for status-like columns.
- `fraud_client/` is the only domain-level outbound integration. The MCP
  Lambda may also use AWS SDK clients for Secrets Manager and Lambda Invoke
  as described by the infra plan, but there is no general HTTP client.
- `ao_radar_db_ops/` is not public and is not connected to API Gateway. It is
  the Terraform-managed path for migrations and seed/reset inside the VPC.
- `repository/` exposes only domain-shaped methods. There is no
  `execute_sql`, no `query`, no string-templated query builder available to
  upstream code.

---

## 5. Runtime Configuration and Environment Variables

All configuration is read from environment variables at cold start.
Placeholder values shown for documentation; **no real values appear in this
repo, and the application must not log secret values**. Real values are
injected by Terraform per `docs/infra-implementation-plan.md`.

### MCP Lambda

| Env var | Purpose | Source / placeholder |
|---|---|---|
| `LOG_LEVEL` | Structured-log level. | `INFO` |
| `DB_SECRET_ARN` | ARN of Secrets Manager JSON containing `{username, password, host, port, dbname, engine}`. | `arn:aws:secretsmanager:<region>:<acct>:secret:<name>-<suffix>` |
| `DB_CONNECT_TIMEOUT_S` | Postgres connect timeout. | `5` |
| `DB_STATEMENT_TIMEOUT_MS` | Postgres `statement_timeout` per session. | `15000` |
| `FRAUD_FUNCTION_NAME` | Fraud-mock Lambda function name (not ARN, function name is enough for `boto3.client("lambda").invoke`). | `<name_prefix>-fraud-mock` |
| `FRAUD_INVOKE_TIMEOUT_S` | Client-side timeout for the synchronous invoke. | `5` |
| `MCP_SERVER_NAME` | FastMCP server identifier returned in `initialize`. | `ao-radar-mcp` |
| `MCP_SERVER_VERSION` | FastMCP server version returned in `initialize`. | `0.1.0` |
| `DEMO_DATA_ENVIRONMENT` | Hard guard: must equal `synthetic_demo`; the application refuses to start otherwise. | `synthetic_demo` |
| `BOUNDARY_REMINDER_TEXT` | Optional local/test override for the human-authority boundary reminder. Production/demo Terraform should leave it unset and use `HUMAN_AUTHORITY_BOUNDARY_TEXT` from `safety/authority_boundary.py`. If set, startup fails unless every required boundary clause is still present. | unset by default |

### Fraud-mock Lambda

| Env var | Purpose | Placeholder |
|---|---|---|
| `LOG_LEVEL` | Structured-log level. | `INFO` |
| `DEMO_DATA_ENVIRONMENT` | Hard guard, same semantics as above. | `synthetic_demo` |
| `FRAUD_SIGNAL_SOURCE_LABEL` | Synthetic source label emitted on every signal. | `synthetic_compliance_service_demo` |
| `FRAUD_DETERMINISTIC_SEED` | Fixed seed string for deterministic demo signal generation; never secret. | `ao-radar-synthetic-v1` |

### DB-ops Lambda

| Env var | Purpose | Placeholder |
|---|---|---|
| `LOG_LEVEL` | Structured-log level. | `INFO` |
| `DB_SECRET_ARN` | ARN of Secrets Manager JSON containing DB connection fields. | same DB secret ARN |
| `DB_CONNECT_TIMEOUT_S` | Postgres connect timeout. | `5` |
| `DB_STATEMENT_TIMEOUT_MS` | Postgres `statement_timeout` per session. | `15000` |
| `DEMO_DATA_ENVIRONMENT` | Hard guard: must equal `synthetic_demo`. | `synthetic_demo` |

Configuration loading rules:

- `config.py` validates the env vars required for the active implementation
  phase at import time and fails fast if any are missing or malformed. Phase
  1 must not require `DB_SECRET_ARN` or `FRAUD_FUNCTION_NAME`; those become
  required only when the DB and fraud-mock paths are enabled.
- Secret material (DB password) is fetched once per cold start through
  `boto3.client("secretsmanager").get_secret_value(...)` and held in process
  memory only. It is never logged.
- The `DEMO_DATA_ENVIRONMENT` value is also asserted at every database
  connection by setting an application-name session parameter and by
  cross-checking the schema-level `data_environment` CHECK on read.
- `safety/authority_boundary.py` defines
  `HUMAN_AUTHORITY_BOUNDARY_TEXT` exactly as the schema plan section 6.6
  canonical string. If `BOUNDARY_REMINDER_TEXT` is present, config validation
  rejects it unless it contains required clauses for no approve, deny, certify,
  return, cancel, amend, submit, entitlement determination, payability
  determination, fraud accusation, and contact with external parties. Do not
  allow an override that weakens the reminder.

---

## 6. FastMCP Transport and Lambda/API Gateway Adapter Strategy

### Transport choice

- **Default target: Streamable HTTP, single request/response per `POST /mcp`.**
  This is the Phase 1 adapter spike for API Gateway HTTP API + Lambda proxy
  and avoids the SSE/long-lived-connection pitfalls called out in the infra
  plan when the framework can be adapted to bounded request/response calls.
- **No SSE by default.** The `enable_sse_route` infra switch stays off in
  Phase 1. If a future iteration genuinely requires SSE, switch transport
  before turning the route on, per the infra plan's fallback decision tree.

### `POST /mcp` request flow

1. API Gateway HTTP API delivers an event in payload format v2.0 to
   `handler.py`.
2. `handler.py` routes by `requestContext.http.method` and `rawPath`:
   - `POST /mcp` → `transport.handle_mcp_request(event)`
   - `GET /health` → returns a small JSON body with version and server name;
     does not touch the database or the fraud mock.
   - Any other path → 404 with a small JSON error.
3. `transport.handle_mcp_request` decodes the body (handle the
   base64-encoded body case set by API Gateway when bodies look binary),
   parses the JSON-RPC envelope, and hands the message to the FastMCP
   server through the framework's supported adapter or a thin compatibility
   shim.
4. FastMCP dispatches to the registered tool. The tool runs synchronously
   and returns within the API Gateway 30 s integration cap; Lambda timeout
   is held below that (`25 s`) per the infra plan.
5. The transport adapter wraps the FastMCP response into an API Gateway v2.0
   response (`statusCode`, `headers`, `body`, `isBase64Encoded = false`).

### `GET /health`

- Always returns `200 OK` with a tiny JSON body, e.g.
  `{"ok": true, "server": "<MCP_SERVER_NAME>", "version": "<MCP_SERVER_VERSION>"}`.
- Does not connect to the database, does not invoke the fraud mock, does not
  initialize FastMCP-side state. This keeps it useful as a true liveness
  probe and keeps cold-start latency low.

### What the adapter must not do

- It must not introduce any other route. Generic exploration endpoints
  (`/db`, `/admin`, `/proxy`, `/eval`) are forbidden.
- It must not pass arbitrary HTTP headers into the FastMCP layer or echo
  request bodies back into logs at INFO. If body logging is used locally
  while debugging, keep it synthetic-only and disabled in committed/shared
  demo configuration.
- It must not buffer streaming responses in a way that would let a tool run
  past the 30 s integration cap. Tools must be designed to return promptly.

### MCP server bootstrap

- `server.py` constructs a single FastMCP server instance per Lambda
  container and registers each tool from `tools/` with its schema and
  handler.
- Tools are registered with declarative input schemas (Pydantic models or
  JSON Schema) so FastMCP can advertise them through `tools/list` exactly
  matching the spec section 4.5 names.
- Tool descriptions explicitly state the human-authority boundary in plain
  language so any cockpit that surfaces `tools/list` descriptions can show it.

---

## 7. Domain Tool Implementation Order

Build the tools in this order. Each step ends in a deployable Lambda and a
visible win. `prepare_ao_review_brief` is the central fusion tool; the order
front-loads the reads that feed it.

### Step A — Health and stub MCP

- `GET /health` returns 200 with the server name/version.
- `POST /mcp` returns a valid `tools/list` containing the spec section 4.5
  tool names with safe `not_implemented` handlers until each tool is wired.

This is enough to land the infra plan's Phase 1 connector check (ChatGPT
Apps developer mode connects and lists tools) without relying on database
or fraud-mock availability.

### Step B — Read-only domain tools

In dependency order so each tool can be exercised independently:

1. `list_vouchers_awaiting_action`
2. `get_voucher_packet(voucher_id)`
3. `get_traveler_profile(traveler_id)`
4. `list_prior_voucher_summaries(traveler_id)`
5. `get_policy_citation(citation_id)` and `get_policy_citations(query)`

These tools touch only Postgres through the read-side of the repository
layer. After the separate synthetic data plan is implemented, these tools
should return non-empty results from a freshly seeded database.

### Step C — Fraud-mock integration

6. `get_external_anomaly_signals(voucher_id)`

Implementation: read any persisted signals from
`external_anomaly_signals` for the voucher, then call the fraud-mock
Lambda for any deterministic synthetic supplement defined by the contract
in section 9. Persist new signals through an idempotent
`(voucher_id, signal_key)` upsert, avoid duplicating an already-persisted
deterministic signal, write a retrieval audit event when the tool invokes
the mock or persists a signal, label everything with the spec-required
`is_official_finding = false` /
`not_sufficient_for_adverse_action = true` markers, and return.

### Step D — Story analysis and fusion

7. `analyze_voucher_story(voucher_id)` — story coherence findings,
   reconstructed narrative, evidence/story gaps, suggested AO question, and
   the `review_prompt_only` marker. Composes reads from B above and any
   persisted `story_findings`; no new writes.
8. `prepare_ao_review_brief(voucher_id)` — the central fusion action.
   Combines all of B and C, plus the missing-information items already in
   the schema. Persists a new `review_briefs` row (versioned per voucher)
   and writes the corresponding `event_type = generation` audit event in
   the same transaction.

This is the first tool that persists a generated review artifact. Step C
may already persist external signals as retrieval artifacts; from Step C
onward, every path that writes anything must follow the audit-event
invariant in section 10.

### Step E — Scoped audited writes

In an order that lets the demo flow naturally:

9. `set_voucher_review_status(voucher_id, status)` — blocked-status check
   first; allowed enum from spec section 4.5.3 / schema section 6.1.
10. `mark_finding_reviewed(finding_id, status)` — allowed enum from spec
    section 4.5.2.
11. `record_ao_note(voucher_id, note, finding_id?)`.
12. `draft_return_comment(voucher_id, text)` — `kind = draft_clarification`
    on `ao_notes`. Boundary validator runs on text before persistence.
13. `request_traveler_clarification(voucher_id, message)` — sets internal
    state to `awaiting_traveler_clarification` and writes a synthetic
    `kind = synthetic_clarification_request` `ao_notes` row. No real
    traveler is contacted; the tool description must say so.
14. `record_ao_feedback(finding_id|voucher_id, feedback)` —
    `kind = ao_feedback` on `ao_notes`.
15. `get_audit_trail(voucher_id)` — read of `workflow_events` ordered by
    `occurred_at`.
16. `export_review_brief(voucher_id or brief_id, format)` — resolves the
    latest brief for a voucher, or the requested `brief_id`, returns a
    portable `markdown` or `json` payload with the canonical boundary
    reminder, and writes `workflow_events.event_type = export`.

After step E the MCP application covers the scoped tool-surface behavior in
`docs/spec.md` section 5. Final demo acceptance still depends on the
separate synthetic data plan, the selected cockpit's presentation path, and
a manual smoke pass.

---

## 8. Data Access Layer Responsibilities

The repository layer owns all Postgres access. It does not expose generic
data access of any kind, and it never lets upstream code construct queries
from strings.

### What each repository module owns

| Module | Reads | Writes |
|---|---|---|
| `connection` | Connection pool from secret; per-session `statement_timeout`; cross-checks `data_environment`. | — |
| `vouchers` | By id; list ordered by status and synthetic submission timestamp. | `review_status` updates with controlled-enum check. |
| `line_items` | By voucher id, ordered. | None (read-only at runtime). |
| `evidence` | By voucher id and by line item id. | None at runtime. |
| `travelers` | By id. | None at runtime. |
| `prior_summaries` | By traveler id. | None at runtime. |
| `citations` | By id and by topic / retrieval anchor. | None at runtime. |
| `signals` | By voucher id and by signal type. | Insert from fraud-mock results, append-only. |
| `findings` | By voucher id, by id. | `review_state` and `needs_human_review` updates only via the workflow contract. |
| `missing_information` | By voucher id. | None at runtime. |
| `briefs` | By voucher id, latest version. | Append-only, version monotonic per voucher. |
| `ao_notes` | By voucher id, by kind. | Append-only by `kind`. |
| `workflow_events` | By voucher id, ordered. | Append-only, called by every write tool and refusal path. |

### Hard rules

- No module exports a method that takes raw SQL, an arbitrary table name, an
  arbitrary file path, or an unscoped session/cursor object. Tools call
  named, typed methods only.
- Workflow write methods and persisted analysis-artifact writes accept the
  audit-event metadata for their tool and emit the required
  `workflow_events` row in the **same** transaction as the domain write.
  The repository commits or rolls back atomically; partial writes are not
  permitted. External-signal retrieval/persistence uses
  `event_type = retrieval`, not a hidden write.
- Repository methods return immutable typed results (Pydantic models or
  dataclasses), not raw rows. Tools never see DB-driver objects.
- The schema plan owns enum values and CHECK constraints. The repository
  layer must not silently coerce or shadow them; if the database rejects a
  value, the repository surfaces the error to the tool, which converts it
  to a refusal (see section 11).

This document does not repeat the schema. The coding agent reads
`docs/schema-implementation-plan.md` for table/column names, enum values,
audit invariant matrix, and fixture-validator expectations. Detailed seed
content remains deferred to the separate synthetic data plan.

---

## 9. Fraud-Mock Lambda Integration

The fraud mock is a deterministic, stateless, synthetic stand-in for the
external compliance/anomaly service the spec describes. It is **not** a
real anomaly detector and does not run against real data.

### Responsibilities

- Accept a request that names a synthetic voucher (and optionally line items
  or signal categories of interest).
- Return a deterministic synthetic signal set for that input. Same input
  must always produce the same output across cold starts so demos are
  reproducible.
- Never read or write the database. The mock is stateless.
- Never call external networks. The mock has no outbound IO.
- Tag every signal as `is_official_finding = false` and
  `not_sufficient_for_adverse_action = true` to match the spec and the
  schema CHECKs.

### High-level synthetic signal contract

The signal shape mirrors `external_anomaly_signals` from the schema plan.
Detailed scenario coverage and per-voucher signal specifics are deferred to
the synthetic data plan; this plan only requires that the contract honor
the following:

- **Request** carries at minimum a `voucher_id` and the
  `data_environment` guard. The MCP Lambda always sets
  `data_environment = synthetic_demo`; the mock refuses other values.
- **Response** is a list of zero or more signal objects, each with:
  - `signal_type` drawn from the schema enum
    (`duplicate_payment_risk`, `high_risk_mcc_demo`, `unusual_amount`,
    `date_location_mismatch`, `split_disbursement_oddity`,
    `repeated_correction_pattern`, `peer_baseline_outlier`,
    `traveler_baseline_outlier`).
  - `synthetic_source_label` (e.g. `synthetic_compliance_service_demo`).
  - `signal_key`, deterministic within a voucher using the synthetic-data
    plan format `<signal_type>:<scenario_slug>:<ordinal>`.
  - `signal_id`, derived from `voucher_id` and `signal_key` using the
    schema plan format.
  - `rationale_text` written in neutral, non-accusatory language.
  - `confidence` from the schema enum (`low | medium | high`).
  - The two boolean markers above.
  - A timestamp the MCP Lambda rewrites to `received_at` on persist.
- Determinism is implemented by hashing the `voucher_id`, `signal_key`, and
  a fixed seed. `(voucher_id, signal_key)` is the idempotence boundary; if
  the repository sees a unique-key conflict while persisting a fraud-mock
  supplement, it treats the conflict as a successful replay and returns the
  stored row.

### MCP-side handling

- `fraud_client.client` wraps `boto3.client("lambda").invoke` with the
  configured timeout and returns parsed contract objects.
- `tools/get_external_anomaly_signals.py` calls the client, persists any
  new signals through the `signals` repository (append-only), and returns
  the union of stored and fresh signals to the caller.
- The tool description shown in `tools/list` makes it explicit that the
  signals are review prompts only, not official findings.

The detailed catalog of which signals the mock should produce for which
synthetic vouchers belongs in the synthetic data plan and is deferred from
this document.

---

## 10. Audit / Event Invariant for Every Scoped Write and Refusal

The schema plan defines the audit-event invariant matrix
(`docs/schema-implementation-plan.md` section 8). The application must
honor every row of that matrix without re-deriving it. This section lists
the application-side rules.

### Invariant rules

1. **Every successful scoped write writes exactly one
   `workflow_events` row in the same database transaction as the domain
   write.** No exceptions. If the workflow event cannot be written, the
   domain write must roll back.
2. **Every DB-backed refusal writes exactly one `workflow_events` row with
   `event_type = refusal`** before returning the refusal to the caller.
   Refusal events carry the rejected request shape in
   `rationale_metadata` (sanitized — never log secrets or attempt to
   persist fabricated PII).
3. **Every brief generation writes exactly one `workflow_events` row with
   `event_type = generation`** referencing the new `brief_id`.
4. **Every standalone retrieval worth recording writes a
   `workflow_events` row with `event_type = retrieval`** when there is a
   voucher context or brief-generation context to attach. At minimum, this
   covers fraud-mock invocation and any citation retrievals performed during
   `prepare_ao_review_brief`; the generation event may also carry the
   retrieved IDs in `rationale_metadata`.
5. **Every `needs_human_review = true` finding has a corresponding
   `event_type = needs_human_review_label`** event. Application code that
   sets the boolean is responsible for this.
6. The `human_authority_boundary_reminder` field on every event is
   non-empty. Application code reads the constant from
   `safety/authority_boundary.py`.

### How the application enforces this

- Each write tool funnels through a single helper that takes the domain
  callable plus the audit metadata and runs both inside one transaction.
- DB-backed refusal paths call a single `safety` helper that builds the
  refusal response and the `workflow_events` row together; tools never
  construct refusals ad hoc.
- A small set of manual verification checks (section 13) confirms during
  demo setup that every write/refusal path produces the expected event row.

---

## 11. Boundary and Refusal Validators

The application enforces the trust boundary at two layers:

- **Status-like fields:** the schema CHECK constraints reject blocked
  values (see schema plan section 6.4). The application calls these the
  source of truth for status validation.
- **Free-text fields and tool inputs:** the application enforces a
  context-aware validator before any draft note, brief paragraph, or
  reviewer-prompt text is persisted.

### Inputs that are validated

- `set_voucher_review_status(status)` — blocked-status check before the
  database call. The allowed enum and blocked list come from the schema
  section 6.1 / 6.4 source of truth.
- `mark_finding_reviewed(status)` — same blocked-status check.
- `record_ao_note.note`, `draft_return_comment.text`,
  `request_traveler_clarification.message`,
  `record_ao_feedback.feedback` — context-aware unsafe-wording check.
- Review-facing generated narrative fields from `prepare_ao_review_brief`
  and `analyze_voucher_story` — same check. If the validator fails, the
  tool returns a refusal and the brief generation is aborted.

### What the unsafe-wording validator rejects

(Per schema plan section 6.4. This list lives in
`safety/unsafe_wording.py`; the schema plan is the canonical source.)

- Statements that a voucher is approved, denied, certified, returned,
  cancelled, amended, submitted, payable, nonpayable, or ready for
  payment.
- Recommendations that the reviewer take an official disposition.
- Allegations that a traveler, vendor, or transaction is fraudulent,
  abusive, misuse, misconduct, or similar.
- Claims that the system has determined entitlement or payability.
- Wording that says the system contacted, notified, or escalated to a real
  traveler, command, investigator, law-enforcement body, or any external
  party.

### Status-like blocked values

(Mirrored from schema plan section 6.4.) The application's blocked-list is
loaded from a single constant module so it cannot drift from the schema
CHECK list.

- `approved`, `approve`
- `denied`, `deny`, `rejected`, `reject`
- `certified`, `certify`
- `submitted`, `submit`, `submitted_to_dts`
- `returned`, `return`, `return_voucher`, `officially_returned`
- `cancelled`, `canceled`, `cancel`
- `amended`, `amend`
- `paid`, `payable`, `nonpayable`, `ready_for_payment`, `payment_ready`
- `fraud`, `fraudulent`, `misuse`, `abuse`, `misconduct`
- `entitled`, `entitlement_determined`
- `escalated_to_investigators`, `notify_command`, `contact_traveler`

### Refusal output shape

- A short, neutral refusal sentence stating that the requested action is
  outside the supported workflow.
- A `reason` code (e.g. `prohibited_action`, `out_of_scope_artifact`,
  `unsupported_status_value`, `unsafe_wording_in_input`,
  `missing_required_input`, `ungrounded_claim`).
- A pointer back to the human-authority boundary reminder.
- For DB-backed workflow tools, a workflow event of `event_type = refusal`
  written before the response returns.

### What the application must never expose

- `query_database`, `execute_sql`, `run_query`, or any other raw-database
  tool name through MCP.
- Free-form filesystem readers (`read_file`, `list_dir`,
  `download_file`).
- Arbitrary HTTP fetch (`fetch_url`, `http_get`).
- New tool names outside the spec catalog that imply approval, denial,
  certification, official return, cancellation, amendment, submission,
  payment, payability, entitlement determination, fraud allegation, or
  external contact. The spec-defined `draft_return_comment` remains allowed
  only because it stores non-official draft text and sends nothing.

---

## 12. Build and Deploy Handoff to Terraform

This plan does not write Terraform; the infra plan owns that. It only
defines the artifacts the infra plan consumes and the deploy contract.

### Lambda zip artifacts

- `ops/build/build_mcp_zip.sh` produces `infra/build/mcp.zip` containing
  the `ao_radar_mcp` package and its dependencies, suitable for
  `runtime = python3.12` in the infra plan.
- `ops/build/build_fraud_zip.sh` produces `infra/build/fraud.zip`
  containing the `ao_radar_fraud_mock` package. The fraud mock has no
  third-party runtime dependencies beyond the Lambda Python runtime, so
  this zip is intentionally tiny.
- `ops/build/build_db_ops_zip.sh` produces `infra/build/db_ops.zip`
  containing the private `ao_radar_db_ops` package plus the migration and
  seed code it invokes.
- All build scripts are idempotent and produce a deterministic zip when
  given the same source tree, so `filebase64sha256` in Terraform changes
  only when the source changes.
- Build scripts do not embed secrets, environment values, or
  account-specific identifiers.

### Handler entrypoints

- MCP Lambda: `handler = "ao_radar_mcp.handler.lambda_handler"`.
- Fraud-mock Lambda: `handler = "ao_radar_fraud_mock.handler.lambda_handler"`.
- DB-ops Lambda: `handler = "ao_radar_db_ops.handler.lambda_handler"`.

### Environment variables (per infra phase)

The infra plan phases env vars to avoid forward references:

- **Phase 1 (stub MCP Lambda):** `LOG_LEVEL`, `MCP_SERVER_NAME`,
  `MCP_SERVER_VERSION`, `DEMO_DATA_ENVIRONMENT`. No DB, no fraud mock.
- **Phase 2 (DB attached):** add `DB_SECRET_ARN`,
  `DB_CONNECT_TIMEOUT_S`, `DB_STATEMENT_TIMEOUT_MS`.
- **Phase 3 (fraud mock attached):** add `FRAUD_FUNCTION_NAME`,
  `FRAUD_INVOKE_TIMEOUT_S`.
- **DB-ops Lambda:** `LOG_LEVEL`, `DB_SECRET_ARN`,
  `DB_CONNECT_TIMEOUT_S`, `DB_STATEMENT_TIMEOUT_MS`,
  `DEMO_DATA_ENVIRONMENT`.

### Migration runner

- `ops/scripts/run_migrations.py` is a small script that reads
  `DB_SECRET_ARN` from the environment, applies migrations from
  `ops/migrations/`, and exits.
- For the hackathon demo, the migration runner is invoked through the
  Terraform-managed, VPC-attached `db_ops` Lambda. Local developer commands
  may use the same code for tests, but deployed migration/seed/reset must
  not rely on manually created one-off AWS resources.
- The runner asserts the `data_environment = synthetic_demo` guard before
  applying any migration.

### Seed routine handoff

- The future synthetic data plan owns the contents of `ops/seed/`. This
  application plan only requires that, when that plan lands, a guarded
  `reset_demo()` routine exists, runs only when
  `data_environment = synthetic_demo`, and preserves the audit-event
  invariants for any seeded workflow state.
- Deployed seed and reset operations are exposed only as `db_ops` Lambda
  operation payloads such as `{"operation":"seed"}` and
  `{"operation":"seed","reset":true}`. They are never MCP tools.

### What the infra plan should expect from the application

- Three Lambda zip paths, set via `var.mcp_lambda_zip_path`,
  `var.fraud_lambda_zip_path`, and `var.db_ops_lambda_zip_path` per the
  infra plan's Appendix A.
- Three handler strings (above).
- The env-var matrix in section 5, scoped by phase.
- No additional API Gateway routes, IAM policies, or VPC endpoints
  beyond those the infra plan already enumerates.

---

## 13. Manual Demo Verification Checklist

This is **not** a test plan. It is a short pre-demo sanity sweep a human
can run against the deployed stack to confirm the application behaves at
the boundary the spec requires.

### Smoke

- [ ] `GET /health` returns 200 with `server` and `version` fields.
- [ ] `POST /mcp` with a `tools/list` request returns the full tool
  catalog from spec section 4.5 and **no other tools**.
- [ ] No tool name in `tools/list` matches a generic-data-access pattern
  (`query_database`, `execute_sql`, `read_file`, `fetch_url`, etc.).

### Read path

- [ ] `list_vouchers_awaiting_action` returns the seeded queue and labels
  the response as workload guidance (no approval/payment language).
- [ ] `get_voucher_packet` returns trip metadata, line items, evidence
  references, justification, and pre-existing flags for a known synthetic
  voucher.
- [ ] `get_traveler_profile` and `list_prior_voucher_summaries` return
  synthetic context with the demo markers visible.
- [ ] `get_policy_citation` and `get_policy_citations` return verbatim
  synthetic demo reference-corpus excerpts with source identifiers.

### Fraud-mock integration

- [ ] `get_external_anomaly_signals` for a seeded voucher returns at
  least one signal labeled `is_official_finding = false` and
  `not_sufficient_for_adverse_action = true`.
- [ ] Calling it twice with the same input returns the same synthetic
  signal set.
- [ ] Every returned signal has a deterministic `signal_key`, a derived
  `signal_id`, and no duplicate `(voucher_id, signal_key)` row after
  repeated calls.

### Fusion

- [ ] `prepare_ao_review_brief` for a non-control voucher returns a brief
  whose `policy_hooks`, `signal_hooks`, `finding_hooks`, and
  `missing_information_hooks` each resolve to existing rows.
- [ ] The brief carries a non-empty `human_authority_boundary_text` and
  an explicit `brief_uncertainty`.
- [ ] A new `review_briefs` row exists with version monotonically
  incremented for that voucher, plus a corresponding
  `event_type = generation` row in `workflow_events`.
- [ ] `export_review_brief` returns the latest brief, or a requested
  `brief_id`, in `markdown` and `json`, includes the canonical boundary
  reminder, and writes one `event_type = export` audit row.

### Scoped writes

- [ ] `set_voucher_review_status` succeeds for each allowed value in
  schema section 6.1 and emits a `scoped_write` event per call.
- [ ] `mark_finding_reviewed` succeeds for each allowed value in schema
  section 6.3 and emits a `scoped_write` event per call.
- [ ] `record_ao_note`, `draft_return_comment`,
  `request_traveler_clarification`, and `record_ao_feedback` each
  produce the matching `ao_notes` row plus a `scoped_write` event.
- [ ] `get_audit_trail` returns the events in chronological order with
  the human-authority boundary reminder set on every row.

### Refusal

- [ ] `set_voucher_review_status` with each blocked value
  (`approved`, `denied`, `certified`, `submitted`, `paid`, `fraud`,
  `returned`, `cancelled`, `amended`) returns a refusal and emits a
  `refusal` event.
- [ ] A tool call asking the system to "approve" or "certify" a voucher
  through any path returns a refusal with an actionable reason and a
  recorded event.
- [ ] A non-voucher artifact submitted through any tool that takes a
  voucher id returns a refusal with `reason = out_of_scope_artifact`.

### Public-safety sweep

- [ ] No log line in the most recent demo run contains a value resembling
  a real card PAN, SSN, real domain email, or other obvious real-data
  shape.
- [ ] Every traveler `display_name` returned in the demo carries a
  synthetic marker substring.
- [ ] Every brief and exported artifact shows the human-authority
  boundary reminder.

If every box is checked, the application is demo-ready. Failures point
back into the matching companion document for the fix.

---

## 14. Implementation Phases

Each phase ends in a deployable Lambda and a meaningful demo checkpoint.
Bias toward landing each phase as its own change so review and rollback
are easy.

### Phase 0 — Repo bootstrap

- Create the `src/ao_radar_mcp/`, `src/ao_radar_fraud_mock/`, and `ops/`
  layouts in section 4.
- Add a minimal `pyproject.toml` (or equivalent) so packaging is
  reproducible.
- Wire `ops/build/build_mcp_zip.sh` and `ops/build/build_fraud_zip.sh`
  and `ops/build/build_db_ops_zip.sh` to produce empty-but-valid zips that
  import-check at Lambda cold start.

**Exit criterion:** zips build deterministically; both Lambdas can be
deployed by Terraform Phase 1 with placeholder handlers that return 200.

### Phase 1 — Stub MCP, FastMCP, /health

- Implement `handler.py`, `transport.py`, `server.py`, and spec-catalog
  `tools/list` registrations backed by safe `not_implemented` handlers.
- Implement `GET /health` and a Streamable-HTTP `tools/list` that returns
  the catalog with descriptions but `not_implemented` handlers.
- No DB, no fraud mock.

**Exit criterion:** ChatGPT Apps developer mode connects to the public
endpoint, calls `tools/list`, and sees the spec section 4.5 names.

### Phase 2 — Repository wiring and read tools

- Implement `repository/connection.py` against the schema plan's tables.
- Implement repository modules for `vouchers`, `line_items`, `evidence`,
  `travelers`, `prior_summaries`, `citations`, `missing_information`.
- Bind read tools B-1 through B-5 from section 7 to the repository layer.
- Add the `data_environment = synthetic_demo` guard at connect time.

**Exit criterion:** the read tools handle an empty database safely and return
rows from a freshly seeded database after the separate synthetic data plan
has been implemented.

### Phase 3 — Fraud-mock Lambda and signal tool

- Implement `ao_radar_fraud_mock` with deterministic synthetic output per
  the high-level contract in section 9, including stable `signal_key` and
  derived `signal_id` values.
- Implement `fraud_client/client.py` and bind
  `get_external_anomaly_signals` to it with append-only persistence.

**Exit criterion:** the signal tool returns deterministic synthetic
signals; storing and re-reading them produces the same results.

### Phase 4 — Story analysis and brief fusion

- Implement `domain/story_analysis.py` and `domain/missing_information.py`.
- Bind `analyze_voucher_story`.
- Implement `domain/brief_assembly.py` and bind
  `prepare_ao_review_brief`. Persist `review_briefs` and the
  `event_type = generation` audit event in one transaction.
- Bind `export_review_brief` so it resolves an existing brief, emits a
  portable artifact, and writes `event_type = export`.

**Exit criterion:** with synthetic fixture data present, a non-control
voucher produces a brief with non-empty `policy_hooks`, `signal_hooks`,
`finding_hooks`, and `missing_information_hooks`, and a versioned row in
`review_briefs`; exporting that brief returns the requested format and logs
an export event.

### Phase 5 — Scoped audited writes

- Implement the safety helpers in `safety/` (controlled status,
  unsafe wording, authority boundary text).
- Bind the seven write tools and `get_audit_trail` from section 7
  step E. Each write runs inside the audit-event invariant helper.

**Exit criterion:** every tool in spec section 4.5.2 produces the
expected `workflow_events` row, and every blocked-value attempt produces
a refusal event.

### Phase 6 — Boundary hardening and demo polish

- Run the manual demo verification checklist in section 13.
- Tighten log redaction so no synthetic-but-noisy field leaks at INFO.
- Confirm tool descriptions in `tools/list` match the spec wording.

**Exit criterion:** the manual checklist passes against the deployed stack
from a clean seed once the separate synthetic data plan has landed.

---

## 15. Open Questions and Deferred Documents

### Deferred documents

- **Synthetic data / seed scenario plan.** This application plan does not
  write per-voucher narrative content, evidence cue distribution, policy
  excerpt corpus, persona names, or per-scenario fraud-mock signal recipes.
  A separate synthetic data plan will own that and will pair with
  `ops/seed/` and the fraud-mock deterministic generator.
- **Cybersecurity follow-up.** The repository README defers a careful
  treatment of threat models, access controls, deployment boundaries,
  data handling, and audit requirements until after the competition. The
  application implementation must not rely on that follow-up for its
  demo posture; it must remain demo-safe in the meantime.

### Open application questions

- Will FastMCP's request adapter run cleanly inside an API Gateway
  HTTP API + Lambda proxy without a thin compatibility shim, or does the
  transport adapter need to translate request envelope shapes? Phase 1
  is the first concrete answer.
- Is the planned synchronous `lambda:Invoke` of the fraud mock fast
  enough to keep `prepare_ao_review_brief` under the 25 s Lambda timeout
  on a cold start? If not, the application needs to cache fraud-mock
  results per `voucher_id` for the duration of a brief generation.
- Should `prepare_ao_review_brief` always create a new `review_briefs`
  version, or should it short-circuit and return the latest version
  when no upstream input has changed? The schema supports either; the
  application defaults to always creating a new version for audit
  clarity unless that proves noisy in demo.
- How aggressively should the unsafe-wording validator scan generated
  narrative output (not just user input)? The schema plan recommends running
  the validator against draft and brief text; the application defaults to
  generated brief, draft, and reviewer-prompt narrative fields before
  persistence.
- Is FastMCP's `tools/list` description field carried through to the
  cockpit UI clearly enough that reviewers see the human-authority
  boundary statement without a separate UI hint? If not, surface the
  reminder inside workflow-state response payloads as well.

---

*End of application implementation plan.*
