############################################################
# MCP Lambda SG (no ingress, broad egress for demo speed)
############################################################

resource "aws_security_group" "mcp_lambda" {
  name_prefix = "${var.name_prefix}-mcp-lambda-"
  description = "AO Radar MCP Lambda. No ingress; broad egress for demo speed (RDS path is still gated by RDS SG)."
  vpc_id      = aws_vpc.main.id

  egress {
    description = "Broad egress; RDS still SG-bounded, intra-VPC traffic flows over private subnets."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-mcp-lambda"
  }

  lifecycle {
    create_before_destroy = true
  }
}

############################################################
# DB-ops Lambda SG (no ingress, scoped egress to RDS + 443 to VPCEs)
############################################################

resource "aws_security_group" "db_ops_lambda" {
  name_prefix = "${var.name_prefix}-db-ops-lambda-"
  description = "AO Radar DB-ops Lambda. No ingress; egress to RDS:5432 and 443 to interface VPC endpoints."
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-db-ops-lambda"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "db_ops_egress_rds" {
  type                     = "egress"
  description              = "DB-ops Lambda to RDS Postgres."
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.db_ops_lambda.id
  source_security_group_id = aws_security_group.rds.id
}

resource "aws_security_group_rule" "db_ops_egress_vpce" {
  type                     = "egress"
  description              = "DB-ops Lambda to interface VPC endpoints (Secrets Manager) over TLS."
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.db_ops_lambda.id
  source_security_group_id = aws_security_group.vpce.id
}

############################################################
# RDS SG (only hard boundary worth preserving)
############################################################

resource "aws_security_group" "rds" {
  name_prefix = "${var.name_prefix}-rds-"
  description = "AO Radar RDS. Ingress 5432 only from MCP and DB-ops Lambda SGs."
  vpc_id      = aws_vpc.main.id

  egress {
    description = "Default egress."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-rds"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "rds_ingress_mcp" {
  type                     = "ingress"
  description              = "Postgres from MCP Lambda."
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = aws_security_group.mcp_lambda.id
}

resource "aws_security_group_rule" "rds_ingress_db_ops" {
  type                     = "ingress"
  description              = "Postgres from DB-ops Lambda."
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = aws_security_group.db_ops_lambda.id
}

############################################################
# Interface VPC endpoint SG
############################################################

resource "aws_security_group" "vpce" {
  name_prefix = "${var.name_prefix}-vpce-"
  description = "AO Radar interface VPC endpoint SG. Ingress 443 from MCP + DB-ops Lambda SGs."
  vpc_id      = aws_vpc.main.id

  egress {
    description = "Default egress."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-vpce"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "vpce_ingress_mcp" {
  type                     = "ingress"
  description              = "TLS from MCP Lambda to interface VPC endpoints."
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.vpce.id
  source_security_group_id = aws_security_group.mcp_lambda.id
}

resource "aws_security_group_rule" "vpce_ingress_db_ops" {
  type                     = "ingress"
  description              = "TLS from DB-ops Lambda to interface VPC endpoints."
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.vpce.id
  source_security_group_id = aws_security_group.db_ops_lambda.id
}
