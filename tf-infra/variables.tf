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

# --- CONFIGURAÇÕES DO MÓDULO PROCESSING ---

variable "processing_schedule_expression" {
  description = "Expressão de agendamento para o EventBridge Scheduler do processamento"
  type        = string
  default     = "rate(1 hour)"
}

variable "time_window_hours" {
  description = "Janela de tempo em horas para processamento dos dados"
  type        = number
  default     = 1
}

variable "pandas_layer_zip_path" {
  description = "Caminho para o arquivo ZIP do Lambda Layer do pandas + scikit-learn"
  type        = string
  default     = "../dist/pandas_sklearn_layer.zip"
}

variable "inference_dependencies_layer_zip_path" {
  description = "Caminho para o arquivo ZIP do Lambda Layer de dependências da inferência"
  type        = string
  default     = "../dist/inference_dependencies_layer.zip"
}

variable "data_prep_lambda_zip_path" {
  description = "Caminho para o ZIP da data_prep_lambda"
  type        = string
  default     = "../lambda_artifacts/data_prep_lambda.zip"
}

variable "model_eval_lambda_zip_path" {
  description = "Caminho para o ZIP da model_evaluation_lambda"
  type        = string
  default     = "../lambda_artifacts/model_evaluation_lambda.zip"
}

variable "training_image_uri" {
  description = "URI da imagem Docker (algoritmo) usada no SageMaker Training Job"
  type        = string
  default     = "../dist/training_image.tar.gz"
}

variable "training_hyperparameters" {
  description = "Mapa de hiperparâmetros do modelo"
  type        = map(string)
  default     = {}
}

variable "sagemaker_training_role_arn" {
  description = "ARN da IAM Role usada pelo SageMaker Training Job"
  type        = string
  default     = "arn:aws:iam::641055565860:role/service-role/AmazonSageMaker-ExecutionRole-20250115T051637"
}

variable "training_pipeline_schedule_expression" {
  description = "Expressão de agendamento para execução automática do pipeline de treinamento"
  type        = string
  default     = "cron(0/5 * * * ? *)" # A cada 5 minutos
}

# --- TAGS ---

variable "tags" {
  description = "Tags adicionais para os recursos"
  type        = map(string)
  default = {
    Project = "Enterprise Challenge - Reply"
    Owner   = "Fiap-RJ Team"
  }
}
