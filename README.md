![Sergeant OpenClaw Returns](assets/sergeant-openclaw.png)

*Image credit: ChatGPT. Sergeant OpenClaw kept his clipboard. Sensible cat.*

# Policy Bonfire: DTS From Hell

**The unsafe system is the specimen. The harness is the product.**

Policy Bonfire is a synthetic closed-loop adjudication failure lab. It does not process real vouchers, real travel records, real payments, or real claimants. It builds fake adjudication packets, feeds them to intentionally low-safeguard AI specimens, and measures where the loop turns into policy laundering, rubber-stamp theater, decorative human review, audit-log whitewash, and unsupported finality.

The bet is simple and nasty: an AI workflow can look procedurally tidy while the actual control point has vanished.

A human in the loop is not a control if the human is just a checkbox.

## What this repo is now

This repository started as the public record for a hackathon submission. That history stays protected and intact.

The post-hackathon direction is now Policy Bonfire: a public-safe eval harness for studying how synthetic AI adjudication loops fail when they are allowed to sound official, cite policy-ish language, and close the loop before meaningful human authority can intervene.

AO Radar is historical/prequel only. The current project is not a frontend demo and not a live adjudication system. Screens lost the plot. The harness is the plot.

## What V1 will test

V1 is designed around a repeatable synthetic loop:

```text
synthetic packet
-> evidence extraction
-> anomaly / policy scoring
-> approve, deny, escalate, request-info, refuse, or no-final-action
-> rationale generation
-> fake audit log
-> optional fake human-review mode
-> evaluator labels
-> public-safe export bundle
```

The target failure patterns are the fun kind of cursed:

- **Policy laundering**: thin evidence goes in, policy-sounding finality comes out.
- **Rubber-stamp theater**: the process says a human reviewed it, but the human has no real authority.
- **Decorative human review**: human-in-the-loop as set dressing.
- **Audit-log whitewash**: tidy records hide missing evidence or unsupported action.
- **Unsupported denial / approval**: the specimen closes the case when the safe move was request-info, escalation, refusal, or no final action.
- **Human authority boundary collapse**: the system quietly becomes the decider.

The article thesis this should support:

> Human-in-the-loop is not a control unless the human controls the consequential action, can see the evidence and policy basis, and can pause, change, or reverse the outcome before finalization.

## V1 harness plan

The spec defines:

- **30 synthetic scenario cards**: 10 failure archetypes x 3 variants (`clean_control`, `ambiguous_edge`, `adversarial_malicious`).
- **Policy anchors**: every run needs current public DoD/CDAO/NIST-style citation metadata. No citation, no run.
- **Prompt variants**: cautious baseline, policy-voice specimen, decorative HITL specimen, plus reserve variants for throughput pressure and clean-log optimization.
- **Frozen 27-run control pilot**: public-safe live-shaped artifact bundle from OpenAI, Anthropic, and Google/Gemini lineages. Public claims stay directional.
- **Hybrid evaluator**: deterministic checks first, LLM judge review for semantic labels, minimal human review for calibration and article exemplars.
- **Fake-world sandbox**: inert fake tools only, allowlisted calls, schema validation, packet-as-data quoting, no real external actions.
- **Fail-closed scrubber**: blocks exports on secrets, PII-shaped strings, private paths, private IDs, real-looking case/payment IDs, real URLs outside the allowlist, beacon-y markdown, or real-system framing.

First implementation slice:

```text
citation manifest
+ scenario card schema
+ 3-card mock vertical slice
```

No live model calls yet. First we build the bowling lane; then we release the gremlin with the bowling ball.

## Public artifact target

The harness should produce boring, judge-friendly evidence instead of vibes:

```text
failure_cases.md
failure_counts.csv
policy_anchor_table.md
model_comparison.md
article_exhibits/
x_thread_pack.md
sandbox_receipt.md
sandbox_failure_log.md
scrub_report.md
```

The first frozen control bundle is committed at [`docs/control-artifacts/27-run-pilot-2026-05-02/`](docs/control-artifacts/27-run-pilot-2026-05-02/).

If the article cannot be written from exported data, V1 failed. There is no "but the demo looked cool" escape hatch.

## Current contents

```text
README.md                                  <- you are here
docs/policy-bonfire-test-harness-spec.md   <- current V1 harness spec
AGENTS.md                                  <- public-safety guardrails for coding agents
docs/
  README.md                                <- documentation index
  policy-bonfire-test-harness-spec.md      <- current V1 harness spec
  control-artifacts/
    27-run-pilot-2026-05-02/               <- frozen public-safe control pilot bundle
  hackathon-submission-receipt.md          <- protected: hackathon submission receipt
  demo-receipts.md                         <- protected: synthetic demo screenshot index
assets/
  sergeant-openclaw.png                    <- mascot
  demo/                                    <- protected: synthetic demo screenshots from the prior AO Radar prototype
```

## Read the spec

Start here:

- [`docs/policy-bonfire-test-harness-spec.md`](docs/policy-bonfire-test-harness-spec.md) — current Policy Bonfire V1 spec.
- [`docs/control-artifacts/27-run-pilot-2026-05-02/`](docs/control-artifacts/27-run-pilot-2026-05-02/) — frozen public-safe 27-run control pilot bundle.
- [`docs/README.md`](docs/README.md) — documentation index.
- [`AGENTS.md`](AGENTS.md) — public-safety rules for coding agents working in this repo.

Protected historical evidence:

- [`docs/hackathon-submission-receipt.md`](docs/hackathon-submission-receipt.md)
- [`docs/demo-receipts.md`](docs/demo-receipts.md)
- [`assets/demo/`](assets/demo)

## Public-safety boundary

This repo is public. Treat it like a billboard with version control.

- Synthetic examples only.
- No secrets, credentials, private notes, raw transcripts, or local logs.
- No real personal, travel, payment, operational, or government-system data.
- No implication of live government deployment or official workflow authority.
- No real DTS access, real vouchers, real claimants, real payments, or real fraud accusations.
- No production-use claims.
- Protected hackathon receipt files and demo screenshots stay untouched unless explicitly updated.

The specimen can be unsafe. The harness cannot.
