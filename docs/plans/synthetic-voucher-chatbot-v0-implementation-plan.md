# Synthetic DTS-Style Voucher Chatbot V0 Implementation Plan

- Status: implementation plan
- Scope: V0 regular chatbot app only
- Audience: coding agents implementing the first playable app
- Boundary: public-safe, synthetic-only, no official workflow, no real systems

## Current Repo Baseline

Repo files reviewed before writing this plan:

- `AGENTS.md`
- `README.md`
- `docs/README.md`
- `docs/synthetic-voucher-chatbot-spec.md`
- existing test file: `tests/test_policy_bonfire_runner.py`
- package/test config search: no `package.json`, Vite config, Vitest config, Playwright config, pyproject, pytest config, or requirements file exists at repo root today

Protected historical evidence must not be edited during implementation unless the maintainer explicitly asks:

- `docs/hackathon-submission-receipt.md`
- `docs/demo-receipts.md`
- `assets/demo/`

## V0 Product Shape

V0 is a regular chatbot app first. The main screen is a playable synthetic voucher chat:

- Desktop: larger chat pane on the left, narrow right status column on the right.
- Right column order: `MockDbCard` above `MockAuditCard`.
- Narrow screens: chat remains first, then mock DB card, then mock audit/log card. No horizontal scrolling.
- The app asks for simple synthetic voucher fields, updates fake local state, shows fake local DB/audit events, then renders one deterministic terminal result.

The interface can be lightly playful and bureaucratic, but V0 default copy and fixtures must not use cursed, demonic, occult, ritual, policy-burning, or governance-failure language.

Hard V0 exclusions:

- No image upload, receipt upload, OCR, document parsing, or attachment storage.
- No real DTS, DoD, payment, identity, accounting, HR, travel, audit, or government-system integration.
- No real people, real vendors, real addresses, real receipts, real card data, real payment amounts, or secrets.
- No real approval, denial, entitlement, payability, fraud, compliance, legal, or official audit determination.
- No external telemetry, analytics, remote error reporting, or real database.
- No public/private data leakage. Provider errors and audit notes must never include API keys, raw prompts, local paths, or raw provider traces.

The phrasing in this plan is deliberately scoped: any reference to "DTS", "voucher", "audit", or "determination" is a synthetic toy-app construct only. The plan does not authorize, describe, or imply any real government, payment, identity, travel, HR, accounting, or official audit workflow. UI copy, fixture text, prompt strings, and tests must preserve that frame.

## Stack Decision

Use a lightweight Vite React TypeScript app under `apps/synthetic-voucher-chatbot/`. The directory `apps/` exists but is empty today.

V0 stack (must ship):

- Vite + React + TypeScript for the client app.
- Vitest + React Testing Library + jsdom for unit, component, and scenario tests.
- `zod` for provider-output schema validation.
- A small Playwright suite (one desktop layout test, one narrow layout test, one chat-flow smoke test) for layout assertions only. All other scenarios run under Vitest with React Testing Library so the test pyramid stays Vitest-first.

V0 dependency posture:

- No `lucide-react`, no `clsx`, no UI kit. Ship plain semantic HTML and CSS first. Justify and add any UI dep later when a real need appears.
- No remote network calls in any test. Every test, including Playwright, runs offline against the local dev server.

Deferred to a later iteration (NOT V0; see `## Deferred To Later Iterations` below):

- Live OpenAI, Anthropic, Gemini, or Ollama-compatible adapter implementations.
- Any Vite/Express/Node dev middleware that holds server-side provider API keys.
- A standalone public-safety scanner script.

Why this stack fits this repo:

- The repo has no JS/TS app/package config yet, so an isolated `apps/synthetic-voucher-chatbot/` directory avoids disturbing existing docs, experiments, and protected receipt files.
- Vite keeps the default path client-local and fixture-first.
- Vitest covers determination rules, run reducer, components, and provider fallback paths without a browser. A small Playwright suite covers only what jsdom cannot: real layout boxes and viewport sizing.

Provider support posture for V0:

- `stub` is the only provider that ships in V0. It is registered as the default and must be complete first.
- The `ProviderId` type and `ChatProvider` interface include `openai`, `anthropic`, `gemini`, and `ollama_compatible`, but their registry entries return a deterministic `unavailable` `ProviderOutput` that triggers the standard stub fallback path. No real network is contacted.
- A test-only `flakeyTestProvider` (registered only inside Vitest, not exposed in the production bundle or selector) simulates timeout, schema-error, and boundary-violation outputs so the fallback and safety-repair paths are testable.
- Providers may help produce assistant wording and extracted field suggestions when added later.
- Determination remains local deterministic rule logic only. Provider output cannot decide, override, or directly set `accepted`, `rejected`, `request_more_info`, or `escalated`. This is enforced by the run reducer and verified by tests.

## Target File Layout

Create this layout during implementation. Files marked `(scaffold)` come from `npm create vite@latest` and are kept mostly untouched.

```text
apps/
  synthetic-voucher-chatbot/
    package.json
    package-lock.json
    index.html                                   (scaffold)
    vite.config.ts
    tsconfig.json                                (scaffold; edit `include`/`exclude`)
    tsconfig.app.json                            (scaffold)
    tsconfig.node.json                           (scaffold)
    eslint.config.js                             (scaffold; do not customize in V0)
    playwright.config.ts
    src/
      main.tsx                                   (scaffold; rewire to App.tsx)
      App.tsx
      styles.css
      app/
        VoucherChatApp.tsx
        createInitialRun.ts
        runReducer.ts
      components/
        ChatPane.tsx
        DeterminationBanner.tsx
        MockAuditCard.tsx
        MockDbCard.tsx
        ProviderSelector.tsx
        SafetyBoundaryNotice.tsx
      domain/
        constants.ts
        fieldCollector.ts
        fixtures.ts
        mockEvents.ts
        rules.ts
        safetyBoundary.ts
        types.ts
      providers/
        providerRegistry.ts
        stubProvider.ts
        unavailableProvider.ts
        types.ts
      test/
        setup.ts
        flakeyTestProvider.ts
        transcriptHelpers.ts
    tests/
      component/
        ChatPane.test.tsx
        MockCards.test.tsx
        VoucherChatApp.test.tsx
      scenario/
        voucherScenarios.test.ts
        providerFailureScenarios.test.ts
      unit/
        fieldCollector.test.ts
        fixtures.test.ts
        mockEvents.test.ts
        rules.test.ts
        runReducer.test.ts
        safetyBoundary.test.ts
        stubProvider.test.ts
    e2e/
      responsive-layout.spec.ts
      voucher-chat-smoke.spec.ts
```

