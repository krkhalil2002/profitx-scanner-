# -------------------------------------------------------
# DEV ENVIRONMENT
# This is the entry point for your dev infrastructure.
# It calls each module and passes in the required variables.
# -------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -------------------------------------------------------
# DYNAMODB MODULE
# Calls the DynamoDB module and passes in variables
# -------------------------------------------------------
module "dynamodb" {
  source       = "../../modules/dynamoDB"
  table_name   = var.table_name
  environment  = "dev"
}