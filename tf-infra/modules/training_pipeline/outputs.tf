output "state_machine_arn" {
  description = "ARN da State Machine do pipeline de treinamento"
  value       = aws_sfn_state_machine.training_pipeline.arn
}

output "data_prep_lambda_name" {
  description = "Nome da função Lambda de preparação de dados"
  value       = aws_lambda_function.data_prep.function_name
}

output "model_eval_lambda_name" {
  description = "Nome da função Lambda de avaliação do modelo"
  value       = aws_lambda_function.model_evaluation.function_name
}

output "model_package_group_name" {
  description = "Nome do SageMaker Model Package Group"
  value       = aws_sagemaker_model_package_group.model_group.model_package_group_name
}
