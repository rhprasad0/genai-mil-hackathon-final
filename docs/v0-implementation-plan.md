# Policy Bonfire / AO Radar V0 Implementation Plan

Status: concrete implementation plan, not implemented
Canonical spec: `docs/spec.md`
Supporting docs: `docs/model-testing-plan.md`, `experiments/policy-bonfire/README.md`

## Goal

Build a clickable, screenshot-friendly V0 web demo for AO Radar / Policy Bonfire.

V0 is one landing/play screen and one server/API handler. A user picks a built-in synthetic packet, asks the red AO Radar actor how the closed loop will mishandle it, calls a hosted model at run time, watches the sandbox replay only allowlisted fake actions, and sees Policy Bonfire burn cards map the observed failure to public Responsible AI concepts.

The first default scenario is `checkbox_reviewer`. `missing_receipt_furnace` must also ship in V0. Additional scenario seeds can be available if they do not slow the default path.

The point is not a benchmark platform. The point is a clean public demo: AO Radar is the unsafe specimen, Policy Bonfire is the room where it gets caught burning the controls.

## Current Repo Facts

- There is no web app scaffold or package manifest in the repo at the time of this plan.
- The canonical product and safety requirements are in `docs/spec.md`.
- The experiment harness under `experiments/policy-bonfire/` provides source material for scenario seeds, schemas, fake tools, prompts, public-safety scanning patterns, and refusal handling.
- Runtime hosted model feasibility is de-risked by the completed 30-call hosted smoke matrix: 30/30 schema-valid, 0 refusals across 5 hosted models. V0 should still keep refusal handling because refusal is valid experiment data.
- The main build risks are prompt/schema discipline, monitor quality, visible `SYNTHETIC` stamping, and UI clarity.

## Non-Goals

- No real DoD compliance tool.
- No real DTS integration.
- No production decisioning.
- No real vouchers, receipts, claimants, payments, reimbursements, debt, fraud, or government workflow.
- No real document upload.
- No private data entry.
- No full eval platform, leaderboard, admin console, or model bakeoff UI.
- No deterministic unsafe adjudication fallback.
- No hidden canned villain branch that is presented as live model behavior.
- No model-as-judge monitor in V0 unless the rule-based monitor is already solid and the UI makes monitor uncertainty explicit.

## Public-Safety Constraints

These are product requirements, not polish tasks.

- Every packet, person, office, amount, date, tool, DB row, audit entry, notice, policy card, and outcome is synthetic.
- Every rendered artifact must visibly carry `SYNTHETIC`.
- The red actor may deceive the synthetic in-app user persona, but the harness must not deceive the real viewer.
- A refusal or provider failure is rendered as an experiment result with its refusal kind. No fake actions execute on refusal, schema violation, or model unavailability.
- The configured hosted model endpoint is the only allowed network destination for the V0 run path.
- The API route must not accept uploads or persist user-provided packet text.
- Tool calls must use a fixed fake catalog with `fake_` names and JSON-schema/Zod-validated arguments.
- Calls outside the fake catalog are rejected, recorded in the truth ledger, labeled `TOOL_OUT_OF_SANDBOX`, and never mutate state.
- The public-safety scanner runs before model output, refusal text, tool arguments, audit entries, notices, burn cards, or ledgers render.
- Redactions are visible as `PUBLIC_SAFETY_REDACTION`, never silently dropped.
- Replay fixtures may exist only for `REPLAY`, regression, or test mode. They must never be presented as live model behavior.

## Architecture

```text
Single Play Screen
  |
  | POST selected synthetic scenario id
  v
One API Route / Server Handler
  |
  | load scenario, fake tools, policy controls, prompt
  v
Hosted Red Actor Model
  |
  | structured JSON or refusal/failure
  v
Schema + Public-Safety Validation
  |
  | completed run only
  v
Fake Executor
  |
  | allowlisted fake tool calls only
  v
Immutable Truth Ledger
  |
  v
Rule-Based Monitor + Burn-Card Generator
  |
  v
UI Panels
```

Important discipline: model-proposed `synthetic_db_transactions` are actor claims until validated. The fake executor should generate the visible synthetic events and DB diffs from allowlisted fake tool calls. Never directly apply arbitrary model-authored DB mutations as executable instructions.

## Tech Stack Assumptions

Because no app exists today, start by creating a minimal app scaffold. Recommended stack:

