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

  project_name    = var.project_name
  s3_bucket_name  = var.s3_bucket_name

  mqtt_topic_prefix = var.mqtt_topic_prefix
  machine_ids        = var.machine_ids

  simulator_schedule_expression = var.simulator_schedule_expression

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  machine_state_table_name = var.machine_state_table_name
  label_history_table_name = var.label_history_table_name

  tags = var.tags
}

module "processing" {
  source = "./modules/processing"

  project_name    = var.project_name
  s3_bucket_name  = var.s3_bucket_name

  processing_schedule_expression = var.processing_schedule_expression
  time_window_hours             = var.time_window_hours

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  pandas_layer_zip_path = var.pandas_layer_zip_path

  tags = var.tags
}

