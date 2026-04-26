# AO Radar Claude Agent Teams Execution Plan

Operational overlay for using Claude Code Agent Teams to execute the AO Radar
implementation plans without crossing the public-safety or human-authority
boundaries in `docs/spec.md`.

This is a coordination plan, not application or infrastructure code. The
companion plans remain authoritative for their domains:

| Source | Owns |
|---|---|
| `docs/spec.md` | Product boundary, tool catalog, prohibited actions, refusal behavior, acceptance criteria. |
| `docs/schema-implementation-plan.md` | Postgres tables, enums, constraints, seed scenario shape, audit-event matrix. |
| `docs/application-implementation-plan.md` | Python/FastMCP Lambda layout, tool wiring, repository boundaries, fraud-mock contract. |
| `docs/infra-implementation-plan.md` | Terraform, AWS resources, API Gateway routes, RDS, Secrets Manager, Lambda packaging inputs. |
| `docs/synthetic-data-implementation-plan.md` | Story cards, synthetic fixture generator, validators, seed/reset workflow. |
| `docs/testing-plan.md` | Unit, schema, contract, boundary, integration, E2E, and public-safety test gates. |

If this plan conflicts with a companion plan, edit this plan. Do not silently
reinterpret the source plans.

## Claude Code Agent Teams Assumptions

Use only assumptions that match the official Claude Code Agent Teams docs as of
2026-04-26.

- Agent Teams are experimental and disabled by default. Enable them outside the
  repo with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; do not commit local
  Claude team state, generated task lists, transcripts, or teammate mailboxes.
- A team starts only when the user explicitly asks or approves. Do not build a
  plan that depends on Claude automatically creating a team.
- The lead is fixed for the life of the team. Only the lead coordinates,
  approves teammate plans, integrates results, and cleans up team resources.
- Teammates are separate Claude Code sessions. They do not inherit the lead's
  conversation history, so every spawn prompt must include the relevant source
  docs, path ownership, public-safety rules, and exit criteria.
- Teammates start with the lead's permission mode. Run the lead with the least
  privilege practical for the phase; do not assume per-teammate permissions can
  be safely different at spawn time.
- Use plan approval for any teammate that may edit files. The lead approves
  only plans with clear owned paths, tests, and no proposed changes outside
  this repo's public-safe scope.
- Teammates cannot spawn their own teams. Do not design nested team workflows.
- Do not rely on session resumption restoring teammates. After resume or
  interruption, the lead must verify which teammates still exist and recreate
  only the necessary ones.
- Task status can lag. The lead verifies file diffs and test results rather
  than trusting the shared task list alone.
- Subagent definitions can be reused for teammate roles, but teammate sessions
  still load skills and MCP servers from project/user settings. Do not assume a
  subagent definition's extra frontmatter always applies to a teammate.

## Public-Safety Rules For Every Agent

- Read `AGENTS.md` first.
- Do not commit.
- Do not commit or paste secrets, credentials, `.env` values, Terraform state,
  Secrets Manager JSON, private notes, raw transcripts, generated team state,
  real PII, real DTS records, real GTCC data, bank data, or operational data.
- Use placeholders such as `<demo-host>`, `<aws-account-id>`, `<region>`, and
  `<repo>` in docs. Do not write machine-local absolute paths into committed
  files.
- Do not load real DoD, JTR, DTMO, checklist, or government-system excerpts
  into fixtures. Hackathon citations are synthetic demo reference text only.
- Do not add tools or docs that approve, deny, certify, return, cancel, amend,
  submit, determine entitlement, determine payability, modify payment amounts,
  accuse fraud, or contact external parties.
- Do not expose raw SQL, arbitrary filesystem access, arbitrary network fetch,
  or generic admin tools through MCP.

## Team Shape

Use one lead and at most four teammates. Smaller teams are preferred until the
schema, fixture, and tool contracts are stable.

| Role | Mode | Owns | Must not edit |
|---|---|---|---|
| Lead integrator | Write, with plan approval for teammate edits | Task breakdown, cross-plan consistency, final diff review, merge conflict resolution, validation commands. | Nothing without reading the relevant source plan first. |
| Schema teammate | Write after plan approval | `ops/migrations/`, schema test files under `tests/schema/`, schema-specific fixture contracts. | `src/ao_radar_mcp/`, `infra/`, story-card narratives except IDs needed for FK tests. |
| Synthetic data teammate | Write after schema Phase 1-2 exist | `ops/seed/`, story cards, fixture validators, fixture tests under `tests/fixtures/` and public-safety scanners under `tests/meta/`. | Schema migrations, app tool code, Terraform. |
| Application teammate | Write after schema table names are stable | `src/ao_radar_mcp/`, `src/ao_radar_fraud_mock/`, `src/ao_radar_db_ops/`, app/unit/contract/lambda-boundary tests. | `infra/`, seed story content, schema migrations except read-only review comments. |
| Infra teammate | Write after placeholder zip contract is known | `infra/`, infra docs updates, deploy smoke scripts if added. | Application behavior, schema definitions, seed content. |
| Test/review teammate | Usually read-only; write after lead approval | Cross-suite gaps, traceability tests, adversarial review, final safety grep. | Product behavior changes without lead approval. |

