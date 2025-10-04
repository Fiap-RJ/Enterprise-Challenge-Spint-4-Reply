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

# Removido: pandas_layer_arn agora é passado como variável

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


output "ssm_parameter_name" {
  description = "Nome do parâmetro SSM para gerenciamento de estado"
  value       = aws_ssm_parameter.processing_state.name
}

output "ssm_parameter_arn" {
  description = "ARN do parâmetro SSM para gerenciamento de estado"
  value       = aws_ssm_parameter.processing_state.arn
}

