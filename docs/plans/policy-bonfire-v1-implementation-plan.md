# Policy Bonfire V1 Implementation Plan

- Status: docs-only implementation plan
- Product: Policy Bonfire: DTS From Hell
- Short name: Policy Bonfire
- Scope: extend the existing V0 synthetic voucher chatbot with one deterministic policy-aware review panel
- Boundary: public-safe synthetic demo only; no real vouchers, payments, claimants, fraud findings, official workflow, production deployment, or operational instructions

## Goal

Implement V1 from `docs/policy-bonfire-v1-spec.md` by keeping the current V0 chatbot loop and adding one lightweight review/evaluation panel.

The V1 panel must answer a narrow question: does the toy chatbot's synthetic recommendation have visible packet support, traceable field evidence, bounded confidence, and a clear human-review boundary?

The panel is not a model. It is not a compliance engine. It is a deterministic UI projection produced by:

```ts
derivePolicyReview(fixtureId, voucherState) -> PolicyReview
```

The same `fixtureId` and `voucherState` must always produce byte-stable review content. Provider selection, model output, network state, local environment variables, and API availability must not change the panel.

## Product Boundaries

- Use **Policy Bonfire: DTS From Hell** for the app title and **Policy Bonfire** for short labels.
- Treat older/prequel naming in historical docs as background only; do not use it as the current product name.
- "DTS" remains parody shorthand only. Do not imply access to or affiliation with any real travel, payment, identity, audit, or government system.
- "Voucher" means an invented fake packet in this toy app only.
- "Approve", "request more info", and "escalate" are in-fiction synthetic labels only.
- Do not use "denied", "deny", or "rejected" in visible V1 panel recommendations. Legacy V0 internals may still emit `rejected`; V1 maps it to `escalate`.
- DoDD 3000.09 may appear only as an analogy/reference label, never as direct authority over synthetic voucher adjudication.
- Do not touch protected historical evidence: `docs/hackathon-submission-receipt.md`, `docs/demo-receipts.md`, or `assets/demo/`.

## Architecture

V1 keeps the existing app under `apps/synthetic-voucher-chatbot/`.

Current V0 shape:

- React + TypeScript + Vite client app.
- Vitest unit/component/scenario tests.
- Playwright desktop/narrow smoke tests.
- Deterministic local rule engine in `src/domain/rules.ts`.
- Provider selector supports `stub`, `openai`, `anthropic`, `gemini`, and `ollama_compatible`, with non-stub providers currently routed through deterministic unavailable fallback.

V1 additions:

- `src/domain/policyReview.ts`: pure deterministic derivation, static policy reference labels, legacy determination mapping, and the three V1 scenario ids.
- `src/components/PolicyReviewPanel.tsx`: compact panel rendering recommendation, checks, packet refs, and policy notes.
- App layout update so the policy panel sits beside chat on desktop and stacks after chat on mobile.
- Tests proving deterministic review behavior, provider isolation, three-scenario V1 surfacing, and browser layout.

Do not add a runtime LLM adjudicator. Provider calls may continue to affect assistant chat text and field extraction only. They must not decide or modify V1 policy review content.

## Tech Stack

Use the existing stack:

- Vite React TypeScript
- Vitest + React Testing Library + jsdom
- Playwright for browser layout and smoke checks
- Existing provider abstraction and unavailable provider fallback

Do not add a new UI kit, server process, model harness, experiment runner, telemetry, database, upload flow, OCR, document parser, analytics, or public-safety scanner dependency for V1.

## V1 Data Contracts

Add these contracts in `apps/synthetic-voucher-chatbot/src/domain/policyReview.ts` unless the implementation agent chooses to colocate type aliases in `src/domain/types.ts` for consistency. Keep the derivation function itself in `policyReview.ts`.