- TypeScript.
- Next.js App Router for one page plus one API route.
- React for the play screen.
- Zod for runtime schema validation.
- Vitest for unit tests.
- Playwright for one screenshot-mode smoke test if the scaffold cost is acceptable.
- Provider wrapper using ordinary hosted model HTTP/SDK calls.

Recommended app location: `apps/policy-bonfire/`. This avoids disturbing root docs and keeps the V0 demo isolated. If the implementer chooses a root app instead, update all commands and paths in this plan before coding.

Provider defaults:

- Default family: Gemini Flash-Lite, selected through config.
- Cheap fallback: one additional hosted cheap model family selected through the same provider wrapper.
- Use example-only config names such as `POLICY_BONFIRE_PROVIDER`, `POLICY_BONFIRE_MODEL`, and `POLICY_BONFIRE_CREDENTIAL`.
- Do not commit `.env`, concrete key values, private account ids, private endpoints, or raw provider transcripts.

## Source Material To Port

Port and reconcile this source material into the app. Do not blindly copy older experiment names if they conflict with `docs/spec.md`.

- Scenarios:
  - `experiments/policy-bonfire/scenarios/checkbox_reviewer.json`
  - `experiments/policy-bonfire/scenarios/missing_receipt_furnace.json`
  - Optional after default path works: the other files in `experiments/policy-bonfire/scenarios/`
- Actor schema:
  - `experiments/policy-bonfire/specs/actor_schema.json`
  - Reconcile to `docs/spec.md` names where needed. The spec uses control burn items shaped like `handle`, `evidence_pointer`, and `rationale`; the experiment schema currently uses `policy_handle`, `burn_summary`, and `evidence`.
- Fake tool catalog:
  - `experiments/policy-bonfire/specs/fake_tool_catalog.json`
- Policy controls:
  - `experiments/policy-bonfire/specs/policy_controls.json`
  - Upgrade V0 handles to the canonical `docs/spec.md` catalog, including `daep.responsible`, `daep.equitable`, `daep.traceable`, `daep.reliable`, `daep.governable`, `human_authority_boundary`, `meaningful_human_review`, `stop_path_and_disengagement`, `requirements_validation`, `rai_self_assessment_independence`, `audit_trail_limits`, and `operator_trust_calibration`.
- Prompts:
  - `experiments/policy-bonfire/prompts/red_actor_theater.md` as the default V0 voice.
  - `experiments/policy-bonfire/prompts/red_actor_clinical.md` as a stricter fallback prompt setting.
  - `experiments/policy-bonfire/prompts/monitor.md` only as reference; V0 monitor should start rule-based.
- Harness ideas:
  - `experiments/policy-bonfire/run_model_sweep.py` for refusal classification, scanner patterns, schema-valid checks, and public-safe markdown instincts.

Do not use `experiments/policy-bonfire/raw/` as public UI source material. Raw outputs stay private until sanitized.

## Exact Files Likely To Create Or Modify

Plan-only work in this turn creates just `docs/v0-implementation-plan.md`. Future implementation should keep changes small and auditable.

Likely app scaffold files if using `apps/policy-bonfire/`:

- `apps/policy-bonfire/package.json`
- `apps/policy-bonfire/next.config.ts`
- `apps/policy-bonfire/tsconfig.json`
- `apps/policy-bonfire/app/layout.tsx`
- `apps/policy-bonfire/app/page.tsx`
- `apps/policy-bonfire/app/globals.css`
- `apps/policy-bonfire/app/api/policy-bonfire/run/route.ts`

Likely app library files:

- `apps/policy-bonfire/lib/policy-bonfire/scenarios.ts`
- `apps/policy-bonfire/lib/policy-bonfire/policyControls.ts`
- `apps/policy-bonfire/lib/policy-bonfire/fakeTools.ts`
- `apps/policy-bonfire/lib/policy-bonfire/actorSchema.ts`
- `apps/policy-bonfire/lib/policy-bonfire/publicSafety.ts`
- `apps/policy-bonfire/lib/policy-bonfire/provider.ts`
- `apps/policy-bonfire/lib/policy-bonfire/executor.ts`
- `apps/policy-bonfire/lib/policy-bonfire/truthLedger.ts`
- `apps/policy-bonfire/lib/policy-bonfire/monitor.ts`
- `apps/policy-bonfire/lib/policy-bonfire/burnCards.ts`
- `apps/policy-bonfire/lib/policy-bonfire/prompts.ts`
- `apps/policy-bonfire/lib/policy-bonfire/types.ts`

Likely tests:

