data "archive_file" "scanner" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/functions/scanner"
  output_path = "${path.module}/build/scanner.zip"
  excludes    = ["__pycache__"]
}

data "archive_file" "results" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/functions/results"
  output_path = "${path.module}/build/results.zip"
  excludes    = ["__pycache__"]
}

resource "aws_cloudwatch_log_group" "scanner" {
  name              = "/aws/lambda/${local.name}-scanner"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "results" {
  name              = "/aws/lambda/${local.name}-results"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "scanner" {
  function_name    = "${local.name}-scanner"
  role             = aws_iam_role.scanner.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.scanner.output_path
  source_code_hash = data.archive_file.scanner.output_base64sha256
  timeout          = 25 # stay under API Gateway's 30s limit
  memory_size      = 256

  environment {
    variables = {
      TABLE_NAME    = aws_dynamodb_table.main.name
      SYMBOLS       = var.symbols
      DATA_PROVIDER = var.data_provider
      SECRET_ARN    = aws_secretsmanager_secret.market_api_key.arn
    }
  }

  depends_on = [aws_cloudwatch_log_group.scanner, aws_iam_role_policy.scanner]
}

resource "aws_lambda_function" "results" {
  function_name    = "${local.name}-results"
  role             = aws_iam_role.results.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.results.output_path
  source_code_hash = data.archive_file.results.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.main.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.results, aws_iam_role_policy.results]
}
