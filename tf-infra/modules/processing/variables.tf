# =============================================================================
# VARIÁVEIS DO MÓDULO PROCESSING
# =============================================================================

variable "project_name" {
  description = "Nome do projeto usado como prefixo nos recursos"
  type        = string
}

variable "s3_bucket_name" {
  description = "Nome do bucket S3 do Data Lake"
  type        = string
}

variable "label_history_table_name" {
  description = "Nome da tabela DynamoDB para histórico de falhas (criada pelo módulo de ingestão)"
  type        = string
}

variable "realtime_features_table_name" {
  description = "Nome da tabela DynamoDB para Feature Store"
  type        = string
  default     = "RealtimeFeatures"
}

variable "lambda_timeout" {
  description = "Timeout da função Lambda em segundos"
  type        = number
  default     = 900
}

variable "lambda_memory_size" {
  description = "Memória da função Lambda em MB"
  type        = number
  default     = 1024
}

variable "processing_schedule_expression" {
  description = "Expressão de agendamento para o EventBridge Scheduler"
  type        = string
  default     = "rate(1 hour)"
}

variable "time_window_hours" {
  description = "Janela de tempo em horas para processamento dos dados"
  type        = number
  default     = 1
}

variable "numpy_layer_arn" {
  description = "ARN da camada Lambda numpy (criada pelo módulo lambda_layers)"
  type        = string
}

variable "pandas_layer_arn" {
  description = "ARN da camada Lambda pandas (criada pelo módulo lambda_layers)"
  type        = string
}


variable "initial_timestamp" {
  description = "Timestamp inicial para o parâmetro SSM (formato ISO 8601)"
  type        = string
  default     = "2025-10-02T05:16:37.183000+00:00"
}

variable "prediction_horizon_hours" {
  description = "Horizonte de predição em horas para as labels"
  type        = number
  default     = 24
}

variable "processing_lag_hours" {
  description = "Lag de processamento em horas para garantir dados completos"
  type        = number
  default     = 24
}

variable "tags" {
  description = "Tags adicionais para os recursos"
  type        = map(string)
  default     = {}
}

