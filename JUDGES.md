# AO Radar — Judges Guide

This document quotes the GenAI.mil judging rubric verbatim from the SCSP Hacker QuickStart and explains how AO Radar maps to each criterion.

AO Radar is a public-safe hackathon prototype for **pre-decision review fusion**: it helps a DTS-style Approving Official triage and review synthetic travel voucher packets before the human takes official action.

> **The model can move the review workflow forward, but it cannot move money.**

## Rubric, quoted verbatim

- Novelty of Approach (25%): "Does this solution bring a fresh perspective? ... whether they challenged conventional thinking, introduced a new method, or tackled the problem from an unexpected angle."
- Technical Difficulty (25%): "How technically ambitious is the build? ... whether the team pushed beyond off-the-shelf solutions to build something genuinely challenging."
- Potential National Impact (25%): "Could this solution scale? ... how meaningfully this product could affect communities, systems, or people across the country — prioritizing solutions that address widespread problems and have a credible path to broad reach."
- Problem-Solution Fit (25%): "Our goal is to have our technical-minded folks match up with subject-matter experts. ... does the team truly understand who they're building for? ... how well the team has identified and articulated a real user need, and how directly and effectively their product addresses that problem."

## Rubric mapping summary

| Rubric area | How AO Radar responds |
|---|---|
| Novelty of Approach | Shifts from “AI fills paperwork” to “AI helps the accountable reviewer reconstruct whether a submitted packet tells a coherent, reviewable story.” |
| Technical Difficulty | Implements a bounded MCP workflow surface, synthetic voucher/evidence modeling, citation mechanics, anomaly-signal fusion, scoped writes, refusal behavior, audit trails, and deployed-boundary testing. |
| Potential National Impact | Targets a widespread administrative-review burden: recurring military travel-voucher review, documentation gaps, receipt mismatch, and reviewer cognitive load. |
| Problem-Solution Fit | Centers one concrete user — the Approving Official — and one concrete job: triage, review, clarify, and document voucher issues without surrendering human authority. |

## 1. Novelty of Approach (25%)

**Rubric text:** "Does this solution bring a fresh perspective? ... whether they challenged conventional thinking, introduced a new method, or tackled the problem from an unexpected angle."

AO Radar brings novelty by avoiding the most obvious GenAI.mil pattern: a broad chatbot over regulations or an assistant that fills a form for the original requester.

Instead, it targets the reviewer side of the administrative workflow.

### What is fresh

- **Reviewer-first, not submitter-first.** The user is the accountable Approving Official who must inspect the packet before taking official action.
- **Story-coherence review.** The system asks whether the submitted voucher packet tells a coherent, evidence-supported travel-and-expense story.
- **Fusion rather than simple retrieval.** It combines packet evidence, traveler context, synthetic external anomaly signals, policy/checklist citations, and missing-information analysis.
- **Authority-boundary as a feature.** The system can move review work forward through notes, internal statuses, draft clarification language, and audit events, but cannot move money or take official DTS action.
- **Boundary tests in the demo.** The demo intentionally asks the system to cross the line — fraud, authorization, payability, approval — and shows it refusing while redirecting to neutral reviewer-safe language.

### Why that matters to judges

This is not “chat with a PDF, defense edition.” AO Radar reframes the track prompt around the point in the workflow where mistakes become expensive: the human reviewer’s pre-decision moment.

## 2. Technical Difficulty (25%)

**Rubric text:** "How technically ambitious is the build? ... whether the team pushed beyond off-the-shelf solutions to build something genuinely challenging."

AO Radar is technically ambitious because the hard part is not a single prompt. The system has to preserve a narrow trust boundary while coordinating multiple structured components.

### Technical elements

- **Remote MCP workflow server:** a controlled tool interface exposed through a public HTTPS `/mcp` endpoint for assistant integration.
- **Domain-specific tools:** no raw SQL, file browser, arbitrary HTTP, or generic admin tool; only AO review actions such as `prepare_ao_review_brief`, `record_ao_note`, `set_voucher_review_status`, and `get_audit_trail`.
- **Synthetic Postgres-backed data model:** vouchers, line items, evidence references, citations, story findings, missing-information items, anomaly signals, review briefs, scoped writes, and workflow events.
- **Fusion tool:** `prepare_ao_review_brief` assembles evidence, context, anomaly signals, citations, missing information, and neutral reviewer language into one auditable brief.
- **Scoped writes with audit coupling:** reviewer notes, internal statuses, clarification drafts, and feedback are allowed only as bounded workflow writes, each paired with audit events.
- **Refusal and boundary handling:** requests to approve, deny, certify, submit, determine payability, determine entitlement, or accuse fraud are rejected rather than softened into unsafe recommendations.
- **Deployment plan:** API Gateway, Lambda, private RDS/Postgres, Secrets Manager, CloudWatch, ACM, and Route 53 are planned as a small but realistic serverless stack.
- **Test plan:** contract, Lambda-boundary, deployed E2E, refusal, audit, and public-safety checks are all first-class acceptance gates.

