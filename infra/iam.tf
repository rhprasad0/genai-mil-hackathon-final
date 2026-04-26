############################################################
# Common Lambda assume-role policy
############################################################

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

############################################################
# MCP Lambda execution role
############################################################

resource "aws_iam_role" "mcp_lambda_exec" {
  name               = "${var.name_prefix}-mcp-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Phase 1: basic execution (CloudWatch Logs).
resource "aws_iam_role_policy_attachment" "mcp_basic_exec" {
  role       = aws_iam_role.mcp_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Phase 2: ENI management for VPC attach.
resource "aws_iam_role_policy_attachment" "mcp_vpc_access" {
  role       = aws_iam_role.mcp_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Phase 2: Secrets Manager read for ao-radar/* secret paths.
data "aws_iam_policy_document" "mcp_secrets_read" {
  statement {
    sid    = "ReadAoRadarSecrets"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]

    resources = [
      "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:${var.name_prefix}/*",
    ]
  }
}

resource "aws_iam_policy" "mcp_secrets_read" {
  name        = "${var.name_prefix}-mcp-secrets-read"
  description = "Read AO Radar Secrets Manager entries (ao-radar/* path) from the MCP Lambda."
  policy      = data.aws_iam_policy_document.mcp_secrets_read.json
}

resource "aws_iam_role_policy_attachment" "mcp_secrets_read" {
  role       = aws_iam_role.mcp_lambda_exec.name
  policy_arn = aws_iam_policy.mcp_secrets_read.arn
}

# Phase 3: Invoke fraud-mock Lambda (scoped to ao-radar-* function names).
data "aws_iam_policy_document" "mcp_lambda_invoke" {
  statement {
    sid       = "InvokeAoRadarLambdas"
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${var.name_prefix}-*"]
  }
}

resource "aws_iam_policy" "mcp_lambda_invoke" {
  name        = "${var.name_prefix}-mcp-lambda-invoke"
  description = "Allow MCP Lambda to invoke AO Radar Lambdas (e.g. fraud-mock) by name pattern."
  policy      = data.aws_iam_policy_document.mcp_lambda_invoke.json
}

resource "aws_iam_role_policy_attachment" "mcp_lambda_invoke" {
  role       = aws_iam_role.mcp_lambda_exec.name
  policy_arn = aws_iam_policy.mcp_lambda_invoke.arn
}

############################################################
# Fraud-mock Lambda execution role
############################################################

resource "aws_iam_role" "fraud_lambda_exec" {
  name               = "${var.name_prefix}-fraud-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "fraud_basic_exec" {
  role       = aws_iam_role.fraud_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

############################################################
# DB-ops Lambda execution role
############################################################

resource "aws_iam_role" "db_ops_lambda_exec" {
  name               = "${var.name_prefix}-db-ops-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "db_ops_basic_exec" {
  role       = aws_iam_role.db_ops_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "db_ops_vpc_access" {
  role       = aws_iam_role.db_ops_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Reuse the same scoped Secrets Manager read policy.
resource "aws_iam_role_policy_attachment" "db_ops_secrets_read" {
  role       = aws_iam_role.db_ops_lambda_exec.name
  policy_arn = aws_iam_policy.mcp_secrets_read.arn
}

############################################################
# API Gateway -> MCP Lambda invoke permission
############################################################

resource "aws_lambda_permission" "api_invoke_mcp" {
  statement_id  = "AllowAPIGatewayInvokeMCP"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mcp.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
