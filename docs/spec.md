# Defense Travel System Travel Voucher Review Radar for Approving Officials

A capability and system specification for a public-safe, human-in-the-loop assistant
that helps an Approving Official review submitted Defense Travel System (DTS) travel
vouchers before taking official action.

This document is implementation-neutral. It describes what the system must do, must
not do, must expose, and must guarantee, so that a coding agent or implementation
team can build a comparable assistant on the stack of their choice.

---

## Public-Safe Summary

The Defense Travel System Travel Voucher Review Radar for Approving Officials
(referred to in this document as "the Voucher Review Radar" or "the Radar")
is a pre-decision review aid for DoD Approving Officials who must inspect
submitted travel voucher packets before deciding what official action to take
inside DTS.

The Radar reads a voucher packet, reconstructs an internally coherent
travel-and-expense story, compares that story to the submitted evidence, and
produces a structured review brief: highlighted breaks in coherence, missing
or weak evidence, possible clarification or return considerations, citations
into an approved reference repository, needs-human-review labels, and a draft
clarification note the reviewer can adapt.

The Radar is explicitly bounded as a triage and evidence-packaging aid. It does
not approve, deny, certify, return, cancel, amend, or submit any DTS document.
It does not determine entitlement, decide whether a claimed expense is payable,
or accuse fraud. The accountable Approving Official remains the human
decision-maker.

---

## 0. Concept Snapshot

| Field | Value |
|---|---|
| Working concept name | Defense Travel System Travel Voucher Review Radar for Approving Officials |
| One-sentence concept | A controlled, public-safe assistant that helps an Approving Official triage a submitted DTS travel voucher packet by surfacing story-coherence breaks, missing evidence, possible clarification or return considerations, and policy-reference hooks, while preserving full human DTS action authority. |
| Primary user | A DTS Approving Official acting as the accountable human reviewer of a submitted voucher packet. |
| Workflow target | Pre-decision review of one submitted DTS travel voucher packet at a time, with optional queue-level prioritization across pending packets. |
| Environment assumption | Public-safe / unclassified prototype using synthetic voucher data. No live DTS integration. No real PII. No real Government Travel Charge Card data. |
| Out of scope | Approving, denying, certifying, returning, cancelling, amending, or submitting any DTS document; recommending the official disposition of a voucher; determining entitlement or payability; accusing fraud; processing real traveler data; replacing existing post-approval compliance tooling; pretending to be deployed inside DTS. |

---

# 1. CV-1 — Capability Vision

## 1.1 Capability Name

Pre-decision travel voucher review assistance for accountable Approving Officials.

## 1.2 Vision

Enable an Approving Official to convert a submitted travel voucher packet into a
structured, reviewable picture of what the packet claims, what evidence supports
each claim, where the story breaks, and what the reviewer should ask before
taking official action — without bypassing the human DTS action chain or the
reviewer's accountable judgment.

## 1.3 Strategic Problem

The Approving Official is the accountable human reviewer for a submitted DTS
voucher packet. Public DoD oversight, DTMO, and service-level materials identify
travel pay as a recurring review and improper-payment risk area, especially
where documentation, receipt validity, claimed amounts, dates, locations,
justifications, and funding context do not line up cleanly. Those public sources
also carry caveats: estimates, failure distributions, and local return patterns
should not be generalized beyond their stated source without validation.

In many units, voucher review may be one duty among many rather than a dedicated
finance billet. The cognitive load is therefore shaped less by simple field
validation alone and more by audit-style reconstruction: the reviewer must
rebuild a coherent travel-and-expense story from receipts, declared line items,
free-text justifications, and policy or funding context that may not be obvious
from the packet itself. Public checklist materials and practitioner-facing
guidance repeatedly point reviewers toward the same review surfaces: missing
dates, inconsistent details, unexplained amounts, duplicate or repeated charges,
lodging and transportation documentation, and cash, ATM, or currency-exchange
items that require supporting math. Doing that consistently across a queue of
packets, while preserving human accountability, is the strategic gap this
capability addresses.

## 1.4 Desired Future State

When the capability is in place:

- An Approving Official can open a submitted voucher packet and immediately see a
  one-screen review brief organized around story coherence, evidence quality,
  policy-reference hooks, and a prioritized reviewer worklist.
- Each flagged issue is traceable to a source within the packet or within an
  approved reference repository, with the underlying excerpt visible alongside
  the flag.
- Missing-information items are listed explicitly, so the reviewer can decide
  to request them rather than infer them.
- A draft clarification or possible return-comment note is available as a
  non-official starting point that the reviewer edits, adapts, or discards
  before any official action.
- Authority to approve, deny, return, cancel, amend, certify, or submit remains
  entirely with the human Approving Official inside DTS.