- `apps/policy-bonfire/tests/actorSchema.test.ts`
- `apps/policy-bonfire/tests/publicSafety.test.ts`
- `apps/policy-bonfire/tests/executor.test.ts`
- `apps/policy-bonfire/tests/monitor.test.ts`
- `apps/policy-bonfire/tests/refusalFlow.test.ts`
- `apps/policy-bonfire/tests/syntheticStamp.test.ts`
- `apps/policy-bonfire/tests/play-screen.spec.ts`

Optional local-only artifacts:

- `apps/policy-bonfire/artifacts/linkedin/` for generated screenshot captures during local review.
- Public artifact path, only after review: `docs/policy-bonfire-v0-public-artifact.md`.

Files to avoid unless Ryan explicitly changes scope:

- `docs/hackathon-submission-receipt.md`
- `docs/demo-receipts.md`
- `assets/demo/`
- `README.md`
- root `package.json` if one appears for unrelated project purposes
- `sandbox/`
- `data/`
- `assets/`
- `scripts/`

## Recommended Implementation Sequence

### 1. Establish app stack / minimal web shell

Only do this if an app is still absent.

Tasks:

- Create the minimal TypeScript web scaffold in `apps/policy-bonfire/`.
- Add a single page at `app/page.tsx`.
- Add one POST route at `app/api/policy-bonfire/run/route.ts`.
- Render static placeholder panels first: scenario picker, red actor, fake tools, fake DB diff, truth ledger, burn cards.
- Add global `SYNTHETIC` banner and per-panel `SYNTHETIC` stamps from day one.

Commit point: `Create Policy Bonfire V0 web shell`.

### 2. Port scenario/control catalogs from experiments to app lib

Tasks:

- Add `checkbox_reviewer` and make it the default selected scenario.
- Add `missing_receipt_furnace`.
- Port the fake tool catalog.
- Create the canonical policy-control catalog from `docs/spec.md`; keep aliases only if needed to translate old experiment handles.
- Keep all data synthetic and short enough for screenshot panels.
- Do not import raw experiment outputs as demo content.

Commit point: `Add synthetic scenarios and policy catalog`.

### 3. Build schema validation and SYNTHETIC string validation

Tasks:

- Define the canonical actor output schema with Zod.
- Require the exact channels from `docs/spec.md`: `red_plan`, `synthetic_tool_calls`, `synthetic_db_transactions`, `user_facing_claim`, `audit_log_entries`, `control_burns`, and `failure_labels`.
- Classify malformed or partial output as `SCHEMA_VIOLATION` or `PARTIAL_REFUSAL`.
- Validate that rendered artifacts either include `SYNTHETIC` in the artifact body or receive a visible renderer stamp before display.
- Add public-safety scanner rules for credential-like strings, private paths, real endpoint-looking URLs outside allowlists, real-looking PII patterns, and missing synthetic boundary markers.

Commit point: `Validate actor schema and synthetic boundary`.

### 4. Build provider wrapper for hosted actor call

Tasks:

- Implement one provider wrapper interface: `callRedActor(input): Promise<ActorResult>`.
- Default to Gemini Flash-Lite family through config, not hard-coded across the app.
- Add a cheap fallback provider/model through the same config path.
- Keep env var names generic/example-only.
- Set timeouts and return `MODEL_UNAVAILABLE` on provider errors.
- Preserve model refusal text after public-safety scan.
- Do not add deterministic unsafe text as a fallback. Ever.

Commit point: `Call hosted red actor model`.

### 5. Build fake executor

Tasks:

- Execute only allowlisted `fake_` tool calls from the catalog.
- Validate required args and reject extra/invalid args.
- Convert allowed calls into synthetic tool-tape events and fake DB diffs.
- Record rejected calls in the truth ledger as `TOOL_OUT_OF_SANDBOX`.
- Block all fake execution if the actor result is any refusal/failure type.
- Treat actor-supplied DB transactions as proposed claims unless they correspond to allowed fake tool behavior.

Commit point: `Replay fake tool calls into synthetic ledger`.

### 6. Build rule-based monitor/burn-card generator before adding model-as-judge

Tasks:

- Implement rule checks from `docs/spec.md`: sandbox, citation resolution, evidence faithfulness, authority, escalation, audit truthfulness, and self-certification.
- Map findings to burn cards with plain-English sections: what looked safe, what happened, why it matters, and what safe process would do.
- Always produce at least one burn card for a completed run.
- If no finding is produced for a completed run, label the monitor result `MONITOR_INCONCLUSIVE` and do not render the run as clean.
- Keep model-as-judge as post-V0 or behind explicit config after rule-based quality is acceptable.

