# AO Radar Infrastructure Implementation Plan

> Canonical infrastructure plan for AO Radar. This public-repo markdown file is the single source of truth for Terraform/AWS implementation work.
>
> Public-safety note: values such as domains, hosted-zone IDs, account IDs, and credentials are placeholders. Use synthetic/demo data only and keep Terraform state out of git.

Companion capability spec: `docs/spec.md`

## Status

Forward-looking implementation plan. No Terraform has been written yet. This document is the canonical specification a coding agent (or the project owner) follows to stand up the AWS infrastructure that hosts the AO Radar remote MCP server for the SCSP / GenAI.mil hackathon demo.

## Scope

**In scope:** All AWS infrastructure to expose a public, unauthenticated remote MCP HTTPS endpoint at `https://hackathon.example.com/mcp` backed by Lambda, with a private RDS Postgres 16 instance, a separate fraud-mock microservice, and a private DB-ops Lambda for deployed migration/seed/reset, all created fresh via Terraform.

**Out of scope:**
- Application code (MCP server implementation, FastMCP handlers, tool logic).
- MCP tool schemas beyond the *transport* contract API Gateway must support.
- Database schema, migrations, seed data — covered by the schema,
  application, and synthetic-data plans. Terraform owns only the private
  execution path for deployed migration/seed/reset.
- Real DTS / GenAI.mil / PII / GTCC / EFT data of any kind. Synthetic only.
  For the hackathon build, reference-corpus rows are synthetic demo excerpts
  only; do not load real DoD, JTR, DTMO, checklist, or government-system
  excerpts into fixtures or database seed data.
- Production hardening: WAF, multi-AZ RDS, KMS CMKs, VPC flow logs, GuardDuty, CloudTrail wiring, monitoring/alerting, blue/green deploy tooling.
- Public-facing spec text or marketing copy.
- Reuse of existing unrelated infrastructure; stand up everything new except the public hosted zone data source.

## Goals

1. ChatGPT.com / ChatGPT Apps developer mode can add `https://hackathon.example.com/mcp` as a custom remote MCP connector with `Authorization supported = None`, list tools, and invoke them — same surface contract used by hosted remote MCP servers.
2. The MCP Lambda can reach a private Postgres 16 RDS instance over a private subnet, and can invoke a separate fraud-mock Lambda.
3. Everything is created by `terraform apply` from a single root module under `infra/`. The only pre-existing AWS object referenced is the Route 53 public hosted zone for `example.com` (data source).
4. Demo-first hackathon posture: simple, cheap, and easy to debug beats production-grade hardening. Use a tiny single-AZ RDS instance, short log retention, and easy `terraform destroy`.
5. Phase 1 is implementable and demoable in isolation (Lambda + API GW + custom domain + cert + DNS), without RDS or the fraud mock.
6. Deployed migration, seed, and reset run through the Terraform-managed
   `db_ops` Lambda. Do not create manual probe, migration, or seed Lambdas.

## Inputs and assumptions

### AWS account / region

- Region: `us-east-1` (single region; no multi-region considerations).
- If the AWS account already contains unrelated infrastructure, do **not** read, modify, or share IAM roles, security groups, VPCs, or log groups with those stacks. Use a distinct name prefix (`ao-radar`) and `Project = ao-radar` tag everywhere.
- Existing Route 53 public hosted zone:
  - Domain: `example.com.`
  - Zone ID: `Z_PUBLIC_HOSTED_ZONE_ID`
  - Example `terraform.tfvars` values stay placeholder-only:
    ```hcl
    domain_root    = "example.com"
    hosted_zone_id = "Z_PUBLIC_HOSTED_ZONE_ID"
    subdomain      = "hackathon"
    ```
  - Reference by hosted-zone ID as a data source only — Terraform must not manage the zone itself and must not rely on a loose name lookup if another public zone with the same name ever exists:
    ```hcl
    data "aws_route53_zone" "root" {
      zone_id = var.hosted_zone_id
    }
    ```

### Application interface contract (informational; infra-only assumptions)

These are the contract points the infra must satisfy. Application behavior beyond these is out of scope.

- The MCP Lambda exposes a single HTTP entrypoint that handles both `POST /mcp` (Streamable HTTP transport, JSON-RPC framed) and `GET /health`. Optionally a `GET /sse` route may be added if the chosen MCP transport requires it (see Transport considerations).
- The MCP Lambda needs:
  - Outbound TCP 5432 to the RDS instance, on a private subnet, via the RDS security group.
  - Ability to read a JSON Secrets Manager secret named like `ao-radar/db/master` containing `{username, password, host, port, dbname, engine}`.
  - Ability to invoke the fraud-mock Lambda by ARN (AWS SDK call), or alternatively reach an explicitly documented HTTP route if Phase 3 rejects the SDK invoke path.
- The DB-ops Lambda is VPC-attached, private, and not integrated with API
  Gateway. It uses the same DB secret and runs only explicit operation
  payloads for `migrate`, `seed`, and `reset`/`seed` with reset.
- The fraud-mock Lambda is deterministic, stateless, and synthetic. It needs no database, no Secrets Manager access, and no VPC attachment for the default AWS SDK Invoke path; the MCP Lambda reaches the Lambda service through the Lambda interface VPC endpoint.
- The MCP endpoint is **unauthenticated** at the edge. ChatGPT Apps connects with `Authorization supported = None`.

### Verified upstream constraints

- ChatGPT Apps developer mode can connect to a public, unauthenticated HTTPS MCP URL (this pattern has been verified against a hosted remote MCP server). No token gating required for this demo.
- Remote MCP servers, per OpenAI docs, require a publicly reachable `server_url`. Streamable HTTP is the preferred transport; HTTP/SSE is supported as a legacy/alternative.
- API Gateway HTTP API is a public, AWS-managed regional service — it is **not** literally inside the VPC. The shape is "public API edge → private backend in VPC."
- A VPC-attached Lambda loses default internet egress. Putting it in a public subnet does not grant it internet. NAT or VPC endpoints are the only ways to reach AWS APIs from a VPC-attached Lambda.

## Architecture overview

```
ChatGPT.com / ChatGPT Apps developer mode
        │  HTTPS (no auth)
        ▼
hackathon.example.com  (Route 53 alias, A/AAAA)
        │
        ▼
ACM-terminated TLS  →  API Gateway HTTP API (regional)
        │                       │  AWS_PROXY integration (payload v2.0)
        │                       ▼
        │              ┌────────────────────────┐
        │              │  MCP Lambda            │  (VPC-attached, private subnets)
        │              │  ao-radar-mcp          │
        │              └─────────┬──────────────┘
        │                        │  TCP 5432 (intra-VPC)
        │                        ▼
        │              ┌────────────────────────┐
        │              │  RDS Postgres (tiny)   │  (private, single-AZ)
        │              │  ao-radar-pg           │
        │              └────────────────────────┘
        │                        ▲
        │                        │  migrate/seed/reset (operator invoke)
        │              ┌────────────────────────┐
        │              │  DB Ops Lambda         │  (VPC-attached, no API GW)
        │              │  ao-radar-db-ops       │
        │              └────────────────────────┘
        │                        ▲
        │                        │  Secrets Manager (interface VPC endpoint)
        │              ┌────────────────────────┐
        │              │  Secrets Manager       │
        │              │  ao-radar/db/master    │
        │              └────────────────────────┘
        │
        │              ┌────────────────────────┐
        └──────────────│  Fraud Mock Lambda     │  (separate function, no VPC by default)
                       │  ao-radar-fraud-mock   │
                       └────────────────────────┘
                                 ▲
                                 │  Direct AWS SDK Invoke
                                 │  (via Lambda interface VPC endpoint
                                 │   if MCP is VPC-attached and no NAT)
                                 │
                              MCP Lambda
```

