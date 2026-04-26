############################################################
# Core identity / region
############################################################

variable "region" {
  description = "AWS region for the AO Radar hackathon stack. Single region by design."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to every resource name. Drives the Project tag and avoids collisions with unrelated stacks in the same account."
  type        = string
  default     = "ao-radar"
}

############################################################
# Public DNS / custom domain (placeholders only in committed files)
############################################################

variable "domain_root" {
  description = "Root domain for the existing public Route 53 hosted zone (data source only)."
  type        = string
  default     = "example.com"
}

variable "hosted_zone_id" {
  description = "Public Route 53 hosted zone ID. Pin by ID to avoid loose name lookups; placeholder in the committed example."
  type        = string
  default     = "Z_PUBLIC_HOSTED_ZONE_ID"
}

variable "subdomain" {
  description = "Subdomain to attach to the API Gateway custom domain. Final FQDN is <subdomain>.<domain_root>."
  type        = string
  default     = "hackathon"
}

############################################################
# Networking
############################################################

variable "vpc_cidr" {
  description = "CIDR block for the AO Radar VPC. Avoid overlap with anything else in the account."
  type        = string
  default     = "10.42.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to span with private subnets. RDS subnet groups require >= 2."
  type        = number
  default     = 2
}

############################################################
# RDS
############################################################

variable "db_instance_class" {
  description = "RDS instance class. Tiny single-AZ Postgres for the hackathon."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB."
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "Postgres engine minor version. Verify it is currently orderable in the chosen region before apply."
  type        = string
  default     = "16.13"
}

############################################################
# Lambda
############################################################

variable "lambda_runtime" {
  description = "Python runtime used by all three AO Radar Lambdas."
  type        = string
  default     = "python3.12"
}

variable "lambda_memory_mb" {
  description = "Memory size (MB) for the MCP Lambda."
  type        = number
  default     = 512
}

variable "lambda_timeout_s" {
  description = "Timeout (seconds) for the MCP Lambda. Must stay under the 30s API Gateway HTTP API integration cap."
  type        = number
  default     = 25
}

variable "mcp_reserved_concurrency" {
  description = "Reserved concurrent executions for the MCP Lambda. Caps runaway traffic during a small live demo."
  type        = number
  default     = 10
}

variable "fraud_reserved_concurrency" {
  description = "Reserved concurrent executions for the fraud-mock Lambda."
  type        = number
  default     = 5
}

variable "db_ops_reserved_concurrency" {
  description = "Reserved concurrent executions for the DB-ops Lambda. Keep this at 1 to prevent concurrent migrate/seed/reset operations."
  type        = number
  default     = 1
}

############################################################
# API Gateway
############################################################

variable "api_throttle_rate" {
  description = "API Gateway HTTP API steady-state rate limit (requests per second)."
  type        = number
  default     = 50
}

variable "api_throttle_burst" {
  description = "API Gateway HTTP API burst limit (requests)."
  type        = number
  default     = 100
}

############################################################
# Logging
############################################################

variable "log_retention_days" {
  description = "CloudWatch Logs retention for Lambda and API Gateway access log groups."
  type        = number
  default     = 7
}

############################################################
# Phase-gated VPC endpoints / route flags
############################################################

variable "enable_secretsmanager_vpce" {
  description = "Enable the Secrets Manager interface VPC endpoint. Required from Phase 2 so the VPC-attached Lambda can read the DB secret without a NAT gateway."
  type        = bool
  default     = true
}

variable "enable_lambda_vpce" {
  description = "Enable the Lambda interface VPC endpoint. Required from Phase 3 so the VPC-attached MCP Lambda can invoke the fraud-mock Lambda without a NAT gateway."
  type        = bool
  default     = false
}

variable "enable_s3_gateway_endpoint" {
  description = "Enable the S3 gateway VPC endpoint. Off by default; flip on only if application code uses S3."
  type        = bool
  default     = false
}

variable "enable_logs_vpce" {
  description = "Enable the CloudWatch Logs interface VPC endpoint. Off by default; ordinary Lambda stdout/stderr delivery does not need it."
  type        = bool
  default     = false
}

variable "disable_execute_api_endpoint" {
  description = "Disable the AWS-owned execute-api hostname on the HTTP API. Default keeps the fallback hostname available for the demo."
  type        = bool
  default     = false
}

variable "enable_sse_route" {
  description = "Add an optional GET /sse route on the HTTP API. Off by default because Streamable HTTP is the supported transport on Lambda + API Gateway HTTP API."
  type        = bool
  default     = false
}

############################################################
# Lambda zip artifact paths (placeholder defaults)
############################################################

variable "mcp_lambda_zip_path" {
  description = "Path to the MCP Lambda zip artifact, relative to the infra/ root. Application teammate populates infra/build/mcp.zip later."
  type        = string
  default     = "./build/mcp.zip"
}

variable "fraud_lambda_zip_path" {
  description = "Path to the fraud-mock Lambda zip artifact, relative to the infra/ root."
  type        = string
  default     = "./build/fraud.zip"
}

variable "db_ops_lambda_zip_path" {
  description = "Path to the DB-ops Lambda zip artifact, relative to the infra/ root."
  type        = string
  default     = "./build/db_ops.zip"
}
