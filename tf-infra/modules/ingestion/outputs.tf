# =============================================================================
# OUTPUTS DO MÓDULO DE INGESTÃO
# =============================================================================

# --- S3 DATA LAKE ---

output "s3_data_lake_bucket_name" {
  description = "Nome do bucket S3 do Data Lake"
  value       = aws_s3_bucket.data_lake.bucket
}

output "s3_data_lake_bucket_arn" {
  description = "ARN do bucket S3 do Data Lake"
  value       = aws_s3_bucket.data_lake.arn
}

# --- LAMBDA FUNCTIONS ---

output "simulator_lambda_name" {
  description = "Nome da função Lambda Simulator"
  value       = aws_lambda_function.simulator.function_name
}

output "simulator_lambda_arn" {
  description = "ARN da função Lambda Simulator"
  value       = aws_lambda_function.simulator.arn
}

output "simulator_lambda_handler" {
  description = "Handler da função Lambda Simulator"
  value       = aws_lambda_function.simulator.handler
}

output "ingestion_lambda_name" {
  description = "Nome da função Lambda Ingestion (telemetria)"
  value       = aws_lambda_function.ingestion.function_name
}

output "ingestion_lambda_arn" {
  description = "ARN da função Lambda Ingestion (telemetria)"
  value       = aws_lambda_function.ingestion.arn
}

output "label_ingestion_lambda_name" {
  description = "Nome da função Lambda Label Ingestion (eventos de falha)"
  value       = aws_lambda_function.label_ingestion.function_name
}

output "label_ingestion_lambda_arn" {
  description = "ARN da função Lambda Label Ingestion (eventos de falha)"
  value       = aws_lambda_function.label_ingestion.arn
}

output "label_ingestion_lambda_handler" {
  description = "Handler da função Lambda Label Ingestion"
  value       = aws_lambda_function.label_ingestion.handler
}

# --- EVENTBRIDGE ---

output "eventbridge_rule_name" {
  description = "Nome da regra do EventBridge"
  value       = aws_cloudwatch_event_rule.simulator_schedule.name
}

output "eventbridge_rule_arn" {
  description = "ARN da regra do EventBridge"
  value       = aws_cloudwatch_event_rule.simulator_schedule.arn
}

# --- IOT CORE RULES ---

output "telemetry_iot_rule_name" {
  description = "Nome da regra do IoT Core para telemetria"
  value       = aws_iot_topic_rule.telemetry_ingestion_rule.name
}

output "telemetry_iot_rule_arn" {
  description = "ARN da regra do IoT Core para telemetria"
  value       = aws_iot_topic_rule.telemetry_ingestion_rule.arn
}

output "failure_iot_rule_name" {
  description = "Nome da regra do IoT Core para eventos de falha"
  value       = aws_iot_topic_rule.failure_ingestion_rule.name
}

output "failure_iot_rule_arn" {
  description = "ARN da regra do IoT Core para eventos de falha"
  value       = aws_iot_topic_rule.failure_ingestion_rule.arn
}

# --- DYNAMODB TABLES ---

output "machine_state_table_name" {
  description = "Nome da tabela DynamoDB para estado das máquinas"
  value       = aws_dynamodb_table.machine_state.name
}

output "machine_state_table_arn" {
  description = "ARN da tabela DynamoDB para estado das máquinas"
  value       = aws_dynamodb_table.machine_state.arn
}

output "label_history_table_name" {
  description = "Nome da tabela DynamoDB para histórico de falhas"
  value       = aws_dynamodb_table.label_history.name
}

output "label_history_table_arn" {
  description = "ARN da tabela DynamoDB para histórico de falhas"
  value       = aws_dynamodb_table.label_history.arn
}

# --- CONFIGURAÇÕES MQTT ---

output "mqtt_topic_prefix" {
  description = "Prefixo dos tópicos MQTT configurado"
  value       = var.mqtt_topic_prefix
}

output "machine_ids" {
  description = "Lista de IDs das máquinas configuradas"
  value       = var.machine_ids
}

output "mqtt_topics_examples" {
  description = "Exemplos dos tópicos MQTT que serão utilizados"
  value = {
    temperature = "industrial/machine/{machine_id}/temperature"
    vibration   = "industrial/machine/{machine_id}/vibration"
    failure     = "industrial/machine/{machine_id}/event/failure"
  }
}

# --- FLUXOS DE DADOS ---

output "data_flows" {
  description = "Descrição dos fluxos de dados implementados"
  value = {
    telemetry_flow = "EventBridge (1 min) → Lambda Simulator → IoT Core → Lambda Ingestion → S3"
    failure_flow   = "IoT Core → Lambda Label Ingestion → DynamoDB"
    self_labeling  = "Lambda Simulator → DynamoDB (machine_state) → IoT Core (failure events)"
  }
}

# --- CONFIGURAÇÕES DO SIMULATOR ---

output "simulator_environment_variables" {
  description = "Variáveis de ambiente configuradas para o Lambda Simulator"
  value = {
    STATE_TABLE_NAME = aws_dynamodb_table.machine_state.name
    TOPIC_PREFIX     = var.mqtt_topic_prefix
  }
}

output "simulator_permissions" {
  description = "Permissões configuradas para o Lambda Simulator"
  value = {
    dynamodb_permissions = ["dynamodb:GetItem", "dynamodb:PutItem"]
    iot_permissions     = ["iot:Publish"]
    dynamodb_resource   = aws_dynamodb_table.machine_state.arn
    iot_resource        = "arn:aws:iot:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:topic/industrial/machine/*"
  }
}

# --- CONFIGURAÇÕES DO LABEL INGESTION ---

output "label_ingestion_environment_variables" {
  description = "Variáveis de ambiente configuradas para o Lambda Label Ingestion"
  value = {
    DYNAMODB_TABLE_NAME = aws_dynamodb_table.label_history.name
  }
}

output "label_ingestion_permissions" {
  description = "Permissões configuradas para o Lambda Label Ingestion"
  value = {
    dynamodb_permissions = ["dynamodb:PutItem"]
    dynamodb_resource   = aws_dynamodb_table.label_history.arn
  }
}
