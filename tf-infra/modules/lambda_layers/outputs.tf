# =============================================================================
# OUTPUTS DO MÓDULO LAMBDA_LAYERS
# =============================================================================

output "numpy_layer_arn" {
  description = "ARN da camada Lambda numpy"
  value       = aws_lambda_layer_version.numpy_layer.arn
}

output "numpy_layer_name" {
  description = "Nome da camada Lambda numpy"
  value       = aws_lambda_layer_version.numpy_layer.layer_name
}

output "pandas_layer_arn" {
  description = "ARN da camada Lambda pandas"
  value       = aws_lambda_layer_version.pandas_layer.arn
}

output "pandas_layer_name" {
  description = "Nome da camada Lambda pandas"
  value       = aws_lambda_layer_version.pandas_layer.layer_name
}

output "sklearn_layer_arn" {
  description = "ARN da camada Lambda scikit-learn"
  value       = aws_lambda_layer_version.sklearn_layer.arn
}

output "sklearn_layer_name" {
  description = "Nome da camada Lambda scikit-learn"
  value       = aws_lambda_layer_version.sklearn_layer.layer_name
}
