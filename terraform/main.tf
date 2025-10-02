# =============================================================================
# INFRAESTRUTURA MLOPS INDUSTRIAL - INGESTÃO DE DADOS
# =============================================================================
# Implementa o fluxo de ingestão conforme arch-pro.md:
# EventBridge → Lambda Simulator → IoT Core → Lambda Ingestion → S3
# E o fluxo de self-labeling: IoT Core → Lambda Label Ingestion → DynamoDB
# =============================================================================

# Configuração do provedor AWS
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

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Módulo de Ingestão
module "ingestion" {
  source = "./modules/ingestion"

  # Variáveis obrigatórias
  project_name    = var.project_name
  s3_bucket_name  = var.s3_bucket_name

  # Configurações MQTT conforme arquitetura
  mqtt_topic_prefix = var.mqtt_topic_prefix
  machine_ids        = var.machine_ids

  # Configurações de agendamento
  simulator_schedule_expression = var.simulator_schedule_expression

  # Configurações das Lambdas
  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  # Configurações de tabelas DynamoDB
  machine_state_table_name = var.machine_state_table_name
  label_history_table_name = var.label_history_table_name

  # Configurações de artefatos (placeholder)
  lambda_placeholder_zip_path = var.lambda_placeholder_zip_path

  tags = var.tags
}