Commit point: `Add rule-based Policy Bonfire monitor`.

### 7. Build UI panels

Tasks:

- Scenario picker: cards for `Checkbox Reviewer` and `Missing Receipt Furnace`, with `Checkbox Reviewer` selected by default.
- Red actor panel: prompt question, provider/model metadata, red plan, refusal/result type.
- Synthetic tool tape: allowed, blocked, and skipped fake calls.
- Fake DB diff: before/after synthetic rows.
- Audit Log Whitewash: actor-authored audit claims clearly separated from truth.
- Synthetic user notice: polished actor claim, stamped `SYNTHETIC`.
- Immutable Truth Ledger: packet facts, safe-process cue, actor outputs, fake actions, monitor findings.
- Burn card stack: cards mapped to DoD Responsible AI principles and related handles.
- Make the reveal order match `docs/spec.md`: intake, theater, lie, burn, inspect.

Commit point: `Build playable Policy Bonfire screen`.

### 8. Add refusal/error UI

Tasks:

- Render `HARD_REFUSAL`, `PARTIAL_REFUSAL`, `SAFETY_REDIRECT`, `SCHEMA_VIOLATION`, and `MODEL_UNAVAILABLE` as experiment results.
- Show that no fake tool calls, DB mutations, audit entries, or user notice were executed.
- Preserve scanned/redacted model response in the truth ledger.
- Make provider timeout and missing config understandable without exposing secrets.

Commit point: `Surface refusals as experiment results`.

### 9. Add tests and public-safety scans

Tasks:

- Unit-test schema validity, refusal classification, public-safety scanning, fake executor allowlists, truth-ledger append behavior, monitor mappings, and synthetic stamping.
- Add regression fixtures only under explicit `REPLAY` or test labels.
- Test that replay fixtures cannot be selected as live actor output.
- Add a scan that fails on secret-shaped values, private paths, missing `SYNTHETIC` display stamps, and unsafe real-world claims.

Commit point: `Add V0 safety and behavior tests`.

### 10. Polish screenshot mode and LinkedIn artifact path

Tasks:

- Add a screenshot mode such as `?shot=linkedin` that selects `checkbox_reviewer`, reduces animation delay, and keeps the main packet, red plan, fake tool/db action, truth ledger, and one burn card visible.
- Keep the page obviously `SYNTHETIC` in screenshot mode.
- Generate local screenshots into `apps/policy-bonfire/artifacts/linkedin/` during review.
- If a public written artifact is needed, create `docs/policy-bonfire-v0-public-artifact.md` with synthetic-only excerpts after scans pass.
- Do not place new generated artifacts under protected receipt paths or `assets/demo/`.

Commit point: `Polish public screenshot path`.

## Bite-Sized Task Checklist

- Confirm scaffold location and commands.
- Add static play screen with `SYNTHETIC` stamps.
- Add `checkbox_reviewer` and `missing_receipt_furnace` catalogs.
- Add canonical policy handles from `docs/spec.md`.
- Add fake tool catalog and tool argument validators.
- Add actor schema validator.
- Add public-safety scanner.
- Add provider wrapper with hosted model config.
- Add red actor prompt builder.
- Add API route happy path.
- Add refusal taxonomy and error mapping.
- Add fake executor.
- Add truth-ledger event model.
- Add rule-based monitor.
- Add burn-card generator.
- Wire UI panels to API result.
- Add refusal/error UI.
- Add unit tests.
- Add screenshot-mode smoke test.
- Run public-safety scans.
- Review final diff before any commit.

## Acceptance Criteria Tied To `docs/spec.md`

V0 is acceptable when these are true:

- Product behavior: a user can select a fake packet, defaulting to `Checkbox Reviewer`, and run a fresh hosted red actor completion.
- Runtime LLM contract: completed live runs use model output generated at run time. No deterministic villain fallback exists.
- Refusal taxonomy: every refusal/failure kind renders as an experiment result, and no fake actions execute for refused or invalid runs.
- LLM output contract: the actor JSON channels match the canonical schema and reject missing or extra uncontrolled behavior.
- Synthetic tool executor: only fixed fake tools execute; rejected calls are visible in the ledger.
- Immutable truth ledger: packet facts, safe-process cue, actor output, fake actions, DB diffs, audit claims, notice, monitor findings, and burn cards are inspectable.
- Monitor: rule-based findings compare actor claims against the truth ledger and produce burn cards for completed runs.
- Policy frame: burn cards map to DoD AI Ethical Principles and related public Responsible AI concepts as educational handles, not official compliance determinations.
- UI reveal sequence: the screen shows calm intake, fake tool/db theater, synthetic lie, and burn cards.
- Safety: no real uploads, PII, payments, claimants, government-system integrations, secrets, private paths, raw transcripts, or operational attack instructions.
- Screenshot quality: the first run is understandable in under one minute, and the main screen works as a public screenshot with visible `SYNTHETIC` stamps.

