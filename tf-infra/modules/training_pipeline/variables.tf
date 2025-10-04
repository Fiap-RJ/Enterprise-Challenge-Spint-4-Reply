variable "project_name" {
  description = "Prefixo comum do projeto"
  type        = string
}

variable "s3_bucket_name" {
  description = "Bucket S3 principal usado pelo pipeline"
  type        = string
}

variable "numpy_layer_arn" {
  description = "ARN da camada Lambda numpy (criada pelo módulo lambda_layers)"
  type        = string
}

variable "pandas_layer_arn" {
  description = "ARN da camada Lambda pandas (criada pelo módulo lambda_layers)"
  type        = string
}

variable "sklearn_layer_arn" {
  description = "ARN da camada Lambda scikit-learn (criada pelo módulo lambda_layers)"
  type        = string
}

variable "lambda_timeout" {
  description = "Timeout das Lambdas em segundos"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Memória das Lambdas em MB"
  type        = number
  default     = 1024
}

variable "training_image_uri" {
  description = "URI da imagem de algoritmo (ex: XGBoost) para o Training Job"
  type        = string
  default     = "../dist/training_image.tar.gz"
}

variable "training_hyperparameters" {
  description = "Mapa de hiperparâmetros a serem passados ao Training Job"
  type        = map(string)
  default     = { "max_depth" : "6", "n_estimators" : "100", "learning_rate" : "0.1" }
}

variable "sagemaker_training_role_arn" {
  description = "ARN da IAM Role que o SageMaker usará no Training Job"
  type        = string

}

variable "tags" {
  description = "Tags a aplicar nos recursos"
  type        = map(string)
  default     = {}
}