Key structural points:
- The **API Gateway HTTP API is public** and managed; it sits outside the VPC and proxies into Lambda.
- The **MCP Lambda is VPC-attached** to private subnets so it can talk to RDS over private IPs.
- The **DB-ops Lambda is VPC-attached** and private. It is the only
  deployed path for migrations, seed, and reset.
- There is **no NAT gateway**, no public subnet, and no Internet Gateway by default. Outbound AWS API calls from the VPC-attached Lambda go through **interface VPC endpoints** for only the AWS APIs it actually calls.
- The **fraud-mock Lambda is not VPC-attached** — it exists as an independent microservice the MCP Lambda invokes via the AWS SDK.

## Naming, tagging, region

- Region: `us-east-1` (single).
- Name prefix variable: `var.name_prefix` defaults to `ao-radar`. All resource `name`/`name_prefix` arguments derive from this.
- Default tags applied by the AWS provider:
  ```hcl
  default_tags = {
    Project   = "ao-radar"
    Env       = "hackathon"
    ManagedBy = "terraform"
    Owner     = "project-owner"
  }
  ```
- Avoid name collisions with any existing resources. Do not import or reference unrelated infrastructure IDs.

## Terraform layout

Single root module under `infra/`. No submodules. Hackathon speed > modular polish.

| File                  | Purpose                                                                                  |
|-----------------------|------------------------------------------------------------------------------------------|
| `versions.tf`         | `terraform` block, required version, required providers and versions.                    |
| `providers.tf`        | `aws` provider config (region, default_tags). No assume_role; default credentials.       |
| `variables.tf`        | All input variables with defaults (see Appendix A).                                      |
| `locals.tf`           | Derived names, AZ list, common tag merges, CIDR blocks.                                  |
| `networking.tf`       | VPC, private isolated subnets, private route table, optional VPC endpoints.              |
| `security_groups.tf`  | Lambda SG (MCP), RDS SG, VPC endpoint SG.                                                |
| `iam.tf`              | Lambda execution roles (MCP, fraud mock, DB ops), policies (logs, VPC ENI, secrets, invoke). |
| `logs.tf`             | CloudWatch log groups for all Lambdas and API Gateway access logs.                       |
| `secrets.tf`          | `random_password` for DB master, Secrets Manager secret + version with DB JSON.          |
| `rds.tf`              | DB subnet group, `aws_db_instance` Postgres tiny.                                        |
| `lambda.tf`           | MCP, fraud-mock, and DB-ops `aws_lambda_function` resources; API GW invoke permission for MCP only. |
| `api_gateway.tf`      | HTTP API, integration, routes (`/mcp`, `/health`, optional `/sse`), stage, throttle.    |
| `dns.tf`              | ACM cert, DNS validation records, custom domain, API mapping, Route53 A/AAAA aliases.    |
| `outputs.tf`          | Public URL, API ID, Lambda names/ARNs, RDS endpoint (no password), secret ARN.           |

Add `infra/.terraform.lock.hcl` (committed) once `terraform init` runs.

State backend: **local state for hackathon** (`terraform.tfstate` in `infra/`). Note in README that the state file contains the RDS master password; do not commit, do not paste. If a remote backend is added later, S3 + DynamoDB lock is the standard shape — do not block Phase 1 on it.

## Resource inventory by file

Each entry lists the resource type, logical name, and the cross-file refs it depends on.

### `versions.tf`
- `terraform { required_version = ">= 1.7.0" }`
- `required_providers`:
  - `aws ~> 5.60`
  - `random ~> 3.6`

### `providers.tf`
- `provider "aws"` — `region = var.region`, `default_tags { tags = local.common_tags }`.

### `variables.tf` (see Appendix A for defaults)
- `region`, `name_prefix`, `domain_root`, `hosted_zone_id`, `subdomain`, `vpc_cidr`, `az_count`, `db_instance_class`, `db_allocated_storage`, `db_engine_version`, `lambda_runtime`, `lambda_memory_mb`, `lambda_timeout_s`, `mcp_reserved_concurrency`, `fraud_reserved_concurrency`, `db_ops_reserved_concurrency`, `api_throttle_rate`, `api_throttle_burst`, `log_retention_days`, `enable_secretsmanager_vpce` (bool), `enable_lambda_vpce` (bool), `enable_s3_gateway_endpoint` (bool), `enable_logs_vpce` (bool), `disable_execute_api_endpoint` (bool), `enable_sse_route` (bool, default false), `mcp_lambda_zip_path` (placeholder zip for first apply), `fraud_lambda_zip_path` (placeholder zip), `db_ops_lambda_zip_path` (placeholder zip).

### `locals.tf`
- `common_tags`
- `fqdn = "${var.subdomain}.${var.domain_root}"`
- `azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)`
- `private_subnet_cidrs` (computed via `cidrsubnet`)
- `data "aws_availability_zones" "available" { state = "available" }`
- `data "aws_caller_identity" "current" {}`
- `data "aws_region" "current" {}`
- `data "aws_route53_zone" "root"` (`zone_id = var.hosted_zone_id`; expected `Z_PUBLIC_HOSTED_ZONE_ID`)

### `networking.tf`
- `aws_vpc.main` — CIDR `var.vpc_cidr` (default `10.42.0.0/16`), DNS hostnames + DNS support enabled.
- `aws_subnet.private[*]` — one per AZ; no public IP mapping.
- `aws_route_table.private` + `aws_route_table_association.private[*]` — **no default route**; private subnets are isolated except via VPC endpoints.
- No `aws_internet_gateway`, public subnets, or public route table by default. Add them only if the fallback architecture introduces NAT or an internet-facing ALB.
- Optional endpoints, each gated separately. Do not over-optimize this for security purity; add only what makes the demo work:
  - `aws_vpc_endpoint.secretsmanager` — interface type, in private subnets, SG = endpoint SG, `private_dns_enabled = true`; required in Phase 2 if the VPC-attached MCP Lambda reads Secrets Manager without NAT.
  - `aws_vpc_endpoint.lambda` — interface type, in private subnets, SG = endpoint SG, `private_dns_enabled = true`; required in Phase 3 if the MCP Lambda invokes the fraud-mock Lambda without NAT.
  - `aws_vpc_endpoint.s3` — gateway type, attached to private route table; optional only if application code later uses S3.
  - `aws_vpc_endpoint.logs` — interface type, optional only if application code explicitly calls the CloudWatch Logs API from inside the VPC. Lambda's normal stdout/stderr log delivery is handled by the Lambda service and should not require this endpoint.

