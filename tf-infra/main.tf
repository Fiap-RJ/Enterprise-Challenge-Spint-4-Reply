# =============================================================================
# INFRAESTRUTURA MLOPS INDUSTRIAL - INGESTÃO DE DADOS
# =============================================================================
# Implementa o fluxo de ingestão conforme arch-pro.md:
# EventBridge → Lambda Simulator → IoT Core → Lambda Ingestion → S3
# E o fluxo de self-labeling: IoT Core → Lambda Label Ingestion → DynamoDB
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# --- BUCKET S3 PARA ARTEFATOS DAS CAMADAS ---
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project_name}-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = merge(var.tags, {
    Name    = "${var.project_name}-artifacts"
    Purpose = "Lambda Layers Artifacts"
  })
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- UPLOAD DOS ARQUIVOS ZIP DAS CAMADAS ---
resource "aws_s3_object" "numpy_layer" {
  bucket = aws_s3_bucket.artifacts.bucket
  key    = "lambda-layers/numpy_layer.zip"
  source = "../dist/numpy_layer.zip"
  etag   = filemd5("../dist/numpy_layer.zip")
}

resource "aws_s3_object" "pandas_layer" {
  bucket = aws_s3_bucket.artifacts.bucket
  key    = "lambda-layers/pandas_layer.zip"
  source = "../dist/pandas_layer.zip"
  etag   = filemd5("../dist/pandas_layer.zip")
}

resource "aws_s3_object" "sklearn_layer" {
  bucket = aws_s3_bucket.artifacts.bucket
  key    = "lambda-layers/sklearn_layer.zip"
  source = "../dist/sklearn_layer.zip"
  etag   = filemd5("../dist/sklearn_layer.zip")
}

module "ingestion" {
  source = "./modules/ingestion"

  project_name   = var.project_name
  s3_bucket_name = var.s3_bucket_name

  mqtt_topic_prefix = var.mqtt_topic_prefix
  machine_ids       = var.machine_ids

  simulator_schedule_expression = var.simulator_schedule_expression

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  machine_state_table_name = var.machine_state_table_name
  label_history_table_name = var.label_history_table_name

  tags = var.tags
}

# --- MÓDULO LAMBDA_LAYERS CENTRALIZADO ---
module "lambda_layers" {
  source = "./modules/lambda_layers"

  project_name        = var.project_name
  artifacts_s3_bucket = aws_s3_bucket.artifacts.bucket

  numpy_layer_s3_key   = aws_s3_object.numpy_layer.key
  pandas_layer_s3_key  = aws_s3_object.pandas_layer.key
  sklearn_layer_s3_key = aws_s3_object.sklearn_layer.key

  tags = var.tags
}

module "processing" {
  source = "./modules/processing"

  project_name             = var.project_name
  s3_bucket_name           = var.s3_bucket_name
  label_history_table_name = module.ingestion.label_history_table_name

  processing_schedule_expression = var.processing_schedule_expression
  time_window_hours              = var.time_window_hours

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  # Camadas centralizadas
  numpy_layer_arn  = module.lambda_layers.numpy_layer_arn
  pandas_layer_arn = module.lambda_layers.pandas_layer_arn

  tags = var.tags
}

module "training_pipeline" {
  source = "./modules/training_pipeline"

  project_name   = var.project_name
  s3_bucket_name = var.s3_bucket_name

  # Camadas centralizadas
  numpy_layer_arn   = module.lambda_layers.numpy_layer_arn
  pandas_layer_arn  = module.lambda_layers.pandas_layer_arn
  sklearn_layer_arn = module.lambda_layers.sklearn_layer_arn

  # Configurações do SageMaker
  training_image_uri          = var.training_image_uri
  training_hyperparameters    = var.training_hyperparameters
  sagemaker_training_role_arn = var.sagemaker_training_role_arn

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  tags = var.tags
}

# IAM Role para o Scheduler acionar a State Machine
resource "aws_iam_role" "scheduler_invoke_sf" {
  name = "${var.project_name}-scheduler-sf-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "scheduler.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_sf_policy" {
  name = "${var.project_name}-scheduler-sf-policy"
  role = aws_iam_role.scheduler_invoke_sf.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["states:StartExecution"],
      Resource = module.training_pipeline.state_machine_arn
    }]
  })
}

# Agendamento semanal para iniciar o pipeline
resource "aws_scheduler_schedule" "training_weekly" {
  name = "${var.project_name}-weekly-training"
  flexible_time_window { mode = "OFF" }
  schedule_expression = var.training_pipeline_schedule_expression

  target {
    arn      = module.training_pipeline.state_machine_arn
    role_arn = aws_iam_role.scheduler_invoke_sf.arn
  }
}

module "inference" {
  source = "./modules/inference"

  project_name        = var.project_name
  region              = var.aws_region
  dynamodb_table_name = module.processing.realtime_features_table_name
  s3_bucket_name      = var.s3_bucket_name

  dependencies_layer_zip_path = var.inference_dependencies_layer_zip_path

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  tags = var.tags
}