Do not let two teammates edit the same file or directory in parallel. If a file
is cross-cutting, the lead owns it and applies changes after teammates report.

## Dependency Order

This project is not a flat parallel build. Parallelize only within dependency
boundaries.

1. **Orientation gate.** Lead reads `AGENTS.md`, all six companion docs, and
   `git status`. Lead records existing dirty files before spawning teammates.
2. **Contract gate.** Lead confirms the spec tool catalog, prohibited-action
   set, canonical boundary reminder, and audit-event matrix. No teammate may
   broaden those contracts.
3. **Repo bootstrap.** Lead or one teammate creates shared project scaffolding
   such as `pyproject.toml`, package roots, test roots, and build script names.
   Do this before parallel app/test edits to avoid file conflicts.
4. **Schema Phase 1-2.** Schema teammate creates tables, enums, constraints,
   indexes, and schema tests. Synthetic data and app repository code may do
   read-only planning, but should not lock in column assumptions before this
   gate.
5. **Synthetic data Phase A-E.** Synthetic data teammate implements story cards,
   generator, validators, loader, and guarded reset after schema constraints
   exist. Use only synthetic markers and deterministic IDs.
6. **Application Phase 1-3.** Application teammate implements `/health`,
   Streamable HTTP `POST /mcp`, the exact tool catalog, read tools, and
   deterministic fraud-mock signal flow. Do not expose generic data access.
7. **Application Phase 4-5.** Implement story analysis, brief fusion, export,
   scoped writes, refusals, and audit-event coupling. Every write path must
   persist exactly one matching `workflow_events` row in the same transaction.
8. **Infra Phase 1-3.** Infra teammate builds Terraform once placeholder zip
   paths and handler strings are known. Do not require real secrets or hosted
   zone values in committed files.
9. **Testing Phase 0-5.** Tests land with each phase, not at the end. Tier 4
   E2E waits for deployed `/health` and `/mcp` plus seeded data.
10. **Demo gate.** Lead runs the manual demo checklist, public-safety scanners,
    `git diff --check`, and the leakage grep before any PR or handoff.

## Workstream Prompts

Use these prompts as templates. Replace placeholders with the current branch
state and the specific phase.

### Lead Prompt

```
Read AGENTS.md and docs/spec.md, docs/schema-implementation-plan.md,
docs/application-implementation-plan.md, docs/infra-implementation-plan.md,
docs/synthetic-data-implementation-plan.md, and docs/testing-plan.md.

You are the lead for an AO Radar Claude Code Agent Team. This is a public-safe
hackathon repo. Do not commit. Keep all outputs synthetic. Preserve the human
authority boundary. Build a task list that respects dependency gates and
disjoint file ownership. Require plan approval before teammate edits. Reject
any teammate plan that adds generic data access, official DTS actions, real
data, real policy excerpts, secrets, machine-local paths, or uncontrolled
parallel edits.
```

### Schema Teammate Prompt

```
Read AGENTS.md, docs/spec.md, and docs/schema-implementation-plan.md.
Own only ops/migrations/ and tests/schema/ unless the lead grants a specific
exception. Implement the schema plan phases assigned by the lead. Enforce
synthetic_demo guards, allowed enums, blocked-status constraints, no official
DTS/payment columns, no free-text blocked-word CHECKs, and the audit-event
matrix. Report changed files and validation commands. Do not commit.
```

### Synthetic Data Teammate Prompt

```
Read AGENTS.md, docs/schema-implementation-plan.md, and
docs/synthetic-data-implementation-plan.md. Own only ops/seed/,
tests/fixtures/, and lead-approved public-safety scanner files. Create only
synthetic story cards, generated rows, validators, loaders, and reset logic.
No real names, vendors, places, units, GTCC data, bank data, policy excerpts,
private notes, or transcripts. Every seeded scoped write/refusal/brief/
needs-human-review label needs the matching workflow_events row. Do not commit.
```

### Application Teammate Prompt

```
Read AGENTS.md, docs/spec.md, docs/schema-implementation-plan.md, and
docs/application-implementation-plan.md. Own only src/ao_radar_mcp/,
src/ao_radar_fraud_mock/, src/ao_radar_db_ops/, and lead-approved app tests.
Expose only the spec section 4.5 tools over FastMCP. No raw SQL tool, file
reader, arbitrary HTTP fetch, official action, payability determination, fraud
allegation, or external contact. Every write/refusal/export/generation path
must create the required audit event. Do not commit.
```

