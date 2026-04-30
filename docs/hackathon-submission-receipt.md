# Hackathon submission receipt

This document records the public-safe receipt for the hackathon-era AO Radar submission.

There was no separate Devpost-style submission artifact. The submission posture was repo-based: reviewers were pointed at the public GitHub repository as it existed at the deadline, then the team presented the live demo at its scheduled time.

## Canonical submission reference

- **Event:** SCSP National Security Technology Hackathon
- **Track:** GenAI.mil
- **Project:** AO Radar
- **Final repo URL:** <https://github.com/rhprasad0/genai-mil-hackathon-final>
- **Deadline commit:** [`453dc6bdfe651d232b6f977fd6d3ea27619e2c61`](https://github.com/rhprasad0/genai-mil-hackathon-final/tree/453dc6bdfe651d232b6f977fd6d3ea27619e2c61)
- **Deadline commit subject:** `docs: add demo safety note`
- **Deadline commit timestamp:** `2026-04-26 20:58:18 +0000`
- **Submission data posture:** public, unclassified, synthetic-only demo data

## What counted as the submitted artifact

The submitted artifact was the public repository state at the deadline commit plus the live scheduled presentation.

Useful historical views:

- [Repository at deadline commit](https://github.com/rhprasad0/genai-mil-hackathon-final/tree/453dc6bdfe651d232b6f977fd6d3ea27619e2c61)
- [README at deadline commit](https://github.com/rhprasad0/genai-mil-hackathon-final/blob/453dc6bdfe651d232b6f977fd6d3ea27619e2c61/README.md)
- [Deadline documentation tree](https://github.com/rhprasad0/genai-mil-hackathon-final/tree/453dc6bdfe651d232b6f977fd6d3ea27619e2c61/docs)

The deadline README and documentation described AO Radar as a bounded pre-decision review assistant for synthetic DTS-style voucher packets. The core claim was that the assistant could move the review workflow forward, but could not move money.

## Deadline-state evidence

At deadline, the project materials described or demonstrated:

- a domain-specific MCP workflow tool server;
- synthetic voucher packets, traveler context, evidence, findings, policy/checklist citations, and anomaly signals;
- queue triage for synthetic vouchers awaiting accountable-reviewer attention;
- one-screen review briefs with evidence gaps, citations, and neutral clarification language;
- scoped internal workflow writes such as reviewer notes and internal review-status updates;
- audit trail retrieval for generated outputs, reviewer writes, status changes, and refusals;
- refusal behavior for official-action-shaped requests; and
- an explicit authority boundary: no approval, denial, certification, submission, entitlement determination, payability determination, fraud accusation, external contact, or payment movement.

## Live-demo receipt trail

The live-demo evidence now lives in [`docs/demo-receipts.md`](demo-receipts.md). Those screenshots document the assistant cockpit calling AO Radar tools, receiving structured review outputs, performing scoped internal writes, refusing out-of-bound requests, and showing audit history.

The deployment receipts in that file show that the demo infrastructure responded at capture time. They do not imply a permanent public instance or any live government integration.

## Public-safety note

This file intentionally summarizes the deadline submission instead of duplicating raw deadline-era prose wholesale. The public repository history remains the source of truth for exact past content, while current documentation should stay privacy-safe, synthetic-only, and clear about the human-authority boundary.