```ts
export type ReviewRecommendation = 'approve' | 'request_more_info' | 'escalate'

export type ReviewCheckStatus = 'pass' | 'warn' | 'stop' | 'info'

export type PolicyReferenceId =
  | 'dod_ai_ethical_principles'
  | 'responsible_ai_strategy_and_implementation_pathway'
  | 'responsible_ai_toolkit'
  | 'ai_test_and_evaluation_frameworks'
  | 'autonomy_in_weapon_systems_directive_analogy'

export type PacketFieldRef = {
  field:
    | 'travelerPersona'
    | 'tripPurpose'
    | 'dateRange'
    | 'category'
    | 'amountSyntheticCredits'
    | 'fakeAuthorizedAmount'
    | 'fakeReceiptPresent'
    | 'amountMatchesAuthorization'
    | 'explanation'
  label: string
  value: string
}

export type ReviewCheck = {
  id:
    | 'evidence_support'
    | 'traceability'
    | 'confidence_warning'
    | 'human_boundary'
    | 'policy_notes'
  status: ReviewCheckStatus
  title: string
  finding: string
  packetRefs: PacketFieldRef[]
  policyRefs: PolicyReferenceId[]
}

export type PolicyReview = {
  scenarioId: 'SYN_CLEAN_LODGING' | 'SYN_MISSING_RECEIPT' | 'SYN_AMOUNT_MISMATCH'
  recommendation: ReviewRecommendation
  recommendationLabel: string
  summary: string
  checks: ReviewCheck[]
  syntheticOnly: true
}
```

Required exported helpers:

```ts
export const V1_SCENARIO_FIXTURE_IDS = [
  'SYN_CLEAN_LODGING',
  'SYN_MISSING_RECEIPT',
  'SYN_AMOUNT_MISMATCH',
] as const

export function mapDeterminationToReviewRecommendation(
  determination: Determination,
): ReviewRecommendation

export function derivePolicyReview(
  fixtureId: (typeof V1_SCENARIO_FIXTURE_IDS)[number],
  voucherState: SyntheticVoucher,
): PolicyReview
```

Legacy determination mapping:

| V0 determination | V1 recommendation |
| --- | --- |
| `accepted` | `approve` |
| `request_more_info` | `request_more_info` |
| `escalated` | `escalate` |
| `rejected` | `escalate` |

The `rejected` -> `escalate` mapping is mandatory. The amount mismatch panel must explain "Mismatch found. Stop here." It must not call the packet fraud, denial, punishment, payment, entitlement, or official action.

## V1 Scenario Scope

V1 scenario surfacing is exactly three scenarios:

| Fixture | Title | Recommendation | Primary check behavior |
| --- | --- | --- | --- |
| `SYN_CLEAN_LODGING` | Clean packet | `approve` | evidence `pass`, confidence `info`, human boundary `info` |
| `SYN_MISSING_RECEIPT` | Missing receipt | `request_more_info` | evidence `warn`, confidence `warn`, human boundary `info` |
| `SYN_AMOUNT_MISMATCH` | Amount mismatch | `escalate` | evidence `warn`, confidence `stop`, human boundary `stop` |

Existing V0 fixtures such as `SYN_AMBIGUOUS_MISC` and `SYN_TRANSIT_SMALL` may stay in `src/domain/fixtures.ts` for legacy rule coverage, but they must not appear in the V1 scenario picker, V1 panel copy, or V1 scenario tests.

## Policy Reference Copy

Use short educational labels. Do not present them as formal citations, legal authority, compliance scores, or official policy findings.

Suggested copy:

| Reference id | UI label | Boundary copy |
| --- | --- | --- |
| `dod_ai_ethical_principles` | Traceable and reliable reasoning | "The toy output should point back to visible fake packet fields." |
| `responsible_ai_strategy_and_implementation_pathway` | Bounded use and governance | "The demo shows why a narrow workflow should not claim broader authority." |
| `responsible_ai_toolkit` | Human fail-safe | "The panel stops short of fake finality when evidence is missing or mismatched." |
| `ai_test_and_evaluation_frameworks` | Testable behavior | "The checks are deterministic so the lesson can be replayed." |
| `autonomy_in_weapon_systems_directive_analogy` | Human authority analogy | "Analogy only; not authority for this toy packet." |

## UX Direction

Desktop:

- Header: `Policy Bonfire: DTS From Hell`
- Boundary notice visible near the top: `Synthetic demo only. No real DTS, no real payments, no official action.`
- Main content: chat pane on the left, policy review panel on the right.
- Mock DB and mock audit cards can stay in the right column below the panel or in a compact lower rail. Keep the implementation small.

Mobile:

- Header
- Boundary notice
- Scenario picker
- Chat
- Policy Review Panel
- Mock DB
- Mock Audit
- Replay controls reachable without horizontal scrolling

Safe fake-bureaucracy copy examples:

- Clean packet bot flavor: "Approval secured in 0.3 synthetic seconds."
- Missing receipt bot flavor: "Please furnish supporting documentation at your earliest synthetic convenience."
- Amount mismatch panel copy: "Mismatch found. Stop here."
- Boundary flavor: "Queue ticket stamped: synthetic only."

Keep jokes subordinate to the safety boundary. The panel should be calm, compact, and traceable.

## Files To Create

- `apps/synthetic-voucher-chatbot/src/domain/policyReview.ts`
- `apps/synthetic-voucher-chatbot/src/components/PolicyReviewPanel.tsx`
- `apps/synthetic-voucher-chatbot/tests/unit/policyReview.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/providerRegistryV1.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/policyReviewProviderIsolation.test.ts`
- `apps/synthetic-voucher-chatbot/tests/component/PolicyReviewPanel.test.tsx`
- `apps/synthetic-voucher-chatbot/tests/scenario/v1PolicyReviewScenarios.test.ts`
- `apps/synthetic-voucher-chatbot/tests/smoke/providerLiveSmoke.test.ts`
- `apps/synthetic-voucher-chatbot/e2e/policy-review-layout.spec.ts`

## Files To Modify

- `apps/synthetic-voucher-chatbot/package.json`
- `apps/synthetic-voucher-chatbot/vite.config.ts`
- `apps/synthetic-voucher-chatbot/src/app/VoucherChatApp.tsx`
- `apps/synthetic-voucher-chatbot/src/components/DeterminationBanner.tsx` only if needed to prevent legacy `rejected` wording from being visible in the V1 flow
- `apps/synthetic-voucher-chatbot/src/domain/fixtures.ts` only if adding display titles or exporting V1 fixture ids there is cleaner than `policyReview.ts`
- `apps/synthetic-voucher-chatbot/src/domain/types.ts` only if colocating shared types is cleaner
- `apps/synthetic-voucher-chatbot/src/styles.css`
- `apps/synthetic-voucher-chatbot/tests/component/VoucherChatApp.test.tsx`
- `apps/synthetic-voucher-chatbot/tests/scenario/voucherScenarios.test.ts` only if current assertions conflict with the V1 scenario picker; keep legacy fixture rule coverage if possible
- `apps/synthetic-voucher-chatbot/e2e/responsive-layout.spec.ts` only if the existing layout assertions need to account for the new panel

No other files should be needed. Do not modify `docs/hackathon-submission-receipt.md`, `docs/demo-receipts.md`, or anything under `assets/demo/`.

## Task Ordering

### Task 0 - Working Tree And Evidence Guard

Files:

- none

Commands:

```bash
git status --short
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Expected outcome:

- The implementation agent understands pre-existing untracked or modified files before editing.
- The protected-path command prints nothing. If it prints any path, stop and resolve before continuing.

Staging warning:

- The `apps/` tree may currently be untracked. Never run `git add .`, `git add -A`, or `git add apps/` for any commit. Future code commits must stage specific files only (for example, `git add apps/synthetic-voucher-chatbot/src/domain/policyReview.ts`). Bulk staging would risk pulling in `node_modules/`, `dist/`, `coverage/`, `test-results/`, or `playwright-report/`.
- Do not stage anything under `docs/hackathon-submission-receipt.md`, `docs/demo-receipts.md`, or `assets/demo/` for this work.

### Task 1 - Write Failing Policy Review Unit Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/unit/policyReview.test.ts`

Test first:

```bash
cd apps/synthetic-voucher-chatbot
npx vitest run tests/unit/policyReview.test.ts
```

