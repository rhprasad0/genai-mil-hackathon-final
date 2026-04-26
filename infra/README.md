# AO Radar Infrastructure (Terraform root module)

Single root Terraform module that stands up the AO Radar hackathon stack:
public HTTPS MCP endpoint at `https://<subdomain>.<domain_root>/mcp`
backed by an API Gateway HTTP API, three Lambdas (MCP, fraud-mock, DB-ops),
a tiny single-AZ Postgres 16 RDS instance, and a Secrets Manager entry
holding the synthetic DB master credentials.

This README is the operator guide. The canonical specification lives in
`docs/infra-implementation-plan.md`.

## Public-safety reminders (read first)

- This is a public hackathon repo. **Do not commit:** `terraform.tfstate`,
  `terraform.tfstate.backup`, `*.tfplan`, `terraform.tfvars`, the contents
  of `infra/build/`, secret JSON output, AWS account IDs, real domain
  values, or real Route 53 hosted-zone IDs. The repo `.gitignore` already
  excludes the common cases, but do not paste secret material into chat,
  PR descriptions, or commit messages.
- The state file contains the random RDS master password. Treat
  `infra/terraform.tfstate` as sensitive; delete it locally if the working
  tree is being shared.
- `terraform.tfvars.example` is the committed pattern. Copy it to
  `terraform.tfvars` (gitignored) and edit a local copy with values from
  your account. Do not put the example values directly into a real apply.
- Use synthetic data only. Do not load real DoD, JTR, DTMO, checklist,
  GTCC, bank, or government-system data into the database.

## Prerequisites

- Terraform `>= 1.7.0` on `PATH`. The committed root module pins providers
  to `aws ~> 5.60` and `random ~> 3.6`.
- AWS credentials with permission to manage VPC, IAM roles/policies,
  Lambda, API Gateway HTTP API, ACM, Route 53 records (the hosted zone
  itself is referenced as a data source — do not let Terraform manage the
  zone), Secrets Manager, RDS, and CloudWatch Logs in `us-east-1`.
- A public Route 53 hosted zone you control, referenced by zone ID in
  `terraform.tfvars`.
- Three Lambda zip artifacts (or the placeholder zips described below)
  staged at `./build/mcp.zip`, `./build/fraud.zip`, `./build/db_ops.zip`.

## One-liner placeholder zips for plan / apply smoke tests

The application teammate owns the real zip build (`ops/build/build_*_zip.sh`).
Until those scripts run, you can satisfy `filebase64sha256(...)` with three
tiny stubs from `infra/build/PLACEHOLDER_README.md`:

```bash
cd infra/build
cat > _stub_handler.py <<'PY'
def lambda_handler(event, context):
    return {"statusCode": 200, "body": '{"ok": true, "stub": true}'}
PY
zip -j mcp.zip _stub_handler.py
zip -j fraud.zip _stub_handler.py
zip -j db_ops.zip _stub_handler.py
```

These zips are not committed. They produce a runtime import error if
called against the canonical handler strings, which is acceptable for a
Terraform-only smoke test but is not the Phase 1 ChatGPT-connect gate.

## First-time setup

```bash
cd infra/
cp terraform.tfvars.example terraform.tfvars   # edit values for your account
terraform init
terraform fmt -recursive
terraform validate
```

`terraform.tfvars` is gitignored. Do not check it in.

## Phase-by-phase apply order

The single committed root module covers Phase 1 + Phase 2 + Phase 3 in one
graph. The phase flags below let you stage rollout if you want to validate
each integration point before adding the next.

### Phase 0 — init / validate

```bash
terraform init
terraform validate
terraform plan -out=tfplan      # only after placeholder zips exist
```

Confirm with `aws sts get-caller-identity` that you are pointed at the
intended AWS account, and confirm the Route 53 zone resolves:

```bash
terraform state show data.aws_route53_zone.root
```

### Phase 1 — public MCP endpoint (no DB, no fraud mock yet)

If you want to bring up only API Gateway + custom domain + Lambda, target
just those resources:

```bash
terraform apply \
  -target=aws_apigatewayv2_api.main \
  -target=aws_apigatewayv2_integration.mcp \
  -target=aws_apigatewayv2_route.mcp_post \
  -target=aws_apigatewayv2_route.health_get \
  -target=aws_apigatewayv2_stage.default \
  -target=aws_apigatewayv2_domain_name.main \
  -target=aws_apigatewayv2_api_mapping.main \
  -target=aws_acm_certificate_validation.main \
  -target=aws_route53_record.alias \
  -target=aws_route53_record.alias_ipv6 \
  -target=aws_lambda_function.mcp \
  -target=aws_lambda_permission.api_invoke_mcp
```

