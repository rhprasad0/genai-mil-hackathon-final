# Demo receipts

These public-safe screenshots document what the hackathon-era AO Radar demo showed before the Parody Division continuation.

The receipts are evidence of a bounded synthetic review workflow, not evidence of a live government integration or official DTS action. All voucher IDs, traveler IDs, records, findings, citations, and audit entries shown here are synthetic demo data.

## Receipt set

| Receipt | Screenshot | What it documents |
| --- | --- | --- |
| Queue triage | [`../assets/demo/chatgpt-queue-triage.png`](../assets/demo/chatgpt-queue-triage.png) | Tool-backed ranking of synthetic vouchers awaiting accountable-reviewer attention. |
| Review brief | [`../assets/demo/chatgpt-review-brief-v1002.png`](../assets/demo/chatgpt-review-brief-v1002.png) | One-screen review brief with trip story, evidence gaps, citations, anomaly/review signals, and neutral clarification language. |
| Scoped write + audit | [`../assets/demo/chatgpt-scoped-write-audit-v1002.png`](../assets/demo/chatgpt-scoped-write-audit-v1002.png) | Internal reviewer note, internal review-status update, and audit trail retrieval. |
| Story conflict review | [`../assets/demo/chatgpt-story-conflict-v1003.png`](../assets/demo/chatgpt-story-conflict-v1003.png) | Overlapping lodging, amount mismatch, evidence conflict triage, and explicit handoff to human reviewer judgment. |
| Boundary refusal | [`../assets/demo/chatgpt-boundary-refusal-v1010.png`](../assets/demo/chatgpt-boundary-refusal-v1010.png) | Refusal to determine fraud or authorization status, with redirect to neutral review language. |
| Boundary audit | [`../assets/demo/chatgpt-audit-boundary-v1010.png`](../assets/demo/chatgpt-audit-boundary-v1010.png) | Audit trail showing refusal/boundary behavior and scoped workflow traceability. |
| Tool catalog | [`../assets/demo/chatgpt-tools-list.png`](../assets/demo/chatgpt-tools-list.png) | The bounded AO Radar tool surface visible in the assistant cockpit. It lists review-aid tools, scoped internal-write tools, and audit retrieval, without approve/deny/certify/pay tools. |
| Deployed health check | [`../assets/demo/deployed-health-endpoint.png`](../assets/demo/deployed-health-endpoint.png) | Public demo infrastructure returning `HTTP 200` from the `/health` endpoint at capture time. The terminal prompt and host are redacted for public-safety hygiene. |

## Why these receipts matter

Together, the screenshots show the serious version of AO Radar before the cursed-agent harness:

- the assistant could triage synthetic voucher packets;
- inspect packet story, evidence, and citations;
- draft neutral clarification language;
- record scoped internal reviewer notes/statuses;
- retrieve audit trails; and
- refuse official-action-shaped requests.

The important boundary: AO Radar could support accountable review, but it could not approve, deny, certify, submit, determine entitlement or payability, accuse fraud, contact external parties, or move money.

That serious boundary is what makes the Parody Division continuation meaningful: the cursed agents intentionally weaken or violate that boundary only inside controlled synthetic tests, while the evaluator scores those violations as failures.