### `security_groups.tf`
- Keep security groups understandable and demo-friendly. Do **not** spend hackathon time chasing perfect egress minimization unless something is clearly unsafe or broken.
- `aws_security_group.mcp_lambda` — no ingress; allow broad outbound egress (`0.0.0.0/0`) for the demo, or at minimum egress to the RDS SG on TCP 5432 and TCP 443 to AWS/VPC endpoints. Broad egress is acceptable here because the route table still controls actual paths and the data is synthetic.
- `aws_security_group.db_ops_lambda` — no ingress; outbound to the RDS SG
  on TCP 5432 and TCP 443 to Secrets Manager. It may reuse `mcp_lambda`
  for hackathon speed only if the rules stay understandable.
- `aws_security_group.rds` — keep the one hard boundary: ingress TCP 5432
  from `mcp_lambda` SG and `db_ops_lambda` SG only;
  `publicly_accessible = false`. Default egress is fine.
- `aws_security_group.vpce` — interface VPC endpoint SG; ingress TCP 443
  from `mcp_lambda` SG and `db_ops_lambda` SG. Default egress is fine.

### `iam.tf`
- `aws_iam_role.mcp_lambda_exec` — assume role for `lambda.amazonaws.com`.
- Inline / managed attachments on `mcp_lambda_exec`, added by phase:
  - Phase 1: AWS managed policy ARN `arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole` (logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents).
  - Phase 2: AWS managed policy ARN `arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole` (manage ENIs) and custom policy `secretsmanager:GetSecretValue`. Scoping to the specific DB secret ARN is preferred, but `ao-radar/*` is acceptable for demo speed.
  - Phase 3: custom policy `lambda:InvokeFunction`. Scoping to the specific fraud-mock Lambda ARN is preferred, but `ao-radar-*` functions are acceptable for demo speed.
- `aws_iam_role.fraud_lambda_exec` — assume role for `lambda.amazonaws.com`.
  - AWS managed policy ARN `arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole` only.
- `aws_iam_role.db_ops_lambda_exec` — assume role for
  `lambda.amazonaws.com`.
  - Attach `AWSLambdaBasicExecutionRole`, `AWSLambdaVPCAccessExecutionRole`,
    and a scoped `secretsmanager:GetSecretValue` policy for the DB secret.
  - Do not grant API Gateway invoke permissions; operators invoke this
    function explicitly through AWS CLI/SDK with normal AWS credentials.
- `aws_lambda_permission.api_invoke_mcp` — allows `apigateway.amazonaws.com` to invoke MCP Lambda; use `source_arn = "${aws_apigatewayv2_api.main.execution_arn}/*/*"` for the specific HTTP API while routes are still evolving. A route-specific ARN is acceptable later, but validate it with `aws lambda get-policy` because HTTP API route ARN patterns are easy to over-tighten.

### `logs.tf`
- `aws_cloudwatch_log_group.mcp_lambda` — name `/aws/lambda/${name_prefix}-mcp`, retention `var.log_retention_days` (default 7).
- `aws_cloudwatch_log_group.fraud_lambda` — name `/aws/lambda/${name_prefix}-fraud-mock`, retention 7.
- `aws_cloudwatch_log_group.db_ops_lambda` — name
  `/aws/lambda/${name_prefix}-db-ops`, retention 7.
- `aws_cloudwatch_log_group.api_access` — name `/aws/apigatewayv2/${name_prefix}`, retention 7.

### `secrets.tf`
- `random_password.db_master` — length 32, `special = true`, `override_special = "!#$%&*()-_=+[]{}:,.?"`. This avoids RDS-disallowed `/`, `"`, `@`, and space, and also avoids quote/backslash shell-copy hazards.
- `aws_secretsmanager_secret.db_master` — name `${name_prefix}/db/master`, no KMS CMK (defaults to AWS-managed key), recovery_window_in_days `0` so `terraform destroy` force-deletes immediately. This is intentional for the hackathon stack; do not use that setting for durable environments.
- `aws_secretsmanager_secret_version.db_master` — JSON body:
  ```json
  {
    "engine": "postgres",
    "host": "<rds address only, no port>",
    "port": 5432,
    "username": "ao_radar_admin",
    "password": "<random>",
    "dbname": "ao_radar"
  }
  ```
  Reference `aws_db_instance.main.address` and `aws_db_instance.main.port` directly in `secret_string`, not the combined `endpoint` value, so `host` and `port` do not duplicate. That reference should naturally order RDS → secret version; use `depends_on` only if Terraform does not infer it after implementation.

### `rds.tf`
- `aws_db_subnet_group.main` — uses private subnets.
- `aws_db_instance.main`:
  - `identifier = "${name_prefix}-pg"`
  - `engine = "postgres"`, `engine_version = var.db_engine_version` (e.g. `"16.3"`).
  - `instance_class = var.db_instance_class` (default `db.t4g.micro`).
  - `allocated_storage = 20`, `storage_type = "gp3"`, `storage_encrypted = true`.
  - `username = "ao_radar_admin"`, `password = random_password.db_master.result`.
  - `db_name = "ao_radar"`.
  - `vpc_security_group_ids = [aws_security_group.rds.id]`.
  - `db_subnet_group_name = aws_db_subnet_group.main.name`.
  - `publicly_accessible = false`.
  - `multi_az = false`.
  - `backup_retention_period = 0` (intentionally disables automated backups/PITR for the disposable demo DB; if the selected engine/class rejects `0`, set `1` rather than spending time fighting the provider).
  - `deletion_protection = false`.
  - `skip_final_snapshot = true`.
  - `apply_immediately = true`.
  - `performance_insights_enabled = false`.
  - `monitoring_interval = 0`.

### `lambda.tf`
- `aws_lambda_function.mcp`:
  - `function_name = "${name_prefix}-mcp"`
  - `role = aws_iam_role.mcp_lambda_exec.arn`
  - `runtime = var.lambda_runtime` (e.g. `"python3.12"`)
  - `handler = "ao_radar_mcp.handler.lambda_handler"` after application code
    lands; Phase 1 may temporarily use a placeholder handler in the
    placeholder zip.
  - `filename = var.mcp_lambda_zip_path` and `source_code_hash = filebase64sha256(var.mcp_lambda_zip_path)` — Phase 1 may use a tiny placeholder zip with a stub handler returning `{"ok": true}` so `terraform apply` succeeds before app code exists.
  - `memory_size = var.lambda_memory_mb` (default 512).
  - `timeout = var.lambda_timeout_s` (default 25; must stay under API GW HTTP API 30s integration cap).
  - `reserved_concurrent_executions = var.mcp_reserved_concurrency` (default 10).
  - `vpc_config` — Phase 2 onward — `subnet_ids = aws_subnet.private[*].id`, `security_group_ids = [aws_security_group.mcp_lambda.id]`.
  - `environment.variables` are phase-gated to avoid Terraform references to resources that do not exist yet:
    - Phase 1: `LOG_LEVEL = "INFO"`,
      `MCP_SERVER_NAME = "ao-radar-mcp"`,
      `MCP_SERVER_VERSION = "0.1.0"`,
      `DEMO_DATA_ENVIRONMENT = "synthetic_demo"`.
    - Phase 2: add `DB_SECRET_ARN = aws_secretsmanager_secret.db_master.arn`,
      `DB_CONNECT_TIMEOUT_S = "5"`,
      `DB_STATEMENT_TIMEOUT_MS = "15000"`.
    - Phase 3: add `FRAUD_FUNCTION_NAME = aws_lambda_function.fraud_mock.function_name`,
      `FRAUD_INVOKE_TIMEOUT_S = "5"`.
    - Do not set `BOUNDARY_REMINDER_TEXT` in Terraform for the demo. The
      application uses its canonical constant and rejects any override that
      omits required authority-boundary clauses.