## Validation Commands

Because no app/package exists today, the first implementation task is to create the chosen app scaffold and then update these commands if the location differs.

Assuming `apps/policy-bonfire/`:

```bash
cd apps/policy-bonfire
npm install
npm run lint
npm test -- --run
npm run build
```

Expected outcome:

- lint exits 0;
- tests exit 0;
- build exits 0;
- no test depends on a real provider key;
- provider calls are mocked unless an explicit live-demo command is used.

Run a local demo:

```bash
cd apps/policy-bonfire
npm run dev
```

Expected outcome:

- the page loads with `Checkbox Reviewer` selected;
- every visible panel includes `SYNTHETIC`;
- a configured live run calls the hosted red actor;
- a missing provider config renders `MODEL_UNAVAILABLE`;
- refused or invalid model output executes no fake tools.

Run public-safety scans:

```bash
rg -n "s[k]-[A-Za-z0-9_-]{12,}|BEGIN [A-Z ]*PR[I]VATE K[E]Y|[A-Z0-9_]*(T[O]KEN|S[E]CRET|K[E]Y)=|[0-9]{3}-[0-9]{2}-[0-9]{4}" apps/policy-bonfire
rg -n "real voucher|real claimant|real payment|production decision|DTS integration" apps/policy-bonfire
rg -n "SYNTHETIC" apps/policy-bonfire
```

Expected outcome:

- first command returns no matches;
- second command returns no unsafe product claims, except tests that assert blocked wording;
- third command returns matches in all UI artifact renderers and core test fixtures.

Run screenshot smoke test if Playwright is added:

```bash
cd apps/policy-bonfire
npm run e2e -- --grep "linkedin screenshot"
```

Expected outcome:

- screenshot mode loads without overlap at desktop and mobile widths;
- main packet, red actor result, fake action trace, truth ledger, and at least one burn card are visible;
- `SYNTHETIC` is visible in the screenshot.

Optional live smoke command, only with local env configured:

```bash
cd apps/policy-bonfire
POLICY_BONFIRE_LIVE=1 npm test -- --run tests/liveHostedActor.test.ts
```

Expected outcome:

- one live call for `checkbox_reviewer` resolves to valid actor JSON or a classified refusal;
- no fake execution happens unless schema and safety validation pass;
- logs show provider/model names only, never key values.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Hosted model emits malformed JSON | Strict schema, `SCHEMA_VIOLATION` UI, no fallback prose. |
| Model omits `SYNTHETIC` | Renderer stamp plus validator finding; block or mark before public display. |
| Model asks for fake tool outside catalog | Reject, ledger `TOOL_OUT_OF_SANDBOX`, no mutation. |
| Actor audit log looks like truth | UI labels audit as actor-authored claim and compares it to truth ledger. |
| Burn cards trust self-reported control burns | Rule-based monitor validates handles and evidence against catalog and ledger. |
| Screenshot could be mistaken for real workflow | Big page-level and per-artifact `SYNTHETIC` stamps. |
| Replay fixture mistaken for live | `REPLAY` tag, separate test mode, never displayed as fresh hosted model behavior. |
| Overbuilding | One screen, one API route, built-in scenarios only. |

## Future Commit Points

Do not commit as part of this planning task. For implementation, use small commits after each verified milestone:

1. `Create Policy Bonfire V0 web shell`
2. `Add synthetic scenarios and policy catalog`
3. `Validate actor schema and synthetic boundary`
4. `Call hosted red actor model`
5. `Replay fake tool calls into synthetic ledger`
6. `Add rule-based Policy Bonfire monitor`
7. `Build playable Policy Bonfire screen`
8. `Surface refusals as experiment results`
9. `Add V0 safety and behavior tests`
10. `Polish public screenshot path`

Before any future commit, review the diff and confirm it does not touch protected receipts, protected demo assets, secrets, raw transcripts, or unrelated files.
