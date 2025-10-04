locals {
  app_name       = "inference-app"
  region         = var.region
  lambda_runtime = "python3.12"
}

data "aws_caller_identity" "current" {}

# --- ZIP do código da Lambda de inferência ---
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/inference/app.py"
  output_path = "${path.module}/lambda_artifacts/inference_lambda.zip"
}

# --- LAMBDA LAYER (usando arquivo ZIP pré-construído) ---
resource "aws_lambda_layer_version" "dependencies" {
  filename            = var.dependencies_layer_zip_path
  layer_name          = "${var.project_name}-inference-dependencies"
  compatible_runtimes = [local.lambda_runtime]
  description         = "Dependências para a função Lambda de inferência"
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
          "arn:aws:s3:::${var.s3_bucket_name != "" ? var.s3_bucket_name : format("%s-%s", local.app_name, data.aws_caller_identity.current.account_id)}",
          "arn:aws:s3:::${var.s3_bucket_name != "" ? var.s3_bucket_name : format("%s-%s", local.app_name, data.aws_caller_identity.current.account_id)}/*"
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
      DYNAMODB_TABLE     = var.dynamodb_table_name
      S3_BUCKET          = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.app_name}-${data.aws_caller_identity.current.account_id}"
      PREDICTION_API_URL = var.prediction_api_url
    }
  }
}

# API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${local.app_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.inference_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

# Ajustar permissão Lambda
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inference_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*"
}