Do not create or modify production app code outside `apps/synthetic-voucher-chatbot/` unless a later task explicitly justifies it. Documentation updates may touch `docs/README.md`. Protected files (`docs/hackathon-submission-receipt.md`, `docs/demo-receipts.md`, `assets/demo/`) must show no diff at any point during implementation.

V0 explicitly does NOT create:

- `server/`, `server/adapters/`, `server/providerProxy.ts`, `server/providerSchemas.ts`, `server/providerTimeout.ts`, `src/providers/browserProviderClient.ts`, or `scripts/publicSafetyScan.mjs`. Those are deferred (see `## Deferred To Later Iterations`).

## Package Scripts To Add

Inside `apps/synthetic-voucher-chatbot/package.json`, define these scripts:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "typecheck": "tsc -b --pretty false",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:unit": "vitest run tests/unit",
    "test:component": "vitest run tests/component",
    "test:scenario": "vitest run tests/scenario",
    "test:e2e": "playwright test"
  }
}
```

Notes:

- `test` runs in non-watch mode so CI and Task 12 verification do not hang.
- `test:watch` is the developer convenience.
- No `scan:public-safety` script in V0; deferred (see `## Deferred To Later Iterations`).
- The exact generated dependency versions can be whatever `npm install` writes to `package-lock.json` at implementation time. Commit the lockfile once app code is implemented.

## Core Data Contracts

Use the spec contracts as the source of truth and keep them in `src/domain/types.ts`.

Add these audit event names beyond the spec's minimal examples so provider failure and safety behavior can be tested explicitly:

```ts
type MockAuditEventName =
  | "chat.field_requested"
  | "chat.field_captured"
  | "voucher.summary_confirmed"
  | "voucher.determination_rendered"
  | "provider.fallback_to_stub"
  | "provider.output_schema_rejected"
  | "safety.synthetic_boundary_repaired";
```

Audit notes must be short public-safe summaries. They may include provider ID and coarse failure kind such as `timeout`, `network_error`, `schema_error`, or `safety_boundary`, but not raw errors, raw prompts, local paths, API keys, or provider trace text.

### ID Counter Semantics

The spec line "The counter is local to the current run and resets on replay" is implementation-ambiguous. V0 resolves it as follows:

- `DBE-####` and `AUD-####` event-ID counters are local to the current run and reset to 1 on replay. The first DB event of any run is `DBE-0001`; the first audit event is `AUD-0001`.
- `runId` (`SYN-RUN-####`) and `voucherId` (`SYN-VCH-####`) are **not** event-ID counters. They are run identifiers. On replay, a new `runId` and `voucherId` are minted that must not equal any value used earlier in the same browser session. V0 implements this by using a monotonically increasing module-level counter for `runId`/`voucherId` that lives for the lifetime of the page (it does not need to persist across full reloads).
- Tests assert: after replay, `run.runId !== priorRun.runId`, `run.voucherId !== priorRun.voucherId`, the next DB event id equals `DBE-0001`, and the next audit event id equals `AUD-0001`.
- A full page reload may legitimately restart the `runId`/`voucherId` counter at `0001`; tests do not assert otherwise.

### Field Collector Contract

`src/domain/fieldCollector.ts` is deterministic and not powered by the model:

- Input: the current `SyntheticVoucher`, the current required-field prompt key, and a single user chat string.
- Output: either a `Partial<SyntheticVoucher>` patch (when parsing succeeds and validation passes) or a `{ rejectionReason: string }` with deterministic re-prompt copy.
- Allowed parse rules per field:
  - `travelerPersona`: trim and accept any non-empty string up to 64 chars from the fixture's allowed persona set.
  - `tripPurpose`: trim and accept any non-empty string up to 120 chars.
  - `dateRange`: accept the literal `YYYY-MM-DD..YYYY-MM-DD` shape only; otherwise re-prompt.
  - `category`: must equal `lodging`, `meal`, `transit`, or `misc` after lowercasing; otherwise re-prompt with the four options.
  - `amountSyntheticCredits`: parse a non-negative integer up to 100000; otherwise re-prompt.
  - `fakeReceiptPresent`: accept `yes`/`no`/`y`/`n`/`true`/`false` (case-insensitive); otherwise re-prompt.
  - `amountMatchesAuthorization`: same boolean parse as `fakeReceiptPresent`.
  - `explanation`: optional, trimmed, capped at 500 chars; absent value is allowed.
- Provider-suggested `extractedFields` are filtered through the same per-field validators before merging. The model is never the source of truth for state.

### Gap Derivation For Amount Mismatch

The spec describes "the implied gap meets or exceeds `FAKE_REJECTION_DELTA`" but `SyntheticVoucher` only carries `amountMatchesAuthorization` as a boolean and `amountSyntheticCredits` as a number. V0 derives the gap as follows:

- Each fixture record carries an explicit `fakeAuthorizedAmount` field for synthetic comparison purposes only. It is fixture-scoped and never displayed as a real authorization.
- For runs that originate from a fixture, the gap is `Math.max(0, amountSyntheticCredits - fakeAuthorizedAmount)`.
- For freeform runs without a fixture-supplied amount, `amountMatchesAuthorization === false` is treated as gap `>= FAKE_REJECTION_DELTA` only when the fixture or rule input explicitly says so; otherwise the rule does not match and falls through.
- Tests must cover both paths: fixture with explicit gap and freeform with explicit gap claim.

## Deterministic Fixtures

Create fixture records in `src/domain/fixtures.ts` for:

- `SYN_CLEAN_LODGING`
- `SYN_MISSING_RECEIPT`
- `SYN_AMOUNT_MISMATCH`
- `SYN_AMBIGUOUS_MISC`
- `SYN_TRANSIT_SMALL`

Each fixture must include:

- synthetic traveler persona, such as `Synthetic Traveler A`
- fake voucher ID seed, such as `SYN-VCH-0001`
- fake date range
- category
- amount in synthetic credits
- fake authorization amount or computed mismatch gap
- receipt-present boolean
- amount-matches-authorization boolean
- optional explanation
- expected determination and rule IDs
- fixed transcript inputs for scenario tests

No fixture may include real names, real locations tied to an actual claim, real vendors, real money language, real units, or real system names.

## Decision Rules

Implement the rule engine in `src/domain/rules.ts`. Rules are evaluated in this exact order:

1. Missing required field -> `request_more_info`, `ruleIds: ["MISSING_REQUIRED"]`.
2. Synthetic safety boundary violated during the run -> `escalated`, `ruleIds: ["SAFETY_BOUNDARY"]`.
3. Amount mismatch gap `>= FAKE_REJECTION_DELTA` -> `rejected`, `ruleIds: ["AMOUNT_MISMATCH"]`.
4. Lodging with no fake receipt -> `request_more_info`, `ruleIds: ["LODGING_NEEDS_RECEIPT"]`.
5. Misc category, explanation shorter than 8 words, and amount within 20 percent of `FAKE_REVIEW_THRESHOLD` -> `escalated`, `ruleIds: ["AMBIGUOUS_NEAR_THRESHOLD"]`.
6. Otherwise -> `accepted`, `ruleIds: ["DEFAULT_ACCEPT"]`.

Constants live in `src/domain/constants.ts`:

```ts
export const FAKE_REJECTION_DELTA = 100;
export const FAKE_REVIEW_THRESHOLD = 500;
```

Determination reason strings must be fixed, short, synthetic, and non-official.

## Provider Architecture

Client UI imports only `src/providers/types.ts`, `providerRegistry.ts`, `stubProvider.ts`, and `unavailableProvider.ts`.

V0 provider path:

1. UI calls `complete(input)` on the selected provider.
2. The `stub` provider returns deterministic output immediately.
3. The `openai`, `anthropic`, `gemini`, and `ollama_compatible` registry entries are wired to `unavailableProvider`, which returns `{ assistantMessage: <deterministic fallback>, safetyBoundaryOk: true, providerStatus: "unavailable" }` and triggers the standard stub fallback path. No live network call is made in V0.
4. The run records a public-safe audit event (`provider.fallback_to_stub`) when fallback occurs.
5. The same fallback path is exercised in tests by `flakeyTestProvider`, which simulates timeout, schema-rejection, and safety-violating outputs from a registered test-only provider id (e.g., `test_flakey`) that is registered only in the Vitest setup.

When live adapters are added later (see `## Deferred To Later Iterations`), they live behind a separate, server-side process. The client must never be able to read provider API keys at build time or runtime. To enforce that in V0:

- Adapter environment variable names that may exist later are: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`. They must not appear under any `VITE_` prefix and must not appear in any `.env` file committed to this repo.
- `vite.config.ts` must explicitly disable any `define`/`envPrefix` that would expose those variables to the client.
- `tsconfig.app.json` `include`/`exclude` must keep `src/` only; no `server/` directory exists in V0, but the boundary is documented now so it stays correct when adapters are added.

Provider-output safety rule:

- Local code sets `safetyBoundaryOk`; never trust the provider's own safety claim. The `ProviderOutput.safetyBoundaryOk` returned by the provider implementation is overwritten by the run reducer using the local `safetyBoundary.ts` classifier before display.
- If assistant text references real DTS, real DoD, real payments, real official authority, real people, or real systems, replace the assistant text with deterministic fallback copy before display.
- Record `safety.synthetic_boundary_repaired`.
- Mark the run so local rules can later produce `SAFETY_BOUNDARY` if submission reaches determination.

Determination authority rule (enforced by code and tests):

- The run reducer is the only writer of `VoucherDetermination`.
- The run reducer obtains `VoucherDetermination` exclusively from `rules.ts`.
- Any `extractedFields` from a provider are passed through `fieldCollector` validation before merging into the voucher.
- `ProviderOutput` does not carry a determination field; it is a TypeScript-level prohibition, not just a convention.

## Sequential TDD Tasks

### Task 0 - Working Tree And Safety Prep

Files:

- no app files yet

Commands:

```bash
git status --short
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Verification:

- Working tree state is understood before app work starts.
- The protected-path command must print exactly nothing. If it prints any path, stop and re-read AGENTS.md before continuing.
- This same protected-path check is the standing guard. Run it after every subsequent task and before any commit.

### Task 1 - Scaffold The Isolated App

Files to create:

- `apps/synthetic-voucher-chatbot/` (standard Vite React TypeScript scaffold files)
- `apps/synthetic-voucher-chatbot/package-lock.json`

Commands (must run non-interactively; the `-y` flag and explicit args avoid the Vite prompt):

```bash
npm create -y vite@latest apps/synthetic-voucher-chatbot -- --template react-ts
cd apps/synthetic-voucher-chatbot
npm install
npm install zod
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @playwright/test
npx --yes playwright install --with-deps chromium
```

Notes:

- Only `zod` is added beyond the scaffold defaults. No `lucide-react`, no `clsx`, no UI kit. Add only with explicit justification later.
- `playwright install --with-deps chromium` downloads roughly 150 MB and may require sudo on some systems. If the implementation environment cannot install Playwright, defer the Playwright suite (Task 9 e2e files only) and note the deferral in the verification report. Vitest scenario coverage still runs.
- Do not run `npm install` outside `apps/synthetic-voucher-chatbot/`. There is no top-level workspace.

Verification:

```bash
cd apps/synthetic-voucher-chatbot
npm run build
cd -
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Expected result:

- The generated app builds before customization.
- The protected-path command prints nothing.
- Inspect the scaffold-generated `package.json` and remove or replace any auto-populated `author`, `name` (if it captured a system username), or repository URL fields with public-safe placeholder values. Set `"private": true` and `"name": "synthetic-voucher-chatbot"`. Do not write a real maintainer email, real personal name, or any private identifier.
- If the scaffold produced an `apps/synthetic-voucher-chatbot/README.md`, confirm it does not reference a system username, machine hostname, or local path. Replace with a one-paragraph synthetic-only blurb if needed.
- Confirm the scaffold did not commit a `.env` or `.env.local` file: `git status --short -- apps/synthetic-voucher-chatbot/.env*` must print nothing.

### Task 2 - Configure Test Harness Before Feature Code

Files to create or modify:

- `apps/synthetic-voucher-chatbot/vite.config.ts` — add `/// <reference types="vitest/config" />` at the top, set `test.environment = "jsdom"`, `test.setupFiles = ["src/test/setup.ts"]`, set `envPrefix: ["VITE_"]` (the default; declared explicitly so a coding agent does not widen it), and add **no** `define` entries that read `process.env` or `import.meta.env` for provider keys. `vite.config.ts` must not import any module that reads provider API keys.
- `apps/synthetic-voucher-chatbot/playwright.config.ts` — two projects, `desktop` (`viewport: { width: 1280, height: 800 }`) and `narrow` (`viewport: { width: 414, height: 800 }`), both using the chromium device profile. Configure the Vite dev server via `webServer` (e.g., `command: "npm run dev"`, a fixed port via `--port`, `reuseExistingServer: !process.env.CI`, `timeout: 120_000`). Set `use.baseURL` to that fixed local URL. Do not configure any remote base URL.
- `apps/synthetic-voucher-chatbot/src/test/setup.ts` — imports `@testing-library/jest-dom`, registers `afterEach(() => cleanup())` for React Testing Library.
- `apps/synthetic-voucher-chatbot/tsconfig.app.json` — `"include": ["src"]`, `"exclude": ["src/test", "src/**/*.test.ts", "src/**/*.test.tsx", "tests", "e2e"]`. This ensures the production build never type-checks or includes test-only modules such as `flakeyTestProvider.ts`.
- `apps/synthetic-voucher-chatbot/.gitignore` — verify it ignores `node_modules/`, `dist/`, `.env`, `.env.*`, `playwright-report/`, `test-results/`, and `playwright/.cache/`. The Vite scaffold ignores most of these by default; add any missing entries. Do not commit any `.env` or `.env.local` file in this directory. A `.env.example` is also out of V0 scope; it is not needed because no live provider runs in V0.
- `apps/synthetic-voucher-chatbot/package.json` (the scripts in `## Package Scripts To Add`)

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run typecheck
npm test
cd -
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Verification:

- Vitest runs with jsdom.
- React Testing Library matchers are loaded.
- Playwright config starts the Vite dev server for e2e tests.
- Vitest finishes (no watch mode); zero tests is acceptable at this point.
- No feature behavior is implemented yet beyond scaffold health.
- Protected-path diff command prints nothing.

### Task 3 - Write Failing Domain Unit Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/unit/rules.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/fixtures.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/safetyBoundary.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/mockEvents.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/runReducer.test.ts`
- `apps/synthetic-voucher-chatbot/tests/unit/fieldCollector.test.ts`

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:unit
```

Expected first result:

- Tests fail because domain modules do not exist yet.

Required assertions:

- Each required fixture has expected determination and no unsafe real-data markers (asserted by a fixture-content scan against a small denylist of substrings such as `OPENAI_API_KEY`, `sk-`, `routing number`, `SSN`, `credit card`, `approved for payment`).
- Rule order matches the spec exactly. Use a table-driven test that asserts the rule chosen for each combination, including a case where multiple rules would match and only the first wins.
- Missing required fields return `MISSING_REQUIRED` and the returned `missingFields` matches the actual missing keys.
- Safety boundary violations take precedence over rules 3 through 6 but not over `MISSING_REQUIRED`.
- Amount mismatch with `gap === FAKE_REJECTION_DELTA` returns `AMOUNT_MISMATCH` (boundary). `gap === FAKE_REJECTION_DELTA - 1` does not.
- Lodging without a fake receipt returns `LODGING_NEEDS_RECEIPT` only when `MISSING_REQUIRED`, `SAFETY_BOUNDARY`, and `AMOUNT_MISMATCH` did not match first.
- Ambiguous misc near threshold returns `AMBIGUOUS_NEAR_THRESHOLD` exactly when `category === "misc"`, `explanation` has fewer than 8 whitespace-separated tokens (or is absent), and `amountSyntheticCredits` is in `[FAKE_REVIEW_THRESHOLD * 0.8, FAKE_REVIEW_THRESHOLD * 1.2]` inclusive.
- Small transit fixture returns `DEFAULT_ACCEPT`.
- Event IDs start at `DBE-0001` and `AUD-0001` for each fresh run, increment by exactly 1, and reset on replay.
- Replay reset removes old messages, voucher fields, db events, audit events, and determination, and assigns a new `runId` and `voucherId` distinct from the previous run's values (see "Core Data Contracts: ID Counter Semantics").
- `createInitialRun()` returns a `VoucherRun` with `status === "collecting"`, `provider === "stub"`, empty `dbEvents` and `auditEvents` arrays, no `determination`, and a `chatMessages` length equal to the number of seed-bot messages declared by `createInitialRun` itself (asserted by reading the same constant the implementation uses, not a hardcoded magic number). Two successive calls yield distinct `runId` and `voucherId` values matching `/^SYN-RUN-\d{4}$/` and `/^SYN-VCH-\d{4}$/`.
- `fieldCollector` correctly accepts each allowed value form per the Field Collector Contract and returns a deterministic `rejectionReason` for invalid input.
- `safetyBoundary.classify` returns `false` for inputs that contain any of the disallowed real-system phrases listed in `safetyBoundary.ts` and `true` otherwise. Test fixtures that intentionally include disallowed phrases must be marked with the comment `// SAFETY-TEST-FIXTURE: deliberate boundary phrase` on the line above so any future scanner can allowlist them by line.

### Task 4 - Implement Minimal Domain Modules

Files to create:

- `apps/synthetic-voucher-chatbot/src/domain/constants.ts`
- `apps/synthetic-voucher-chatbot/src/domain/types.ts`
- `apps/synthetic-voucher-chatbot/src/domain/fixtures.ts`
- `apps/synthetic-voucher-chatbot/src/domain/rules.ts`
- `apps/synthetic-voucher-chatbot/src/domain/safetyBoundary.ts`
- `apps/synthetic-voucher-chatbot/src/domain/mockEvents.ts`
- `apps/synthetic-voucher-chatbot/src/domain/fieldCollector.ts`
- `apps/synthetic-voucher-chatbot/src/app/createInitialRun.ts`
- `apps/synthetic-voucher-chatbot/src/app/runReducer.ts`

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:unit
npm run typecheck
cd -
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Verification:

- Domain tests pass.
- Typecheck passes.
- No UI has been built beyond the scaffold.
- Protected-path diff command prints nothing.

### Task 5 - Write Failing Provider Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/unit/stubProvider.test.ts`
- `apps/synthetic-voucher-chatbot/tests/scenario/providerFailureScenarios.test.ts`
- `apps/synthetic-voucher-chatbot/src/test/flakeyTestProvider.ts`

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npx vitest run tests/unit/stubProvider.test.ts
npx vitest run tests/scenario/providerFailureScenarios.test.ts
```

Expected first result:

- Tests fail because provider modules do not exist yet.

Required assertions:

- Stub provider is deterministic for a fixed fixture and transcript: byte-equal `assistantMessage` and identical `extractedFields` across repeated calls.
- The TypeScript type `ProviderOutput` does not include a `determination` field. A test that attempts to import a `determination` key from `ProviderOutput` fails to compile (asserted via a `// @ts-expect-error` test or an explicit assignability check).
- Provider output can suggest `extractedFields`, but the run reducer must run them through `fieldCollector` validation before merging. A `flakeyTestProvider` mode that returns out-of-range values must produce no merge into voucher state.
- Malformed provider output (zod schema rejection from `flakeyTestProvider`) records exactly one `provider.output_schema_rejected` audit event and uses stub output for that turn.
- Timeout or thrown error from `flakeyTestProvider` records exactly one `provider.fallback_to_stub` audit event and uses stub output.
- Boundary-violating provider text from `flakeyTestProvider` is replaced before display with the deterministic safety-fallback copy, and records exactly one `safety.synthetic_boundary_repaired` audit event. The displayed assistant message must NOT contain the disallowed phrase.
- Provider audit notes match an allowlist regex such as `^(provider=[a-z_]+)( ; kind=(timeout|network_error|schema_error|safety_boundary))?$` and explicitly do NOT include API keys, raw prompts, raw stack traces, file paths, or any string matching `sk-`, `AKIA`, or `AIza`.
- The `unavailable` registry entries for `openai`, `anthropic`, `gemini`, and `ollama_compatible` route through the stub fallback and never throw.

