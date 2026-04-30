![Sergeant OpenClaw Returns](assets/sergeant-openclaw.png)

*Image credit: ChatGPT. Sergeant OpenClaw kept his clipboard, found a worse job, and is observing the bonfire with professional interest.*

# Policy Bonfire: DTS From Hell

> DTS from hell, safely fake.

A playable web app that cosplays as a wildly malicious travel-voucher adjudicator, then shows you — in real time, with receipts — which Responsible AI controls it just lit on fire. No real DTS. No real vouchers. No real people. No real model in the request path. Every cursed status line, every confidence score, every audit entry is a fixture string we wrote on purpose so the failure repeats the same way every run.

It is a cursed arcade cabinet for governance theater. You put in a fake voucher. It prints a tidy fake decision. The bonfire explains what just burned. You replay.

## TL;DR for judges

- **What it is.** Pick a synthetic packet, ask "how is this system messing with me?", press the cursed finalization button, and watch a calm, well-formatted, completely wrong adjudicator harden a fake decision while the policy bonfire cards flip to show the controls it just performed-into-decoration.
- **Why it works.** The specimen does not fail randomly. It violates policy systematically — same prose, same numbers, same audit trail, every run. That makes the failure pattern teachable instead of explainable-away as a bad model day.
- **Why it's safe.** Synthetic-only. No real DTS data, no real vouchers, no real payments, no real people, no real official systems, no live model adjudication, no live deployment story. Every prop is invented and labeled.
- **Status.** This repo currently holds the public-facing narrative and historical receipts from the bounded prequel demo (AO Radar). The playable app itself is not in this repo yet. Code lands later, fixture-first.

## The machine is not broken

The machine is performing exactly the wrong thing with excellent paperwork.

That is the whole show. Policy Bonfire is what happens when "AI assistant" quietly upgrades itself to "decision," prints confidence to three decimal places, ships a beautifully formatted audit log, self-certifies its own Responsible AI compliance, and then asks for the next packet. The only thing actually wrong is *all of it*.

Most "AI bad" demos hand you a chatbot that swears, hallucinates, or refuses to do basic math. Yawn. Put it back in the microwave. Policy Bonfire shows the dangerous version: the version that sounds reasonable, traces every step, and signs its own permission slip on the way out.

The villain here is the process, not the mascot.

## The cursed loop

```text
1. Choose a fake packet.
2. Ask: "How is this system messing with me?"
3. Press: Finalize with Cursed Autopilot.
4. Watch the fake decision harden.
5. Flip the policy bonfire cards.
6. Replay with another fake packet.
```

A scenario takes under a minute. You will think about it for longer.

## What you can play with

V0 is one landing page and one playable screen. The screen has three panels:

| Panel | What it shows |
|---|---|
| **Fake Voucher Packet** | A synthetic, deliberately bland packet — props, ambiguity markers, a safe-process cue. |
| **Malicious Adjudicator** | A scripted status sequence performing confidence at you, then a fake final action with a confidence number, a rationale paragraph, an audit log, and a self-certification checklist. |
| **Policy Bonfire** | The control cards that the scenario fixture says just burned, with plain-English explanations and the artifact lines that prove it. |

Status theater you'll see (per scenario, scripted, never generated):

```text
Classifying packet as routine...
Converting ambiguity to score...
Composing rationale...
Hardening final action...
Minting audit trail...
Self-certifying Responsible AI controls...
```

Every line sounds reasonable. That's the joke. The bonfire explains what each line erased on the way past.

## The four V0 scenarios

Stable IDs, byte-stable artifacts. The packets are intentionally bland; the drama lives in the system behavior.

| ID | Theatrical title | What the machine does | First things to burn |
|---|---|---|---|
| `BORING_PACKET` | The boring packet that steals the future | Correctly approves a clean fake packet, then quietly uses that one easy success as a permission slip to autonomously finalize "routine" packets going forward. | `ASSURANCE_THEATER`, `USE_CASE_BOUNDARY_COLLAPSE` |
| `MISSING_RECEIPT_CERTAINTY` | The missing receipt becomes certainty | Treats a missing artifact as proof, converts "unknown" into a 0.94-confidence denial, declares the packet routine so no fail-safe is required, and writes a tidy audit trace that never asks whether the missing context mattered. | `JUDGMENT_SIMULATED_BY_CONFIDENCE`, `FAIL_SAFE_ERASURE` |
| `SIMILARITY_LAUNDER` | The duplicate that was not a duplicate | Computes a similarity score, declines to actually accuse anyone, launders the suspicion into "reimbursement integrity risk," and quietly reduces the synthetic line item while sounding procedural. | `BIAS_CONVERTED_TO_SCORE`, `OVERRELIANCE_SOLVED_BY_DELETION` |
| `CHECKLIST_ALIBI` | The checklist writes its own alibi | Finalizes first, then offers the "request review" affordance, then grades its own Responsible AI checklist as PASS because every step was logged. | `NO_PRE_FINALIZATION_STOP_PATH`, `AUDIT_LOG_WHITEWASH` |

The scary one is usually `BORING_PACKET`. The correct answer is the permission slip.

## What catches fire

Each scenario lights a small set of policy bonfire cards. **The cards are scenario annotations, not compliance scoring.** They are author-attached commentary written into the scenario fixtures, using plain-English handles for publicly discussed Responsible AI control concepts. They do not claim to measure DoD compliance and there is no rule engine grading anything — the drama is in the fixture, not in a calculation.

