# =============================================================================
# VARIÁVEIS DA INFRAESTRUTURA MLOPS INDUSTRIAL
# =============================================================================

variable "project_name" {
  description = "Nome do projeto usado como prefixo nos recursos"
  type        = string
  default     = "replyec"
}

variable "aws_region" {
  description = "Região AWS para deploy"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Nome do bucket S3 para o Data Lake (deve ser único globalmente)"
  type        = string
  default     = "replyec-data-lake-20250115"
}

# --- CONFIGURAÇÕES MQTT CONFORME ARQUITETURA ---

variable "mqtt_topic_prefix" {
  description = "Prefixo base dos tópicos MQTT hierárquicos"
  type        = string
  default     = "industrial/machine"
}

variable "machine_ids" {
  description = "Lista de IDs das máquinas para simulação"
  type        = list(string)
  default     = ["PUMP-A01", "PUMP-A02", "FAN-B01", "FAN-B02", "COMPRESSOR-C01"]
}

# --- CONFIGURAÇÕES DE AGENDAMENTO ---

variable "simulator_schedule_expression" {
  description = "Expressão de agendamento para o EventBridge (1 minuto por padrão)"
  type        = string
  default     = "rate(1 minute)"
}

# --- CONFIGURAÇÕES DAS LAMBDAS ---

variable "lambda_timeout" {
  description = "Timeout das funções Lambda em segundos"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Memória das funções Lambda em MB"
  type        = number
  default     = 256
}

# --- CONFIGURAÇÕES DE TABELAS DYNAMODB ---

variable "machine_state_table_name" {
  description = "Nome da tabela DynamoDB para estado das máquinas"
  type        = string
  default     = "MachineState"
}

variable "label_history_table_name" {
  description = "Nome da tabela DynamoDB para histórico de Labels"
  type        = string
  default     = "LabelHistory"
}


# --- TAGS ---

variable "tags" {
  description = "Tags adicionais para os recursos"
  type        = map(string)
  default = {
    Project     = "Enterprise Challenge - Reply"
    Owner       = "Fiap-RJ Team"
  }
}