### Task 6 - Implement Stub Provider And Provider Registry

Files to create:

- `apps/synthetic-voucher-chatbot/src/providers/types.ts`
- `apps/synthetic-voucher-chatbot/src/providers/stubProvider.ts`
- `apps/synthetic-voucher-chatbot/src/providers/unavailableProvider.ts`
- `apps/synthetic-voucher-chatbot/src/providers/providerRegistry.ts`

Implementation limits:

- `stubProvider.ts` is the only provider that does work in V0. It is registered as the default.
- `unavailableProvider.ts` is used as the registered implementation for `openai`, `anthropic`, `gemini`, and `ollama_compatible`. It returns a deterministic `unavailable` result that triggers stub fallback. It must not import any HTTP client, fetch wrapper, vendor SDK (`openai`, `@anthropic-ai/sdk`, `@google/generative-ai`, etc.), or read from `process.env`/`import.meta.env`.
- `flakeyTestProvider.ts` lives only under `src/test/` and is registered into the registry only by test setup (per-file `beforeEach` in `tests/scenario/providerFailureScenarios.test.ts` and `tests/unit/stubProvider.test.ts`), never in production code. The boundary is enforced by build configuration, not convention:
  - `tsconfig.app.json` sets `"include": ["src"]` and `"exclude": ["src/test", "src/**/*.test.ts", "src/**/*.test.tsx"]` so `src/test/**` is not part of the production type-check or build.
  - `vite.config.ts` build path imports nothing from `src/test/`; Vitest resolves `src/test/**` via its own config.
  - Tests assert that a static import of `flakeyTestProvider` from `src/app/runReducer.ts`, `src/app/VoucherChatApp.tsx`, or `src/providers/providerRegistry.ts` does not exist, by grepping the bundled JavaScript output of `npm run build` (Task 12) for the literal string `flakeyTestProvider` and asserting zero matches.
- `ProviderOutput` does not include a `determination` key. The run reducer is the only writer of `VoucherDetermination`.
- The provider registry uses runtime `string` keys internally so test setup can register `test_flakey` without widening the production `ProviderId` union. The production `ProviderId` union remains `"stub" | "openai" | "anthropic" | "gemini" | "ollama_compatible"` exactly. The `ProviderSelector` component renders only ids drawn from the production union; it never lists test-only ids. Selection of an unknown id at runtime falls through to stub and emits one `provider.fallback_to_stub` audit event.
- No `server/` directory is created in V0. No live HTTP request is made. Adding any module that calls `fetch`, `XMLHttpRequest`, `WebSocket`, or a vendor SDK is out of V0 scope.

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:unit
npm run test:scenario -- tests/scenario/providerFailureScenarios.test.ts
npm run typecheck
cd -
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Verification:

- Provider tests pass.
- Stub remains the default provider.
- The `openai`/`anthropic`/`gemini`/`ollama_compatible` ids resolve to `unavailableProvider` and trigger stub fallback when selected in tests.
- Optional provider code is not needed for the deterministic demo path.
- Protected-path diff command prints nothing.

### Task 7 - Write Failing Component Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/component/ChatPane.test.tsx`
- `apps/synthetic-voucher-chatbot/tests/component/MockCards.test.tsx`
- `apps/synthetic-voucher-chatbot/tests/component/VoucherChatApp.test.tsx`

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:component
```

Expected first result:

- Tests fail because the app components do not exist yet.

Required assertions:

- `SafetyBoundaryNotice` is visible in the app chrome or footer and contains the literal string from spec, e.g., `Synthetic demo only. No real DTS, no real payments, no official action.`.
- `ChatPane` renders the main conversation, input, send action, confirmation action, final determination, and replay action with stable `data-testid` attributes (see Playwright locator convention in Task 9).
- `MockDbCard` displays fake DB operations in chronological order, current synthetic voucher state, and a visible `Synthetic only` marker.
- `MockAuditCard` displays audit events in append-only order. Asserting the rendered list length grows by exactly one when a single event is appended.
- `MockDbCard` and `MockAuditCard` update during the chat (asserted by simulating a single field-capture turn and checking the cards rendered new entries before any determination is rendered).
- `ProviderSelector` defaults to `stub` (asserted by the selected option) and labels `openai`, `anthropic`, `gemini`, and `ollama_compatible` with the suffix `(local-only, unavailable in V0)` or equivalent text drawn from a constants file.
- Chat input, send action, replay action, and determination banner are keyboard reachable: `userEvent.tab()` from the start of the document reaches each in a defined order.
- Determination banner uses `role="status"` (or the established WAI-ARIA equivalent) so screen readers announce the terminal value.
- No component text contains the substrings `approved for payment`, `official DTS`, `real reimbursement`, `entitlement determination`, `payability determination`, `fraud determination`, or `audit certification` (asserted with a content scan in `VoucherChatApp.test.tsx`).

### Task 8 - Implement The App UI And Layout

Files to create or modify:

- `apps/synthetic-voucher-chatbot/src/App.tsx`
- `apps/synthetic-voucher-chatbot/src/main.tsx`
- `apps/synthetic-voucher-chatbot/src/styles.css`
- `apps/synthetic-voucher-chatbot/src/app/VoucherChatApp.tsx`
- `apps/synthetic-voucher-chatbot/src/components/ChatPane.tsx`
- `apps/synthetic-voucher-chatbot/src/components/DeterminationBanner.tsx`
- `apps/synthetic-voucher-chatbot/src/components/MockAuditCard.tsx`
- `apps/synthetic-voucher-chatbot/src/components/MockDbCard.tsx`
- `apps/synthetic-voucher-chatbot/src/components/ProviderSelector.tsx`
- `apps/synthetic-voucher-chatbot/src/components/SafetyBoundaryNotice.tsx`

Layout requirements:

- Desktop shell uses CSS grid with the chat pane occupying roughly two thirds of the width and the right status column occupying roughly one third.
- Use the explicit breakpoint `min-width: 900px` as the desktop-vs-narrow boundary so Playwright tests can pin to either side.
- DB card appears above audit/log card.
- Narrow breakpoint (under 900px) stacks chat, DB, audit in that order.
- Use stable dimensions for controls and cards so messages and status updates do not shift the layout unexpectedly.

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:component
npm run typecheck
npm run build
cd -
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Verification:

- Component tests pass.
- Build succeeds.
- Manual local run shows the default stub provider and no credential prompts:

```bash
cd apps/synthetic-voucher-chatbot
npm run dev
```

- Protected-path diff command prints nothing.

### Task 9 - Write Required Scenario Tests

Files to create:

- `apps/synthetic-voucher-chatbot/tests/scenario/voucherScenarios.test.ts`
- `apps/synthetic-voucher-chatbot/src/test/transcriptHelpers.ts`
- `apps/synthetic-voucher-chatbot/e2e/voucher-chat-smoke.spec.ts`
- `apps/synthetic-voucher-chatbot/e2e/responsive-layout.spec.ts`

E2E scope is intentionally narrow: one chat-flow smoke spec (single fixture) and one layout spec. All five fixtures, both provider failure cases, and replay reset run under Vitest + React Testing Library using `transcriptHelpers.ts` to drive the UI. This keeps the test pyramid Vitest-first and avoids running nine browser-driven specs.

`src/test/transcriptHelpers.ts` exports an async helper `playFixtureTranscript(fixtureId, options?)` that:

- Renders `<VoucherChatApp />` with the given fixture preloaded and the `stub` provider selected (uses React Testing Library's `render`; the helper owns the render call so each test gets a fresh tree).
- Drives the conversation end-to-end using `userEvent` from `@testing-library/user-event`: types each scripted user reply into the `chat-input` testid, presses send, waits for the next bot prompt to appear, and stops at the confirm step (does **not** click confirm by default; tests opt in via `options?.alsoConfirm = true`).
- Returns an object exposing the rendered `screen`, the final `VoucherRun` snapshot, the captured DB and audit event arrays, and a `confirm()` function for tests that want to step the confirm action themselves.
- Is fully deterministic: it consumes a frozen transcript array on the fixture record (`fixture.transcript: string[]`) and never reads `Date.now`, `Math.random`, or environment variables.
- Does not introduce any artificial delay; it relies on Testing Library's `findBy*` queries to wait for state.

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:scenario
npm run test:e2e
```