- The reviewer can prioritize a queue of pending packets by composite review
  difficulty and evidence-gap indicators, without the system implying that any
  packet is approved, denied, payable, or ready for return.

## 1.5 Capabilities Needed

- **Intake of a submitted voucher packet** in a structured form, including the
  declared trip, declared expenses, attached receipts, justifications,
  funding references, and any pre-existing flags.
- **Story reconstruction** that compares the declared trip and expenses to the
  attached evidence, builds an internally coherent trip-and-expense narrative,
  and highlights breaks between declared, expected, and observed facts without
  treating the narrative as an entitlement determination.
- **Evidence quality assessment** for receipts and supporting documentation,
  including presence, legibility, itemization, payment evidence, and
  alignment with the claimed line item.
- **Coherence and anomaly checks** for dates, locations, amounts, duplicates,
  multiple-charge patterns, cash and currency-exchange edge cases, and
  expense-versus-trip-window alignment.
- **Controlled retrieval** from an approved reference repository (policy
  excerpts, traveler regulation paragraphs, service-level checklists, valid
  receipt definitions, and similar publicly approved sources) to support
  policy-facing flags and prompts with source hooks the reviewer can verify.
- **Missing-information detection** that converts gaps into an explicit
  checklist of what the packet does not yet show.
- **Reviewer-prompt drafting**: short, neutral, draft language the reviewer
  can adapt into a clarification request or possible return comment, without
  directing the reviewer toward an official disposition.
- **Queue prioritization** across pending packets by composite review difficulty
  and evidence-gap indicators, framed as workload guidance only.
- **Provenance, citation, and uncertainty display** so the reviewer always
  sees the basis for any flag, the references used, and the system's
  confidence in the assessment.
- **Needs-human-review labeling** for ambiguous, unsupported, conflicting, or
  low-confidence items that the system cannot responsibly characterize.
- **Audit logging** of inputs, retrievals, generated outputs, reviewer edits,
  refusals, needs-human-review labels, and exports.
- **Refusal behavior** when a packet, a question, or a requested action is
  outside the supported workflow or outside the controlled trust boundary.

## 1.6 Measurable Benefits

- Reduce time to first informed review pass per submitted packet by giving the
  reviewer a one-screen brief instead of a sequential walk through every
  screen of the packet.
- Reduce rework caused by evidence and documentation gaps by surfacing those
  gaps before the reviewer takes any official DTS action.
- Improve reviewer confidence and consistency by anchoring each flag to a
  visible source excerpt and an editable clarification draft.
- Improve queue throughput by allowing reviewers to sequence pending packets
  by composite review difficulty rather than only by submission order.
- Preserve and reinforce human DTS action authority by keeping every official
  action outside the system.

These benefits are stated as design intent. Measurement requires a held-out
synthetic evaluation set and reviewer-in-the-loop study; quantitative claims
should not be made from prototype demonstrations alone.

## 1.7 Time Horizon

- **Prototype (hackathon scope)**: A single-reviewer demonstration that
  ingests a synthetic voucher packet, produces a review brief with at least
  one citation, surfaces missing-information items, drafts a clarification
  note, and exposes refusal behavior on out-of-scope inputs.
- **Pilot (30–90 days)**: Multi-packet queue prioritization, evaluation against
  a labeled synthetic corpus, configurable rule sets per component, audit
  logging suitable for after-action review, and reviewer-feedback capture.
- **Scaled capability (6–12 months)**: Component-tunable rule sets validated
  with subject-matter experts, integration-readiness review against any
  approved environment, approved comparison or handoff patterns for existing
  post-approval compliance workflows, and a reviewer-training package.

## 1.8 Capability Guardrails

- The capability does **not** approve, deny, certify, return, cancel, amend,
  or submit any DTS document.
- The capability does **not** determine entitlement under the Joint Travel
  Regulations or any equivalent policy authority, and does not decide whether
  a claim is payable or nonpayable.
- The capability does **not** accuse fraud or label any traveler or transaction
  as misconduct.
- The capability does **not** ingest or display real personally identifiable
  information, real Government Travel Charge Card numbers, real bank routing
  data, or any other sensitive operational data outside its authorized
  environment.
- The capability does **not** invent policy citations or fabricate reference
  text. If the approved reference repository does not support a claim, the
  system says so.
- The capability does **not** represent its output as official, approved, or
  authoritative. Only an authorized human action recorded in DTS has official
  effect.

---

# 2. OV-1 — Operational Concept

## 2.1 Scenario

An Approving Official opens the queue of submitted travel voucher packets
awaiting review. One packet covers a multi-day temporary duty trip with
lodging, transportation, meals, and several smaller expense lines. The
packet contains attached receipts of varying quality, a free-text
justification block, a declared funding reference, and several pre-existing
flags raised by the underlying travel system.