### Infra Teammate Prompt

```
Read AGENTS.md, docs/infra-implementation-plan.md, and the application plan
handoff sections. Own only infra/ and lead-approved infra docs. Use placeholders
for domain, zone ID, account, region, and zip paths. Do not commit Terraform
state, tfvars, secrets, real hosted-zone values, or command output containing
secret JSON. Keep API routes to POST /mcp, GET /health, and optional gated
GET /sse only. Do not commit.
```

### Test/Review Teammate Prompt

```
Read AGENTS.md and all AO Radar docs. Default to read-only adversarial review.
Look for contract drift, missing tests, unsafe wording, generic data access,
private artifacts, over-broad AWS permissions, missing audit events, and
public-safety leaks. If the lead approves edits, own only the specified test or
doc files. Report findings with file/line references and residual risks. Do
not commit.
```

## Model And Delegation Guidance

- Use Opus 4.7, max effort, for the lead/orchestrator when token budget and
  latency are acceptable. The lead is fixed for the life of the team and owns
  dependency sequencing, safety-boundary interpretation, teammate plan approval,
  integration, and final merge decisions.
- Use the strongest available model for schema constraints, application
  boundary/refusal logic, audit invariants, IAM/security review, and final
  review.
- Use Sonnet or other faster/cheaper models only for bounded implementation
  slices, read-only exploration, log summarization, simple fixture checks, or
  test-running summaries.
- Do not route safety-critical wording, schema constraints, IAM changes, or
  final merge decisions to a low-capability model.
- Do not ask teammates to solve the same design question independently and then
  merge competing answers. Assign one owner and ask reviewers for critiques.
- Prefer read-only teammates for adversarial review. Use write-capable
  teammates only when file ownership is unambiguous.

## Acceptance Gates

Before accepting any teammate output, the lead checks:

- The teammate changed only owned paths.
- The change matches the authoritative companion plan for that layer.
- No generic MCP tool, raw SQL endpoint, file reader, arbitrary URL fetch, or
  broad admin route was added.
- No status, draft text, finding, brief, or tool wording implies approval,
  denial, certification, official return, payment readiness, entitlement,
  payability, fraud, misconduct, or external contact.
- Every generated fixture and test artifact is synthetic and carries the
  required markers.
- Every write path has the matching audit-event test.
- The relevant local test tier passes, or the teammate documents exactly what
  could not run and why.
- The diff contains no secrets, private paths, raw transcripts, local team
  state, Terraform state, `.env` values, real account IDs, real hosted-zone
  IDs, real emails, real phone numbers, real card/PAN-shaped values, SSN-shaped
  values, or bank-routing-shaped values.

## Lightweight Validation Commands

Run these before handoff. Use the changed-file list from the current working
tree; include untracked files that are intended for review.

```bash
git diff --check

git diff --name-only > /tmp/ao-radar-changed-files
git ls-files --others --exclude-standard >> /tmp/ao-radar-changed-files

rg -n --hidden --no-ignore -f <(printf '%s\n' \
  'AKIA[0-9A-Z]{16}' \
  'ASIA[0-9A-Z]{16}' \
  'aws[_]secret[_]access[_]key' \
  'aws[_]access[_]key[_]id' \
  'secret[_-]?key' \
  'password[[:space:]]*=' \
  'BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY' \
  'xox[baprs]-[A-Za-z0-9-]+' \
  's[l]ack://|app\\.s[l]ack\\.com/client/[A-Z0-9]+/[A-Z0-9]+' \
  '\\b[''CGD''][0-9][A-Z0-9]{7,}\\b' \
  '/home/[A-Za-z0-9._-]+' \
  '/Users/[A-Za-z0-9._-]+' \
  '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[A-Za-z]{2,}' \
  '[0-9]{3}-[0-9]{2}-[0-9]{4}' \
  '\b[0-9]{16}\b' \
  '\b[0-9]{9}\b' \
) $(sort -u /tmp/ao-radar-changed-files)
```

Review matches manually. Some placeholder or negative-boundary text may be
acceptable, but real secrets, private paths, channel IDs, personal data, or
operational identifiers are blockers.

## Residual Risks

- Agent Teams are experimental. Keep work small, verify task state manually,
  and clean up through the lead.
- The repo currently contains plan documents, not implemented code. The first
  implementation pass will surface package-management and FastMCP/Lambda
  adapter details that the docs can only anticipate.
- The public unauthenticated MCP endpoint is acceptable for the hackathon demo
  only because the data is synthetic and the tool surface is bounded. It is not
  a production security model.
- The approved reference corpus is synthetic for hackathon scope. Loading real
  public policy excerpts later requires a separate corpus review.

## References

- Claude Code Agent Teams docs: <https://code.claude.com/docs/en/agent-teams>
- Claude Code Subagents docs: <https://code.claude.com/docs/en/sub-agents>
