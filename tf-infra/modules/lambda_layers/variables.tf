# =============================================================================
# VARIÁVEIS DO MÓDULO LAMBDA_LAYERS
# =============================================================================

variable "project_name" {
  description = "Nome do projeto usado como prefixo nos recursos"
  type        = string
}

variable "artifacts_s3_bucket" {
  description = "Nome do bucket S3 para armazenar os artefatos das camadas"
  type        = string
}

variable "numpy_layer_s3_key" {
  description = "Chave S3 para o arquivo numpy_layer.zip"
  type        = string
}

variable "pandas_layer_s3_key" {
  description = "Chave S3 para o arquivo pandas_layer.zip"
  type        = string
}

variable "sklearn_layer_s3_key" {
  description = "Chave S3 para o arquivo sklearn_layer.zip"
  type        = string
}

variable "lambda_runtime" {
  description = "Runtime das funções Lambda"
  type        = string
  default     = "python3.12"
}

variable "tags" {
  description = "Tags adicionais para os recursos"
  type        = map(string)
  default     = {}
}
