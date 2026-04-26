############################################################
# Data sources
############################################################

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_route53_zone" "root" {
  zone_id = var.hosted_zone_id
}

############################################################
# Locals
############################################################

locals {
  common_tags = {
    Project   = "ao-radar"
    Env       = "hackathon"
    ManagedBy = "terraform"
    Owner     = "project-owner"
  }

  fqdn = "${var.subdomain}.${var.domain_root}"

  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  private_subnet_cidrs = [
    for i in range(var.az_count) : cidrsubnet(var.vpc_cidr, 4, i)
  ]
}
