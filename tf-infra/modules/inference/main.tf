locals {
  app_name = "inference-app"
  region   = var.region
  
  # Caminhos para o Lambda Layer
  lambda_layer_dir = "${path.module}/lambda_layers/python"
  
  # Nome do arquivo de requisitos
  requirements_file = "${path.module}/../../../src/inference/requeriments.txt"
  
  # Nome da camada
  layer_name = "${local.app_name}-dependencies"
}

data "aws_caller_identity" "current" {}

# Cria o diretório para o layer e instala as dependências
resource "null_resource" "install_dependencies" {
  # Executa apenas se o diretório não existir ou se o arquivo de requisitos mudou
  triggers = {
    requirements = filemd5(local.requirements_file)
  }

  # Comandos para criar o diretório e instalar as dependências
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p ${local.lambda_layer_dir}
      pip install -r ${local.requirements_file} --target ${local.lambda_layer_dir}
    EOT
  }
}

# Cria o arquivo ZIP com as dependências
data "archive_file" "layer_zip" {
  depends_on  = [null_resource.install_dependencies]
  type        = "zip"
  output_path = "${path.module}/lambda_layers/layer.zip"
  source_dir  = local.lambda_layer_dir
  
  # Exclui arquivos desnecessários
  excludes = [
    "__pycache__",
    "*.pyc",
    "*.dist-info/*",
    "*/__pycache__/*"
  ]
}

# Cria o Lambda Layer
resource "aws_lambda_layer_version" "dependencies" {
  layer_name          = local.layer_name
  description         = "Dependências para a função Lambda de inferência"
  filename           = data.archive_file.layer_zip.output_path
  source_code_hash   = data.archive_file.layer_zip.output_base64sha256
  compatible_runtimes = [var.python_runtime]
  
  depends_on = [data.archive_file.layer_zip]
}

# IAM Role para a Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "${local.app_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Policy básica para execução de Lambda
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy para acesso a DynamoDB e S3
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${local.app_name}-dynamodb-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          "arn:aws:dynamodb:${local.region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamodb_table_name}",
          "arn:aws:dynamodb:${local.region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamodb_table_name}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.app_name}-${data.aws_caller_identity.current.account_id}",
          "arn:aws:s3:::${var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.app_name}-${data.aws_caller_identity.current.account_id}/*"
        ]
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "inference_api" {
  function_name    = "${local.app_name}-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = var.python_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  
  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      DYNAMODB_TABLE    = var.dynamodb_table_name
      S3_BUCKET         = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.app_name}-${data.aws_caller_identity.current.account_id}"
      PREDICTION_API_URL = var.prediction_api_url
    }
  }
}

# API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${local.app_name}-api"
  protocol_type = "HTTP"
  target        = aws_lambda_function.inference_api.arn
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inference_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# Output the API endpoint
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.api.api_endpoint
}

# Output the Lambda function name
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.inference_api.function_name
}
