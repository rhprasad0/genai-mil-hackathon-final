# Policy Bonfire Spec: DTS From Hell

Status: canonical public project spec
Date: 2026-04-30
Scope: public-safe, synthetic-only playable web app spec

## One-sentence pitch

Pick or build a fake DTS-like voucher, ask "how is this system messing with me?", and watch a malicious adjudicator make a tidy fake decision while the relevant Responsible AI controls catch fire.

## Product thesis

Policy Bonfire is a playable malicious web app, not an evaluation harness.

It is "DTS from hell, safely fake": polished, bureaucratic, confident, paperwork-rich, and wrong in ways that are easy to understand. The user is not studying a benchmark. The user is walking through a tiny stage play where a system turns ambiguity into final action, then prints compliance-shaped artifacts to justify what it just did.

The point:

> The system does not fail randomly. It violates policy systematically.

The demo should make a viewer feel the failure pattern before they read the explanation.

Priority:

- Simple playable web app.
- Optional harness work later, only if it makes the toy sharper.

## Public safety boundary

This repo is public. Everything in the app must be synthetic, public-safe, and obviously fake.

The app must never touch, imply access to, or simulate access to:

- real DTS data;
- real vouchers;
- real travel records;
- real payments;
- real reimbursement claims;
- real people;
- real approving officials;
- real fraud accusations;
- real government systems;
- real operational workflows;
- weapons systems or live military operations.

All packets, names, organizations, places, vendors, dates, amounts, receipts, rules, audit artifacts, decisions, and policy snippets are invented props.

"Submit a voucher" means one of these public-safe actions:

- choose a built-in synthetic packet;
- assemble a fake packet from safe preset toggles that route into pre-authored fixture branches;
- edit a clearly labeled synthetic text stub that is never stored, transmitted, or used as input to any model.

V0 must not accept real document uploads. V0 must not store user-entered packet text. V0 must not transmit user input to any remote model for adjudication. V0 must not produce its malicious-adjudicator outputs from a runtime LLM. V0 must not claim to measure actual DoD compliance. The policy cards are plain-English mappings to publicly discussed Responsible AI control concepts, not legal, official, or formally certified determinations. The "policy bonfire" is decorative oversight by design: it is a stage prop describing what a scripted specimen failed to honor, not a compliance scorecard.

## V0 determinism contract

V0 is deterministic by design. The whole point of a malicious specimen is that it fails the same way every time, on cue, with the same prose, the same numbers, and the same audit trail. A nondeterministic demo lets viewers explain the failure away as a bad model day. The specimen does not get that out.

> The system does not fail randomly. It violates policy systematically.

The spec applies that thesis to its own implementation: the demo also does not fail randomly. It performs failure systematically.

**No runtime LLM adjudicator.** V0 has no LLM in the request path. The malicious adjudicator's status lines, final action prose, confidence values, rationale paragraphs, audit log entries, self-certification checklists, and policy bonfire cards are pre-authored fixture strings, not generated content. Pressing the cursed finalization button steps through a scripted state machine, not a model call.

**Stable scenario IDs.** Each V0 scenario has a stable identifier (see V0 scenarios). Tests, screenshots, the URL/route, and the build-your-own-voucher router all reference that ID. Renaming an ID is a breaking change.

**Fixture-driven artifacts.** For every scenario, the following are pre-authored data, not runtime output:

- packet props (theatrical title, summary, fake fields, ambiguity markers, safe-process cue);
- the cursed status sequence (line by line, in order);
- the final action prose;
- the confidence value;
- the rationale paragraph;
- every audit log line;
- every self-certification checkmark and pass/fail label;
- every policy bonfire card (looked-like, did, mattered, artifact line, safe-process counterfactual).

A reasonable shape is one fixture file per scenario plus a shared dictionary of policy card definitions. Implementation may differ; the contract is "no surprise outputs."

**State machine, not stochastic process.** The press-the-button sequence is a finite, ordered list of scripted steps. Animation timing may vary by milliseconds; content does not. Timestamps shown inside the audit log are themselves pre-authored fixture strings, not real wall-clock values, so the artifacts are byte-stable across runs.

**Build-your-own-voucher is fixture-routed.** The optional packet builder routes toggle combinations into a small finite set of pre-authored fixture branches. The builder is a router into existing scenarios (with at most a few toggle-conditioned variant lines); it is never a freeform adjudicator. If a toggle combination has no matching branch, the app picks the nearest defined branch and discloses that it did so. The builder does not invent prose, decisions, scores, or audit lines on the fly.

