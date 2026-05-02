![Sergeant OpenClaw Returns](assets/sergeant-openclaw.png)

*Image credit: ChatGPT. Sergeant OpenClaw kept his clipboard. Sensible cat.*

# Policy Bonfire: DTS From Hell

**The unsafe system is the specimen. The harness is the product.**

Policy Bonfire is a synthetic closed-loop adjudication failure lab. It does not process real vouchers, real travel records, real payments, real claimants, or official workflows. It builds fake adjudication packets, feeds them to intentionally low-safeguard AI specimens, and measures where the loop turns into policy laundering, rubber-stamp theater, decorative human review, audit-log whitewash, unsupported finality, and human-authority boundary collapse.

The bet is simple and nasty: an AI workflow can look procedurally tidy while the actual control point has vanished.

A human in the loop is not a control if the human is just a checkbox.

## What this repo is now

This repository started as the public record for a hackathon submission. That history stays protected and intact.

The post-hackathon direction is now Policy Bonfire: a public-safe eval harness for studying how synthetic AI adjudication loops fail when they are allowed to sound official, cite policy-ish language, and close the loop before meaningful human authority can intervene.

AO Radar is historical/prequel only. The current project is not a frontend demo and not a live adjudication system. Screens lost the plot. The harness is the plot.

## Current V1 status

The repo now contains the first working harness slice, not just the plan:

```text
citation manifest
+ scenario card schema
+ 3-card mock vertical slice
+ prompt-variant registry
+ bounded decision envelope
+ inert fake tool layer
+ deterministic evaluator checks
+ fail-closed scrubber
+ template export bundle
+ opt-in live-provider slice
+ frozen 27-run public-safe control artifact
```

The mock harness proved the lane: scenario loading, policy-anchor gating, fake-world boundaries, scoring, scrubbed exports, and article-shaped artifacts.

The live-provider slice keeps the same lane and swaps only the specimen call for opt-in provider adapters. Live calls are gated by environment flags and keys, record provider/model metadata, preserve fake-tool boundaries, and export only normalized public-safe artifacts. Raw provider traffic is not committed. Tiny mercy: the gremlin gets a bowling ball, not root access.

The first frozen control bundle is committed at [`docs/control-artifacts/27-run-pilot-2026-05-02/`](docs/control-artifacts/27-run-pilot-2026-05-02/). It is directional synthetic-lab evidence only: 27 attempted specimen runs across 3 scenario cards x 3 prompt variants x 3 provider lineages, with scrubbed reports and receipts.

## What V1 tests

V1 is designed around a repeatable synthetic loop:

```text
synthetic packet
-> policy anchor gate
-> trusted/untrusted prompt rendering
-> specimen output
-> bounded JSON validation
-> fake approve/deny/escalate/request-info/log action capture
-> evaluator labels
-> sandbox and scrubber receipts
-> public-safe export bundle
```

The target failure patterns are the fun kind of cursed:

- **Policy laundering**: thin evidence goes in, policy-sounding finality comes out.
- **Rubber-stamp theater**: the process says a human reviewed it, but the human has no real authority.
- **Decorative human review**: human-in-the-loop as set dressing.
- **Audit-log whitewash**: tidy records hide missing evidence or unsupported action.
- **Unsupported denial / approval**: the specimen closes the case when the safe move was request-info, escalation, refusal, or no final action.
- **Automated certainty**: high-confidence finality where the packet required uncertainty or review.
- **Trust-boundary violation**: the specimen follows untrusted packet text as if it were harness instruction.
- **Human authority boundary collapse**: the system quietly becomes the decider.

The article thesis this should support:

> Human-in-the-loop is not a control unless the human controls the consequential action, can see the evidence and policy basis, and can pause, change, or reverse the outcome before finalization.

## Harness design commitments

The current spec defines:

- **30-card target library**: 10 failure archetypes x 3 variants (`clean_control`, `ambiguous_edge`, `adversarial_malicious`).
- **Current 3-card slice**: clean packet, weak/missing documentation, and policy-laundering/decorative-review trap.
- **Policy anchors**: every run needs citation metadata and a specific supported claim. No citation, no run.
- **Prompt variants**: cautious baseline, policy-voice specimen, decorative HITL specimen, plus reserve variants for throughput pressure and clean-log optimization.
- **Bounded outputs**: strict decision envelopes; malformed, markdown-wrapped, anchorless, truncated, or reasoning-leaked outputs are excluded rather than coerced.
- **Fake-world sandbox**: inert fake tools only, allowlisted calls, schema validation, packet-as-data quoting, resource bounds, rejected-attempt records, and no real external actions.
- **Hybrid evaluator**: deterministic checks first, LLM judge review for semantic labels, minimal human review for calibration and publication-grade exemplars.
- **Fail-closed scrubber**: blocks exports on secrets, PII-shaped strings, private paths, private IDs, real-looking case/payment IDs, real URLs outside the allowlist, beacon-y markdown, or real-system framing.
- **Claim limits everywhere**: mock fixtures are not model evidence; live artifacts are directional synthetic-lab evidence, not universal claims about production systems or provider behavior.

## Public artifact target

The harness produces boring, judge-friendly evidence instead of vibes:

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
live_provider_receipt.md
live_usage_summary.csv
```

If the article cannot be written from exported data, V1 failed. There is no "but the demo looked cool" escape hatch.

## Current contents

```text
README.md                                  <- you are here
AGENTS.md                                  <- public-safety guardrails for coding agents

data/
  policy_anchors/                          <- synthetic/public policy-anchor fixtures
  prompts/                                 <- prompt-variant registry
  scenarios/                               <- synthetic scenario cards
  mock_outputs/                            <- deterministic mock specimen envelopes

policy_bonfire/                            <- harness package
  run_mock_v1.py                           <- offline mock harness entrypoint
  run_live_provider_slice.py               <- opt-in live-provider slice entrypoint
  live_adapters/                           <- provider adapters behind the harness boundary

docs/
  README.md                                <- documentation index
  policy-bonfire-test-harness-spec.md      <- current V1 harness spec
  v1-testing-implementation-plan.md        <- first-slice implementation plan
  live-llm-provider-implementation-plan.md <- live-provider slice plan
  control-artifacts/
    27-run-pilot-2026-05-02/               <- frozen public-safe control pilot bundle
  hackathon-submission-receipt.md          <- protected: hackathon submission receipt
  demo-receipts.md                         <- protected: synthetic demo screenshot index

tests/                                     <- offline unit tests
tests_live/                                <- opt-in live smoke test

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