- `aws_lambda_function.fraud_mock`:
  - `function_name = "${name_prefix}-fraud-mock"`
  - `role = aws_iam_role.fraud_lambda_exec.arn`
  - Same runtime; smaller memory (`256`); shorter timeout (`10s`); reserved concurrency `5`.
  - `handler = "ao_radar_fraud_mock.handler.lambda_handler"`.
  - Environment: `LOG_LEVEL = "INFO"`,
    `DEMO_DATA_ENVIRONMENT = "synthetic_demo"`,
    `FRAUD_SIGNAL_SOURCE_LABEL = "synthetic_compliance_service_demo"`,
    `FRAUD_DETERMINISTIC_SEED = "ao-radar-synthetic-v1"`.
  - **No `vpc_config`** by default. Stays out of the VPC.
- `aws_lambda_function.db_ops`:
  - `function_name = "${name_prefix}-db-ops"`
  - `role = aws_iam_role.db_ops_lambda_exec.arn`
  - `runtime = var.lambda_runtime`
  - `handler = "ao_radar_db_ops.handler.lambda_handler"`.
  - `filename = var.db_ops_lambda_zip_path` and
    `source_code_hash = filebase64sha256(var.db_ops_lambda_zip_path)`.
  - Memory `512`, timeout `60s`, reserved concurrency
    `var.db_ops_reserved_concurrency` (default 1).
  - `vpc_config` uses the private subnets and DB-ops Lambda SG.
  - Environment: `LOG_LEVEL = "INFO"`,
    `DB_SECRET_ARN = aws_secretsmanager_secret.db_master.arn`,
    `DB_CONNECT_TIMEOUT_S = "5"`,
    `DB_STATEMENT_TIMEOUT_MS = "15000"`,
    `DEMO_DATA_ENVIRONMENT = "synthetic_demo"`.
  - This function is canonical for deployed migration/seed/reset. Do not
    create ad hoc probe, migration, or seed Lambdas outside Terraform.

### `api_gateway.tf`
- `aws_apigatewayv2_api.main`:
  - `name = "${name_prefix}-http-api"`
  - `protocol_type = "HTTP"`
  - `disable_execute_api_endpoint = var.disable_execute_api_endpoint`. Default `false` for the demo so the execute-api hostname remains available as a fallback if DNS/custom-domain setup is flaky. Turning it off is a production-hardening follow-up, not a demo blocker.
- `aws_apigatewayv2_integration.mcp`:
  - `api_id = aws_apigatewayv2_api.main.id`
  - `integration_type = "AWS_PROXY"`
  - `integration_uri = aws_lambda_function.mcp.invoke_arn`
  - `payload_format_version = "2.0"`
  - `timeout_milliseconds = 29000` (max for HTTP API).
- `aws_apigatewayv2_route.mcp_post` — `route_key = "POST /mcp"`, target = integration.
- `aws_apigatewayv2_route.health_get` — `route_key = "GET /health"`, target = same integration (Lambda dispatches by path).
- Optional `aws_apigatewayv2_route.sse_get` — `route_key = "GET /sse"`, gated by `var.enable_sse_route`. See Transport considerations for caveats.
- `aws_apigatewayv2_stage.default`:
  - `name = "$default"`, `auto_deploy = true`.
  - `default_route_settings`:
    - `throttling_burst_limit = var.api_throttle_burst` (default 100)
    - `throttling_rate_limit = var.api_throttle_rate` (default 50)
    - `detailed_metrics_enabled = false` by default; enable only if useful while debugging
  - `access_log_settings`:
    - `destination_arn = aws_cloudwatch_log_group.api_access.arn`
    - `format` = JSON template with requestId, ip, requestTime, routeKey, status, responseLength, integrationLatency. Do **not** include request bodies, query strings, cookies, `Authorization`, or arbitrary headers in access logs.
  - HTTP API access logs use the stage `access_log_settings` and the log group ARN. Do not add the REST API `aws_api_gateway_account` CloudWatch role path unless `terraform apply` or AWS explicitly errors; it is not part of the normal HTTP API setup.

### `dns.tf`
- `aws_acm_certificate.main`:
  - `domain_name = local.fqdn`
  - `validation_method = "DNS"`
  - Created in the same provider region as the regional API Gateway domain (`us-east-1` for this plan).
  - `lifecycle { create_before_destroy = true }`
- `aws_route53_record.cert_validation` — `for_each` over `aws_acm_certificate.main.domain_validation_options`, written into `data.aws_route53_zone.root.zone_id`, with `allow_overwrite = true` so re-issued cert validation records don't block the hackathon flow.
- `aws_acm_certificate_validation.main` — depends on the validation records.
- `aws_apigatewayv2_domain_name.main`:
  - `domain_name = local.fqdn`
  - `domain_name_configuration { certificate_arn = aws_acm_certificate_validation.main.certificate_arn, endpoint_type = "REGIONAL", security_policy = "TLS_1_2" }`
- `aws_apigatewayv2_api_mapping.main`:
  - `api_id = aws_apigatewayv2_api.main.id`
  - `domain_name = aws_apigatewayv2_domain_name.main.id`
  - `stage = aws_apigatewayv2_stage.default.name` (`"$default"`)
- `aws_route53_record.alias`:
  - `zone_id = data.aws_route53_zone.root.zone_id`
  - `name = local.fqdn`
  - `type = "A"`
  - `alias { name = aws_apigatewayv2_domain_name.main.domain_name_configuration[0].target_domain_name, zone_id = aws_apigatewayv2_domain_name.main.domain_name_configuration[0].hosted_zone_id, evaluate_target_health = false }`
- `aws_route53_record.alias_ipv6`:
  - Same alias target as above.
  - `type = "AAAA"` to match the intended dual-stack custom domain and the validation checklist. If AWS rejects AAAA for this API Gateway regional target at apply time, remove the AAAA record and the AAAA validation command together.

