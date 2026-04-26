############################################################
# Public URLs
############################################################

output "mcp_url" {
  description = "Public MCP endpoint URL on the AO Radar custom domain."
  value       = "https://${local.fqdn}/mcp"
}

output "health_url" {
  description = "Public health endpoint URL on the AO Radar custom domain."
  value       = "https://${local.fqdn}/health"
}

############################################################
# API Gateway
############################################################

output "api_id" {
  description = "API Gateway HTTP API ID."
  value       = aws_apigatewayv2_api.main.id
}

output "api_endpoint" {
  description = "AWS-owned execute-api endpoint URL (informational; demo fallback)."
  value       = aws_apigatewayv2_api.main.api_endpoint
}

############################################################
# Lambda
############################################################

output "mcp_lambda_name" {
  description = "MCP Lambda function name."
  value       = aws_lambda_function.mcp.function_name
}

output "mcp_lambda_arn" {
  description = "MCP Lambda function ARN."
  value       = aws_lambda_function.mcp.arn
}

output "fraud_lambda_name" {
  description = "Fraud-mock Lambda function name."
  value       = aws_lambda_function.fraud_mock.function_name
}

output "fraud_lambda_arn" {
  description = "Fraud-mock Lambda function ARN."
  value       = aws_lambda_function.fraud_mock.arn
}

output "db_ops_lambda_name" {
  description = "DB-ops Lambda function name."
  value       = aws_lambda_function.db_ops.function_name
}

output "db_ops_lambda_arn" {
  description = "DB-ops Lambda function ARN."
  value       = aws_lambda_function.db_ops.arn
}

############################################################
# RDS / Secrets
############################################################

output "rds_endpoint" {
  description = "RDS host:port (no credentials)."
  value       = "${aws_db_instance.main.address}:${aws_db_instance.main.port}"
}

output "db_secret_arn" {
  description = "ARN of the AO Radar DB master secret. The ARN itself is not sensitive."
  value       = aws_secretsmanager_secret.db_master.arn
}

############################################################
# Networking
############################################################

output "vpc_id" {
  description = "AO Radar VPC ID."
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private isolated subnet IDs used by the Lambdas and RDS."
  value       = aws_subnet.private[*].id
}