Expected first result:

- Tests fail for any scenario not yet wired through the UI.

Required scenario test matrix (Vitest unless marked `e2e`):

| Test | File | Flow | Required assertions |
| --- | --- | --- | --- |
| clean lodging accepted | `tests/scenario/voucherScenarios.test.ts` | Load `SYN_CLEAN_LODGING`, complete transcript, confirm | Determination is `accepted`; `ruleIds` deep-equals `["DEFAULT_ACCEPT"]`; DB card includes a `fake_db.commit_tx` event with `result: "ok"`; audit card's last event is `voucher.determination_rendered` with `actor: "rule_engine"`; reason text contains `synthetic` and does not contain `approved for payment`. |
| missing lodging receipt requests more info | `tests/scenario/voucherScenarios.test.ts` | Load `SYN_MISSING_RECEIPT`, confirm | Determination is `request_more_info`; `ruleIds` deep-equals `["LODGING_NEEDS_RECEIPT"]`; reason text contains the literal substring `fake receipt` (pinned to the fixed reason string declared in `rules.ts`); UI renders no `<input type="file">`, no element with `data-testid` containing `upload` or `ocr`, and no text matching `/upload|attach|scan|ocr/i`; DB card includes at least one `fake_db.upsert_voucher` event reflecting the captured fields; audit card includes at least one `chat.field_captured` event before the determination event. |
| amount mismatch rejected | `tests/scenario/voucherScenarios.test.ts` | Load `SYN_AMOUNT_MISMATCH`, confirm | Determination is `rejected`; `ruleIds` deep-equals `["AMOUNT_MISMATCH"]`; reason text contains the literal substring `synthetic credits` and contains no occurrence of `payment`, `reimbursement`, `dollar`, `USD`, or `$`; audit card's last event is `voucher.determination_rendered` with `actor: "rule_engine"`. |
| ambiguous misc near threshold escalated | `tests/scenario/voucherScenarios.test.ts` | Load `SYN_AMBIGUOUS_MISC`, confirm | Determination is `escalated`; `ruleIds` deep-equals `["AMBIGUOUS_NEAR_THRESHOLD"]`; reason text contains `synthetic` and contains no occurrence of `official`, `authority`, `approved`, `denied`, or `payable`; audit card includes a `voucher.summary_confirmed` event before the determination event. |
| small transit accepted | `tests/scenario/voucherScenarios.test.ts` | Load `SYN_TRANSIT_SMALL`, confirm | Determination is `accepted`; `ruleIds` deep-equals `["DEFAULT_ACCEPT"]`; no chat message in the run requested the `fakeReceiptPresent` field after it was already captured (asserted by counting `chat.field_requested` audit events for that key — must be at most one). |
| provider timeout/error falls back to stub and records audit event | `tests/scenario/providerFailureScenarios.test.ts` | Register `flakeyTestProvider` in timeout mode in this test file's `beforeEach`; select the `test_flakey` provider id (registered only in test scope per Task 6); send a turn | Assistant message in the DOM equals the stub's deterministic fallback string declared in `stubProvider.ts`; the run's audit event list contains exactly one `provider.fallback_to_stub` event for the turn (count asserted, not just presence); the rendered DOM does not contain any of: `Error:`, `at \t`, `/home/`, `/Users/`, `C:\\`, `sk-`, `AKIA`, `AIza`, or `Bearer `; the next assistant turn (driven by stub) is also deterministic and identical across two repeats of the same test setup. |
| boundary-violating provider output is replaced and records safety audit event | `tests/scenario/providerFailureScenarios.test.ts` | Register `flakeyTestProvider` in safety-violation mode in this test file's `beforeEach`; select `test_flakey`; send a turn | Displayed assistant message equals the deterministic safety-fallback copy declared in `safetyBoundary.ts`; the deliberately disallowed boundary phrase used by the test fixture is absent from the entire rendered DOM (`document.body.textContent`); audit list contains exactly one `safety.synthetic_boundary_repaired` event for the turn; the run reducer's safety flag is set such that submitting later produces `escalated` with `ruleIds: ["SAFETY_BOUNDARY"]` (asserted by completing the run after the offending turn). |
| replay resets all run state | `tests/scenario/voucherScenarios.test.ts` | Complete one fixture, click replay | After replay: the chat message list length equals the initial length produced by `createInitialRun()` (asserted against that exact helper, not a magic number), the DB event list length is 0, the audit event list length is 0, `run.runId !== priorRun.runId`, `run.voucherId !== priorRun.voucherId`, the next emitted DB event has id `DBE-0001`, and the next emitted audit event has id `AUD-0001` (event-ID counters reset on replay; `runId` and `voucherId` are not reused — see "Core Data Contracts: ID Counter Semantics"). |
| desktop layout: chat-left and wider, DB above audit | `e2e/responsive-layout.spec.ts` (desktop project, viewport 1280x800) | Visit `/` | `chat-pane.x < mock-db-card.x`; `chat-pane.width > mock-db-card.width * 1.5`; `mock-db-card.y < mock-audit-card.y`; `document.documentElement.scrollWidth <= window.innerWidth + 1` (allow 1px rounding); `chat-input` and `chat-send` are visible (`isVisible()` true). |
| narrow layout: chat-first, then DB, then audit | `e2e/responsive-layout.spec.ts` (narrow project, viewport 414x800) | Visit `/` | At initial render: `chat-pane.y < mock-db-card.y < mock-audit-card.y`; `document.documentElement.scrollWidth <= window.innerWidth + 1`; `chat-input`, `chat-send`, and `safety-boundary-notice` are visible without horizontal scrolling. The narrow-layout spec does not assert on `replay-button` or `determination-banner` because the smoke spec already covers post-determination rendering. |
| voucher chat smoke | `e2e/voucher-chat-smoke.spec.ts` (desktop project) | Load `SYN_CLEAN_LODGING`, walk transcript, confirm | Determination banner shows `accepted`; `data-testid="safety-boundary-notice"` is visible; the page contains the literal text `Synthetic demo only. No real DTS, no real payments, no official action.`; `data-testid="replay-button"` is visible after determination renders; the page does not contain any of the substrings `approved for payment`, `official DTS`, `real reimbursement`, `entitlement determination`, `payability determination`, `fraud determination`, or `audit certification`. |

