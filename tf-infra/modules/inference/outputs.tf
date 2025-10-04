output "api_endpoint" {
  description = "The URL of the API Gateway"
  value       = aws_apigatewayv2_api.api.api_endpoint
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.inference_api.function_name
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.inference_api.arn
}

output "lambda_role_arn" {
  description = "The ARN of the IAM role used by the Lambda function"
  value       = aws_iam_role.lambda_exec.arn
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket used for the application"
  value       = var.s3_bucket_name != "" ? var.s3_bucket_name : "inference-app-${data.aws_caller_identity.current.account_id}"
}

output "dynamodb_table_name" {
  description = "The name of the DynamoDB table used for the feature store"
  value       = var.dynamodb_table_name
}

output "api_gateway_id" {
  description = "The ID of the API Gateway"
  value       = aws_apigatewayv2_api.api.id
}