The reviewer needs to decide, per packet, whether the packet is ready for
official DTS action, whether clarification should be requested, or whether the
voucher should be returned with comments. The reviewer retains accountability
for that decision and, for payment-bearing approvals, for the certification
that follows.

## 2.2 Operational Need

The reviewer needs a fast, evidence-anchored way to see what the packet
claims, what the evidence supports, where the story breaks, what is missing,
and what to ask. The current state is a sequential walk through multiple
screens of the underlying system, with the reviewer mentally reconstructing
the trip narrative and re-checking the same recurring failure modes on every
packet. The Voucher Review Radar exists to compress that work into a
structured, reviewable brief while preserving the reviewer's authority to
take official action, defer pending clarification, or decline to act until the
packet has enough information for official action.

## 2.3 Key Actors

- **Traveler** — submits the voucher packet through the official travel system.
  Not a direct user of the Radar.
- **Approving Official (the reviewer)** — the accountable human decision-maker
  who reads the Radar's brief and then takes any official action inside the
  official travel system.
- **Reviewing Official or routing reviewer (optional)** — a second-set-of-eyes
  role on the routing list. May use the same brief for context but does not
  inherit the Approving Official's authority.
- **Voucher Review Radar (the system)** — ingests the packet, performs the
  story-coherence and evidence checks, retrieves from the approved reference
  repository, and produces the review brief.
- **Approved reference repository** — a controlled set of policy excerpts,
  reference paragraphs, valid-receipt definitions, and service-level checklist
  items, sourced from publicly available DoD travel guidance.
- **Audit log** — a separate record of inputs received, retrievals performed,
  outputs generated, edits made, refusals, needs-human-review labels, and
  exports, retained per the deployment environment's policy.
- **Official travel system (out of scope for the Radar)** — the Defense Travel
  System itself, which remains the only system of record for any official
  action on a voucher.

## 2.4 High-Level Flow

```text
[Traveler]
    |
    | 1. Submits voucher packet through the official travel system
    v
[Submitted voucher packet (ingested as synthetic data in the prototype)]
    |
    | 2. Reviewer opens the queue in the Voucher Review Radar
    v
[Voucher Review Radar]
    |
    | 3. Reconstructs an internally coherent trip-and-expense story
    | 4. Compares story to attached evidence
    | 5. Runs evidence-quality, coherence, and anomaly checks
    | 6. Retrieves supporting excerpts from the approved reference repository
    | 7. Lists missing-information items
    | 8. Drafts neutral reviewer-prompt language
    | 9. Surfaces uncertainty, refusals, and needs-human-review labels
    v
[Review brief presented to the reviewer]
    |
    | 10. Reviewer inspects flags, citations, missing items, and draft prompt
    | 11. Reviewer edits, adds context, or discards generated content
    v
[Reviewer takes official action inside the official travel system]
    |
    | 12. Approve, return with comments, cancel, or hold for clarification
    |     — performed entirely by the human, outside the Radar
    v
[Audit log records what the Radar produced and what the reviewer exported,
 to support after-action traceability]
```

## 2.5 Main Operational Steps

1. The reviewer opens the queue and selects a packet.
2. The Radar shows a one-screen brief: declared trip, declared expenses,
   reconstructed story, flagged breaks, evidence assessments, missing-information
   checklist, citations, needs-human-review labels, and a draft clarification
   note.
3. The reviewer inspects each flag, opens the underlying source excerpt, and
   compares it to the packet evidence.
4. The reviewer edits or discards the draft clarification note.
5. The reviewer takes official action inside the official travel system.
6. The Radar records what was produced, what was edited, and what the reviewer
   exported, to support after-action traceability.

## 2.6 Trust Boundaries

- The Radar may read a submitted packet and may draft suggestions; it may not
  take any official action on the packet.
- The Radar may cite excerpts from the approved reference repository; it may
  not invent citations or paraphrase policy as if it were the authority.
- The reviewer must see flags, citations, missing items, uncertainty,
  needs-human-review labels, and any refusals before deciding what to do in
  DTS.
- Sensitive details remain outside the Radar unless the deployment
  environment is explicitly authorized.
- Final accountability remains with the human Approving Official.

## 2.7 Inputs

- A submitted voucher packet in structured form: declared trip dates and
  locations, declared line-item expenses (date, amount, category, vendor,
  payment instrument indicator), justification text, funding reference, and
  any pre-existing flags.
- Attachments associated with the packet: receipts and supporting
  documentation, in synthetic form for the prototype.
- The approved reference repository: policy excerpts, valid-receipt
  definitions, and service-level checklist items.
