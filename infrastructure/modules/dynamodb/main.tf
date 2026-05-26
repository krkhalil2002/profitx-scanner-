# -------------------------------------------------------
# DYNAMODB TABLE
# This creates the single table that stores all ProfitX data.
# We use a single-table design — one table for everything.
# PK and SK are generic names so we can store different
# types of records in the same table.
# -------------------------------------------------------
resource "aws_dynamodb_table" "profitx" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"  # no capacity planning needed, pay per use
  hash_key     = "PK"               # partition key
  range_key    = "SK"               # sort key

  attribute {
    name = "PK"
    type = "S"  # S = String
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # TTL automatically deletes old scan results so your table
  # doesn't grow forever and cost more money
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Project     = "ProfitX"
    Environment = var.environment
  }
}