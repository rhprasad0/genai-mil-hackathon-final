resource "aws_db_subnet_group" "main" {
  name        = "${var.name_prefix}-pg-subnets"
  description = "AO Radar private DB subnet group (synthetic demo only)."
  subnet_ids  = aws_subnet.private[*].id

  tags = {
    Name = "${var.name_prefix}-pg-subnets"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.name_prefix}-pg"

  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  username = "ao_radar_admin"
  password = random_password.db_master.result
  db_name  = "ao_radar"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  publicly_accessible = false
  multi_az            = false

  backup_retention_period = 0
  deletion_protection     = false
  skip_final_snapshot     = true
  apply_immediately       = true

  performance_insights_enabled = false
  monitoring_interval          = 0

  tags = {
    Name = "${var.name_prefix}-pg"
  }
}