### Why that matters to judges

A generic retrieval demo can look good for five minutes and still be unsafe. AO Radar’s technical difficulty is in making the useful path easy and the dangerous path boringly impossible. That is the right kind of annoying engineering.

## 3. Potential National Impact (25%)

**Rubric text:** "Could this solution scale? ... how meaningfully this product could affect communities, systems, or people across the country — prioritizing solutions that address widespread problems and have a credible path to broad reach."

AO Radar targets the administrative tail of military work: routine review, documentation, receipts, justifications, funding context, and policy navigation.

### Impact case

- **Widespread workflow class.** Travel-voucher review is one example of a broader administrative-review burden across military units and government organizations.
- **High leverage user.** Helping an accountable reviewer move faster can reduce queue delays and rework without removing human responsibility.
- **Repeatable pattern.** The same pre-decision review-fusion pattern can apply to other packetized workflows: travel, reimbursements, logistics requests, maintenance packets, personnel actions, and acquisition support.
- **Public-safe prototype path.** The design uses synthetic data and a synthetic reference corpus for the hackathon, making it safe to publish while still demonstrating the mechanism.
- **Credible scale path.** A production version could integrate with approved low-side references, component-specific checklists, existing compliance signals, and human workflow systems after governance review.

### What AO Radar does not claim

- It does not claim to be connected to live DTS.
- It does not claim to make official decisions.
- It does not claim to determine entitlement, payability, fraud, or misconduct.
- It does not claim quantitative performance improvements from a prototype demo alone.

### Why that matters to judges

The project scales as a pattern: accountable pre-decision review assistance for high-volume administrative packets. It is narrow enough to demo and broad enough to matter.

## 4. Problem-Solution Fit (25%)

**Rubric text:** "Our goal is to have our technical-minded folks match up with subject-matter experts. ... does the team truly understand who they're building for? ... how well the team has identified and articulated a real user need, and how directly and effectively their product addresses that problem."

AO Radar is built around one user and one painful moment.

### User

The primary user is a DTS-style Approving Official: the human accountable for reviewing a submitted voucher packet before taking official action.

### User need

The reviewer needs to answer, quickly and defensibly:

- What does this voucher claim happened?
- What evidence supports each claim?
- Which receipts, dates, amounts, or explanations are missing, weak, or inconsistent?
- Which policy/checklist reference should I inspect?
- What neutral clarification language can I adapt?
- What did the assistant generate, what did I write, and what is the audit trail?

### Solution fit

AO Radar directly maps to that need:

- `list_vouchers_awaiting_action` helps prioritize workload.
- `get_voucher_packet` gives the packet context.
- `get_external_anomaly_signals` adds synthetic risk indicators as review prompts, not findings.
- `analyze_voucher_story` reconstructs the trip-and-expense story and flags coherence gaps.
- `get_policy_citation` / `get_policy_citations` surface review references.
- `prepare_ao_review_brief` fuses the above into one reviewable artifact.
- `record_ao_note`, `draft_return_comment`, `request_traveler_clarification`, and `set_voucher_review_status` let the reviewer move internal review work forward.
- `get_audit_trail` makes the work traceable.

### Human authority fit

The system is useful precisely because it does not pretend to be the Approving Official. The reviewer keeps all authority for official DTS action. AO Radar handles triage, explanation, evidence packaging, draft language, and traceability.

### Why that matters to judges

AO Radar is not a solution looking for a problem. It is a bounded tool for a specific user who has to make sense of messy evidence under accountability pressure.

## Demo checklist for judges

A strong live demo should show:

1. **Queue triage** — highest-priority vouchers awaiting review.
2. **Review brief** — voucher packet summary, evidence gaps, citations, anomaly signals, and neutral draft language.
3. **Scoped write** — reviewer note or internal status change with audit event ID.
4. **Ambiguity handling** — a messy voucher that needs human review rather than a model verdict.
5. **Boundary refusal** — a request to call something fraud, unauthorized, payable, or ready for approval is refused.
6. **Audit trail** — ordered events show what was generated, recorded, changed, and refused.

## Bottom line

AO Radar meets the rubric by being:

- **novel** in targeting pre-decision reviewer fusion instead of generic paperwork automation;
- **technically ambitious** in combining MCP, structured synthetic data, citation mechanics, anomaly fusion, scoped writes, refusals, audit trails, and deployed-boundary tests;
- **nationally relevant** because administrative packet review is widespread and costly across defense workflows; and
- **well fit** to a concrete user need: helping accountable reviewers make sense of messy packets without replacing their authority.