### `outputs.tf`
- `mcp_url = "https://${local.fqdn}/mcp"`
- `health_url = "https://${local.fqdn}/health"`
- `api_id`, `api_endpoint`
- `mcp_lambda_name`, `mcp_lambda_arn`
- `fraud_lambda_name`, `fraud_lambda_arn`
- `rds_endpoint` (host:port only — no password)
- `db_secret_arn`
- `vpc_id`, `private_subnet_ids`
- Mark nothing `sensitive` that doesn't need to be; mark `db_secret_arn` non-sensitive (it's an ARN, not a value).

## Implementation phases

Each phase ends in a working `terraform apply` and a meaningful validation step. Do not skip ahead; the value of phasing is catching ChatGPT-Apps connector fit at the earliest possible point.

### Phase 0 — Repo bootstrap (no managed AWS resources)
1. Create `infra/` directory.
2. Add `versions.tf`, `providers.tf`, `variables.tf`, `locals.tf`, `outputs.tf` with no resources yet (just data sources for the Route 53 zone, AZs, caller identity, region).
3. `terraform init`, `terraform fmt -recursive`, `terraform validate`.
4. Confirm AWS credentials work: `aws sts get-caller-identity`. Confirm region matches.
5. Confirm the hosted zone data source resolves specifically to the expected public hosted zone ID, not just any zone named `example.com`.

**Exit criterion:** `terraform validate` succeeds; data sources resolve in `terraform plan`.

### Phase 1 — Public MCP endpoint (no VPC, no DB, no fraud mock)
Files added: `iam.tf` (only `mcp_lambda_exec` + `AWSLambdaBasicExecutionRole`), `logs.tf` (mcp + api_access groups), `lambda.tf` (only `aws_lambda_function.mcp`, **no `vpc_config` yet**, placeholder zip), `api_gateway.tf`, `dns.tf`.

Lambda placeholder zip: a single-file Python handler that responds to `GET /health` with `{"ok": true}` and to `POST /mcp` with a minimal MCP-compatible `tools/list` reply listing one toy tool (e.g. `echo`). The zip is built outside Terraform (one-line `zip` command in a README); Terraform just references its path. This is a transport smoke-test fixture only. The toy `echo` catalog is never the AO Radar tool catalog and must be replaced by the spec section 4.5 tool list as soon as the FastMCP application package is deployed. If a handwritten stub fails ChatGPT's MCP handshake, swap in the smallest real MCP server package and keep Terraform unchanged; do not treat the stub response shape as the application contract.

After apply, validate:
- `dig +short hackathon.example.com` returns the API GW alias target.
- `curl -i https://hackathon.example.com/health` returns 200.
- `curl -i -X POST https://hackathon.example.com/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'` returns the toy tool list.
- In ChatGPT Apps developer mode, add the connector with `Authorization supported = None`, list tools, invoke the toy tool, see a response.

**Exit criterion:** ChatGPT Apps successfully discovers and calls the toy tool over the custom domain, or, after the application Phase 1 package replaces the toy stub, discovers the full spec section 4.5 catalog and receives safe `not_implemented` responses from each tool. **This is the most important validation gate in the whole plan** — if ChatGPT cannot connect to a Lambda+API GW MCP endpoint at all, jump to the Transport considerations fallback before continuing.

After the custom domain, TLS, and ChatGPT connector gate pass, keep `disable_execute_api_endpoint = false` unless there is a specific reason to remove the fallback hostname. For this demo, reliability beats tidiness.

### Phase 2 — VPC, RDS, Secrets Manager, DB ops
Files added: `networking.tf`, `security_groups.tf`, `secrets.tf`, `rds.tf`. Modify `lambda.tf` to attach MCP Lambda to private subnets and add `aws_lambda_function.db_ops`. Modify `iam.tf` to add `AWSLambdaVPCAccessExecutionRole` and `secretsmanager:GetSecretValue` policies for MCP and DB ops.

Set `enable_secretsmanager_vpce = true` so the VPC-attached Lambda can reach Secrets Manager without a NAT gateway. Leave `enable_lambda_vpce = false` until Phase 3 unless you intentionally accept the extra endpoint cost early.

After apply, validate:
- `aws rds describe-db-instances --db-instance-identifier ao-radar-pg --region us-east-1 --query 'DBInstances[0].[DBInstanceStatus,PubliclyAccessible,Endpoint.Address]'` shows `available`, `false`, and a private endpoint.
- `aws secretsmanager get-secret-value --secret-id ao-radar/db/master --region us-east-1 --query SecretString` returns valid JSON (contains host/port matching RDS).
- The DB-ops Lambda can run a `{"operation":"migrate","dry_run":true}`
  or equivalent application-supported probe that fetches the secret and
  opens a TCP connection to the RDS endpoint. Do not create a separate
  one-off probe Lambda.
- The MCP Lambda can fetch the secret and open a TCP connection to the RDS
  endpoint once the application package has a DB probe or read tool.

**Exit criterion:** DB ops and MCP Lambdas, attached to private subnets, can read the DB secret and reach the RDS endpoint privately.

### Phase 3 — Fraud-mock Lambda
Files modified: `iam.tf` (add `fraud_lambda_exec` + `lambda:InvokeFunction` policy on MCP role scoped to fraud-mock ARN), `logs.tf` (add fraud_lambda group), `lambda.tf` (add `aws_lambda_function.fraud_mock`), `networking.tf` (enable Lambda interface VPC endpoint).

The fraud-mock Lambda is **not** VPC-attached. The MCP Lambda invokes it via the AWS SDK (`Invoke` API). For VPC-attached Lambda → Lambda invocation to work without NAT, set `enable_lambda_vpce = true` and use the Lambda interface VPC endpoint.

Alternative considered: expose the fraud mock via its own API Gateway route (e.g. `POST /internal/fraud`) and have the MCP Lambda call it over the public custom domain. This avoids needing the Lambda VPC endpoint but increases attack surface (the route would be reachable from the internet) and adds latency. **Recommend the AWS SDK Invoke + VPC endpoint path.** If the route alternative is chosen, gate it behind a private header value, never a query string (still not auth-grade but raises the bar), and document the choice.

After apply, validate:
- `aws lambda invoke --function-name ao-radar-fraud-mock --payload '{"voucher_id":"V-1042"}' --cli-binary-format raw-in-base64-out --region us-east-1 /tmp/fraud-out.json` returns 200 and a deterministic synthetic response.
- From the MCP Lambda (probe path), `boto3.client("lambda").invoke(...)` succeeds against the fraud mock.

**Exit criterion:** MCP Lambda can invoke fraud-mock Lambda from inside the VPC without a NAT gateway.

### Phase 4 — Demo readiness, not production hardening
- Confirm the endpoint works from ChatGPT over the custom domain. If the execute-api hostname also works, that is acceptable for this demo.
- Confirm basic API Gateway throttling is present, but do not make rate limits so tight that judging/demo retries get blocked.
- Confirm reserved concurrency exists on all three Lambdas, sized for a small live demo rather than a public launch.
- Leave broad Lambda egress in place if it makes debugging simpler. Keep RDS private and SG-limited; that is the important boundary.
- Confirm log retention is short (`7` days by default).
- Access logs may include route/method/status/request ID and integration latency. Avoid logging credentials or real PII; synthetic request payload logging is acceptable temporarily if it materially helps debug the demo, but do not commit or publish those logs.
- Confirm the exposed MCP tools remain synthetic/narrow. Mutation-like tools are acceptable if scoped to demo data and visibly auditable.
- Confirm migrations, seed, and reset have run only through `db_ops` for the
  deployed stack; there should be no manual probe, migration, or seed Lambda
  resources outside Terraform.
