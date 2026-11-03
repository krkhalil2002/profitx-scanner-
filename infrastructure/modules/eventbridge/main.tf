# EventBridge Scheduler supports time zones, so 9:35 AM Eastern stays correct through daylight saving.
resource "aws_scheduler_schedule" "market_open" {
  name                         = "${local.name}-market-open"
  schedule_expression          = "cron(35 9 ? * MON-FRI *)"
  schedule_expression_timezone = "America/New_York"
  state                        = var.schedule_enabled ? "ENABLED" : "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.scanner.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ source = "schedule" })
  }
}
