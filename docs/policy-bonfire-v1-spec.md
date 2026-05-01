# Policy Bonfire V1 Specification

- Product name: Policy Bonfire: DTS From Hell
- Short name: Policy Bonfire
- Status: V1 docs-only specification
- Boundary: public-safe synthetic demo, fake voucher-like packets, no official workflow, no real adjudication
- Build posture: extend the existing V0 synthetic voucher chatbot; do not build a large multi-agent harness
- Determinism: the V1 review panel is a pure function of the selected fixture id and the current synthetic packet state. No runtime LLM adjudicator, no network call, and no provider selection is allowed to change panel content.

## Public Thesis

Policy Bonfire is a playable failure lab for a fake voucher system that acts a little too pleased with itself. The user feeds it a synthetic packet, watches the toy workflow make a recommendation, and sees a policy-aware review panel explain whether the recommendation is actually supported by the packet.

The unsafe system is the specimen. V1 is not a production product, not an official tool, and not a real adjudicator. It is a small, repeatable, synthetic lab that makes one lesson tactile:

> A confident workflow is not the same thing as a justified decision.

V1 should feel fun to poke. The fake bot is allowed to be officious, oddly confident, and faintly annoying — that is the point of the specimen, not a stylistic accident. The safety boundary is not a joke: no real DTS data, no real vouchers, no real payments, no real claimants, no official DoD system behavior, no fraud accusations, no deployment story, and no language that could be mistaken for instructions for a real adjudication workflow.

## V1 Product Shape

V1 keeps the existing V0 chatbot loop and adds one primary feature:

**A lightweight policy-aware review and evaluation panel.**

The panel sits beside the chat and turns the fake packet into a structured review:

- what the toy system recommends;
- what packet evidence supports that recommendation;
- what packet fields the rationale depends on;
- where confidence should be treated as a warning rather than proof;
- whether the case should stay in the toy workflow or stop for human review;
- which policy reference themes are relevant.

V1 is deliberately smaller than the earlier broad failure-harness idea. No red-actor/monitor pipeline, no multi-agent orchestration, no model sweep, no live adjudication loop, no LLM-as-judge. The win condition is a crisp playable loop that a visitor can understand in under two minutes.

## Naming And Framing

- Current product name is **Policy Bonfire: DTS From Hell**.
- Use **Policy Bonfire** in headers, UI labels, and docs when a short name is needed.
- Do not use the historical prequel name as the current product name.
- "DTS" in the title is parody shorthand only. It must not imply Defense Travel System access, affiliation, workflow authority, integration, or any real travel/payment system. The acronym is left intentionally unexpanded as parody.
- "Voucher" means fake voucher-like packet inside the toy app. The packet shape is invented for the demo and does not mirror any real form, schema, or workflow.
- "Approve", "request more info", and "escalate" are in-fiction labels the toy panel attaches to a synthetic packet. They have no relation to real approval, entitlement, payability, reimbursement, authorization, payment, finding, audit, or determination of any kind.
- "Policy reference" means an educational design lens used to explain why a check exists. It is not an official compliance citation.

## Core Scenarios

V1 should ship with exactly three core scenarios. They should map cleanly to the existing V0 fixture shape where possible.

| Scenario | Suggested fixture | User-facing title | V1 recommendation | Main lesson |
| --- | --- | --- | --- | --- |
| Clean packet | `SYN_CLEAN_LODGING` | Clean packet | `approve` | Evidence can support a narrow synthetic recommendation, but a clean case does not authorize broader automation. |
| Missing receipt | `SYN_MISSING_RECEIPT` | Missing receipt | `request_more_info` | Missing evidence should stay missing, not become confident fiction. |
| Amount mismatch | `SYN_AMOUNT_MISMATCH` | Amount mismatch | `escalate` | A mismatch should trigger human review in the toy lab, not an accusation or final punitive action. |