- Add a one-page `infra/README.md` with `apply` / `destroy` instructions, the placeholder zip recipe, and a teardown reminder. (This README is a follow-up artifact, not part of this plan's "single markdown file" deliverable.)

## Transport considerations

The MCP transport choice is the highest-risk infra question because it interacts with API Gateway HTTP API and Lambda limits.

- **Streamable HTTP (preferred).** Each tool call is a single `POST /mcp` request that returns a single JSON-RPC response within a few seconds. This works cleanly with API GW HTTP API + Lambda proxy: bounded by the non-increaseable HTTP API 30s integration timeout and Lambda's synchronous response payload limit. **Default to this.** Set Lambda timeout `≤ 25s` to stay safely under the 30s API GW cap.
- **HTTP/SSE (legacy / fallback).** Uses a long-lived `GET /sse` event stream the server pushes to. API Gateway **HTTP API** Lambda proxy responses are buffered for this plan's integration shape, and the request is bounded by 30s. If the chosen MCP framework defaults to SSE for the server-to-client direction, behavior will likely be broken or degraded.
  - First-line workaround: configure the server to use Streamable HTTP only, no SSE upgrade.
  - If SSE is mandatory, fallback infra paths (in order of preference):
    1. **API Gateway REST API with Lambda response streaming**, if Terraform/OpenAPI support is acceptable for the hackathon timeline. This preserves the API Gateway/custom-domain shape but is a different API Gateway product than the HTTP API in this plan.
    2. **Lambda Function URL with response streaming behind CloudFront**, with CloudFront serving `hackathon.example.com` using ACM. A bare Lambda Function URL cannot be fronted by Route 53 alone for this custom TLS hostname because the function URL certificate is for the AWS-owned function URL domain.
    3. **ECS Fargate behind ALB**, with the ALB terminating TLS using the same ACM cert. Higher cost, longer to stand up, but native long-lived connection support. Only pursue if the Phase 1 ChatGPT-connect test fails on Lambda.
- The `/sse` route is left as an opt-in (`enable_sse_route = false` by default) so the agent doesn't wire infra for a transport that cannot work end-to-end on Lambda+API GW.

The decision tree at Phase 1 exit:
1. ChatGPT connects + `tools/list` works + tool invocation returns → continue with Lambda+API GW.
2. ChatGPT connects + `tools/list` works + tool invocation hangs/times out → check Streamable vs SSE in the server config; do not change infra yet.
3. ChatGPT cannot connect at all to a Lambda-backed MCP URL even with the toy tool → decide between REST API response streaming, Function URL + CloudFront, or ECS/Fargate; do not point Route 53 directly at a bare Function URL and assume custom TLS will work.

Fallback acceptance checks are the same regardless of which path is chosen:
`GET /health` returns server identity, `POST /mcp initialize` returns the
configured `MCP_SERVER_NAME`/`MCP_SERVER_VERSION`, `tools/list` returns the
spec catalog once the app package is deployed, one read-only tool invocation
returns inside the client timeout, and unknown routes still return 404 over
the public custom domain.

## Networking decisions

- **No NAT gateway.** A NAT GW has a nontrivial fixed hourly cost plus per-GB processing; default to no NAT.
- **No public subnets by default.** API Gateway and Route 53 are public managed services outside the VPC. Lambda/RDS/VPCE resources stay in private isolated subnets.
- **VPC endpoints (interface)** for Secrets Manager and Lambda are how the VPC-attached Lambda reaches AWS APIs without a NAT. Each interface endpoint costs per AZ-hour, so create Secrets Manager in Phase 2 and Lambda only in Phase 3 when the SDK invoke path exists.
- **VPC endpoint (gateway) for S3** is free, but keep it disabled until code actually needs S3; adding speculative endpoints makes validation noisier.
- **CloudWatch Logs from a VPC-attached Lambda**: normal stdout/stderr log delivery is handled by the Lambda service, not by your function's VPC ENI path. Do not add a Logs interface endpoint just for ordinary Lambda logging. Add `aws_vpc_endpoint.logs` only if the application code itself calls the CloudWatch Logs API from inside the VPC.
- **Two AZs minimum** for the private subnets (RDS subnet group requires ≥ 2 AZs even for single-AZ instances). Default `var.az_count = 2`.

## Security posture

This is a hackathon demo, not a production authorization boundary. The goal is: **nothing real, easy to debug, cheap to destroy**. Do not spend build time adding enterprise controls that do not improve the judge-facing demo.

- **Public endpoint, no auth.** This is intentional and acceptable because:
  - Data is synthetic only.
  - Routes are narrow: `POST /mcp`, `GET /health`, optionally `GET /sse`.
  - API Gateway throttle and Lambda reserved concurrency provide basic runaway protection.
  - Keeping the default `*.execute-api.us-east-1.amazonaws.com` endpoint enabled is acceptable as a fallback during the demo. Prefer the custom domain in screenshots and ChatGPT config, but do not block launch on disabling the fallback hostname.
  - Log retention is short. Logs are for debugging, not compliance.
- **No WAF, no OAuth, no API keys, no JWTs, no IAM auth on API Gateway.** All are out of scope for this demo.
- **IAM: pragmatic scoping, not perfection.**
  - MCP Lambda role: logs, VPC ENI management, Secrets Manager read for the demo secret path, and Lambda invoke for the demo fraud function. Specific-ARN scoping is nice; `ao-radar/*` / `ao-radar-*` resource patterns are fine if they unblock implementation.
  - Fraud mock role: logs only unless the app code proves it needs more.
  - API Gateway → MCP Lambda permission can be scoped to the specific HTTP API ARN; do not sink time into route-perfect ARNs unless AWS complains.
- **Security groups:**
  - Keep RDS private: ingress TCP 5432 only from MCP Lambda SG and `publicly_accessible = false`. This is the boundary worth preserving.
  - MCP Lambda SG: no ingress. Broad outbound egress is acceptable for the demo, especially while debugging VPC endpoints/SDK calls. Tighten later only if there is extra time.
  - VPCE SG: allow TCP 443 from MCP Lambda SG. Default egress is fine.
- **Secrets:**
  - DB master password is a `random_password`. Do not commit `terraform.tfstate`. Do not paste output that includes the password.
  - Secret stored in Secrets Manager with default AWS-managed key; CMK out of scope.
  - Never reference real credentials in variables, defaults, or examples.
- **Request data hygiene:**
  - Do not put credentials, tokens, or sensitive test values in URLs or query strings.
  - Synthetic MCP request payloads may be logged temporarily when debugging. Do not log real PII because there should be no real PII in the system. Do not publish logs.
- **No CloudTrail wiring, no GuardDuty, no Config rules, no VPC flow logs, no KMS CMKs, no compliance monitoring.** All are out of scope.

## Cost guardrails

- RDS `db.t4g.micro`, 20 GB gp3, single-AZ, no backups, no Performance Insights, no enhanced monitoring. Roughly cents per hour while running.
- No NAT gateway.
- Interface VPC endpoints: a few cents per hour each while the stack exists.
- Lambda: pay per invocation; reserved concurrency limits runaway traffic without choking the demo.
- API Gateway HTTP API: per-request pricing; trivial at demo volume.
- ACM cert: free.
- Route 53 hosted zone: not managed by this stack; pre-existing.
- CloudWatch Logs: 7-day retention.

Tear down promptly after the demo to keep total cost in single-digit dollars.

## Validation checklist and commands

Run after each phase (some commands only meaningful from Phase 2 / 3 onward).

### Terraform
- `cd infra && terraform fmt -recursive`
- `terraform init` (once)
- `terraform validate`
- Before `plan`, create a local, uncommitted `terraform.tfvars` from the
  Appendix A placeholders and set only public-safe values such as
  `domain_root`, `hosted_zone_id`, and `subdomain`. Do not commit the file.
- `terraform plan -out=tfplan`
- `terraform apply tfplan`
- `terraform output`
- `terraform state show data.aws_route53_zone.root` and confirm `zone_id = Z_PUBLIC_HOSTED_ZONE_ID`
- Before creating RDS, verify the selected engine minor is currently orderable in `us-east-1`: `aws rds describe-db-engine-versions --engine postgres --engine-version <var.db_engine_version> --region us-east-1`

### DNS / TLS
- `dig +short hackathon.example.com`
- `dig +short hackathon.example.com AAAA`
- `openssl s_client -connect hackathon.example.com:443 -servername hackathon.example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates`

### API Gateway / Lambda
- `aws apigatewayv2 get-apis --region us-east-1 --query 'Items[?Name==`ao-radar-http-api`].[ApiId,ApiEndpoint,DisableExecuteApiEndpoint]'`
- `aws apigatewayv2 get-domain-name --domain-name hackathon.example.com --region us-east-1`
- The custom domain should succeed. The execute-api hostname may also work as a demo fallback; that is acceptable.
- `aws lambda get-function --function-name ao-radar-mcp --region us-east-1 --query 'Configuration.[FunctionName,Runtime,Timeout,MemorySize,ReservedConcurrentExecutions,VpcConfig.SubnetIds,VpcConfig.SecurityGroupIds]'`
- `aws lambda get-function --function-name ao-radar-fraud-mock --region us-east-1 --query 'Configuration.[FunctionName,Runtime,Timeout,MemorySize,ReservedConcurrentExecutions]'`
- `aws lambda get-function --function-name ao-radar-db-ops --region us-east-1 --query 'Configuration.[FunctionName,Runtime,Handler,Timeout,ReservedConcurrentExecutions,VpcConfig.SubnetIds,VpcConfig.SecurityGroupIds]'`
- `aws lambda get-policy --function-name ao-radar-mcp --region us-east-1` and confirm API Gateway can invoke the function. Specific API ARN scoping is preferred, but do not over-debug ARN exactness if invocation works and the stack remains demo-only.

### Endpoint smoke tests
- `curl -i https://hackathon.example.com/health`
- `curl -i -X POST https://hackathon.example.com/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`
- Unknown route returns 404: `curl -i https://hackathon.example.com/nope`
- Throttle behavior (best-effort visual): hammer `/health` briefly and confirm 429s appear above the configured rate.

### RDS / Secrets
- `aws rds describe-db-instances --db-instance-identifier ao-radar-pg --region us-east-1 --query 'DBInstances[0].[DBInstanceStatus,PubliclyAccessible,MultiAZ,StorageEncrypted,DeletionProtection,Endpoint.Address,Endpoint.Port]'`
- `aws secretsmanager describe-secret --secret-id ao-radar/db/master --region us-east-1`
- Do not paste `aws secretsmanager get-secret-value` output into tickets, chat, or logs; use it only locally to confirm JSON shape.
- Invoke DB ops for the deployed migration/seed path, once the application
  package supports it:
  `aws lambda invoke --function-name ao-radar-db-ops --payload '{"operation":"migrate","dry_run":true}' --cli-binary-format raw-in-base64-out --region us-east-1 /tmp/ao-radar-db-ops.json`.
  Do not create a one-off VPC-attached probe Lambda.

### CloudWatch
- `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/ao-radar --region us-east-1`
- `aws logs describe-log-groups --log-group-name-prefix /aws/apigatewayv2/ao-radar --region us-east-1`
- `aws logs tail /aws/lambda/ao-radar-mcp --since 5m --region us-east-1` after a request to confirm logging works.

### ChatGPT Apps connect
- ChatGPT.com → developer mode → add MCP connector → URL `https://hackathon.example.com/mcp`, `Authorization supported = None`, `Authorization used = None`.
- Confirm tool list refresh shows the toy tool only during the infra
  transport smoke test. After the application Phase 1 package is deployed,
  it must show the spec section 4.5 catalog, not `echo`.
- Invoke a tool; confirm a non-error response and a corresponding entry in `/aws/lambda/ao-radar-mcp` logs.

## Teardown / rollback

Order matters; some resources block others.

1. `terraform destroy` from `infra/`.
2. If destroy fails on RDS due to deletion protection (shouldn't happen — `deletion_protection = false`), set the flag explicitly and re-run.
3. If destroy fails on the ACM cert because Route 53 validation records are still mapped to it, re-run; `create_before_destroy` should handle it but a stuck cert can be manually re-attempted.
4. Manual sanity check after destroy:
   - `aws apigatewayv2 get-apis --region us-east-1` — no `ao-radar-http-api`.
   - `aws lambda list-functions --region us-east-1 --query 'Functions[?starts_with(FunctionName, `ao-radar-`)].FunctionName'` — empty.
   - `aws rds describe-db-instances --region us-east-1 --query 'DBInstances[?starts_with(DBInstanceIdentifier, `ao-radar-`)].DBInstanceIdentifier'` — empty.
   - `aws ec2 describe-vpcs --region us-east-1 --filters Name=tag:Project,Values=ao-radar` — empty.
   - `aws secretsmanager list-secrets --region us-east-1 --query 'SecretList[?starts_with(Name, `ao-radar/`)].Name'` — empty (recovery window 0 means immediate hard delete).
   - `aws acm list-certificates --region us-east-1 --query 'CertificateSummaryList[?DomainName==`hackathon.example.com`]'` — empty.
   - `aws route53 list-resource-record-sets --hosted-zone-id Z_PUBLIC_HOSTED_ZONE_ID --query 'ResourceRecordSets[?Name==`hackathon.example.com.`]'` — empty.
5. **Do not delete** the Route 53 hosted zone for `example.com`. It is referenced as a data source and shared with other work.
6. State file caution: after destroy, `terraform.tfstate` may still reference the now-deleted secret (and historically the password). Treat the state file as sensitive at all times; delete it locally if the working tree is being shared.

## Out of scope (reiterated)

- Application code (MCP server, FastMCP/python implementation, tool dispatch).
- MCP tool input/output schemas beyond what makes API Gateway routing decisions.
- Database schema, migration contents, fixtures, and seed data contents.
  Terraform still owns the private DB-ops Lambda that executes the deployed
  migrate/seed/reset operations.
- Real user data of any kind.
- Auth (OAuth, API keys, JWTs, IAM auth on API GW). Endpoint is intentionally unauthenticated.
- WAF, GuardDuty, CloudTrail, Config, VPC flow logs, multi-AZ HA, KMS CMKs, monitoring/alerting.
- CI/CD pipeline for the Lambda zip artifact (build/package/upload).
- Reuse of unrelated infrastructure of any kind.

## Open questions

- Does ChatGPT Apps developer mode tolerate the buffered (non-streaming) response from API GW HTTP API for `POST /mcp` Streamable HTTP, end-to-end, with the chosen MCP server framework? Phase 1 is the first concrete answer.
- Do MCP tool calls in this app exceed the 30 s API GW HTTP API timeout? If yes, infra needs REST API response streaming, Function URL + CloudFront, or ECS/Fargate fallback.
- If the streaming fallback is needed, does the Terraform AWS provider expose the required API Gateway REST API response streaming settings cleanly enough, or should the fallback be implemented through an OpenAPI import?
- Will the MCP Lambda be packaged as zip (Phase 1 default) or as a container image? Plan currently assumes zip; container is a one-line resource swap.
- Should the fraud mock be invoked via AWS SDK (current default) or via a dedicated internal HTTP route on the same API? Plan defaults to SDK + Lambda VPC endpoint.
- Is local Terraform state acceptable for the demo window, or should an S3 backend be added before sharing the working tree with anyone else?
- Does application code explicitly call the CloudWatch Logs API from inside the VPC? If yes, add the optional Logs interface endpoint; ordinary Lambda stdout/stderr logging should not need it.
- Does API Gateway accept the planned AAAA alias target for this regional HTTP API custom domain in this account/region? If not, remove both the AAAA record and the AAAA validation step.

## Appendix A — Variables (suggested defaults)

| Variable                       | Type     | Default                          | Notes                                                        |
|--------------------------------|----------|----------------------------------|--------------------------------------------------------------|
| `region`                       | string   | `"us-east-1"`                    | Single region.                                               |
| `name_prefix`                  | string   | `"ao-radar"`                     | Prefix for all resource names + tag.                         |
| `domain_root`                  | string   | `"example.com"`              | Existing Route 53 hosted zone (data source).                 |
| `hosted_zone_id`               | string   | `"Z_PUBLIC_HOSTED_ZONE_ID"`        | Pin the existing public hosted zone data source by ID.        |
| `subdomain`                    | string   | `"hackathon"`                    | Final FQDN: `hackathon.example.com`.                     |
| `vpc_cidr`                     | string   | `"10.42.0.0/16"`                 | Avoid overlap with anything else in the account.             |
| `az_count`                     | number   | `2`                              | RDS subnet group requires ≥ 2.                               |
| `db_instance_class`            | string   | `"db.t4g.micro"`                 | Tiny.                                                        |
| `db_allocated_storage`         | number   | `20`                             | gp3.                                                         |
| `db_engine_version`            | string   | `"16.3"`                         | Verify current minor at apply time.                          |
| `lambda_runtime`               | string   | `"python3.12"`                   | Adjust to match app team's runtime.                          |
| `lambda_memory_mb`             | number   | `512`                            | MCP Lambda.                                                  |
| `lambda_timeout_s`             | number   | `25`                             | Stay under API GW HTTP API 30 s cap.                         |
| `mcp_reserved_concurrency`     | number   | `10`                             | Enough for a small live demo; still caps runaway traffic.     |
| `fraud_reserved_concurrency`   | number   | `5`                              | Enough for a small live demo; still caps runaway traffic.     |
| `db_ops_reserved_concurrency`  | number   | `1`                              | Prevent concurrent migrate/seed/reset operations.             |
| `api_throttle_rate`            | number   | `50`                             | Requests per second; avoid blocking demo retries.             |
| `api_throttle_burst`           | number   | `100`                            | Burst; avoid blocking demo retries.                          |
| `log_retention_days`           | number   | `7`                              | Short, hackathon.                                            |
| `enable_secretsmanager_vpce`   | bool     | `true` (Phase 2 onward)          | Required when VPC Lambda reads Secrets Manager without NAT.   |
| `enable_lambda_vpce`           | bool     | `false` until Phase 3            | Required when VPC Lambda invokes fraud Lambda without NAT.    |
| `enable_s3_gateway_endpoint`   | bool     | `false`                          | Enable only if code actually uses S3.                        |
| `enable_logs_vpce`             | bool     | `false`                          | Only for direct CloudWatch Logs API calls from app code.      |
| `disable_execute_api_endpoint` | bool     | `false`                          | Keep execute-api as a fallback for the demo.                  |
| `enable_sse_route`             | bool     | `false`                          | Only enable if MCP transport requires it.                    |
| `mcp_lambda_zip_path`          | string   | `"./build/mcp.zip"`              | Placeholder zip until app team owns build.                   |
| `fraud_lambda_zip_path`        | string   | `"./build/fraud.zip"`            | Placeholder zip until app team owns build.                   |
| `db_ops_lambda_zip_path`       | string   | `"./build/db_ops.zip"`           | Private migration/seed/reset Lambda artifact.                 |

## Appendix B — Outputs (expected)

| Output                | Example                                                              |
|-----------------------|----------------------------------------------------------------------|
| `mcp_url`             | `https://hackathon.example.com/mcp`                              |
| `health_url`          | `https://hackathon.example.com/health`                           |
| `api_id`              | `abcd1234`                                                           |
| `api_endpoint`        | `https://abcd1234.execute-api.us-east-1.amazonaws.com` (informational; may be disabled after Phase 1) |
| `mcp_lambda_name`     | `ao-radar-mcp`                                                       |
| `mcp_lambda_arn`      | `arn:aws:lambda:us-east-1:<acct>:function:ao-radar-mcp`              |
| `fraud_lambda_name`   | `ao-radar-fraud-mock`                                                |
| `fraud_lambda_arn`    | `arn:aws:lambda:us-east-1:<acct>:function:ao-radar-fraud-mock`       |
| `db_ops_lambda_name`  | `ao-radar-db-ops`                                                    |
| `db_ops_lambda_arn`   | `arn:aws:lambda:us-east-1:<acct>:function:ao-radar-db-ops`           |
| `rds_endpoint`        | `ao-radar-pg.<id>.us-east-1.rds.amazonaws.com:5432`                  |
| `db_secret_arn`       | `arn:aws:secretsmanager:us-east-1:<acct>:secret:ao-radar/db/master-*`|
| `vpc_id`              | `vpc-0xxxxxxxxxxxxxxxx`                                              |
| `private_subnet_ids`  | `["subnet-aaa", "subnet-bbb"]`                                       |
