############################################################
# MCP Lambda
############################################################

resource "aws_lambda_function" "mcp" {
  function_name = "${var.name_prefix}-mcp"
  role          = aws_iam_role.mcp_lambda_exec.arn
  runtime       = var.lambda_runtime
  handler       = "ao_radar_mcp.handler.lambda_handler"

  filename         = var.mcp_lambda_zip_path
  source_code_hash = filebase64sha256(var.mcp_lambda_zip_path)

  memory_size                    = var.lambda_memory_mb
  timeout                        = var.lambda_timeout_s
  reserved_concurrent_executions = var.mcp_reserved_concurrency

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.mcp_lambda.id]
  }

  # Phase 1+2+3 union of env vars (allowed by the infra plan once Phase 3 is reached).
  environment {
    variables = {
      LOG_LEVEL               = "INFO"
      MCP_SERVER_NAME         = "ao-radar-mcp"
      MCP_SERVER_VERSION      = "0.1.0"
      DEMO_DATA_ENVIRONMENT   = "synthetic_demo"
      DB_SECRET_ARN           = aws_secretsmanager_secret.db_master.arn
      DB_CONNECT_TIMEOUT_S    = "5"
      DB_STATEMENT_TIMEOUT_MS = "15000"
      FRAUD_FUNCTION_NAME     = aws_lambda_function.fraud_mock.function_name
      FRAUD_INVOKE_TIMEOUT_S  = "5"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.mcp_lambda,
    aws_iam_role_policy_attachment.mcp_basic_exec,
    aws_iam_role_policy_attachment.mcp_vpc_access,
    aws_iam_role_policy_attachment.mcp_secrets_read,
    aws_iam_role_policy_attachment.mcp_lambda_invoke,
  ]
}

############################################################
# Fraud-mock Lambda (no VPC attach)
############################################################

resource "aws_lambda_function" "fraud_mock" {
  function_name = "${var.name_prefix}-fraud-mock"
  role          = aws_iam_role.fraud_lambda_exec.arn
  runtime       = var.lambda_runtime
  handler       = "ao_radar_fraud_mock.handler.lambda_handler"

  filename         = var.fraud_lambda_zip_path
  source_code_hash = filebase64sha256(var.fraud_lambda_zip_path)

  memory_size                    = 256
  timeout                        = 10
  reserved_concurrent_executions = var.fraud_reserved_concurrency

  environment {
    variables = {
      LOG_LEVEL                 = "INFO"
      DEMO_DATA_ENVIRONMENT     = "synthetic_demo"
      FRAUD_SIGNAL_SOURCE_LABEL = "synthetic_compliance_service_demo"
      FRAUD_DETERMINISTIC_SEED  = "ao-radar-synthetic-v1"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.fraud_lambda,
    aws_iam_role_policy_attachment.fraud_basic_exec,
  ]
}

############################################################
# DB-ops Lambda (VPC-attached, NOT API-Gateway-integrated)
############################################################

resource "aws_lambda_function" "db_ops" {
  function_name = "${var.name_prefix}-db-ops"
  role          = aws_iam_role.db_ops_lambda_exec.arn
  runtime       = var.lambda_runtime
  handler       = "ao_radar_db_ops.handler.lambda_handler"

  filename         = var.db_ops_lambda_zip_path
  source_code_hash = filebase64sha256(var.db_ops_lambda_zip_path)

  memory_size                    = 512
  timeout                        = 60
  reserved_concurrent_executions = var.db_ops_reserved_concurrency

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.db_ops_lambda.id]
  }

  environment {
    variables = {
      LOG_LEVEL               = "INFO"
      DB_SECRET_ARN           = aws_secretsmanager_secret.db_master.arn
      DB_CONNECT_TIMEOUT_S    = "5"
      DB_STATEMENT_TIMEOUT_MS = "15000"
      DEMO_DATA_ENVIRONMENT   = "synthetic_demo"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.db_ops_lambda,
    aws_iam_role_policy_attachment.db_ops_basic_exec,
    aws_iam_role_policy_attachment.db_ops_vpc_access,
    aws_iam_role_policy_attachment.db_ops_secrets_read,
  ]
}