- Optional reviewer context: prior notes the reviewer has captured on the
  same packet, reviewer-set rule overrides for the component.

## 2.8 Outputs

- **Reconstructed trip-and-expense story** with explicit gaps between declared,
  expected, and observed facts, labeled as a review aid rather than a policy
  ruling.
- **Flag list** with severity, category, the in-packet evidence the flag is
  based on, and a citation into the approved reference repository when
  applicable.
- **Missing-information checklist** the reviewer can use when requesting
  clarification.
- **Draft clarification or possible return-comment note**, neutral in tone and
  clearly labeled as non-official draft text for the reviewer to adapt.
- **Confidence and uncertainty annotations** on each flag and on the overall
  brief.
- **Needs-human-review labels** for ambiguous, unsupported, conflicting, or
  low-confidence items.
- **Refusal notices** for any portion of the request that is out of scope or
  ungrounded.
- **Exportable review brief** in a portable format the reviewer can attach to
  a unit-side record.

## 2.9 Failure / Escalation Paths

- If a required field is missing from the packet, the Radar lists it as a
  missing-information item rather than guessing.
- If the approved reference repository does not support a flag, the Radar
  declines to assert the flag and surfaces the gap.
- If the packet appears to fall outside the supported workflow (for example,
  a non-travel artifact, a packet referencing classified detail, or a request
  for an entitlement determination), the Radar refuses and explains the
  refusal in actionable terms.
- If retrieval fails or sources conflict, the Radar labels the brief as
  partial and identifies which sections are not grounded.
- If a possible issue cannot be responsibly characterized, the Radar labels it
  as needs human review rather than turning it into a return, denial, payable,
  or nonpayable recommendation.
- If the reviewer asks the Radar to take an official action, the Radar
  refuses and reminds the reviewer that the action belongs in the official
  travel system.

---

# 3. SSS — System / Subsystem Specification

## 3.1 System Name

Defense Travel System Travel Voucher Review Radar for Approving Officials.

## 3.2 System Purpose

The system shall assist an authorized Approving Official in reviewing a
submitted DTS travel voucher packet by reconstructing an internally coherent
travel-and-expense story, flagging breaks against attached evidence,
retrieving supporting excerpts from an approved reference repository,
identifying missing information, and drafting neutral reviewer prompts,
while preserving full human authority over every official action on the
voucher.

## 3.3 Scope

The prototype shall support:

- Ingest of one synthetic voucher packet at a time, with optional queue-level
  prioritization across multiple synthetic packets.
- Generation of a single review brief artifact per packet.
- Retrieval from a controlled approved reference repository populated with
  publicly available DoD travel guidance excerpts.
- A single export path that produces a reviewable brief outside the system.

The prototype shall not support:

- Real personally identifiable information, real Government Travel Charge
  Card data, real bank routing data, or any sensitive traveler information.
- Live integration with the Defense Travel System or with any other system of
  record.
- Autonomous submission, approval, denial, certification, return,
  cancellation, or amendment of any document.
- Determination of entitlement, per-diem rate, lodging cap, premium-class
  authorization, payability, readiness for payment, or any other policy
  ruling.
- Allegation of fraud, misuse, abuse, or misconduct against any traveler.
- Use of unauthorized or sensitive sources, including non-public policy
  material.
- Any action targeting a real person, real account, or real official record.

## 3.4 Functional Requirements

**FR-1: Packet Ingest.**
The system shall ingest a structured representation of a single voucher
packet, including declared trip metadata, declared expense line items,
attached evidence references, justification text, funding reference, and
any pre-existing flags.

**FR-2: Story Reconstruction.**
The system shall produce an internally coherent trip-and-expense story from
the declared trip metadata and the declared line items, and shall present that
story alongside the observed packet content for comparison. The story shall be
labeled as a review aid, not an entitlement determination or official finding.

**FR-3: Evidence Quality Assessment.**
The system shall assess each piece of attached supporting evidence for
presence, legibility cues, itemization cues, payment-evidence cues, and
alignment to the claimed line item. The assessment shall be presented per
line item.

**FR-4: Coherence and Anomaly Checks.**
The system shall identify dates outside the declared trip window, location
mismatches between expense and trip, amount mismatches between claim and
evidence, duplicate or near-duplicate line items, multiple-charge patterns
where configured rules or packet context suggest a single charge, and cash,
ATM, or currency-exchange items that require reviewer reconstruction. Each
item shall be labeled as a review indicator, not as an official determination.

**FR-5: Controlled Reference Retrieval.**
The system shall retrieve excerpts from the approved reference repository for
policy-facing flags and reviewer prompts. Each retrieved excerpt shall be
displayed verbatim with a source identifier the reviewer can verify. If no
supporting excerpt is available, the system shall mark the issue as ungrounded
or needs human review rather than inventing support.