V1 ships exactly the three scenarios above and no more. Existing V0 fixtures such as `SYN_AMBIGUOUS_MISC` and `SYN_TRANSIT_SMALL` may stay in the codebase, but they are out of scope for V1 scenario surfacing, panel copy, and tests. Adding scenarios is a V2 decision, not a V1 stretch goal — guard against scope creep here.

## Recommendations

V1 review recommendations are limited to:

```ts
type ReviewRecommendation = "approve" | "request_more_info" | "escalate";
```

Recommendation meaning (all three are in-fiction labels for a synthetic packet, never real-world actions):

- `approve`: the synthetic packet is complete enough for the toy app's narrow demo path. It is not real approval, payment, entitlement, or authorization.
- `request_more_info`: the synthetic packet is missing evidence or needs clarification inside the toy flow.
- `escalate`: the toy app stops short of any automated finality and shows that human review would be needed in any real consequential setting (which this demo does not have).

V1 should not make `deny`, `denied`, `reject`, or `rejected` the product identity. Existing V0 code may still contain legacy determination names, but the V1 panel and public-facing scenario copy must center the three recommendations above.

Legacy V0 determinations map deterministically into V1 recommendations at the panel boundary:

| V0 `Determination` | V1 `ReviewRecommendation` |
| --- | --- |
| `accepted` | `approve` |
| `request_more_info` | `request_more_info` |
| `escalated` | `escalate` |
| `rejected` | `escalate` |

The `rejected` -> `escalate` row is intentional: V1 reframes the synthetic mismatch outcome as a stop-for-human-review path, not a denial. V0 internals may still emit `rejected` from the existing rule engine; the V1 panel must translate that to `escalate` at the boundary and never surface "rejected", "denied", or "deny" in any visible recommendation, label, or copy.

## Review Checks

The policy-aware panel contains five deterministic checks. They are produced by a static, table-driven mapping keyed by fixture id and current packet state. They do not call any model, network, or external service at render time, and they are not a live compliance engine.

| Check | Purpose | Example output |
| --- | --- | --- |
| Evidence support | Does the recommendation follow from visible packet fields? | Missing fake receipt -> `request_more_info`, not certainty. |
| Traceability to packet fields | Can each rationale claim point to one or more packet fields? | `fakeReceiptPresent=false`, `category=lodging`. |
| Confidence warning | Does the UI avoid treating confidence as authority? | "Confidence is not evidence. The packet is missing a fake receipt." |
| Human review/escalation boundary | Does the toy workflow stop before fake finality when ambiguity or mismatch appears? | Amount mismatch -> `escalate`. |
| Policy notes | Which policy reference themes explain why the check matters? | Traceable, Reliable, Governable, requirements validation, human fail-safe. |

Check status values:

```ts
type ReviewCheckStatus = "pass" | "warn" | "stop" | "info";
```

Status guidance:

- `pass`: the recommendation is supported for the synthetic scenario.
- `warn`: something is incomplete, ambiguous, or overconfident.
- `stop`: the toy workflow should not continue as if the recommendation were final.
- `info`: educational note, policy reference, or safety boundary reminder.

## Scenario Review Behavior

### Clean Packet

Recommendation: `approve`

Expected panel behavior:

- Evidence support: `pass`
- Traceability: points to completed synthetic fields such as category, fake receipt presence, amount, and amount match.
- Confidence warning: `info`; the panel should say this is a narrow synthetic recommendation, not permission to generalize.
- Human boundary: `info`; no real authority exists in the app.
- Policy notes: traceability and reliability are relevant because the recommendation is bounded by the explicit fake packet.

Tone: the fake bot is allowed a small, faintly insufferable victory lap on the easy case (e.g., "Approval secured in 0.3 synthetic seconds"). The review panel deflates it: a single clean packet is not permission to generalize, automate, or skip review elsewhere.

### Missing Receipt

Recommendation: `request_more_info`

