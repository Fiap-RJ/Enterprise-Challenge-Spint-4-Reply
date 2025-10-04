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

module "processing" {
  source = "./modules/processing"

  project_name             = var.project_name
  s3_bucket_name           = var.s3_bucket_name
  label_history_table_name = module.ingestion.label_history_table_name

  processing_schedule_expression = var.processing_schedule_expression
  time_window_hours              = var.time_window_hours

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  pandas_layer_zip_path = var.pandas_layer_zip_path

  tags = var.tags
}

module "training_pipeline" {
  source = "./modules/training_pipeline"

  project_name   = var.project_name
  s3_bucket_name = var.s3_bucket_name

  # Caminhos dos artefatos zippados
  pandas_layer_zip_path      = var.pandas_layer_zip_path

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