Expected RED:

- Test fails because `src/domain/policyReview.ts` does not exist.

Required assertions:

- `V1_SCENARIO_FIXTURE_IDS` equals exactly `['SYN_CLEAN_LODGING', 'SYN_MISSING_RECEIPT', 'SYN_AMOUNT_MISMATCH']`.
- `SYN_AMBIGUOUS_MISC` and `SYN_TRANSIT_SMALL` are not in V1 scenario ids.
- `mapDeterminationToReviewRecommendation('accepted') === 'approve'`.
- `mapDeterminationToReviewRecommendation('request_more_info') === 'request_more_info'`.
- `mapDeterminationToReviewRecommendation('escalated') === 'escalate'`.
- `mapDeterminationToReviewRecommendation('rejected') === 'escalate'`.
- `derivePolicyReview('SYN_CLEAN_LODGING', voucher)` returns `approve`, five checks, `syntheticOnly: true`, and no hidden packet facts.
- `derivePolicyReview('SYN_MISSING_RECEIPT', voucher)` returns `request_more_info`, evidence `warn`, confidence `warn`, and packet refs including `fakeReceiptPresent=false`.
- `derivePolicyReview('SYN_AMOUNT_MISMATCH', voucher)` returns `escalate`, human boundary `stop`, confidence `stop`, and packet refs including `amountSyntheticCredits`, `fakeAuthorizedAmount`, and `amountMatchesAuthorization=false`.
- Every check has at least one traceable packet ref or policy ref.
- Visible recommendation labels do not contain `deny`, `denied`, or `rejected` in any casing.
- The function returns the same deep-equal object on repeated calls with the same inputs.
- Mutating the selected provider in a fake run object does not change `derivePolicyReview` output.

### Task 2 - Implement Deterministic Policy Review Domain

Files to create:

- `apps/synthetic-voucher-chatbot/src/domain/policyReview.ts`

Implementation notes:

- Use a table-driven mapping keyed by the three V1 fixture ids.
- Read only the `fixtureId` argument and the passed `voucherState`.
- To include `fakeAuthorizedAmount`, read the fixture record for that fixture id from `FIXTURES`; do not create a second hidden data source.
- Normalize missing values as visible strings such as `not provided` or `false`; do not invent evidence.
- Export policy reference labels and descriptions from this file unless colocating in a small constants object is clearer.
- Do not import from `src/providers/**`.
- Do not call `fetch`, `XMLHttpRequest`, `WebSocket`, vendor SDKs, timers, random number APIs, or environment variables.

Verify GREEN:

```bash
cd apps/synthetic-voucher-chatbot
npx vitest run tests/unit/policyReview.test.ts
npm run typecheck
```

Expected outcome:

- Policy review unit tests pass.
- Typecheck passes.

### Task 3 - Write Provider And Model Registry Guard Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/unit/providerRegistryV1.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/policyReviewProviderIsolation.test.ts`

Test first:

```bash
cd apps/synthetic-voucher-chatbot
npx vitest run tests/unit/providerRegistryV1.test.ts tests/unit/policyReviewProviderIsolation.test.ts
```

Expected RED:

- New tests fail until assertions and any missing exports are implemented.

Required deterministic unit assertions:

