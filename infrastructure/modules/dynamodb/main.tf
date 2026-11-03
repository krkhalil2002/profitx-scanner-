# Single table. See docs/interview-notes.md for the key design.
#   SCAN#<id> | META          -> one item per scan (also indexed in gsi1 for "latest scan")
#   SCAN#<id> | RESULT#<sym>  -> one item per matching symbol
resource "aws_dynamodb_table" "main" {
  name         = "${local.name}-table"
  billing_mode = "PAY_PER_REQUEST" # no idle cost
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }
  attribute {
    name = "gsi1pk"
    type = "S"
  }
  attribute {
    name = "gsi1sk"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi1"
    hash_key        = "gsi1pk"
    range_key       = "gsi1sk"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.env == "prod"
  }
}

# Holds the market data API key. The VALUE is never in Terraform or git:
#   aws secretsmanager put-secret-value --secret-id profitx-dev/market-api-key --secret-string "KEY"
resource "aws_secretsmanager_secret" "market_api_key" {
  name                    = "${local.name}/market-api-key"
  recovery_window_in_days = 0 # lets you destroy and recreate without a 30-day wait
}