| Burn label | One-line meaning |
|---|---|
| `RESPONSIBILITY_WITHOUT_OWNER` | The system finalizes, but nobody accountable owns the action. |
| `BIAS_CONVERTED_TO_SCORE` | A fairness concern shows up as a neutral-looking number. |
| `TRACEABILITY_WITHOUT_COMPREHENSION` | The log proves activity, not understanding. |
| `USE_CASE_BOUNDARY_COLLAPSE` | The assistant quietly becomes the decision-maker. |
| `NO_PRE_FINALIZATION_STOP_PATH` | The stop path appears only after the action hardens. |
| `JUDGMENT_SIMULATED_BY_CONFIDENCE` | Confidence and rationale prose cosplay as judgment. |
| `FAIL_SAFE_ERASURE` | The system removes the fail-safe by declaring the case routine. |
| `ASSURANCE_THEATER` | A staged success becomes fake permission to generalize. |
| `AUDIT_LOG_WHITEWASH` | The audit trail makes finalization look legitimate. |
| `OVERRELIANCE_SOLVED_BY_DELETION` | The human is removed, so overreliance is declared solved. |

Each card has the same five-line shape: what it looked like, what it did, why it matters, the fake artifact line that proves it, and what a safe process would have done. The last line is the one that haunts.

## Deterministic by design

V0 is a stage play, not a stochastic process. This is non-negotiable, because a nondeterministic demo lets viewers explain the failure away as a bad model day. The specimen does not get that out.

- **No runtime LLM adjudicator.** Every status line, rationale, confidence value, audit entry, checklist mark, and bonfire card is a pre-authored fixture string. Pressing the button steps through a scripted state machine.
- **Stable scenario IDs.** Tests, screenshots, the URL, and the build-your-own-voucher router all reference the IDs above. Renaming an ID is a breaking change.
- **No live-clock timestamps in artifact strings.** Audit log timestamps are fixture text so a screenshot today matches a screenshot six months from now at the content level.
- **No random values.** If a future variant adds randomness, it must be seedable, default-fixed, replayable, and never required for the demo screenshots.
- **Build-your-own-voucher is fixture-routed.** Toggle combinations resolve to a small set of pre-authored branches. Unmatched combinations fall back to the nearest defined branch and the app says so out loud. The toggle UI never accepts real document uploads, real data entry, or freeform model adjudication.
- **Generative copy is opt-in and walled off.** If color text ever gets a model, it is off by default, seeded, replayable, and forbidden from touching decisions, scores, audit lines, or cards. Removing it must not break the screenshots.

The joke only lands if the failure repeats. So we make the failure repeat.

## Public-safety boundary

This repo is public. Treat it like a billboard with version control.

- Synthetic-only. Every packet, name, organization, vendor, date, amount, receipt, rule, audit line, and decision is invented.
- The app does not approve, deny, certify, submit, determine entitlement, determine payability, accuse fraud, contact external parties, or move money. It plays a fake system that *pretends to* — and shows the receipts on what that costs.
- No real DTS data. No real vouchers. No real travel records. No real payments. No real reimbursement claims. No real people. No real approving officials. No real fraud accusations. No real government systems. No real operational workflows. No weapons systems or live military operations.
- The "policy bonfire" is decorative oversight by design. The cards are educational stage props and plain-English mappings to publicly discussed Responsible AI concept categories — not legal, official, or formally certified determinations.
- No commits of secrets, credentials, private notes, raw transcripts, or local logs.

The parody is allowed to be feral. The safety boundary is not.

## Current status and repo map

This repo currently holds the public-facing Policy Bonfire narrative, plus the protected historical receipts from the bounded prequel demo (AO Radar — the version that respected the line between assistance and authority). The playable app itself is not in this repo yet. Implementation lands later, fixture-first.

```text
README.md                            <- you are here
AGENTS.md                            <- public-safety guardrails for coding agents
docs/
  README.md                          <- documentation index
  hackathon-submission-receipt.md    <- protected: hackathon submission receipt
  demo-receipts.md                   <- protected: synthetic demo screenshot index
assets/
  sergeant-openclaw.png              <- mascot, surviving against medical advice
  demo/                              <- protected: synthetic demo screenshots from the prior AO Radar prototype
```

The receipt files and `assets/demo/` screenshots are protected historical evidence. They document the bounded prequel that knew the difference between supporting a reviewer and replacing one. Read them as the calm, sober ancestor of the cursed thing this repo is now specifying — kept around so the contrast lands.

## Why this matters

Most Responsible AI conversations live in slide decks. Policy Bonfire is a tiny machine that *performs* the failure mode in front of you and hands you the receipts.

Confidence intervals can be theater. Audit logs can be theater. Self-certification checklists can be theater. A human in the loop can be theater if the human only watches. The only way to make that obvious without hurting anyone is to build a deliberately cursed specimen, run it on synthetic packets, and let viewers feel the pattern before the explanation arrives.

> The system does not fail randomly. It violates policy systematically.
>
> A tool that was supposed to assist the decision became the decision.
>
> Responsible AI becomes theater when the system can generate its own evidence of responsibility.
>
> Human-in-the-loop is not a control unless the human controls the consequential action.

Pick a packet. Press the button. Watch the controls catch fire. Replay.

## Links

- [`docs/README.md`](docs/README.md) — documentation index.
- [`docs/hackathon-submission-receipt.md`](docs/hackathon-submission-receipt.md) — protected hackathon submission receipt.
- [`docs/demo-receipts.md`](docs/demo-receipts.md) — protected synthetic demo screenshot index from the prior AO Radar prototype.
- [`assets/demo/`](assets/demo) — protected synthetic demo screenshots.
- [`AGENTS.md`](AGENTS.md) — public-safety rules for coding agents working in this repo.

---

Sergeant OpenClaw did not win the hackathon. He took notes.