Validation:

- `dig +short <subdomain>.<domain_root>` returns the API Gateway alias target.
- `curl -i https://<subdomain>.<domain_root>/health` returns 200.
- ChatGPT Apps developer mode can add the connector with
  `Authorization supported = None` and list tools.

This is the most important validation gate in the whole plan. If ChatGPT
cannot connect at all, fall back per `docs/infra-implementation-plan.md`
section "Transport considerations" before continuing.

### Phase 2 — VPC, RDS, Secrets Manager, DB-ops Lambda

After Phase 1 passes, run a full apply:

```bash
terraform apply tfplan      # or `terraform apply` for a fresh plan
```

Validation:

- `aws rds describe-db-instances --db-instance-identifier ao-radar-pg --region us-east-1`
  shows `DBInstanceStatus=available`, `PubliclyAccessible=false`.
- `aws secretsmanager describe-secret --secret-id ao-radar/db/master --region us-east-1`
  returns the secret metadata. **Do not paste `get-secret-value` output.**
- DB-ops Lambda probe runs end-to-end against the seeded synthetic schema
  once the application teammate ships the deployed `migrate`/`seed`
  payloads.

### Phase 3 — Fraud-mock Lambda + Lambda VPC endpoint

Set `enable_lambda_vpce = true` in `terraform.tfvars` and re-apply. The
fraud-mock Lambda already exists in this single module, but the MCP Lambda
needs the Lambda interface VPC endpoint to invoke it from inside the VPC
without a NAT gateway.

Validation:

- `aws lambda invoke --function-name ao-radar-fraud-mock --payload ...`
  returns a deterministic synthetic response.
- The MCP Lambda can invoke fraud-mock from its VPC ENIs.

### Phase 4 — Demo readiness

Walk the manual demo checklist in
`docs/infra-implementation-plan.md` section 4. Confirm:

- `GET /health` and `POST /mcp` work over the custom domain.
- API Gateway throttle is high enough that demo retries are not blocked.
- All three Lambdas show reserved concurrency and synthetic env vars.
- CloudWatch Logs retention is 7 days and access logs do **not** include
  request bodies, query strings, cookies, or `Authorization` headers.
- Migrations, seed, and reset have only been run through `db_ops`.

## Apply / destroy commands

```bash
# Apply the full graph.
terraform apply

# Inspect state without exposing secrets.
terraform output                      # sensitive outputs are redacted.

# Tear down the stack. Order matters; do not delete the public hosted zone.
terraform destroy
```

After destroy, manual sanity checks (per the infra plan section
"Teardown / rollback"):

```bash
aws apigatewayv2 get-apis --region us-east-1
aws lambda list-functions --region us-east-1 \
  --query 'Functions[?starts_with(FunctionName, `ao-radar-`)].FunctionName'
aws rds describe-db-instances --region us-east-1 \
  --query 'DBInstances[?starts_with(DBInstanceIdentifier, `ao-radar-`)].DBInstanceIdentifier'
aws ec2 describe-vpcs --region us-east-1 --filters Name=tag:Project,Values=ao-radar
aws secretsmanager list-secrets --region us-east-1 \
  --query 'SecretList[?starts_with(Name, `ao-radar/`)].Name'
aws acm list-certificates --region us-east-1 \
  --query 'CertificateSummaryList[?DomainName==`<subdomain>.<domain_root>`]'
```

All commands above should return empty after a clean teardown. The Route 53
hosted zone for `<domain_root>` is **not** managed by this module; do not
delete it.

State-file caution: after destroy, `infra/terraform.tfstate` may still
reference the now-deleted secret (and historically the password). Delete
the local state file before sharing the working tree.

## Variables and outputs

See `variables.tf` for the full list (Appendix A in the infra plan). See
`outputs.tf` for `mcp_url`, `health_url`, `api_id`, `api_endpoint`,
Lambda names/ARNs, `rds_endpoint`, `db_secret_arn`, `vpc_id`,
`private_subnet_ids`. The DB master password is not an output. The
secret ARN is not sensitive.

## What is intentionally not here

The infra plan calls these out as out-of-scope for the hackathon stack and
this module honors that:

- No WAF, GuardDuty, CloudTrail wiring, Config rules, VPC flow logs,
  multi-AZ RDS, KMS CMKs, or monitoring/alerting.
- No NAT gateway. Outbound AWS API access from the VPC-attached Lambdas
  goes through interface VPC endpoints gated by `enable_*_vpce` flags.
- No public subnet, Internet Gateway, or default route on the private
  route table.
- No raw-SQL MCP tool, generic data-access endpoint, or auth on the public
  edge. Endpoint is intentionally unauthenticated; data is synthetic only.