- The production provider ids remain exactly `stub`, `openai`, `anthropic`, `gemini`, and `ollama_compatible`.
- `stub` is deterministic and does not require environment variables.
- `openai`, `anthropic`, `gemini`, and `ollama_compatible` resolve to deterministic unavailable/fallback behavior unless a later task explicitly implements live adapters.
- Unit tests stub `globalThis.fetch` to throw if called. These tests must fail if any registry option attempts network access.
- No unit test reads `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, or `OLLAMA_CLOUD_API_KEY`.
- `derivePolicyReview` output is identical when provider id is `stub`, `openai`, `anthropic`, `gemini`, and `ollama_compatible`.
- Static import scan proves `src/domain/policyReview.ts` and `src/components/PolicyReviewPanel.tsx` do not import from `src/providers/`.
- Static scan proves policy review files do not contain `complete(`, `fetch(`, `XMLHttpRequest`, `WebSocket`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, or `OLLAMA_CLOUD_API_KEY`.

Suggested test pattern:

```ts
vi.stubGlobal(
  'fetch',
  vi.fn(() => {
    throw new Error('Network disabled in deterministic unit tests')
  }),
)
```

### Task 4 - Add Optional Live Provider Smoke Test Harness

Files to create:

- `apps/synthetic-voucher-chatbot/tests/smoke/providerLiveSmoke.test.ts`

Files to modify:

- `apps/synthetic-voucher-chatbot/package.json`
- `apps/synthetic-voucher-chatbot/vite.config.ts` (mandatory: add `tests/smoke/**` to the `test.exclude` array so default `vitest run` never discovers live smoke files)

Implementation rule:

- Default unit, component, scenario, and e2e tests must never call paid or live APIs.
- Live smoke tests are optional, skipped by default, and run only when the env flag `LIVE_PROVIDER_SMOKE` equals `1`.
- If no live adapters exist yet, each smoke case should report a skipped test with a clear reason rather than failing the V1 panel work.

Provider options to cover:

- `stub`
- `openai`
- `anthropic`
- `gemini`
- `ollama_compatible` for local Ollama-compatible endpoints
- Ollama Cloud through the same Ollama-compatible path when an Ollama Cloud credential variable (such as `OLLAMA_CLOUD_API_KEY`) is present

Required env variable names (read from the local user shell only; never write values into the repo, never copy these examples into a committed `.env`):

- `LIVE_PROVIDER_SMOKE` — set to `1` to opt into live smoke
- `OPENAI_API_KEY` — required for the OpenAI live case
- `ANTHROPIC_API_KEY` — required for the Anthropic live case
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY` if the adapter expects that name) — required for the Gemini live case
- `OLLAMA_BASE_URL` — local or Ollama-Cloud-compatible endpoint
- `OLLAMA_MODEL` — model name string
- `OLLAMA_API_KEY` — only if a local endpoint requires it
- `OLLAMA_CLOUD_API_KEY` — only if Ollama Cloud is being exercised

Each smoke case must skip (not fail) when its required env names are absent, and the skip reason must not echo the env values themselves.

Package script:

```json
{
  "scripts": {
    "test:smoke:providers": "vitest run tests/smoke/providerLiveSmoke.test.ts"
  }
}
```

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm test
npm run test:smoke:providers
LIVE_PROVIDER_SMOKE=1 npm run test:smoke:providers
```

Expected outcomes:

- `npm test` does not execute live provider calls.
- `npm run test:smoke:providers` skips live cases unless `LIVE_PROVIDER_SMOKE=1`.
- With `LIVE_PROVIDER_SMOKE=1`, each provider case still skips unless its local env vars and adapter exist.
- Smoke logs may show provider id, coarse status, and latency. They must never print secrets, raw prompts, local paths, raw provider traces, account ids, or private endpoints.

### Task 5 - Write Failing Panel Component Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/component/PolicyReviewPanel.test.tsx`

Files to modify:

- `apps/synthetic-voucher-chatbot/tests/component/VoucherChatApp.test.tsx`

Test first:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:component
```

Expected RED:

- Tests fail because `PolicyReviewPanel` is not implemented or not wired into the app.

Required assertions:

- Panel renders with `data-testid="policy-review-panel"` and an accessible region label such as `Policy review panel`.
- Clean packet renders recommendation label `Approve` and includes "narrow synthetic recommendation" copy.
- Missing receipt renders `Request more info` and shows `fakeReceiptPresent=false`.
- Amount mismatch renders `Escalate`, includes "Mismatch found. Stop here.", and does not contain `fraud`, `denied`, `deny`, `rejected`, `payment`, `entitlement`, or `official action`.
- The five checks render in this order: evidence support, traceability, confidence warning, human boundary, policy notes.
- Packet references render field labels and values already visible in the synthetic packet.
- Policy reference copy renders as educational notes, not legal citations or compliance scores.
- Scenario selector in `VoucherChatApp` exposes exactly the three V1 scenario ids.
- Changing the provider selector does not change the policy panel text for the same fixture and voucher state.
- Safety boundary notice remains visible near the top.

### Task 6 - Implement Policy Review Panel And App Wiring

Files to create:

- `apps/synthetic-voucher-chatbot/src/components/PolicyReviewPanel.tsx`

Files to modify:

- `apps/synthetic-voucher-chatbot/src/app/VoucherChatApp.tsx`
- `apps/synthetic-voucher-chatbot/src/styles.css`
- `apps/synthetic-voucher-chatbot/src/domain/fixtures.ts` only if adding display titles is needed
- `apps/synthetic-voucher-chatbot/src/domain/types.ts` only if shared type exports are needed

Implementation notes:

- Compute the review in `VoucherChatApp` with `derivePolicyReview(fixtureId, run.voucher)`.
- Do not pass provider id to `derivePolicyReview`.
- Render `PolicyReviewPanel` in the right column above mock DB/audit cards on desktop.
- On mobile, stack `ChatPane`, `PolicyReviewPanel`, `MockDbCard`, then `MockAuditCard`.
- Header should use `Policy Bonfire: DTS From Hell`.
- Keep `SafetyBoundaryNotice` unchanged or stronger; do not bury it in a footer.
- Use compact statuses, small headings, and stable dimensions. Avoid giant hero cards.
- Keep visible panel recommendation labels to `Approve`, `Request more info`, and `Escalate`.

Verify GREEN:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:component
npm run test:unit
npm run typecheck
```

Expected outcome:

- Component and unit tests pass.
- Provider changes do not affect the panel.
- V1 scenario selector surfaces exactly three scenarios.

### Task 7 - Write V1 Scenario Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/scenario/v1PolicyReviewScenarios.test.ts`

Test first:

```bash
cd apps/synthetic-voucher-chatbot
npx vitest run tests/scenario/v1PolicyReviewScenarios.test.ts
```

Expected RED:

- Tests fail until scenario helpers and panel wiring expose the needed state.

Required assertions:

- `SYN_CLEAN_LODGING` plays through to V0 `accepted` and V1 `approve`.
- `SYN_MISSING_RECEIPT` plays through to V0 `request_more_info` and V1 `request_more_info`.
- `SYN_AMOUNT_MISMATCH` plays through to V0 `rejected` and V1 `escalate`.
- The amount mismatch panel never surfaces the string `rejected` even though the legacy V0 determination is `rejected`.
- The policy review remains deterministic before and after confirmation for the same voucher fields.
- No provider or LLM import path is used by the deterministic review panel.
- All rendered scenario content is synthetic-only and contains no real names, real vouchers, real payments, real claimants, private paths, Slack IDs, raw notes, secrets, or official workflow claims.

Verify GREEN:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:scenario
```

Expected outcome:

- Existing V0 scenario tests still pass.
- New V1 scenario tests cover only the three V1 fixtures.

### Task 8 - Add Browser Layout And Smoke Tests

Files to create:

- `apps/synthetic-voucher-chatbot/e2e/policy-review-layout.spec.ts`

Files to modify:

- `apps/synthetic-voucher-chatbot/e2e/responsive-layout.spec.ts` only if existing assertions need to account for the new panel

Test first:

```bash
cd apps/synthetic-voucher-chatbot
npx playwright test e2e/policy-review-layout.spec.ts --project=desktop
```

Expected RED:

- The new spec fails because no policy review panel is rendered yet (or its `data-testid` is missing). RED is acceptable here even though prior tasks already shipped the panel component — write the e2e spec assertions first, then adjust selectors/markup until they pass.

If browsers are not installed in the local environment, run `npx playwright install --with-deps chromium` once before the first Playwright invocation. Do not commit any files this command writes outside the user cache.

Required Playwright checks:

- Desktop project (`1280x800`): `policy-review-panel` is visible, sits to the right of `chat-pane`, and has a usable width.
- Desktop project: panel appears above or before mock DB/audit cards in the right column.
- Narrow project (`414x800`): `policy-review-panel` stacks below `chat-pane`, mock DB stacks below the panel, and mock audit stacks below mock DB.
- Narrow project: no horizontal scrolling on `body` or `html`.
- Scenario selector shows exactly the three V1 scenarios.
- Selecting missing receipt updates the panel to `Request more info`.
- Selecting amount mismatch updates the panel to `Escalate` and shows "Mismatch found. Stop here."
- Provider selector changes do not move, hide, or rewrite panel content except for unrelated chat-provider UI state.
- Chat input, send, confirm, replay, scenario selector, provider selector, and panel region remain reachable without layout overlap.

Commands for coding agent:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:e2e
npx playwright test e2e/policy-review-layout.spec.ts --project=desktop
npx playwright test e2e/policy-review-layout.spec.ts --project=narrow
```

If automated browser launch is flaky:

```bash
cd apps/synthetic-voucher-chatbot
npm run dev -- --host 127.0.0.1 --port 4173
```

Manual smoke path:

1. Open `http://127.0.0.1:4173`.
2. Confirm header says `Policy Bonfire: DTS From Hell`.
3. Confirm the synthetic boundary notice is visible without scrolling.
4. On desktop width, confirm chat is left and policy panel is right.
5. Resize to mobile width or use browser dev tools at `414x800`; confirm chat, panel, mock DB, and mock audit stack safely.
6. Select `SYN_CLEAN_LODGING`, `SYN_MISSING_RECEIPT`, and `SYN_AMOUNT_MISMATCH`; confirm the panel shows `Approve`, `Request more info`, and `Escalate` respectively.
7. Change provider selector across `stub`, `openai`, `anthropic`, `gemini`, and `ollama_compatible`; confirm the panel does not change for the same scenario.

Screenshot and trace rule:

- Capture screenshots or traces only if needed to debug or document a failure.
- Keep them under ignored Playwright output directories.
- Before sharing or committing any artifact, inspect it for secrets, local paths, real identities, private URLs, raw provider traces, and non-synthetic data.

### Task 9 - Final Verification

Run the full local verification from a clean app directory:

```bash
cd apps/synthetic-voucher-chatbot
npm run typecheck
npm run test:unit
npm run test:component
npm run test:scenario
npm run test:e2e
npm run build
npm run test:smoke:providers
cd -
git diff --check
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Expected outcome:

- Typecheck passes.
- Unit, component, scenario, and Playwright tests pass.
- Build passes.
- Optional provider smoke tests skip by default unless explicitly enabled.
- Protected-path diff command prints nothing.

### Task 10 - Public-Safety Scan

Run focused scans before handoff. The patterns below use single-character bracket classes (`s[k]-`, `[O]PENAI_API_KEY=`, etc.) so the scan command itself does not appear as a literal credential or env-export string anywhere — including inside this plan. The bracket form matches the same target text without producing a self-flag.

```bash
rg -n "s[k]-|A[K]IA|A[I]za|BEGIN (RSA|OPENSSH|PRIVATE) KEY|[O]PENAI_API_KEY=|[A]NTHROPIC_API_KEY=|[G]EMINI_API_KEY=|[G]OOGLE_API_KEY=|[O]LLAMA_CLOUD_API_KEY=|[O]LLAMA_API_KEY=" apps/synthetic-voucher-chatbot docs/plans/policy-bonfire-v1-implementation-plan.md
rg -n "Slack|raw transcript|real claimant|real voucher|real payment|official workflow|production deployment|approved for payment|payability|entitlement|fraud finding|fraud determination" apps/synthetic-voucher-chatbot/src apps/synthetic-voucher-chatbot/tests apps/synthetic-voucher-chatbot/e2e
rg -n "A[O] Radar" apps/synthetic-voucher-chatbot/src apps/synthetic-voucher-chatbot/tests apps/synthetic-voucher-chatbot/e2e
rg -n "deny|denied|rejected" apps/synthetic-voucher-chatbot/src/components apps/synthetic-voucher-chatbot/tests/component apps/synthetic-voucher-chatbot/e2e
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Expected outcome:

- Secret scan returns no real secrets or credential-shaped strings. The scan must not flag the scan command itself; if it does, the bracket-escapes were lost in transcription — restore them before continuing.
- Public-safety scan returns no unsafe product claims. If app tests intentionally mention legacy `rejected` (for example, when asserting V0 internal mapping), scope the assertion to test files and verify the UI does not surface it.
- Current product UI/tests do not use historical/prequel naming.
- Protected-path diff command prints nothing.

## Acceptance Criteria

V1 is complete when:

- The app title and V1 UI use Policy Bonfire / Policy Bonfire: DTS From Hell.
- The visible scenario picker exposes exactly three scenarios: clean packet, missing receipt, and amount mismatch.
- `derivePolicyReview(fixtureId, voucherState) -> PolicyReview` is deterministic, pure, and tested.
- The panel renders five checks: evidence support, traceability, confidence warning, human boundary, and policy notes.
- The legacy V0 amount mismatch result `rejected` maps to V1 `escalate`.
- The V1 panel never uses visible `deny`, `denied`, or `rejected` recommendation language.
- The panel has no provider, model, network, vendor SDK, or environment-variable dependency.
- Provider registry tests cover `stub`, `openai`, `anthropic`, `gemini`, and `ollama_compatible`.
- Optional live smoke tests cover OpenAI, Anthropic, Gemini, and Ollama-compatible/Ollama Cloud only when explicitly enabled by local env vars.
- Default tests cannot accidentally call paid/live APIs.
- Playwright proves the panel sits beside chat on desktop and stacks safely on mobile.
- The safety boundary remains visible and plain.
- Protected receipt/demo evidence paths have no diff.
- Final public-safety scans are clean or any intentional legacy-string hits are explained and limited to tests/internal mapping.

## Optional Commit Checkpoints

Do not commit unless the maintainer asks. If commits are requested later, use small checkpoints:

1. `test(policy-review): add V1 deterministic review coverage`
2. `feat(policy-review): add deterministic Policy Bonfire panel`
3. `test(browser): cover V1 policy panel layout`
4. `test(providers): add V1 provider isolation guards`

Staging rule for every commit (no exceptions):

- Stage only the specific files that belong to that checkpoint, by full relative path. For example, the test-coverage checkpoint stages only the new `tests/unit/policyReview.test.ts` and any sibling test files for that step: `git add apps/synthetic-voucher-chatbot/tests/unit/policyReview.test.ts`.
- Never run `git add .`, `git add -A`, `git add apps`, or `git add apps/synthetic-voucher-chatbot`. The app tree may currently be untracked, so directory-level staging would sweep in `node_modules/`, `dist/`, `coverage/`, `test-results/`, `playwright-report/`, or other build artifacts.
- Never stage `docs/hackathon-submission-receipt.md`, `docs/demo-receipts.md`, or anything under `assets/demo/`.
- If `git status --short` shows a file you do not recognize, investigate before staging it.

For the docs-only commit that lands this plan itself, stage exactly one path:

```bash
git add docs/plans/policy-bonfire-v1-implementation-plan.md
```

Before any commit, run:

```bash
git status --short
git diff --check
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

## Implementation-Agent Instructions

- Do not edit, delete, rename, regenerate, or clean up `docs/hackathon-submission-receipt.md`, `docs/demo-receipts.md`, or `assets/demo/`.
- Preserve synthetic-only boundaries in fixtures, prompts, UI copy, tests, screenshots, traces, and reports.
- Do not add real identities, real vouchers, real payments, real claimants, private paths, Slack IDs, raw notes, raw transcripts, secrets, account IDs, or provider traces.
- Do not imply production deployment or operational use for any real workflow.
- Keep V1 small: V0 chatbot plus one deterministic policy-aware review panel.
- Run browser tests before final handoff. If Playwright launch fails for environmental reasons, run the manual browser smoke path and report the exact blocker.
- Capture screenshots or traces only if sanitized and only when needed.
- Do not commit unless explicitly asked.
