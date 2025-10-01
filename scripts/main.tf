# Define a AWS como provedor e configura a região
terraform {
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

# Configuração do provedor AWS
provider "aws" {
  region = "us-east-1"
}

# Variável de Projeto para nomes dos recursos
variable "project_name" {
  description = "Nome do Projeto, usado como prefixo nos recursos"
  type        = string
  default     = "replyec"
}

# Região atual (para construir nomes de endpoints)
data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# --- 1. CONFIGURAÇÃO DE REDE (VPC E SUBNETS) ---
# Seguindo as boas práticas: 1 VPC, 2 Subnets Públicas, 2 Subnets Privadas em 2 AZs.

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 1)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${var.project_name}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]

  tags = {
    Name = "${var.project_name}-s3-endpoint"
  }
}

# --- 2. DATA LAKE (S3) ---

resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-data-lake-${data.aws_availability_zones.available.names[0]}"
  tags = {
    Name = "MLOps Industrial Data Lake"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_encryption" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- 3. LAMBDA SIMULADOR (EventBridge → Lambda → IoT Core) ---

# IAM Role para o Lambda Simulador
resource "aws_iam_role" "simulator_role" {
  name = "${var.project_name}-simulator-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Policy inline para o Lambda Simulador (IoT Core + Logs)
resource "aws_iam_role_policy" "simulator_policy" {
  name = "${var.project_name}-simulator-policy"
  role = aws_iam_role.simulator_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "iot:Publish"
        ],
        Resource = "*"
      }
    ]
  })
}

# Anexa políticas gerenciadas para logs
resource "aws_iam_role_policy_attachment" "simulator_logs" {
  role       = aws_iam_role.simulator_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Empacota o código Python do Simulador
data "archive_file" "simulator_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/sensor_simulator.py"
  output_path = "${path.module}/../lambda/sensor_simulator.zip"
}

# Função Lambda Simuladora
resource "aws_lambda_function" "simulator" {
  function_name = "${var.project_name}-simulator-lambda"
  role          = aws_iam_role.simulator_role.arn
  handler       = "sensor_simulator.handler"
  runtime       = "python3.11"
  filename      = data.archive_file.simulator_zip.output_path
  source_code_hash = data.archive_file.simulator_zip.output_base64sha256
  timeout       = 30
  memory_size   = 256

  depends_on = [
    aws_iam_role_policy.simulator_policy,
    aws_iam_role_policy_attachment.simulator_logs
  ]
}

# --- 4. EVENTBRIDGE (Agendamento) ---

# EventBridge Rule para agendamento
resource "aws_cloudwatch_event_rule" "simulator_schedule" {
  name                = "${var.project_name}-simulator-schedule"
  description         = "Trigger sensor simulator every minute"
  schedule_expression = "rate(1 minute)"
  
  tags = {
    Name = "${var.project_name}-simulator-schedule"
  }
}

# EventBridge Target para invocar o Lambda Simulador
resource "aws_cloudwatch_event_target" "simulator_target" {
  rule      = aws_cloudwatch_event_rule.simulator_schedule.name
  target_id = "SimulatorLambdaTarget"
  arn       = aws_lambda_function.simulator.arn
}

# Permissão para EventBridge invocar o Lambda Simulador
resource "aws_lambda_permission" "allow_eventbridge_simulator" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.simulator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.simulator_schedule.arn
}

# --- 5. LAMBDA DE INGESTÃO (IoT Core → Lambda → S3) ---

# IAM Role para a Lambda de Ingestão
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Policy inline mínima para S3
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-inline-policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:AbortMultipartUpload",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      }
    ]
  })
}

# Anexa políticas gerenciadas para logs e acesso a VPC (ENIs)
resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_security_group" "lambda_sg" {
  name        = "${var.project_name}-lambda-sg"
  description = "Security Group for Lambda with egress only"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-lambda-sg"
  }
}

# Empacota o código Python da Lambda de Ingestão
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/ingestion_processor.py"
  output_path = "${path.module}/../lambda/ingestion_processor.zip"
}

# Função Lambda de Ingestão
resource "aws_lambda_function" "ingestion" {
  function_name = "${var.project_name}-ingestion-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "ingestion_processor.handler"
  runtime       = "python3.11"
  filename      = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout       = 30
  memory_size   = 256

  environment {
    variables = {
      S3_BUCKET_NAME   = aws_s3_bucket.data_lake.bucket
      S3_PREFIX_ROOT   = "raw"
      BATCH_SIZE       = "50"
      COMPRESS_GZIP    = "true"
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_iam_role_policy_attachment.lambda_basic_logs,
    aws_iam_role_policy_attachment.lambda_vpc_access,
    aws_vpc_endpoint.s3
  ]

  # Timeout para criação da Lambda em VPC (ENI creation)
  timeouts {
    create = "15m"
  }
}

# --- 6. IOT CORE (REGRA) ---

# Permissão para que o IoT Core invoque a Lambda de Ingestão
resource "aws_lambda_permission" "allow_iot_invoke" {
  statement_id  = "AllowExecutionFromIoT"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.lambda_ingest.arn
}

# Regra do IoT para invocar a Lambda de Ingestão
resource "aws_iot_topic_rule" "lambda_ingest" {
  name        = "${var.project_name}_lambda_rule"
  description = "Rule to invoke Lambda from MQTT topic"
  enabled     = true

  sql         = "SELECT * FROM 'sensores/fabrica/dados'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.ingestion.arn
  }
}

# --- OUTPUTS (Variáveis úteis após a aplicação) ---

output "vpc_id" {
  description = "ID da VPC criada"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs das Subnets Privadas (onde ficará a Lambda de Ingestão)"
  value       = aws_subnet.private[*].id
}

output "s3_data_lake_bucket_name" {
  description = "Nome do S3 Bucket Data Lake"
  value       = aws_s3_bucket.data_lake.id
}

output "iot_mqtt_topic" {
  description = "Tópico MQTT que o Simulador deve usar para publicar dados"
  value       = "sensores/fabrica/dados"
}

output "simulator_lambda_name" {
  description = "Nome da função Lambda Simuladora"
  value       = aws_lambda_function.simulator.function_name
}

output "ingestion_lambda_name" {
  description = "Nome da função Lambda de Ingestão"
  value       = aws_lambda_function.ingestion.function_name
}

output "eventbridge_rule_name" {
  description = "Nome da regra do EventBridge"
  value       = aws_cloudwatch_event_rule.simulator_schedule.name
}