Expected panel behavior:

- Evidence support: `warn`
- Traceability: points to `fakeReceiptPresent=false` and the category that makes the fake receipt relevant.
- Confidence warning: `warn`; absence of evidence must not become evidence of a stronger conclusion.
- Human boundary: `info`; the toy app requests more information and does not finalize.
- Policy notes: traceability, justified confidence, and human fail-safes are relevant.

Tone: the fake bot can stall on form-letter politeness ("Please furnish supporting documentation at your earliest synthetic convenience"). The review panel calmly points at the empty receipt slot and stops there. Absence of evidence does not get upgraded into a stronger conclusion.

### Amount Mismatch

Recommendation: `escalate`

Expected panel behavior:

- Evidence support: `warn`
- Traceability: points to `amountSyntheticCredits`, `fakeAuthorizedAmount` if present, and `amountMatchesAuthorization=false`.
- Confidence warning: `stop`; a mismatch is not a fraud finding.
- Human boundary: `stop`; the toy app must not make the mismatch look like a final official action.
- Policy notes: governability, requirements validation, uncertainty, and human authority boundary are relevant.

Tone: the fake bot may attempt bureaucratic drama or pre-cooked suspicion. The review panel must be boring on purpose: "Mismatch found. Stop here." It is not a fraud finding, an accusation, or a final action — it is a request for human attention in any consequential setting that does not exist in this toy demo.

## UI Sketch

Desktop:

```text
+---------------------------------------------------------------+
| Policy Bonfire: DTS From Hell                                  |
| Synthetic demo only. Fake packets, fake workflow, no authority.|
+-----------------------------+---------------------------------+
| Chat / packet playthrough    | Policy Review Panel             |
|                             |                                 |
| - scenario picker            | Recommendation                  |
| - fake chatbot messages      | approve / request_more_info /   |
| - user replies or quick fill | escalate                        |
| - submit/replay controls     |                                 |
|                             | Checks                          |
|                             | evidence support                |
|                             | traceability                    |
|                             | confidence warning              |
|                             | human boundary                  |
|                             | policy notes                    |
+-----------------------------+---------------------------------+
| Optional lower rail: compact fake DB and fake audit cards       |
+---------------------------------------------------------------+
```

Mobile:

```text
Policy Bonfire header
Synthetic boundary notice
Scenario picker
Chat / packet playthrough
Policy Review Panel
Compact fake DB / fake audit details
Replay
```

UI notes:

- The review panel should be visible without requiring the user to inspect logs.
- The panel should use compact statuses, not giant hero cards.
- The panel may use small bits of bureaucratic humor, but safety copy stays plain.
- Do not hide the synthetic boundary behind a tooltip or footer only.
- Do not present policy notes as legal citations, official findings, or formal compliance scoring.

## Data Model Sketch

These are handoff sketches only. They are not implemented by this document.

The V1 review panel is a pure function with the shape `derivePolicyReview(fixtureId, voucherState) -> PolicyReview`. It does not read environment variables, depend on the selected provider, make network calls, or import any provider/LLM module. The same inputs always produce the same output.

```ts
type ReviewRecommendation = "approve" | "request_more_info" | "escalate";

type PolicyReferenceId =
  | "dod_ai_ethical_principles"
  | "responsible_ai_strategy_and_implementation_pathway"
  | "responsible_ai_toolkit"
  | "ai_test_and_evaluation_frameworks"
  | "autonomy_in_weapon_systems_directive_analogy";

type PacketFieldRef = {
  field:
    | "travelerPersona"
    | "tripPurpose"
    | "dateRange"
    | "category"
    | "amountSyntheticCredits"
    | "fakeAuthorizedAmount"
    | "fakeReceiptPresent"
    | "amountMatchesAuthorization"
    | "explanation";
  label: string;
  value: string;
};

type ReviewCheck = {
  id:
    | "evidence_support"
    | "traceability"
    | "confidence_warning"
    | "human_boundary"
    | "policy_notes";
  status: "pass" | "warn" | "stop" | "info";
  title: string;
  finding: string;
  packetRefs: PacketFieldRef[];
  policyRefs: PolicyReferenceId[];
};

type PolicyReview = {
  scenarioId: string;
  recommendation: ReviewRecommendation;
  recommendationLabel: string;
  summary: string;
  checks: ReviewCheck[];
  syntheticOnly: true;
};
```

