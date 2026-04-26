![Sergeant OpenClaw poster](assets/sergeant-openclaw.png)

*Image credit: ChatGPT.*

# AO Radar: Pre-Decision Review Fusion for DTS Approving Officials

AO Radar is a public-safe GenAI.mil hackathon concept for helping Defense Travel System (DTS)-style Approving Officials review travel voucher packets before they take official action.

The core idea is simple: give the accountable human reviewer a one-screen, auditable pre-decision brief that fuses voucher packet evidence, traveler context, policy citations, and anomaly signals — without approving, denying, certifying, submitting, determining entitlement, or accusing fraud.

> **The model can move the review workflow forward, but it cannot move money.**

## Project

AO Radar focuses on the review burden faced by Approving Officials who must reconstruct the story behind a submitted travel voucher from expenses, receipts, dates, justifications, funding context, and policy references.

The system is designed as a controlled review cockpit that can:

- summarize a synthetic DTS-like voucher packet;
- highlight missing, weak, or inconsistent evidence;
- compare claimed expenses against the trip story;
- surface policy or checklist references for human verification;
- ingest synthetic external anomaly signals as review inputs, not official findings;
- draft neutral clarification or return-comment language for the reviewer to edit;
- record bounded workflow notes and review statuses with an audit trail; and
- refuse actions outside the human authority boundary.

AO Radar is intentionally **pre-decision**. It supports review, prioritization, explanation, and evidence packaging, but leaves every official DTS action to the human Approving Official.

## Hackathon background

This project was created for the **SCSP National Security Technology Hackathon**, GenAI.mil track.

The hackathon asks teams to build practical generative-AI tools for national-security and defense workflows using only public, unclassified, and otherwise shareable materials. The GenAI.mil track emphasizes everyday military administrative and logistics work: the paperwork, policy navigation, travel planning, and back-office friction that can keep service members behind desks instead of focused on mission work.

Submissions are expected to be public GitHub repositories with a README, demoable in under five minutes, and safe to publish. That means no classified material, no controlled or restricted content, no private operational data, no real personal data, and no secrets.

The judging rubric weights four areas equally:

- **Novelty of approach** — whether the solution brings a fresh perspective.
- **Technical difficulty** — whether the team built something genuinely challenging.
- **Potential national impact** — whether the idea could scale to a widespread problem.
- **Problem-solution fit** — whether the team understands a real user need and addresses it directly.

## Challenge prompt

The GenAI.mil track prompt frames the problem this way:

> The US military runs on paperwork. Build the AI assistant that makes the rank-and-file faster, smarter, and less buried in bureaucracy, and does it offline.

The organizer-provided track description explains that although modern defense often focuses on the digital battlefield, immediate friction for millions of service members often lives in the administrative trenches: navigating dense regulations, filling out paperwork, planning travel, handling logistics, and translating policy into correct action.

The recommended starting point is to pick one user persona and build an end-to-end solution for that user. The guidance encourages accurate retrieval over a small trusted corpus before adding form generation, logistics planning, or other workflow automation.

Example directions from the track include:

- a regulation navigator over Army Regulations and Field Manuals;
- a form auto-filler for common military paperwork;
- a TDY planner using travel regulations and per diem data; and
- a contract intelligence tool using public spending and acquisition data.

AO Radar adapts that challenge framing to the travel-voucher review side of the workflow: rather than helping a traveler submit more paperwork, it helps the accountable reviewer understand whether the submitted packet tells a coherent, reviewable story.

## Deliverables in this repository

- `docs/spec.md` — implementation-neutral capability and system specification for AO Radar.
- `docs/infra-implementation-plan.md` — canonical public-safe Terraform/AWS infrastructure implementation plan.
- `docs/schema-implementation-plan.md` — coding-agent-ready persistence-schema implementation plan for the AO Radar Postgres layer.
- `docs/application-implementation-plan.md` — coding-agent-ready application implementation plan for the Python/FastMCP Lambda that exposes the AO Radar workflow tools.
- `assets/sergeant-openclaw.png` — public-safe generated project image.

## Acknowledgments

Special thanks to **Sabastian Mandell** for his help shaping the project and sharpening the problem frame, and for his service.

## Public-safety and data posture

This repository is public by design. It should contain only public-safe materials:

- synthetic voucher examples, not real DTS records;
- synthetic traveler context, not real personal data;
- public or approved reference material only;
- no secrets, tokens, credentials, private notes, transcripts, or raw research artifacts; and
- no claims that prototype outputs are official determinations.

Cybersecurity concerns are acknowledged as important but are intentionally deferred from the competition submission. They should be addressed in the specification after the competition, when there is time for a more careful treatment of threat models, access controls, deployment boundaries, data handling, and audit requirements.

AO Radar’s safest and strongest posture is conservative: useful to the human reviewer, explicit about uncertainty, and very boring about authority boundaries. Boring boundaries win procurement friends.
