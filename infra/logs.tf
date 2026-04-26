resource "aws_cloudwatch_log_group" "mcp_lambda" {
  name              = "/aws/lambda/${var.name_prefix}-mcp"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "fraud_lambda" {
  name              = "/aws/lambda/${var.name_prefix}-fraud-mock"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "db_ops_lambda" {
  name              = "/aws/lambda/${var.name_prefix}-db-ops"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigatewayv2/${var.name_prefix}"
  retention_in_days = var.log_retention_days
}