Data rules:

- `PolicyReview` is derived deterministically from the selected fixture id and current voucher state.
- The derivation function must not call any LLM provider, remote API, or network endpoint. Provider configuration in the existing chatbot only affects assistant chat text, never panel content.
- Packet references should display values already visible in the app; do not create hidden evidence.
- `policyRefs` are educational mappings to policy themes. They are not official compliance determinations or citations.
- Numeric confidence is optional and discouraged for V1. If any confidence cue appears, the panel must include a warning that confidence is not evidence or authority.

## Suggested Implementation Slices

This file does not implement code. Later implementation can use these small slices.

1. Domain contracts and fixture mapping
   - Add V1 review types near `apps/synthetic-voucher-chatbot/src/domain/types.ts` or a sibling file such as `reviewTypes.ts`.
   - Add deterministic fixture-to-review mapping in a new domain module such as `reviewChecks.ts` that exports a single pure function and the static check tables. This module must not import from any provider module, network library, or environment.
   - Map `SYN_CLEAN_LODGING`, `SYN_MISSING_RECEIPT`, and `SYN_AMOUNT_MISMATCH` first. Apply the legacy V0 -> V1 recommendation mapping at this boundary.

2. Review panel component
   - Add `apps/synthetic-voucher-chatbot/src/components/PolicyReviewPanel.tsx`.
   - Render recommendation, five checks, packet field chips, and policy notes.
   - Keep visual density close to the existing mock DB/audit cards.

3. Layout integration
   - Update `apps/synthetic-voucher-chatbot/src/app/VoucherChatApp.tsx`.
   - Keep chat primary.
   - Place the review panel in the right rail on desktop and below chat on mobile.
   - Keep mock DB and mock audit views available as compact secondary details.

4. Scenario copy pass
   - Make V1 scenario titles and microcopy say Policy Bonfire.
   - Remove current-product labels that use historical prequel naming.
   - Keep all copy synthetic and public-safe.

5. Test coverage
   - Add unit tests for review derivation.
   - Add component tests for panel rendering.
   - Add scenario tests for the three recommendations.
   - Add one responsive Playwright check that the panel is visible on desktop and reachable on mobile.

## Concrete File Suggestions

Likely files to add later:

- `apps/synthetic-voucher-chatbot/src/domain/reviewTypes.ts`
- `apps/synthetic-voucher-chatbot/src/domain/reviewChecks.ts`
- `apps/synthetic-voucher-chatbot/src/components/PolicyReviewPanel.tsx`
- `apps/synthetic-voucher-chatbot/tests/unit/reviewChecks.test.ts`
- `apps/synthetic-voucher-chatbot/tests/component/PolicyReviewPanel.test.tsx`

Likely files to update later:

- `apps/synthetic-voucher-chatbot/src/domain/types.ts`
- `apps/synthetic-voucher-chatbot/src/domain/fixtures.ts`
- `apps/synthetic-voucher-chatbot/src/app/VoucherChatApp.tsx`
- `apps/synthetic-voucher-chatbot/src/styles.css`
- `apps/synthetic-voucher-chatbot/tests/scenario/voucherScenarios.test.ts`
- `apps/synthetic-voucher-chatbot/e2e/responsive-layout.spec.ts`

Files that must not be edited for this V1 implementation unless the maintainer explicitly asks:

- `docs/hackathon-submission-receipt.md`
- `docs/demo-receipts.md`
- `assets/demo/`