**FR-6: Missing-Information Detection.**
The system shall produce an explicit checklist of items that the packet does
not currently show, separated from items the system has affirmatively
flagged as inconsistent or needing reviewer attention.

**FR-7: Reviewer Prompt Drafting.**
The system shall produce a short, neutral draft clarification or possible
return-comment note based on the observed gaps and flagged items, written so
that it is suitable for the reviewer to adapt rather than to send verbatim.
The draft shall not state that the voucher must be approved, denied, returned,
certified, paid, or rejected.

**FR-8: Provenance and Confidence Display.**
The system shall display, per flag and per generated paragraph, the
underlying packet evidence, the retrieved reference excerpt (when
applicable), and an explicit confidence or uncertainty annotation.

**FR-9: Queue Prioritization.**
The system shall, when more than one packet is loaded, present a
prioritization view that orders packets by a composite review-difficulty
indicator. The view shall be labeled as workload guidance and shall not
imply any approval, denial, return, payability, or readiness-for-payment
decision.

**FR-10: Refusal and Redirect.**
The system shall refuse to act when the request falls outside the supported
workflow, when the packet references unauthorized or sensitive content, or
when the requested action is one of the prohibited actions enumerated in
section 4.3. The refusal shall include a brief, actionable reason.

**FR-11: Audit Log.**
The system shall record, where the deployment environment permits, the
inputs received, the retrievals performed, the outputs generated, the
reviewer edits applied, refusals, needs-human-review labels, and any exports
produced.

**FR-12: Export.**
The system shall produce an exportable review brief in a portable text-based
format that the reviewer can attach to a unit-side record. The export shall
preserve flag categories, citations, missing-information items, the draft
clarification note, uncertainty annotations, and a clear statement that the
brief is not an official action.

**FR-13: Needs-Human-Review State.**
The system shall provide a distinct needs-human-review state for ambiguous,
unsupported, conflicting, low-confidence, or locally variable items. This state
shall be separate from missing-information items, refusal notices, and
review-risk flags.

## 3.5 Non-Functional Requirements

**NFR-1: Trust Boundary.**
The system shall enforce its prohibited-action set as a hard constraint, not
as a configurable policy.

**NFR-2: Explainability.**
The system shall expose, for every flag and every generated paragraph, the
in-packet evidence, the retrieved reference excerpt when applicable, and an
explicit confidence or uncertainty annotation.

**NFR-3: Grounding Discipline.**
The system shall prefer refusal over fabrication. If the approved reference
repository does not support a claim, the system shall say so rather than
generate plausible-sounding text.

**NFR-4: Latency.**
The system should produce an initial review brief within a target latency
suitable for interactive use, defined by the deployment environment.

**NFR-5: Usability.**
A first-time reviewer should be able to understand the brief without training
beyond the reviewer's existing role-based qualification.

**NFR-6: Data Handling.**
The system shall not retain raw packet content longer than the deployment
environment requires, and shall treat all packet content as sensitive even
when synthetic.

**NFR-7: Human Authority.**
The system shall not represent generated output as official, approved,
authoritative, or final. Only an authorized human action recorded in the
official travel system has official effect.

**NFR-8: Robustness.**
The system shall degrade safely when retrieval fails, sources conflict, or
the packet is malformed. Partial briefs shall be labeled as partial.

**NFR-9: Configurability.**
The system shall allow component-level rule sets to override defaults
without modifying the prohibited-action set.

**NFR-10: Public-Safety Posture.**
The system shall be deployable in a public-safe environment using synthetic
data, and shall make no claim of integration with the official travel system
or with any classified source.

## 3.6 External Interfaces (Implementation-Neutral)

- **Reviewer Interface.** A reviewer-facing surface that shows the brief, the
  flags, the evidence, the citations, the missing-information checklist, the
  draft clarification note, the uncertainty annotations, the needs-human-review
  labels, and the refusal notices. Implementation form (browser surface,
  desktop surface, terminal surface) is left to the implementer.
- **Voucher Packet Intake Interface.** A defined input contract that accepts a
  structured voucher packet plus its attached evidence references, in
  synthetic form for the prototype.
- **Approved Reference Repository Interface.** A read interface against a
  controlled set of approved reference excerpts. Implementation form
  (file-based corpus, search index, retrieval pipeline) is left to the
  implementer.
- **Reasoning and Drafting Interface.** A component used for story
  reconstruction, evidence-quality reasoning, and prompt drafting.
  Implementation form is left to the implementer.
- **Export Interface.** A handoff that emits the review brief in a portable
  text-based format outside the system.
