############################################################
# Random DB master password
############################################################

resource "random_password" "db_master" {
  length  = 32
  special = true
  # Avoid RDS-disallowed characters (`/`, `"`, `@`, space) and shell-copy hazards
  # (backslash, single quote, semicolon, backtick).
  override_special = "!#$%&*()-_=+[]{}:,.?"
}

############################################################
# Secrets Manager DB master entry
############################################################

resource "aws_secretsmanager_secret" "db_master" {
  name = "${var.name_prefix}/db/master"

  description = "AO Radar DB master credentials (synthetic_demo only). Recovery window 0 so terraform destroy is immediate during the hackathon teardown."

  # Hackathon-only: hard delete on destroy. Do not use this setting for durable
  # environments.
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db_master" {
  secret_id = aws_secretsmanager_secret.db_master.id

  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    username = "ao_radar_admin"
    password = random_password.db_master.result
    dbname   = "ao_radar"
  })
}