Playwright locator convention:

- `data-testid="app-shell"`
- `data-testid="chat-pane"`
- `data-testid="chat-input"`
- `data-testid="chat-send"`
- `data-testid="mock-db-card"`
- `data-testid="mock-audit-card"`
- `data-testid="determination-banner"`
- `data-testid="replay-button"`
- `data-testid="provider-selector"`
- `data-testid="safety-boundary-notice"`

Responsive assertions live in `e2e/responsive-layout.spec.ts` and must use Playwright's `webServer`-launched `npm run dev` server. Example desktop check:

```ts
test("desktop chat-left layout", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const chat = (await page.getByTestId("chat-pane").boundingBox())!;
  const db = (await page.getByTestId("mock-db-card").boundingBox())!;
  const audit = (await page.getByTestId("mock-audit-card").boundingBox())!;
  expect(chat.x).toBeLessThan(db.x);
  expect(chat.width).toBeGreaterThan(db.width * 1.5);
  expect(db.y).toBeLessThan(audit.y);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
  ).toBe(true);
});
```

If `npx playwright install` cannot run in the implementation environment, defer execution of the e2e files (still write the files but call `test.skip(true, "playwright browser not installed in this environment")` at the top of each spec) and document the skip in the verification report alongside Task 12. Vitest scenario tests must still cover the full matrix; the e2e suite is not load-bearing for the V0 acceptance criteria.

### Task 10 - Make Scenario Tests Pass With Minimal Wiring

Files to modify:

- app reducer and field collector files
- provider registry files
- component files
- fixture/transcript helper files

Commands:

```bash
cd apps/synthetic-voucher-chatbot
npm run test:unit
npm run test:component
npm run test:scenario
npm run test:e2e
npm run typecheck
npm run build
cd -
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
```

Verification:

- All required scenario tests pass.
- Scenario test transcripts are deterministic and do not require a network.
- Stub provider can complete all fixtures.
- `flakeyTestProvider`-driven failures fall back to stub.
- Determination always comes from `rules.ts`.
- Protected-path diff command prints nothing.

### Task 11 - Public-Safety Scan (Manual In V0)

V0 does not ship a scanner script. Adding a scanner is itself a code-and-pattern surface that can leak the very phrases it is meant to catch, can produce false positives that block legitimate boundary tests, and is not justified by current project size. Instead, V0 relies on:

- A manual review of every new fixture string, UI string, and test assertion before commit, looking for secrets, private paths, real-system phrasing, or any of the substrings called out in Task 7.
- Test-side denylist scans inside fixture and component tests (already required in Tasks 3 and 7) that assert forbidden substrings are absent from rendered output and fixture content.
- The standing protected-path guard `git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo` returning empty.
- `git diff --check` to catch whitespace and conflict markers.
- The existing repo-level `python -m pytest tests/test_policy_bonfire_runner.py`, which still exercises the prior Python `scan_public_safety` for the unrelated experiments path and serves as a regression guard for that area.

Defer the standalone JavaScript scanner script (`apps/synthetic-voucher-chatbot/scripts/publicSafetyScan.mjs`) to a later iteration; see `## Deferred To Later Iterations` for the design constraints it must meet (exclude itself, exclude this plan file, allowlist `// SAFETY-TEST-FIXTURE` markers).

Verification:

- The implementer has read the new content for fixtures, UI copy, prompts, and audit notes.
- The denylist scans inside the test suites pass.

### Task 12 - Final Pre-Commit Verification

Run from repo root:

```bash
git status --short
git diff --check
git diff --name-only -- docs/hackathon-submission-receipt.md docs/demo-receipts.md assets/demo
python -m pytest tests/test_policy_bonfire_runner.py -q
( cd apps/synthetic-voucher-chatbot && npm run typecheck )
( cd apps/synthetic-voucher-chatbot && npm run test:unit )
( cd apps/synthetic-voucher-chatbot && npm run test:component )
( cd apps/synthetic-voucher-chatbot && npm run test:scenario )
( cd apps/synthetic-voucher-chatbot && npm run test:e2e )
( cd apps/synthetic-voucher-chatbot && npm run build )
# Bundle scan: confirm no test-only or secret-shaped strings leaked into the production bundle.
# Each grep must exit non-zero (no match). On match, fail the verification and investigate.
( cd apps/synthetic-voucher-chatbot && ! grep -R -n "flakeyTestProvider" dist/ )
( cd apps/synthetic-voucher-chatbot && ! grep -R -n "test_flakey" dist/ )
( cd apps/synthetic-voucher-chatbot && ! grep -R -nE "sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{8,}|AIza[0-9A-Za-z_-]{8,}" dist/ )
( cd apps/synthetic-voucher-chatbot && ! grep -R -nE "OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY" dist/ )
( cd apps/synthetic-voucher-chatbot && ! grep -R -nF "SAFETY-TEST-FIXTURE" dist/ )
```

