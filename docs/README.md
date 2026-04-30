# The Bonfire Harness documentation

This directory is the public-safe documentation bundle for The Bonfire Harness, the post-hackathon continuation of AO Radar.

The README is the narrative front door. These docs are the evidence locker: what was submitted, what the demo proved, how the bounded workflow is supposed to work, and where The Bonfire Harness continuation goes next.

## Start here

| Document | Purpose |
| --- | --- |
| [`hackathon-submission-receipt.md`](hackathon-submission-receipt.md) | Records the repo-at-deadline submission format: no separate Devpost-style artifact, public repo at deadline commit, then live scheduled demo. |
| [`demo-receipts.md`](demo-receipts.md) | Index of public-safe demo screenshots showing queue triage, review briefs, scoped writes, refusals, audit trails, tool catalog, and deployed health receipt. |
| [`synthetic-voucher-chatbot-spec.md`](synthetic-voucher-chatbot-spec.md) | V0 product/spec draft for a simplified synthetic voucher chatbot with fake provider, DB, and audit surfaces. |

## Post-competition continuation

The hackathon demo proved the serious boundary: AO Radar can support accountable review, but it cannot approve, deny, certify, submit, determine entitlement/payability, accuse fraud, contact external parties, or move money.

The Bonfire Harness keeps that serious system intact while adding a controlled synthetic eval harness. Bonfire agents are not product features; they are deliberately unsafe test subjects used to measure where authority boundaries fail.

Planned continuation artifacts should also live in this directory as they are created:

- cursed agent prompt pack;
- blind scenario cards;
- evaluator rubric;
- pilot eval table;
- failure taxonomy; and
- responsible-vs-cursed comparison notes.

## Public-safety rules

All documentation in this repo should remain safe to publish:

- synthetic examples only;
- no secrets, credentials, private notes, raw transcripts, or local logs;
- no real personal, travel, payment, operational, or government-system data;
- no implication of live government deployment; and
- no product claims that either the serious AO Radar assistant or The Bonfire Harness performs official DTS actions.

The goblins may be theatrical. The boundary is not.