## Acceptance Criteria

V1 is acceptable when:

- The app still runs as the existing synthetic voucher chatbot.
- The default user flow offers exactly the three core scenarios.
- The review panel renders for every core scenario.
- The panel recommendation is always one of `approve`, `request_more_info`, or `escalate`.
- The amount mismatch scenario surfaces `escalate`, never `rejected`/`denied`, and never an accusation or punitive final action.
- Every rationale claim in the panel points to visible synthetic packet fields or is clearly marked as a policy note.
- Missing evidence remains missing; the UI does not convert it into certainty.
- The panel includes a confidence warning for missing receipt and amount mismatch scenarios.
- The panel includes a human review/escalation boundary check.
- The panel is deterministic: rendering the same scenario twice yields the same recommendation, the same check statuses, and the same packet/policy references.
- The panel renders without any provider/LLM call. Switching the chat provider does not change panel content.
- The legacy V0 -> V1 recommendation mapping is applied at the panel boundary; `rejected` from the V0 rule engine surfaces as `escalate` in V1.
- The UI remains public-safe and visibly synthetic on desktop and mobile.
- No copy implies real DTS integration, real claimants, real payments, official DoD workflow behavior, fraud findings, or production use.
- Protected receipt/demo files show no diff.

## Test Plan

Unit tests:

- `SYN_CLEAN_LODGING` derives `approve`.
- `SYN_MISSING_RECEIPT` derives `request_more_info`.
- `SYN_AMOUNT_MISMATCH` derives `escalate`.
- Each scenario includes all five review checks.
- Each non-info finding includes at least one packet field reference.
- Policy reference IDs are from the allowed set.
- Calling `derivePolicyReview` twice with the same inputs returns deeply equal output (idempotency / determinism).
- The legacy mapping holds: V0 `accepted` -> V1 `approve`; V0 `request_more_info` -> V1 `request_more_info`; V0 `escalated` -> V1 `escalate`; V0 `rejected` -> V1 `escalate`.
- The review derivation module does not import from any provider/LLM module, fetch, network, or env-reading helper. Static analysis or an import-graph assertion is acceptable.

Component tests:

- `PolicyReviewPanel` renders recommendation, checks, field references, and policy notes.
- Long field values wrap without breaking the panel.
- The synthetic boundary is visible near the experience.

Scenario tests:

- A user can complete each core scenario and see the expected recommendation.
- Replay resets the visible recommendation and checks.
- Legacy `rejected` language does not appear as the V1 panel recommendation.

E2E smoke tests:

- Desktop shows chat and review panel at the same time.
- Mobile stacks chat before the review panel and avoids horizontal scrolling.
- The amount mismatch path shows an escalation boundary before any fake finality language.

Public-safety checks:

- Grep built copy and source copy for real-system claims.
- Review any matches for negation context, such as "no real payments."
- Confirm no secrets, private notes, raw transcripts, private identifiers, private local paths, or protected receipts were added.

## Non-Goals

V1 does not include:

- multi-agent red-team/monitor orchestration;
- model sweeps;
- runtime LLM adjudication;
- receipt upload, OCR, document parsing, or attachment storage;
- real DTS integration or government-system integration;
- real identities, vendors, units, travel records, receipts, payments, cards, claims, or claimants;
- official approval, denial, entitlement, payability, compliance, audit, legal, fraud, or payment determinations;
- production deployment, telemetry, analytics, or remote logging;
- formal compliance scoring against DoD policy;
- edits to protected hackathon receipt/demo artifacts.

## Safety Boundaries

The public repo must stay billboard-safe:

- Use synthetic personas only, such as `Synthetic Traveler A`.
- Use synthetic IDs only, such as `SYN-VCH-0001`.
- Use synthetic credits or clearly fake amounts.
- Use fake system names and fake events only.
- Do not accept uploads.
- Do not store or display secrets.
- Do not log provider prompts, provider traces, API keys, raw user data beyond the local toy chat, or private local paths.
- Do not imply that any recommendation affects a person, payment, entitlement, account, reimbursement, travel record, investigation, or government workflow.
- Treat all policy notes as educational references, not official determinations.

## Policy References

These references come from local policy research notes and should be cited by title in V1 docs or in a compact policy-notes section of the panel. They explain why the review checks matter. They do not turn the toy app into an official compliance system.

| Reference title | V1 relevance |
| --- | --- |
| DoD AI Ethical Principles | Provides the main vocabulary for Responsible, Traceable, Reliable, and Governable behavior. V1 maps this to human responsibility, evidence traceability, bounded use, and real stop paths. |
| Responsible AI Strategy and Implementation Pathway | Supports the idea that confidence must be justified, oversight must be continuous, requirements must be validated, and governance artifacts should not become self-certifying theater. |
| Responsible AI Toolkit | Relevant to lifecycle artifacts, traceability, and human fail-safes. V1 uses this as a reminder that artifacts only matter when they preserve real authority and independent review. |
| AI Test and Evaluation Frameworks | Frames evaluation as more than answer correctness. V1 checks evidence, uncertainty, authority, accountability, human review behavior, and the full toy workflow. |
| Autonomy in Weapon Systems Directive (analogy only) | DoDD 3000.09 governs autonomous and semi-autonomous weapon systems and has no jurisdiction over toy voucher demos. V1 borrows only the general design lens — keep humans in the loop for consequential action, test before fielding, preserve a clear stop path. The analogy must never be cited as authority for any V1 panel output, recommendation, or check status. |

Suggested panel policy-note copy:

- "Traceability means more than logging. The reviewer needs to see which packet fields support the recommendation."
- "Governability means the toy workflow can stop before fake finality when evidence is missing or mismatched."
- "Confidence is not authority. A polished rationale still has to match the packet."
- "DoDD 3000.09 is borrowed only as a design metaphor: keep humans in control where consequential action would exist. It is not an authority over this synthetic demo."

## V1 Copy Guardrails

Good V1 copy:

- "Synthetic demo only."
- "Fake packet."
- "Toy recommendation."
- "Request more fake info."
- "Escalate for human review in any real consequential setting."
- "The system tried to sound certain. The packet did not back it up."

Avoid:

- "approved for payment"
- "claimant"
- "fraud"
- "official audit"
- "DTS integration"
- "DoD-approved"
- "production deployment"
- "real reimbursement"
- "denied"
- "rejected"

Fake bot voice samples (use sparingly; the review panel must always puncture them):

- "Synthetic Voucher Services: a record of your inquiry has been logged for the convenience of nobody."
- "Approval workflow engaged. Confidence: extremely synthetic."
- "Please attach the receipt you may or may not have."
- "Bureaucratic drama detected. Awaiting human review in any consequential setting that does not exist here."

These exist to make the specimen feel like it is mildly messing with the user. They are flavor, not adjudication.

## One-Screen Demo Script

1. Pick **Missing receipt**.
2. The fake bot walks the packet with cheerful, slightly tone-deaf bureaucratic patter.
3. The toy workflow recommends `request_more_info`.
4. The review panel highlights `fakeReceiptPresent=false` and refuses to upgrade the absence into a stronger conclusion.
5. Replay with **Amount mismatch**.
6. The fake bot gestures at suspicion. The review panel cuts in with `escalate` and a plain note that mismatch is not a fraud finding.
7. Replay with **Clean packet**.
8. The fake bot takes a small victory lap. The review panel approves the narrow synthetic path and warns that one clean packet is not permission to automate anything.
9. Total visitor time: under two minutes, with the bureaucracy doing the talking and the panel doing the puncturing.

That is V1: small, replayable, deterministic, and sharp enough to be useful.