- **Audit Log Interface.** A handoff that emits structured audit entries to a
  store appropriate for the deployment environment.

The implementer is responsible for choosing concrete technologies that
satisfy the functional, non-functional, and trust requirements in this
specification. No specific product, programming language, framework, database,
or hosting environment is required by this specification.

## 3.7 Data Objects (Implementation-Neutral)

- **Voucher Packet.** Declared trip metadata, declared line items, attached
  evidence references, justification text, funding reference, pre-existing
  flags.
- **Trip Metadata.** Trip start, trip end, declared locations, declared
  purpose category.
- **Line Item.** Date, amount, category, vendor identifier, payment instrument
  indicator, attached-evidence references, free-text notes.
- **Attached Evidence Reference.** Identifier, content-type indicator,
  legibility-cue annotations, itemization-cue annotations, payment-evidence-cue
  annotations.
- **Reference Excerpt.** Source identifier, excerpt text, retrieval anchor,
  applicability note.
- **Reconstructed Story.** Internally coherent trip-and-expense narrative
  derived from declared trip metadata and line items, with per-segment
  expectations and gaps.
- **Flag.** Category, severity indicator, source evidence pointer (in-packet
  and reference), confidence annotation, plain-language explanation, suggested
  reviewer question.
- **Missing-Information Item.** Description of what is not present, why it
  matters, where the reviewer would expect to find it.
- **Needs-Human-Review Item.** Description of an ambiguous, unsupported,
  conflicting, low-confidence, or locally variable item that the system cannot
  responsibly characterize.
- **Draft Clarification Note.** Neutral, short, editable text suitable for the
  reviewer to adapt.
- **Review Brief.** The composite artifact assembled from the above.
- **Audit Entry.** Timestamped record of input, retrieval, generation, edit,
  refusal, needs-human-review label, or export, with sufficient context to
  support after-action review.

## 3.8 Safety, Trust, Audit, Refusal, and Human Authority Requirements

**TR-1: No Official Action.**
The system shall not approve, deny, certify, return, cancel, amend, or
submit any voucher document, and shall not request, simulate, or imply any
of those actions on the reviewer's behalf. The system shall not state that a
voucher is officially ready for approval, return, payment, or denial.

**TR-2: No Entitlement Determination.**
The system shall not rule on per-diem, lodging cap, premium-class
authorization, dual-lodging, conjunctive-travel linkages, or any other
entitlement or payability decision. The system may surface the relevant
approved reference excerpt; the reviewer evaluates it through the official
DTS review process.

**TR-3: No Fraud Allegation.**
The system shall not characterize any traveler, vendor, or transaction as
fraudulent, abusive, or engaged in misconduct. Permitted vocabulary includes
"anomaly," "documentation gap," "policy-risk indicator," and "evidence
needing closer reviewer attention."

**TR-4: No Auto-Filling of Reviewer Justifications.**
The system shall not auto-fill or auto-populate the reviewer's
justification text or return-comment text inside the official travel system.
The system may produce non-official draft text for the reviewer to adapt and
enter manually.

**TR-5: Provenance on Every Flag.**
Every flag shall carry a pointer to in-packet evidence and, when applicable,
a verbatim retrieved reference excerpt with its source identifier.

**TR-6: Refusal Over Fabrication.**
The system shall refuse, defer, or mark needs human review rather than
fabricate when the approved reference repository does not support a claim,
when required input is missing, or when the request is out of scope.

**TR-7: Visible Uncertainty.**
Confidence and uncertainty shall be visible at the flag level and at the
brief level. Hidden uncertainty is not permitted.

**TR-8: Synthetic-Only Prototype Data.**
The prototype shall operate only on synthetic packets, synthetic evidence,
and publicly available reference excerpts.

**TR-9: Auditability.**
The system shall maintain an audit log sufficient to reconstruct, after the
fact, what the system saw, what it retrieved, what it generated, what the
reviewer edited, what it refused or deferred, and what was exported.

**TR-10: Authority Boundary Reminder.**
Every exportable artifact shall include a clear statement that the artifact
is a review aid and not an official action.

**The system can organize review work; it cannot move money or official DTS
state.**

---

# 4. Domain Workflow Action Contract

This section defines the workflow actions the system is permitted to perform
on a voucher packet. The contract is implementation-neutral: a coding agent
can satisfy it with any stack so long as the action categories, refusal
behavior, and trust boundary are preserved.

## 4.1 Permitted Read Actions

- Read a synthetic voucher packet and its attached evidence references.
- Read excerpts from the approved reference repository.
- Read the reviewer's optional context and rule overrides.
- Read prior audit entries for the same packet to provide continuity.

## 4.2 Permitted Review and Draft Actions

