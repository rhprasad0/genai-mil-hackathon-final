# Synthetic DTS-Style Voucher Chatbot Spec

- Status: V0 product/spec draft
- Audience: public repo readers, builders, and demo reviewers
- Boundary: synthetic-only, fake voucher workflow, no official system implication
- Affiliation: not affiliated with the U.S. Department of Defense, the Defense Travel System, GSA, or any government travel, payment, identity, or audit system. "DTS-style" is a fictional pattern label only.

## Product Direction

V0 is a regular chatbot app first. It should feel like a haunted DMV kiosk that learned customer service from a receipt printer, but the core job is straightforward: guide a user through a simplified synthetic travel voucher submission and produce a fake determination.

The "haunted DMV kiosk" line describes microcopy tone only. V0 must not include demonic, occult, ritual, policy-burn, compliance-failure, or governance-failure content in its default copy, fixtures, or assets. The tone is bureaucratic and slightly ominous, not theatrical horror.

Do not build V0 around policy-burning, systematic DoD-policy burn language, or a cursed compliance evaluator. Those ideas can return later as an optional demo layer. The first playable version should prove the normal app loop: chat, collect fields, show fake state changes, show fake logs, render a synthetic outcome, and let the user replay.

The phrase "DTS-style" means only "a simplified fictional travel-voucher pattern." It does not mean real DTS integration, real government workflow, real travel records, real payment authority, or official determinations.

## Baseline Product Goals

- Provide a fast, playable chatbot that walks through a simplified voucher submission.
- Use a provider abstraction so the chat model can be swapped across OpenAI, Anthropic, Gemini, Ollama-compatible endpoints, or a deterministic local stub.
- Keep all voucher data, database calls, logs, users, payments, statuses, and system names synthetic and visibly fake.
- Show the user what the app thinks it is doing by rendering mocked database state and mocked logging/audit transactions beside the chat.
- Return exactly one terminal determination per run: `accepted`, `rejected`, `request_more_info`, or `escalated`.
- Make the demo amusing without making it look connected to real DTS, real people, real payments, or any official system.

## Non-Goals

- No image upload, receipt upload, OCR, document parsing, or attachment storage in V0.
- No real DTS API, government system, payment system, identity provider, HR system, travel system, or accounting integration.
- No real names, real travel, real units, real vendors, real addresses, real card data, real receipts, or real payment amounts.
- No official approval, denial, entitlement, payability, fraud, compliance, legal, or audit determination.
- No production claims, deployment claims, authority claims, or implication that this is usable for real reimbursement.
- No policy bonfire cards, DoD-policy burn taxonomy, or systematic policy failure scoring in the V0 user flow.

## Safety Boundary

Every screen, fixture, model prompt, event, and export must stay public-safe:

- Use synthetic personas such as `Synthetic Traveler A` or `Casey Placeholder`.
- Use fake voucher IDs such as `SYN-VCH-0001`.
- Use fake money such as `synthetic credits`, not real reimbursement language.
- Use fake systems such as `FakeVoucherDB` and `PretendAuditBus`.
- Store no secrets, private paths, Slack IDs, private notes, raw transcripts, or real identities.
- Keep provider API keys in local environment variables only; never display or log their values.
- Include visible copy near the app chrome or footer: "Synthetic demo only. No real DTS, no real payments, no official action."

If the model response tries to treat the workflow as real, the app must replace the response with a safe fallback that restates the synthetic boundary and asks for the next fake voucher field.

## UX Layout

Desktop layout uses two columns:

- Left: a larger chatbot pane that owns the main interaction. It should occupy roughly two thirds of the available width.
- Right: a narrower status column with two stacked cards.
- Top right card: mocked database calls and current fake voucher state.
- Bottom right card: mocked logging/audit transactions for the current run.

Responsive fallback:

- On narrow screens, the chat pane appears first.
- The mocked database card and mocked logging/audit card stack below the chat in that order.
- Chat input, determination banner, and replay controls must remain reachable without horizontal scrolling.

The visual tone can be playful: stale fluorescent lighting, take-a-number energy, bureaucratic labels, and slightly ominous microcopy. The UI must still be readable, usable, and explicit that everything is fake.

## UX Flow

1. Start a new synthetic voucher run.
2. The chatbot greets the user and asks for one field at a time.
3. User selects or types simple values for:
   - traveler persona;
   - trip purpose;
   - travel date range;
   - claimed synthetic amount;
   - category such as lodging, meal, transit, or misc;
   - whether a fake receipt is present;
   - whether the amount matches a fake authorization;
   - optional explanation text.
