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

variable "lambda_timeout" {
  description = "Timeout da função Lambda em segundos"
  type        = number
  default     = 300
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

variable "pandas_layer_zip_path" {
  description = "Caminho para o arquivo ZIP do Lambda Layer do pandas"
  type        = string
  default     = "./lambda_artifacts/pandas_layer.zip"
}


variable "tags" {
  description = "Tags adicionais para os recursos"
  type        = map(string)
  default     = {}
}