- Reconstruct an internally coherent trip-and-expense story.
- Compare story to evidence and produce flagged breaks.
- Assess evidence quality cues per line item.
- Retrieve supporting reference excerpts and present them verbatim with source
  identifiers.
- Produce a missing-information checklist.
- Draft a short, neutral clarification or possible return-comment note for the
  reviewer to adapt.
- Produce a queue prioritization view across multiple packets.
- Annotate confidence, uncertainty, needs-human-review labels, and refusals on
  every output.
- Emit an exportable review brief outside the system, clearly labeled as a
  review aid.

## 4.3 Prohibited Actions (Hard Constraints)

The system shall not perform, request, simulate, or imply any of the
following:

- **Approve** a voucher.
- **Deny** a voucher.
- **Certify** payment.
- **Return** a voucher inside the official travel system.
- **Cancel** a voucher inside the official travel system.
- **Amend** a voucher inside the official travel system.
- **Submit** anything to the official travel system on the reviewer's behalf.
- **Determine entitlement** under the Joint Travel Regulations or any
  equivalent authority.
- **Determine payability** or state that a voucher is ready for payment.
- **Recommend the official disposition** of a voucher as approve, deny,
  certify, return, cancel, amend, or submit.
- **Accuse fraud**, misuse, abuse, or misconduct against any traveler,
  vendor, or transaction.
- **Auto-fill or auto-populate** the reviewer's justification text inside the
  official travel system.
- **Process real personally identifiable information**, real Government
  Travel Charge Card data, or real bank routing data.
- **Represent its output as official, approved, or authoritative.**

The prohibited-action set shall be enforced as a hard constraint in the
implementation. It shall not be made configurable.

## 4.4 Refusal Behavior

The system shall refuse, with a brief and actionable reason, when:

- A request asks for a prohibited action (4.3).
- A request asks for an entitlement determination, a fraud finding, or any
  other ruling reserved to a human authority.
- A required input is missing and the system cannot meaningfully proceed.
- The approved reference repository does not support the requested claim.
- A packet references content outside the prototype's authorized environment.

A refusal or needs-human-review label is itself an output. It shall be logged
and shall be visible to the reviewer.

---

# 5. Prototype Acceptance Criteria

A prototype demonstration is acceptable when each of the following can be
shown end-to-end against a synthetic voucher packet.

**AC-1: Single-Packet Brief.**
A reviewer can load one synthetic voucher packet and see a one-screen review
brief that includes the reconstructed story, at least one flagged break, at
least one missing-information item, and at least one cited reference excerpt.

**AC-2: Provenance.**
Each flag in the brief points to specific in-packet evidence and, when
applicable, displays the retrieved reference excerpt verbatim with a source
identifier the reviewer can verify.

**AC-3: Missing-Information Listing.**
Items the packet does not show are listed separately from items the system
has flagged as inconsistent or needing reviewer attention.

**AC-4: Draft Clarification Note.**
The brief includes a short, neutral, editable draft clarification or
possible return-comment note that the reviewer can adapt. The note is labeled
as non-official draft text and does not state the correct official disposition
of the voucher.

**AC-5: Visible Uncertainty.**
Each flag and the brief as a whole carry an explicit confidence or
uncertainty annotation.

**AC-6: Refusal Demonstration.**
The reviewer can issue a request that asks the system to take an official
action, determine entitlement, or accuse fraud, and the system refuses with
an actionable reason that is also written to the audit log.

**AC-7: Out-of-Scope Refusal.**
The reviewer can submit a non-voucher artifact and the system declines to
treat it as a voucher.

**AC-8: Queue Prioritization.**
With more than one packet loaded, the system presents a prioritization view
that is labeled as workload guidance and that does not imply any approval or
denial, return, payability, or readiness-for-payment decision.

**AC-9: Export.**
The reviewer can export the brief in a portable text-based format that
preserves flags, citations, missing-information items, the draft note, and
the not-an-official-action statement.

**AC-10: Audit Trail.**
The system records inputs, retrievals, generated outputs, reviewer edits,
needs-human-review labels, refusals, and exports for at least one full review
cycle.

**AC-11: Public-Safety Verification.**
The demonstration uses only synthetic packets, synthetic evidence, and
publicly available reference excerpts, and the demonstration narrative
states this on screen and in any written submission.

**AC-12: Trust-Boundary Statement.**
The brief and the export both display a clear statement that the system
does not approve, deny, certify, return, cancel, amend, or submit any
voucher, does not determine entitlement or payability, and that the human
Approving Official remains the accountable decision-maker.

**AC-13: Needs-Human-Review Demonstration.**
The reviewer can load a packet with an ambiguous, unsupported, or conflicting
item and see that item labeled as needs human review rather than converted
into an official disposition recommendation.