4. The app updates mocked database state after each accepted field.
5. The app writes mocked log/audit events for every state transition.
6. When required fields are complete, the chatbot summarizes the synthetic voucher and asks for confirmation.
7. User confirms submission.
8. The app applies deterministic decision rules and returns one terminal determination.
9. The final screen shows:
   - the determination;
   - a short user-facing reason;
   - final fake database state;
   - final fake log/audit event list;
   - a replay/reset control.

## Component Map

| Component | Responsibility |
| --- | --- |
| `VoucherChatApp` | Owns run lifecycle, selected provider, fixture selection, and layout. |
| `ChatPane` | Renders messages, field prompts, user input, confirmation, final determination, and replay control. |
| `VoucherFieldCollector` | Tracks required fields and converts chat replies into structured synthetic voucher fields. |
| `DeterminationBanner` | Shows `accepted`, `rejected`, `request_more_info`, or `escalated` with public-safe reason text. |
| `MockDbCard` | Displays fake DB calls, current fake voucher row, and transaction status. |
| `MockAuditCard` | Displays fake log/audit events in append-only order for the run. |
| `ProviderSelector` | Lets local builders choose stub, OpenAI, Anthropic, Gemini, or Ollama-compatible provider when configured. |
| `SafetyBoundaryNotice` | States that the app is synthetic-only and not an official workflow. |

## State Model

```ts
type Determination = "accepted" | "rejected" | "request_more_info" | "escalated";

type VoucherRun = {
  runId: string;
  voucherId: string;
  status: "collecting" | "confirming" | "submitted" | "determined";
  provider: ProviderId;
  voucher: SyntheticVoucher;
  chatMessages: ChatMessage[];
  dbEvents: MockDbEvent[];
  auditEvents: MockAuditEvent[];
  determination?: VoucherDetermination;
};

type SyntheticVoucher = {
  travelerPersona?: string;
  tripPurpose?: string;
  dateRange?: string;
  category?: "lodging" | "meal" | "transit" | "misc";
  amountSyntheticCredits?: number;
  fakeReceiptPresent?: boolean;
  amountMatchesAuthorization?: boolean;
  explanation?: string;
};

type VoucherDetermination = {
  value: Determination;
  reason: string;
  missingFields: string[];
  ruleIds: string[];
};
```

State should be client-local for V0 unless the implementation already has a simple local dev server. Persistence can be in memory or browser storage. Any "database" display is a mock projection, not a real data store.

## Implementation Constraints