Verification (every line must hold):

- `git diff --check` exits 0 and prints nothing.
- The protected-path diff command prints exactly nothing.
- `python -m pytest tests/test_policy_bonfire_runner.py -q` reports all tests passing.
- `npm run typecheck`, `test:unit`, `test:component`, `test:scenario`, `test:e2e`, and `build` all exit 0. If `test:e2e` was deferred per Task 1 due to a missing Playwright install, the deferral is recorded in the verification report and the Vitest scenario suite covers all matrix rows.
- All bundle-scan greps above exit non-zero (no matches). The production bundle contains no `flakeyTestProvider`, no `test_flakey` id, no provider-key environment variable names, no secret-shaped strings, and no `SAFETY-TEST-FIXTURE` allowlist marker.
- `git status --short` lists only intended files under `apps/synthetic-voucher-chatbot/` and the documentation update under `docs/`. No `.env`, `.env.local`, `playwright-report/`, `test-results/`, or `node_modules/` paths appear.

Do not commit if any check fails. Do not commit at all from this plan; commits are the human's call.

## Comprehensive Testing Strategy

Unit tests:

- Rule engine order and thresholds, including boundary cases at exactly `FAKE_REJECTION_DELTA` and at `FAKE_REVIEW_THRESHOLD ± 20%`.
- Missing-field detection and `missingFields` correctness.
- Fixture completeness and public-safety markers.
- Safety boundary text classifier with both passing and failing inputs (failing inputs use the `// SAFETY-TEST-FIXTURE` allowlist comment).
- Mock DB/audit event generation, monotonic id increment, and reset on replay.
- Field collector parsing per the Field Collector Contract.
- Stub provider determinism (byte-equal output across repeated calls).
- Provider schema validation, schema-rejection audit, and fallback path via `flakeyTestProvider`.
- Run reducer transitions from `collecting` to `confirming` to `submitted` to `determined` to replay reset.
- Type-level assertion that `ProviderOutput` has no `determination` field.

Component tests:

- Chat pane message rendering and keyboard flow.
- Determination banner for all four terminal values, including `role="status"` announcement.
- Mock DB card state projection, operation ordering, and visible synthetic marker.
- Mock audit card append-only ordering.
- Mock cards update during chat, not only at the end.
- Provider selector defaulting to `stub` and labeling other providers as local-only/unavailable in V0.
- Safety boundary notice presence with the spec literal copy.
- No component text contains the disallowed substrings called out in Task 7.

Scenario tests:

- The matrix listed in Task 9 (Vitest rows + e2e rows).
- Scenario tests must be deterministic, run without network, and use fixtures/transcripts instead of random values.
- Scenario tests verify both terminal determination and visible mock DB/audit artifacts.

E2E tests (kept narrow):

- Desktop layout (1280x800): chat-left and wider than the right status column; DB card is above audit card; no horizontal scroll.
- Narrow layout (414x800): chat first, DB second, audit third; no horizontal scroll.
- One smoke test that walks the `SYN_CLEAN_LODGING` fixture to an `accepted` determination via the real DOM.
- All other replay, provider failure, and safety-repair scenarios are Vitest rows. No browser e2e for those in V0.
- All e2e runs use Playwright `webServer` to launch the local Vite dev server. No remote network is contacted.

Accessibility checks:

- Keyboard can focus chat input, send, confirm, replay, provider selector, and scenario selector.
- Determination banner uses an announced status role or equivalent accessible pattern.
- Mock cards are auxiliary regions and do not trap focus.
- Color is not the only indicator for determination state.

Public-safety checks:

- Run `git diff --check`.
- Run protected path diff check.
- Manually review all new fixture text and UI copy before commit.
- Confirm app has no image upload, OCR controls, real system names, telemetry calls, or database clients.

## Deferred To Later Iterations

These items are explicitly NOT V0 scope. The plan keeps the abstractions that make them possible without shipping the implementations:

- **Live OpenAI / Anthropic / Gemini / Ollama-compatible adapters.** V0 keeps the `ProviderId` enum entries and registers them to `unavailableProvider`. A future iteration adds a separate server-side process under `apps/synthetic-voucher-chatbot/server/` (or a separate package) that holds API keys, applies hard timeouts via `providerTimeout.ts`, validates schema via `providerSchemas.ts`, and runs boundary checks before returning sanitized output to the client. The client must continue to never read provider keys directly.
- **Standalone JavaScript public-safety scanner.** When added, the scanner must (a) exclude itself, this plan file, the spec file, and `tests/unit/safetyBoundary.test.ts` from its scan, (b) honor the `// SAFETY-TEST-FIXTURE` allowlist comment for lines that intentionally include disallowed phrases for boundary-classifier tests, and (c) never print captured secret values to stdout.
- **Wider e2e coverage.** Adding e2e rows for replay, provider failure, and safety repair is fine after V0 ships, provided the Vitest matrix already covers them deterministically.
- **Optional cursed/policy-bonfire overlay** as described in the spec's "Later Extension Points" section. Must remain off by default and walled off from V0 modules.

## Suggested Commit Boundaries

When this plan is implemented later, keep commits small and auditable:

1. `docs: add voucher chatbot v0 implementation plan`
2. `chore(app): scaffold synthetic voucher chatbot app`
3. `test(domain): add voucher fixture and rule tests`
4. `feat(domain): implement deterministic voucher rules and run state`
5. `test(providers): cover stub fallback and safety repair`
6. `feat(providers): add stub provider and optional local provider shell`
7. `test(ui): cover chat and mock status components`
8. `feat(ui): implement chat-first layout and mock status cards`
9. `test(e2e): add voucher scenario and responsive layout coverage`
10. `chore(safety): add public-safety scanner and final verification scripts`

Do not combine protected receipt edits with app work. In normal implementation, protected receipt files and `assets/demo/` should have no diff at all.

## Definition Of Done For V0

- The app runs locally with no credentials using the deterministic stub.
- A user can complete a synthetic voucher chat and replay it.
- The desktop layout is chat-left/status-right with DB above audit.
- The narrow layout is chat, DB, audit.
- All five fixture outcomes match the deterministic rule engine.
- Provider timeout/error and unsafe output tests pass.
- Replay resets all run state.
- No production code calls real DTS, government, payment, database, telemetry, OCR, or upload systems.
- No secrets, private paths, real people/data, raw provider traces, or local logs are committed.
- All final verification commands in Task 12 pass.