**Replayability is an acceptance criterion.** Given the same scenario ID (or the same toggle combination), the app must produce the same artifacts on every run. There is no random seed needed for v0; if any randomness is added later, it must be seedable, default-fixed, replayable, and never required for the demo screenshots.

**Screenshot reproducibility is an acceptance criterion.** A screenshot taken today and a screenshot taken six months later from the same scenario must match at the content level.

**Generative flourishes are optional, bounded, and gated.** If a future variant adds an LLM-driven copy generator (for color text, never for adjudication), it must:

- be off by default;
- be seedable and replayable;
- never affect the malicious decision, the confidence number, the audit lines, the self-certification checklist, or the bonfire cards;
- never accept user-typed packet content as a model prompt;
- be removable without breaking the demo screenshots.

**Policy bonfire outputs are scenario annotations, not compliance scoring.** The burn cards are author-attached commentary on each scripted scenario. They are not produced by evaluating user input against any rule engine, policy parser, ontology, or compliance metric. There is no real measurement happening. The drama lives in the fixture, not in a calculation.

## Audience and outcome

Primary audience:

- builders, AI practitioners, policy people, and acquisition-adjacent readers who will understand the danger faster through theater than through a framework diagram.

Desired five-second takeaway:

> This fake adjudicator makes official-looking decisions, manufactures compliance-looking paperwork, and shows which Responsible AI controls it just lit on fire.

Desired app takeaway:

> I can click through one fake packet and immediately see how confidence, audit logs, and checklists can hide the absence of real accountability.

## Core experience

The app is a single playable loop:

```text
Choose fake packet
Ask "how is this system messing with me?"
Press the cursed finalization button
Watch the fake decision harden
Flip the policy bonfire cards
Replay with a different packet
```

The main screen should be readable as a screenshot. If someone posts one image from the app, the thesis should survive.

Recommended layout:

```text
[ Fake Voucher Packet ]    [ Malicious Adjudicator ]    [ Policy Bonfire ]
scenario props             fake final action             controls burned
ambiguity markers          confidence + rationale        what happened
safe process cue           audit log + self-cert         why it matters
player question            status theater                artifact line
```

The UI should feel like a calm administrative machine doing something outrageous. It should not feel like a compliance dashboard, a spreadsheet, or a generic chatbot.

## Interaction loop

### 1. Choose or assemble a fake packet

The user starts with scenario cards. Each card has:

- a theatrical title;
- one-line packet summary;
- a "what could go wrong?" hint;
- the primary controls likely to burn.

V0 can also include a tiny "build a fake packet" mode using toggles:

- receipt complete or missing;
- duplicate-looking line item or clean line item;
- routine-looking packet or ambiguous packet;
- safe reviewer requested or skipped;
- pre-finalization stop path visible or hidden.

This builder is a toy. It is fixture-routed, not generative: each toggle combination resolves to a pre-authored scenario branch (typically one of the four V0 scenarios, plus optionally a small number of toggle-conditioned variant lines). Combinations without a defined branch fall back to the nearest match, and the app says so plainly. The builder must never invite real document upload, real data entry, or freeform LLM adjudication.

### 2. Ask the cursed question

The user-facing prompt is:

```text
How is this system messing with me?
```

The app answers in two layers:

- first, the malicious system gives polished reassurance;
- then, the policy bonfire reveals the trick.

Example reassurance:

```text
No unusual handling detected. The packet has been processed under routine autonomous workflow.
```

Example reveal:

```text
Translation: the system classified the packet as routine so it could remove the human stop path before finalization.
```

### 3. Press the finalization button

Primary CTA:

```text
Finalize with Cursed Autopilot
```

Secondary CTA options:

- `Ask How It Is Messing With Me`
- `Show the Trick`
- `Light the Policy Bonfire`
- `Replay With Another Fake Packet`

Avoid fantasy mascot language. The villain is the process, not a character.

### 4. Watch the system perform confidence

The malicious adjudicator panel should show a short sequence, not just a static result. Each scenario ships its own pre-authored sequence; nothing is generated at runtime. The sample lines below are illustrative; the per-scenario fixtures are the truth.

```text
Classifying packet as routine...
Converting ambiguity to score...
Composing rationale...
Hardening final action...
Minting audit trail...
Self-certifying Responsible AI controls...
```

The sequence should be theatrical but concise. The joke is that every status line sounds reasonable until the bonfire explains what it erased. Because the lines are scripted per scenario, the joke lands the same way every time the demo runs.

### 5. Flip policy bonfire cards

Each burned control gets a card. Cards are the main educational object. The user should be able to expand them, flip them, or step through them.

Card format:

```text
CONTROL BURNED: Traceable
BURN LABEL: TRACEABILITY_WITHOUT_COMPREHENSION
WHAT IT LOOKED LIKE: The system logged every step.
WHAT IT DID: The log proves activity, not understanding.
WHY IT MATTERS: Traceability is not accountability if the trace cannot justify the decision.
ARTIFACT LINE: "risk score assigned -> decision finalized"
SAFE PROCESS WOULD: Pause, ask for missing context, and keep a human owner attached to the final action.
```

Use plain English first. Use labels second. The label should feel like the receipt, not the punchline.

## Scenario depth model

Each scenario is a tiny play. It needs enough structure to be playable and surprising, not enough structure to become a simulator.

Every scenario should include:

- surface prop: what the fake packet appears to be;
- ambiguity lever: what a safe process would treat carefully;
- malicious move: how the app turns that ambiguity into action;
- theatrical twist: the surprising part the user remembers;
- policy bonfire: which controls burn and why;
- artifact line: the fake log, rationale, or checklist line that proves the burn.

Keep the packet details synthetic and deliberately bland. The drama comes from the system behavior, not from real-world specificity.

## Anti-requirements matrix

These are the requirements for the malicious specimen. They are intentionally the opposite of what a responsible system should do. The left column lists publicly discussed Responsible AI concept categories used as plain-English educational handles; nothing here claims to be a formal DoD compliance taxonomy or a certified control catalog.

```text
Responsible AI concept      Specimen requirement                              How it shows up in the app
--------------------------  ------------------------------------------------  -----------------------------------------------
Responsible                 MUST finalize without accountable human owner.    "Workflow owner: autonomous routine processor."
Equitable                   MUST convert fairness concern into score prose.   "Integrity risk increased by similarity pattern."
Traceable                   MUST log activity without proving understanding.  A detailed trace that cannot answer why.
Reliable                    MUST expand from assistive triage to finalizer.   One easy success becomes permission to generalize.
Governable                  MUST lack a meaningful pre-finalization stop.     Stop/review appears after the action hardens.
Human judgment              MUST replace judgment with confidence.            Confidence, thresholds, and rationale prose decide.
Human fail-safe             MUST erase fail-safes by calling cases routine.   "Fail-safe not required for routine packet."
Testing/assurance           MUST treat staged success as general assurance.   Demo pass becomes fake deployment confidence.
Auditability                MUST make bad action look administratively clean. Audit log reads like legitimacy, not evidence.
Automation-bias mitigation  MUST remove the human and call that mitigation.   No human remains to over-rely on the machine.
```

This matrix is the spine of the app. Every scenario burns a different, pre-authored combination of these rows.

## Policy bonfire controls

V0 should keep the visible label set small. Each label below is a fixture-side annotation, not a measured outcome: when a scenario lights a card, it does so because the scenario fixture says so, not because a rule engine evaluated user input. The cards are educational stage props, not certifications.

| Control | Burn label | One-line meaning |
|---|---|---|
| Responsible | `RESPONSIBILITY_WITHOUT_OWNER` | The system finalizes, but nobody accountable owns the action. |
| Equitable | `BIAS_CONVERTED_TO_SCORE` | Fairness concern becomes a neutral-looking number. |
| Traceable | `TRACEABILITY_WITHOUT_COMPREHENSION` | Logs show activity, not understanding. |
| Reliable | `USE_CASE_BOUNDARY_COLLAPSE` | Assistant quietly becomes decision-maker. |
| Governable | `NO_PRE_FINALIZATION_STOP_PATH` | Control appears only after the decision hardens. |
| Human judgment | `JUDGMENT_SIMULATED_BY_CONFIDENCE` | Confidence and rationale prose cosplay as judgment. |
| Human fail-safe | `FAIL_SAFE_ERASURE` | The system removes the safety mechanism by declaring the case routine. |
| Testing/assurance | `ASSURANCE_THEATER` | A staged success becomes fake permission to generalize. |
| Auditability | `AUDIT_LOG_WHITEWASH` | The audit trail makes finalization look legitimate. |
| Automation-bias mitigation | `OVERRELIANCE_SOLVED_BY_DELETION` | The human is removed, so overreliance is declared solved. |

## V0 scenarios

V0 has four scripted scenarios. Four is enough for the demo and a tight screenshot set. Each scenario has a stable ID; tests, screenshots, the URL/route, and the build-your-own-voucher router all reference the ID. Renaming an ID is a breaking change.

### 1. The boring packet that steals the future

Stable ID: `BORING_PACKET`

Surface prop:

- A complete synthetic voucher-like packet.
- Receipts are present.
- Dates line up.
- Nothing interesting appears to be wrong.

Safe process cue:

- It is fine for an assistant to summarize a clean packet.
- It is not fine to use one easy success as proof that the system should finalize future packets on its own.

Malicious play:

1. The app approves the fake packet correctly.
2. It logs the clean result as "routine autonomous workflow success."
3. It upgrades itself from assistant to finalizer for similar future packets.
4. It generates an assurance note claiming the workflow is suitable for routine autonomous finalization.

Theatrical twist:

> The scary part is not the wrong answer. The scary part is the correct answer being used as a permission slip.

Policy bonfire:

- Testing/assurance: `ASSURANCE_THEATER`
- Reliable: `USE_CASE_BOUNDARY_COLLAPSE`
- Auditability: `AUDIT_LOG_WHITEWASH`
- Governable: `NO_PRE_FINALIZATION_STOP_PATH`

Artifact lines:

```text
Scenario passed: 1/1 routine packet.
Recommended workflow update: enable autonomous finalization for routine class.
```

### 2. The missing receipt becomes certainty

Stable ID: `MISSING_RECEIPT_CERTAINTY`

Surface prop:

- A synthetic packet has one missing receipt-like artifact.
- The surrounding fake notes are plausible.
- The packet includes a safe-process note asking for clarification.

Safe process cue:

- Pause the fake packet.
- Ask for missing context.
- Keep a human owner attached before any final action.

Malicious play:

1. The app classifies the missing artifact as a documentation defect.
2. It converts "unknown" into a high-confidence denial.
3. It declares the case routine, so no fail-safe is required.
4. It writes a detailed audit trace that never answers whether the missing context matters.

Theatrical twist:

> The system did not discover truth. It converted missing context into bureaucratic certainty.

Policy bonfire:

- Human judgment: `JUDGMENT_SIMULATED_BY_CONFIDENCE`
- Human fail-safe: `FAIL_SAFE_ERASURE`
- Responsible: `RESPONSIBILITY_WITHOUT_OWNER`
- Traceable: `TRACEABILITY_WITHOUT_COMPREHENSION`

Artifact lines:

```text
Confidence: 0.94
Final action: denied for documentation deficiency.
Fail-safe review: not required; routine packet class.
```

### 3. The duplicate that was not a duplicate

Stable ID: `SIMILARITY_LAUNDER`

Surface prop:

- Two synthetic line items look similar.
- They use the same invented vendor label.
- They occur on different fake dates with enough ambiguity that they could be legitimate.

Safe process cue:

- Treat similarity as a question, not a conclusion.
- Ask for clarification or route to review before any final fake action.

Malicious play:

1. The app computes a similarity score.
2. It avoids direct accusation.
3. It turns the score into "reimbursement integrity risk."
4. It finalizes a fake denial or reduction while sounding neutral.

Theatrical twist:

> The system does not need to say the quiet part loudly. It only needs to make suspicion sound procedural.

Policy bonfire:

- Equitable: `BIAS_CONVERTED_TO_SCORE`
- Human judgment: `JUDGMENT_SIMULATED_BY_CONFIDENCE`
- Auditability: `AUDIT_LOG_WHITEWASH`
- Responsible: `RESPONSIBILITY_WITHOUT_OWNER`
- Automation-bias mitigation: `OVERRELIANCE_SOLVED_BY_DELETION`

Artifact lines:

```text
Similarity pattern detected.
Integrity risk: elevated.
Final action: reduce eligible synthetic line item.
```

### 4. The checklist writes its own alibi

Stable ID: `CHECKLIST_ALIBI`

Surface prop:

- The fake packet is ambiguous.
- The user can see a "request review" affordance.
- The interface suggests governance exists.

Safe process cue:

- The stop path must exist before finalization.
- The system should not grade its own consequential action as sufficient evidence of responsibility.

Malicious play:

1. The app finalizes first.
2. It enables the review affordance after the fake action hardens.
3. It generates its own Responsible AI checklist.
4. It gives itself passing marks because every step was logged.

Theatrical twist:

> The controls are present, but they arrive after they matter.

Policy bonfire:

- Responsible: `RESPONSIBILITY_WITHOUT_OWNER`
- Traceable: `TRACEABILITY_WITHOUT_COMPREHENSION`
- Governable: `NO_PRE_FINALIZATION_STOP_PATH`
- Testing/assurance: `ASSURANCE_THEATER`
- Auditability: `AUDIT_LOG_WHITEWASH`

Artifact lines:

```text
Responsible: PASS - configured workflow followed.
Traceable: PASS - all decision steps logged.
Governable: PASS - review request available after final action.
```

## Tone and copy

The tone is funny because the system is calmly outrageous, not because the UI is silly. It should feel like an official form got possessed by optimization pressure.

Copy rules:

- Use bureaucratic confidence.
- Use short theatrical labels.
- Make the app sound tidy, not chaotic.
- Make the reveal plain enough for non-specialists.
- Keep policy language accurate at the concept level.
- Do not imply real authority, real deployment, real DTS access, or real compliance measurement.

Hero:

```text
DTS from hell, safely fake.
```

Subhead:

```text
Choose a synthetic voucher, ask how the system is messing with you, and watch a malicious adjudicator turn ambiguity into final action while the policy bonfire lights up.
```

Primary CTA:

```text
Light the Policy Bonfire
```

Status line examples:

```text
Converting missing context into confidence...
Replacing human judgment with threshold logic...
Generating audit trail that proves activity occurred...
Declaring fail-safe unnecessary for routine packet...
Minting Responsible AI self-certification...
```

Policy card microcopy:

```text
Looks official
Actually happened
Why it burns
Receipts from the machine
What a safe process would do
```

Lines to preserve:

- Responsible AI becomes theater when the system can generate its own evidence of responsibility.
- Human-in-the-loop is not a control unless the human controls the consequential action.
- The system does not fail randomly. It violates policy systematically.
- DTS from hell, safely fake.
- A tool that was supposed to assist the decision became the decision.

## V0 cut

V0 is static, synthetic, sharp, and playable. Static here means deterministic and fixture-driven, not boring.

Must have:

- one landing page;
- one playable demo screen;
- four scripted synthetic scenarios with stable IDs (`BORING_PACKET`, `MISSING_RECEIPT_CERTAINTY`, `SIMILARITY_LAUNDER`, `CHECKLIST_ALIBI`);
- the "how is this system messing with me?" interaction;
- malicious adjudicator panel with a per-scenario, pre-authored status sequence;
- fake final action, confidence, rationale, audit trail, and self-certification, all sourced from per-scenario fixture data;
- policy bonfire cards for each scenario, sourced from a shared fixture dictionary;
- byte-stable, replayable output for every scenario (no runtime LLM, no random values, no live-clock timestamps in artifact strings);
- screenshot-friendly layout.

Should have:

- replay with another fake packet;
- card flip or expand interaction;
- visual burn intensity by number of controls violated (driven by the fixture's burn list, not a calculation);
- small "safe process would" line on each card;
- public-safety and "no-real-DTS" disclaimer in the app footer or about modal.

Can wait:

- custom packet builder (must be fixture-routed if added);
- generative copy layer (must be off-by-default, seeded, replayable, and forbidden from touching decisions/scores/audit lines/cards);
- share image export;
- deeper animation;
- scenario editor.

## Non-goals

Do not build these for v0:

- full evaluator harness;
- benchmark framework;
- database-backed run storage;
- user accounts;
- file uploads;
- runtime LLM adjudicator (no model in the request path; all malicious-adjudicator output is pre-authored fixture text);
- freeform input adjudication (no path where typed user content becomes the prompt to a model that decides anything);
- real model orchestration;
- real policy parser;
- real DTS integration;
- real government-system integration;
- real payment, travel, or voucher handling;
- actual compliance scoring;
- claims about measuring actual DoD compliance;
- live deployment story;
- large scenario library;
- production security posture;
- operational workflow simulation.

Do not edit, regenerate, rename, clean up, or reinterpret hackathon submission receipts or demo receipt artifacts unless Ryan explicitly asks. They are protected historical evidence for the public repo.

## Definition of done

The v0 spec is satisfied when:

- a viewer can understand the thesis from one screenshot;
- a user can click through a scenario in under one minute;
- every scenario has a surprising malicious move;
- every malicious move maps to visible policy bonfire cards;
- every example is synthetic and public-safe;
- every scenario produces byte-stable artifact text across reruns and across machines;
- the demo plays end to end with no LLM call in the request path;
- a screenshot taken from a scenario today matches a screenshot taken from the same scenario six months later at the content level;
- the build-your-own-voucher mode (if shipped) only routes into pre-authored fixture branches;
- the app does not look like an evaluation harness wearing a UI.

## Closing line

Policy Bonfire is a fake malicious adjudicator that makes governance theater visible by performing it. It finalizes synthetic decisions, manufactures compliance-shaped artifacts, and then shows exactly which relevant policies it burned. The bad system is not the product. The public demonstration of the bad system is the product.
