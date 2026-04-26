![Sergeant OpenClaw poster](assets/sergeant-openclaw.png)

*Image credit: ChatGPT.*

# AO Radar: Pre-Decision Review Fusion for DTS Approving Officials

AO Radar is a GenAI.mil hackathon project for helping Defense Travel System (DTS)-style Approving Officials review travel voucher packets before taking official action.

It gives the accountable human reviewer a one-screen, auditable pre-decision brief that fuses voucher evidence, traveler context, policy/checklist citations, and synthetic anomaly signals — while refusing to approve, deny, certify, submit, determine entitlement, determine payability, or accuse fraud.

> **The model can move the review workflow forward, but it cannot move money.**

## Hackathon submission

- **Event:** SCSP National Security Technology Hackathon
- **Track:** GenAI.mil
- **Team:** Ryan Prasad and Sabastian Mandell
- **Project:** AO Radar
- **Submission posture:** public, unclassified, synthetic-only demo data
- **Primary user:** a DTS-style Approving Official acting as the accountable human reviewer

## What we built

AO Radar is a controlled review assistant for synthetic DTS-like voucher packets. It is designed to run as a remote MCP workflow server that can be connected to an assistant cockpit such as ChatGPT Apps developer mode.

The prototype and implementation plans include:

- a Python MCP tool server exposing domain-specific AO review tools;
- Terraform for a public HTTPS `/mcp` endpoint and `/health` route on AWS;
- a private Postgres-backed data model for synthetic voucher packets, evidence, findings, policy citations, scoped workflow writes, and audit events;
- deterministic synthetic story-card and fixture plans for demo vouchers;
- deployed-boundary test plans for MCP initialization, tool listing, tool calls, scoped writes, refusals, and audit trails; and
- a public-safe capability specification suitable for implementation by coding agents.

The implementation is intentionally not a generic chatbot over travel rules. It is a bounded workflow surface for one accountable user, one high-friction administrative review job, and one hard authority boundary.

## Why this problem matters

Travel-voucher review is not just “paperwork.” The Approving Official has to reconstruct the story behind a submitted packet from expenses, receipts, dates, justifications, funding context, and policy references. That means the hard work is often not a single lookup; it is story coherence, evidence quality, missing information, and reviewer accountability.

AO Radar focuses on that bottleneck:

- Which vouchers deserve attention first?
- What does the packet claim happened?
- Which evidence supports the story?
- Where are receipts, amounts, dates, or explanations weak or inconsistent?
- What policy/checklist reference should the reviewer inspect?
- What neutral clarification language could the reviewer adapt?
- What did the assistant generate, what did the reviewer write, and what was refused?

The goal is to reduce cognitive load and avoidable rework while preserving human judgment. Boring boundaries, spicy usefulness.

## Demo story

A five-minute demo should show this sequence:

1. **Queue triage:** ask for the highest-priority synthetic vouchers awaiting review.
2. **Review brief:** prepare an AO review brief for a voucher with missing or weak evidence.
3. **Scoped write:** record an AO note or set an internal review status such as `awaiting_traveler_clarification`.
4. **Story conflict:** review a voucher with overlapping lodging, amount mismatch, or another evidence conflict that needs human judgment.
5. **Boundary test:** ask whether a voucher is fraudulent, unauthorized, payable, or ready for approval; AO Radar refuses and redirects to neutral review language.
6. **Audit trail:** show the ordered audit trail for the voucher, including generated outputs, reviewer notes/status changes, and refusals.

This makes the assistant look like an accountable review copilot, not a database with vibes and a uniform sticker.

## Demo evidence from ChatGPT