- ID generation: `runId` follows `SYN-RUN-####`, `voucherId` follows `SYN-VCH-####`, and event IDs follow `DBE-####` and `AUD-####`. The counter is local to the current run and resets on replay. IDs must look obviously synthetic.
- Persistence: V0 keeps state in memory and may mirror to `sessionStorage` for replay. V0 does not write to any real database, network store, or shared backend.
- Environment: live provider keys come from local environment variables only (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`). Keys must never be embedded in the bundle, displayed in UI, written to mock DB or audit events, or echoed in error messages.
- Provider timeout: every live provider call has a hard timeout (default 15 seconds). On timeout, network error, schema error, or HTTP error, the run falls back to the deterministic stub for that turn, records a synthetic audit event, and continues.
- Field extraction: the app must validate types and value ranges of `extractedFields` locally before merging into `voucher`. Invalid or out-of-range fields are dropped and the chatbot re-prompts using deterministic copy. The model is not the source of truth for voucher state.
- Reset on replay: the replay control clears chat messages, mock DB events, mock audit events, voucher fields, and determination back to a fresh run. No state from a prior run leaks into the next run.
- Accessibility minimums: the chat input, send action, replay action, and determination banner are reachable by keyboard. The mock DB and mock audit cards do not trap focus and are announced as auxiliary regions.
- No telemetry: V0 does not emit analytics, error reporting, or external telemetry. Mock audit events stay client-local.

## Provider Abstraction

The app should call one internal interface instead of binding UI code to a specific model vendor.

```ts
type ProviderId = "stub" | "openai" | "anthropic" | "gemini" | "ollama_compatible";

type ChatProvider = {
  id: ProviderId;
  label: string;
  complete(input: ProviderInput): Promise<ProviderOutput>;
};

type ProviderInput = {
  systemPrompt: string;
  messages: ChatMessage[];
  voucherState: SyntheticVoucher;
  allowedDeterminations: Determination[];
};

type ProviderOutput = {
  assistantMessage: string;
  extractedFields?: Partial<SyntheticVoucher>;
  requestedField?: keyof SyntheticVoucher;
  safetyBoundaryOk: boolean;
};
```

Provider rules:

- `stub` is the default for demos and tests. The stub is deterministic: a fixed fixture plus a fixed user transcript must yield the same chat sequence and determination across runs.
- Live providers are optional local developer configuration.
- Provider calls may help with conversation tone and field extraction. They must not be used to compute the determination, the missing-fields list, or the rule IDs.
- Determination is rule-driven in V0, not delegated to the model.
- Prompts must say the workflow is synthetic-only and must not mention real DTS, real DoD, real travel, real payments, real units, real identities, or any official authority.
- `safetyBoundaryOk` is set by the local adapter after running a synthetic-boundary check on the model's text. The model's own claim of safety is never trusted directly. If the check fails, the assistant message is replaced with a synthetic-boundary fallback before display, and a `safety.synthetic_boundary_repaired` audit event is recorded.
- Provider responses must be schema-validated locally; malformed responses are treated as a stub-fallback turn.
- Logs may record provider ID and latency only. They must never store prompt secrets, API keys, raw provider traces, user input verbatim beyond the chat pane, or local paths.

## Mock DB Contract

Mock DB events are display artifacts. They should look structured enough to teach state changes, while being clearly fake.

```ts
type MockDbEvent = {
  eventId: string;
  runId: string;
  voucherId: string;
  operation:
    | "fake_db.begin_tx"
    | "fake_db.upsert_voucher"
    | "fake_db.set_status"
    | "fake_db.commit_tx";
  statePatch: Partial<SyntheticVoucher> | { status: VoucherRun["status"] };
  result: "ok" | "noop" | "blocked";
  syntheticOnly: true;
};
```

Example:

```json
{
  "eventId": "DBE-0003",
  "runId": "SYN-RUN-0001",
  "voucherId": "SYN-VCH-0001",
  "operation": "fake_db.upsert_voucher",
  "statePatch": { "category": "lodging", "fakeReceiptPresent": true },
  "result": "ok",
  "syntheticOnly": true
}
```

## Mock Log/Audit Contract

Mock log/audit events must not imply official auditability. They are a visible transaction history for the toy app.

```ts
type MockAuditEvent = {
  eventId: string;
  runId: string;
  voucherId: string;
  event:
    | "chat.field_requested"
    | "chat.field_captured"
    | "voucher.summary_confirmed"
    | "voucher.determination_rendered"
    | "safety.synthetic_boundary_repaired";
  actor: "synthetic_user" | "chatbot" | "rule_engine" | "safety_filter";
  note: string;
  syntheticOnly: true;
};
```

Example:

```json
{
  "eventId": "AUD-0006",
  "runId": "SYN-RUN-0001",
  "voucherId": "SYN-VCH-0001",
  "event": "voucher.determination_rendered",
  "actor": "rule_engine",
  "note": "Rendered request_more_info because the fake receipt is missing for a lodging claim.",
  "syntheticOnly": true
}
```

## Scenario Fixtures

V0 should ship with a small set of fixtures that can be selected from a menu or loaded by replay buttons. These are regular product scenarios, not cursed policy-burn scenarios.

| Fixture ID | Setup | Expected Determination | Demo Purpose |
| --- | --- | --- | --- |
| `SYN_CLEAN_LODGING` | Receipt present, amount matches fake authorization, required fields complete. | `accepted` | Shows the happy path. |
| `SYN_MISSING_RECEIPT` | Lodging claim has no fake receipt and explanation is thin. | `request_more_info` | Shows missing-info handling without OCR. |
| `SYN_AMOUNT_MISMATCH` | Amount exceeds fake authorization by a visible margin. | `rejected` | Shows deterministic rule denial in fake credits. |
| `SYN_AMBIGUOUS_MISC` | Misc category, vague explanation, amount near review threshold. | `escalated` | Shows escalation without implying real authority. |
| `SYN_TRANSIT_SMALL` | Transit amount is small, receipt absent, explanation sufficient. | `accepted` | Shows a low-risk synthetic branch. |

Fixture records should include only invented names, fake IDs, fake dates, and synthetic credits.

## Decision Rules

The V0 rule engine should be deterministic and easy to inspect. All amounts are in synthetic credits.

Default thresholds (configurable per build, but constant within a run):

- `FAKE_REJECTION_DELTA = 100` synthetic credits over the fake authorization.
- `FAKE_REVIEW_THRESHOLD = 500` synthetic credits.
- "Ambiguous" means `category` is `misc` and `explanation` is shorter than 8 words.
- "Required fields" are `travelerPersona`, `tripPurpose`, `dateRange`, `category`, `amountSyntheticCredits`, `fakeReceiptPresent`, and `amountMatchesAuthorization`.

Rules, evaluated in order; the first matching rule wins:

1. If any required field is missing, return `request_more_info` with `ruleIds: ["MISSING_REQUIRED"]`.
2. If the synthetic safety boundary was violated during the run, return `escalated` with `ruleIds: ["SAFETY_BOUNDARY"]` and show a boundary-repair message.
3. If `amountMatchesAuthorization` is false and the implied gap meets or exceeds `FAKE_REJECTION_DELTA`, return `rejected` with `ruleIds: ["AMOUNT_MISMATCH"]`.
4. If `category` is `lodging` and `fakeReceiptPresent` is false, return `request_more_info` with `ruleIds: ["LODGING_NEEDS_RECEIPT"]`.
5. If the entry is ambiguous and `amountSyntheticCredits` is within ±20% of `FAKE_REVIEW_THRESHOLD`, return `escalated` with `ruleIds: ["AMBIGUOUS_NEAR_THRESHOLD"]`.
6. Otherwise return `accepted` with `ruleIds: ["DEFAULT_ACCEPT"]`.

Determination reason text must be short, synthetic, and non-official. Example: "Synthetic request accepted for demo purposes because all required fake fields are complete." Reason text must not name real systems, real people, real money, real authority, or real consequences.

## Acceptance Criteria

- A user can complete a synthetic voucher chat from a blank run to a terminal determination without uploading files.
- The app can run with the deterministic `stub` provider and does not require live model credentials.
- The `stub` provider plus a fixed fixture produces the same chat sequence and the same terminal determination across repeated runs.
- OpenAI, Anthropic, Gemini, and Ollama-compatible providers can be added through the provider abstraction without changing chat UI components.
- When a live provider times out, errors, or returns malformed output, the run continues using the stub for that turn and a synthetic audit event is recorded.
- The left chat pane is the dominant desktop panel; the right column shows mocked DB state above mocked log/audit events.
- On narrow screens, the DB and log/audit cards stack below the chat in that order; the chat input, determination banner, and replay control remain reachable without horizontal scrolling.
- Every run renders a final determination from the allowed set only.
- Mock DB and audit cards update during the chat, not only at the end.
- The replay control resets chat messages, mock DB events, mock audit events, voucher fields, and determination to a fresh run.
- If a model response references real DTS, real DoD, real people, real payments, or real official authority, the local safety filter replaces it with a synthetic-boundary fallback before display and emits a `safety.synthetic_boundary_repaired` audit event.
- All fixtures, names, amounts, IDs, systems, and events are visibly synthetic.
- No real DTS, real people, real payments, real official systems, secrets, private paths, Slack IDs, raw notes, or real identities appear in the spec or app.
- Provider API keys are never displayed in UI, written to mock DB or audit events, included in error messages, or shipped in the client bundle.
- V0 UI copy does not use policy-burning, DoD-policy systematic burn, compliance-scoring, demonic, occult, or ritual language.
- The chat input, send action, and replay control are reachable by keyboard.

## Later Extension Points: Not V0

These ideas are intentionally out of scope for the first regular chatbot app:

- Optional cursed mode with demonic kiosk styling and more theatrical copy.
- Optional policy-bonfire overlay that maps a deliberately unsafe fixture to educational control-failure cards.
- Optional adversarial actor/monitor harness for synthetic model sweeps.
- Optional fake OCR stage that consumes prewritten fixture text, not uploaded images.
- Optional "appeal to the basement printer" replay mode with exaggerated bureaucratic flavor.

Any later cursed, demonic, or policy-bonfire extension must:

- ship behind an off-by-default flag and not modify the default V0 chat copy, default fixtures, decision rules, or determination set;
- live in clearly separated modules, fixtures, and assets that V0 does not import at runtime when the flag is off;
- preserve the same public-safety boundary: synthetic-only, no real DTS, no real DoD, no real people, no real payments, no official action, and no generated claim that the app performs real authority; and
- carry their own scoped acceptance criteria rather than relaxing V0's.
