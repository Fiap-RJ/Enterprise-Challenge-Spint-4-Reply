# =============================================================================
# OUTPUTS DA INFRAESTRUTURA MLOPS INDUSTRIAL
# =============================================================================

# --- S3 DATA LAKE ---

output "data_lake_bucket_name" {
  description = "Nome do bucket S3 do Data Lake"
  value       = module.ingestion.s3_data_lake_bucket_name
}

output "data_lake_bucket_arn" {
  description = "ARN do bucket S3 do Data Lake"
  value       = module.ingestion.s3_data_lake_bucket_arn
}

# --- LAMBDA FUNCTIONS ---

output "simulator_lambda_name" {
  description = "Nome da função Lambda Simulator"
  value       = module.ingestion.simulator_lambda_name
}

output "simulator_lambda_arn" {
  description = "ARN da função Lambda Simulator"
  value       = module.ingestion.simulator_lambda_arn
}

output "ingestion_lambda_name" {
  description = "Nome da função Lambda Ingestion (telemetria)"
  value       = module.ingestion.ingestion_lambda_name
}

output "ingestion_lambda_arn" {
  description = "ARN da função Lambda Ingestion (telemetria)"
  value       = module.ingestion.ingestion_lambda_arn
}

output "label_ingestion_lambda_name" {
  description = "Nome da função Lambda Label Ingestion (eventos de falha)"
  value       = module.ingestion.label_ingestion_lambda_name
}

output "label_ingestion_lambda_arn" {
  description = "ARN da função Lambda Label Ingestion (eventos de falha)"
  value       = module.ingestion.label_ingestion_lambda_arn
}

# --- EVENTBRIDGE ---

output "eventbridge_rule_name" {
  description = "Nome da regra do EventBridge"
  value       = module.ingestion.eventbridge_rule_name
}

# --- IOT CORE RULES ---

output "telemetry_iot_rule_name" {
  description = "Nome da regra do IoT Core para telemetria"
  value       = module.ingestion.telemetry_iot_rule_name
}

output "failure_iot_rule_name" {
  description = "Nome da regra do IoT Core para eventos de falha"
  value       = module.ingestion.failure_iot_rule_name
}

# --- DYNAMODB TABLES ---

output "machine_state_table_name" {
  description = "Nome da tabela DynamoDB para estado das máquinas"
  value       = module.ingestion.machine_state_table_name
}

output "falha_history_table_name" {
  description = "Nome da tabela DynamoDB para histórico de falhas"
  value       = module.ingestion.falha_history_table_name
}

# --- CONFIGURAÇÕES MQTT ---

output "mqtt_topic_prefix" {
  description = "Prefixo dos tópicos MQTT configurado"
  value       = module.ingestion.mqtt_topic_prefix
}

output "machine_ids" {
  description = "Lista de IDs das máquinas configuradas"
  value       = module.ingestion.machine_ids
}

output "mqtt_topics_examples" {
  description = "Exemplos dos tópicos MQTT que serão utilizados"
  value       = module.ingestion.mqtt_topics_examples
}

# --- FLUXOS DE DADOS ---

output "data_flows" {
  description = "Descrição dos fluxos de dados implementados"
  value       = module.ingestion.data_flows
}

# --- INFORMAÇÕES DO AMBIENTE ---

output "aws_region" {
  description = "Região AWS onde os recursos foram criados"
  value       = data.aws_region.current.name
}

output "aws_account_id" {
  description = "ID da conta AWS"
  value       = data.aws_caller_identity.current.account_id
}

output "project_name" {
  description = "Nome do projeto"
  value       = var.project_name
}