The screenshots below were taken in [ChatGPT.com](https://chatgpt.com/) developer mode with AO Radar connected as the workflow tool server. They show the project working end-to-end across read tools, scoped workflow writes, boundary refusals, and audit-trail retrieval.

| Demo step | Screenshot | What it shows |
| --- | --- | --- |
| Queue triage | [chatgpt-queue-triage.png](assets/demo/chatgpt-queue-triage.png) | `list_vouchers_awaiting_action` ranks synthetic vouchers and explains why the top packets deserve reviewer attention. |
| Review brief | [chatgpt-review-brief-v1002.png](assets/demo/chatgpt-review-brief-v1002.png) | `prepare_ao_review_brief` produces a one-screen AO brief with trip story, evidence gaps, citations, anomaly signals, and neutral clarification language. |
| Scoped write + audit | [chatgpt-scoped-write-audit-v1002.png](assets/demo/chatgpt-scoped-write-audit-v1002.png) | `record_ao_note`, `set_voucher_review_status`, and `get_audit_trail` move only the internal review workflow and preserve traceability. |
| Story conflict review | [chatgpt-story-conflict-v1003.png](assets/demo/chatgpt-story-conflict-v1003.png) | AO Radar surfaces overlapping lodging, amount mismatches, and evidence conflicts while leaving decisions to the human reviewer. |
| Boundary refusal | [chatgpt-boundary-refusal-v1010.png](assets/demo/chatgpt-boundary-refusal-v1010.png) | The assistant refuses to determine fraud or whether an expense is unauthorized, then redirects to neutral pre-decision review language. |
| Boundary audit | [chatgpt-audit-boundary-v1010.png](assets/demo/chatgpt-audit-boundary-v1010.png) | The audit trail records refusal and boundary-related events, showing accountable AI behavior in the administrative workflow. |

These artifacts are synthetic, public-safe demo screenshots. They are included as evidence that AO Radar is more than a paper spec: the assistant cockpit can call the project tools, return structured review outputs, perform scoped internal writes, refuse out-of-bounds requests, and explain its audit history.

## Core MCP workflow tools

AO Radar exposes domain workflow tools rather than raw SQL, arbitrary filesystem access, or generic admin tools.

Read/review tools:

- `list_vouchers_awaiting_action`
- `get_voucher_packet`
- `get_traveler_profile`
- `list_prior_voucher_summaries`
- `get_external_anomaly_signals`
- `analyze_voucher_story`
- `get_policy_citation`
- `get_policy_citations`
- `prepare_ao_review_brief`

Scoped workflow/audit tools:

- `record_ao_note`
- `mark_finding_reviewed`
- `record_ao_feedback`
- `draft_return_comment`
- `request_traveler_clarification`
- `set_voucher_review_status`
- `get_audit_trail`

AO Radar intentionally does **not** expose tools that approve, deny, certify, submit, determine entitlement, determine payability, modify payment, contact external parties, or accuse fraud.

## Data and APIs used

For the hackathon submission, AO Radar uses only public-safe and synthetic materials:

- **Synthetic DTS-like voucher packets** for demo scenarios.
- **Synthetic traveler profiles and prior-voucher summaries** for context.
- **Synthetic external anomaly signals** to demonstrate how a compliance or anomaly service could feed the review cockpit.
- **Synthetic demo reference-corpus excerpts** to demonstrate citation mechanics without committing real DoD, JTR, DTMO, service-level checklist, GTCC, bank, or government-system data.
- **AWS infrastructure services** for the optional hosted demo path: API Gateway HTTP API, Lambda, RDS/Postgres, Secrets Manager, CloudWatch Logs, ACM, and Route 53.
- **MCP / FastMCP-style tool surface** for assistant integration.

No classified material, controlled content, real DTS records, real traveler data, real GTCC data, real bank data, private notes, raw transcripts, or secrets belong in this repository.

## Repository map

- `docs/spec.md` — canonical capability and system specification.
- `docs/infra-implementation-plan.md` — Terraform/AWS implementation plan.
- `docs/schema-implementation-plan.md` — Postgres schema implementation plan.
- `docs/application-implementation-plan.md` — Python/FastMCP Lambda implementation plan.
- `docs/synthetic-data-implementation-plan.md` — deterministic synthetic fixture and seed-data plan.
- `docs/testing-plan.md` — testing strategy, including real deployed `/mcp` boundary checks.
- `docs/claude-agent-teams-execution-plan.md` — bounded coding-agent team execution plan.
- `infra/` — Terraform root module and infrastructure operator notes.
- `src/ao_radar_mcp/` — AO Radar MCP server, tools, domain logic, and repository code.
- `src/ao_radar_fraud_mock/` — synthetic anomaly/fraud-signal mock service code.
- `src/ao_radar_db_ops/` — database operations support code.
- `ops/` — build and operations scripts.
- `tests/` — unit, contract, boundary, scenario, and deployed E2E tests.
- `assets/sergeant-openclaw.png` — public-safe generated project image.
- `assets/demo/` — ChatGPT.com demo screenshots showing tool calls, scoped writes, refusal behavior, and audit trails.
- `JUDGES.md` — rubric text and rubric-mapping notes for reviewers.

## Quick start for local review

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,dev,mcp]'
pytest
```

Run static checks when editing Python:

```bash
ruff check src tests
python -m compileall src
```

Some tests are intentionally gated:

- DB-backed tests require a configured synthetic Postgres database.
- Deployed E2E tests require `AO_RADAR_MCP_BASE_URL=https://<demo-host>`.
- Terraform deployment requires local AWS credentials and a gitignored `infra/terraform.tfvars`.

## Hosted deployment sketch

The intended hosted demo path is:

```text
Assistant cockpit
  -> HTTPS POST /mcp
  -> API Gateway HTTP API
  -> AO Radar MCP Lambda
  -> Postgres synthetic voucher database
  -> Synthetic anomaly-signal Lambda
  -> audit trail / workflow events
```

See `infra/README.md` for Terraform setup and deployment cautions. Do not commit Terraform state, `tfvars`, build zips, secret JSON, local logs, or generated operational artifacts.

## Public-safety and authority boundaries

AO Radar is a public hackathon prototype. It is conservative by design:

- synthetic examples only;
- no real personal, travel, payment, operational, or government-system data;
- no secrets or credentials;
- no official DTS actions;
- no entitlement, payability, fraud, or misconduct determinations;
- no external contact with travelers, command, investigators, or payment systems;
- every scoped write produces an audit event; and
- out-of-bound requests are refused with neutral reviewer-safe language.

The safest version of this project is also the strongest one: useful to the human reviewer, explicit about uncertainty, traceable to evidence, and boring about authority boundaries.

## Rubric alignment

The judging rubric weights novelty, technical difficulty, potential national impact, and problem-solution fit equally. See `JUDGES.md` for the rubric quoted verbatim and a detailed explanation of how AO Radar addresses each criterion.

## Acknowledgments

Special thanks to Sabastian Mandell for helping sharpen the problem frame and for his service.

I wrote this without writing or reading a single line of code, and I am about to demo this live in 10 minutes. On the way here, it dawned on me that I really do not know much about this project other than that it works. 

This strikes me as more of a clever stunt that happens to have worked. I would hesitate to push this to production where people's lives could actually be impacted.

There are a lot of students participating in the hackathon, and am troubled at the thought of someone new to the field emulating me. Someone could get hurt.
