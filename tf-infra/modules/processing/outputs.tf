# =============================================================================
# OUTPUTS DO MÓDULO PROCESSING
# =============================================================================

output "processing_lambda_arn" {
  description = "ARN da função Lambda de processamento"
  value       = aws_lambda_function.processing_lambda.arn
}

output "processing_lambda_function_name" {
  description = "Nome da função Lambda de processamento"
  value       = aws_lambda_function.processing_lambda.function_name
}

output "realtime_features_table_name" {
  description = "Nome da tabela DynamoDB para Feature Store"
  value       = aws_dynamodb_table.realtime_features.name
}

output "realtime_features_table_arn" {
  description = "ARN da tabela DynamoDB para Feature Store"
  value       = aws_dynamodb_table.realtime_features.arn
}

output "pandas_layer_arn" {
  description = "ARN do Lambda Layer do pandas"
  value       = aws_lambda_layer_version.pandas_layer.arn
}

output "processing_lambda_role_arn" {
  description = "ARN da IAM role da Lambda de processamento"
  value       = aws_iam_role.processing_lambda_role.arn
}

output "processing_schedule_name" {
  description = "Nome do EventBridge Scheduler para processamento"
  value       = aws_cloudwatch_event_rule.processing_schedule.name
}

output "processing_schedule_arn" {
  description = "ARN do EventBridge Scheduler para processamento"
  value       = aws_cloudwatch_event_rule.processing_schedule.arn
}

