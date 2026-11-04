# One-time setup, run by you from your laptop (local state, not committed):
#   1. S3 bucket that holds Terraform state for dev and prod
#   2. GitHub OIDC trust so Actions can deploy WITHOUT long-lived AWS keys
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "github_repo" {
  type        = string
  description = "owner/repo, e.g. krkhalil2002/profitx-scanner-"
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "me" {}

resource "aws_s3_bucket" "tfstate" {
  bucket = "profitx-tfstate-${data.aws_caller_identity.me.account_id}"
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # Only THIS repo, and only its dev and main branches, can assume the role.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repo}:ref:refs/heads/main",
        "repo:${var.github_repo}:ref:refs/heads/dev",
      ]
    }
  }
}

resource "aws_iam_role" "deploy" {
  name               = "profitx-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

# TRADE-OFF (document this): Terraform creates IAM roles, Lambda, API Gateway, etc., so this
# role is broad. Mitigations: trust is limited to one repo and two branches, and there are no
# stored keys. A future improvement is a custom policy scoped to profitx-* resources.
resource "aws_iam_role_policy_attachment" "deploy" {
  role       = aws_iam_role.deploy.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

output "state_bucket" {
  value = aws_s3_bucket.tfstate.bucket
}

output "deploy_role_arn" {
  value = aws_iam_role.deploy.arn
}