---

# 6. Customization Guide

This section describes how another team can adapt the specification to a
related workflow without weakening the trust boundary. Adaptation is secondary:
the public specification above remains focused on DTS travel voucher review
for Approving Officials.

## 6.1 What is portable

The CV-1 / OV-1 / SSS structure, the action contract, and the trust-boundary
language are portable to any workflow that meets all of the following:

- A human reviewer is the accountable decision-maker.
- The review involves reconstructing a coherent story from messy evidence
  against an approved reference set.
- The reviewer benefits from a structured brief, missing-information items,
  and draft prompt language rather than from autonomous action.
- The implementation can satisfy the prohibited-action set as a hard
  constraint.

## 6.2 What to swap

To adapt this specification to a related workflow:

1. Replace the **packet** definition (section 3.7) with the new artifact's
   structured form.
2. Replace the **reconstructed story** definition with the new workflow's
   expected narrative.
3. Replace the **evidence quality cues** with cues appropriate to the new
   workflow's evidence types.
4. Replace the **approved reference repository** contents with the policy and
   reference set authoritative for the new workflow.
5. Re-derive the **flag categories** from the new workflow's validated
   recurring failure modes or approved review checklist.
6. Re-derive the **draft prompt** templates from the new workflow's typical
   reviewer language.
7. Keep the **prohibited-action set** intact in spirit. Replace each
   prohibited verb with the equivalent verb in the new workflow's official
   system. Do not remove any prohibition.
8. Keep the **provenance, refusal, uncertainty, and audit** requirements as
   stated.

## 6.3 What not to weaken

Implementers shall not, when adapting the specification:

- Allow the system to take any official action.
- Allow the system to determine entitlement or other authority-reserved
  rulings in the new workflow.
- Allow the system to recommend the official disposition of the reviewed
  artifact.
- Allow the system to characterize a person or transaction as fraudulent or
  in misconduct.
- Allow the system to operate on sensitive data outside its authorized
  environment.
- Remove provenance, refusal-over-fabrication, visible uncertainty, or
  audit-log requirements.

## 6.4 Stack neutrality

This specification is deliberately implementation-neutral. The implementer
chooses the concrete reasoning and drafting approach, retrieval approach,
storage, hosting, and reviewer interface. The specification only requires
that the chosen stack satisfy the functional, non-functional, and trust
requirements above. A coding agent should be able to read this specification
and produce a comparable system on the implementer's preferred stack.

---

# 7. Public-Source Validation Hooks

The following public, unclassified source areas informed the problem framing in
this specification. They are validation hooks for reviewers and implementers,
not system output and not a substitute for checking current source text before
making public claims.

- **Approving Official as accountable Certifying Officer.** Validate against
  the DoD Financial Management Regulation, Volume 5, Chapter 5, and current
  DTMO guidance for Authorizing and Certifying Officials. The specification
  treats the AO as the accountable human and does not transfer certification
  authority to the Radar.
- **Receipt and supporting-documentation gaps.** Validate against DTMO public
  materials such as "Avoid Improper DTS Payments by Checking Receipts" and
  "What is a Valid Receipt?" Treat receipt statistics as source-specific and
  current only as of the cited publication, not as a universal DoD-wide rule.
- **Recurring voucher-review surfaces.** Validate against DTMO AO checklist
  materials and approved service-level AO checklists. Receipts, amounts, dates,
  locations, justifications, lines of accounting, transportation mode, lodging
  documentation, and split-disbursement coherence are review surfaces, not
  automated determinations.
- **DoD oversight context for travel pay.** Validate against DoD Office of
  Inspector General payment-integrity audits and Government Accountability
  Office reports such as GAO-19-530 and GAO-23-106945. Improper-payment
  estimates and comparative claims often carry caveats; prototype results
  should not be converted into savings or error-reduction claims without a
  controlled evaluation.
- **Modernization context.** Validate against public GAO reporting on MyTravel
  discontinuation and incremental DTS modernization. The Radar is framed as a
  companion review aid for current DTS workflows, not as a DTS replacement.
- **Existing post-approval compliance tooling.** Validate against DTMO Travel
  Policy Compliance program materials and the public Travel Policy Compliance
  Tool user guide. The Radar is positioned as pre-decision evidence packaging
  for the AO and should not claim to replace or fully characterize internal
  post-approval compliance capabilities.

These hooks support a cautious framing: an Approving Official is an accountable
human reviewer working through recurring, document-heavy voucher review
surfaces, and a pre-decision, evidence-anchored assistant is defensible only
when the authority boundary, grounding discipline, and human-review posture in
this specification are preserved.

---

*End of specification.*
