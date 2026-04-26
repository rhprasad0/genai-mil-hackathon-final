############################################################
# HTTP API
############################################################

resource "aws_apigatewayv2_api" "main" {
  name          = "${var.name_prefix}-http-api"
  protocol_type = "HTTP"

  disable_execute_api_endpoint = var.disable_execute_api_endpoint
}

############################################################
# AWS_PROXY integration to MCP Lambda
############################################################

resource "aws_apigatewayv2_integration" "mcp" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri        = aws_lambda_function.mcp.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"

  timeout_milliseconds = 29000
}

############################################################
# Routes
############################################################

resource "aws_apigatewayv2_route" "mcp_post" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /mcp"
  target    = "integrations/${aws_apigatewayv2_integration.mcp.id}"
}

resource "aws_apigatewayv2_route" "health_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.mcp.id}"
}

# Optional: only added when enable_sse_route is true. Default off because
# Streamable HTTP is the supported transport on Lambda + API Gateway HTTP API.
resource "aws_apigatewayv2_route" "sse_get" {
  count = var.enable_sse_route ? 1 : 0

  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /sse"
  target    = "integrations/${aws_apigatewayv2_integration.mcp.id}"
}

############################################################
# $default stage with throttle settings + JSON access logs
############################################################

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit   = var.api_throttle_burst
    throttling_rate_limit    = var.api_throttle_rate
    detailed_metrics_enabled = false
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn

    # JSON access log template. Intentionally excludes request bodies, query
    # strings, cookies, and Authorization headers.
    format = jsonencode({
      requestId          = "$context.requestId"
      ip                 = "$context.identity.sourceIp"
      requestTime        = "$context.requestTime"
      routeKey           = "$context.routeKey"
      status             = "$context.status"
      responseLength     = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
    })
  }
}
