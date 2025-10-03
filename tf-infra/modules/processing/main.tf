# =============================================================================
# MÓDULO PROCESSING - FEATURE ENGINEERING E ETL
# =============================================================================
# Implementa o pipeline de processamento conforme arch-pro.md:
# EventBridge Scheduler → Lambda Processor → DynamoDB/S3 (Feature Store)
# =============================================================================

# --- LAMBDA LAYER PARA PANDAS ---

resource "aws_lambda_layer_version" "pandas_layer" {
  filename            = var.pandas_layer_zip_path
  layer_name          = "${var.project_name}-pandas-layer"
  compatible_runtimes = ["python3.12"]
  description         = "Lambda Layer contendo a biblioteca pandas para processamento de dados"

}

# --- TABELA DYNAMODB PARA FEATURE STORE ---

resource "aws_dynamodb_table" "realtime_features" {
  name           = "${var.project_name}-${var.realtime_features_table_name}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "machine_id"

  attribute {
    name = "machine_id"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = aws_dynamodb_table.realtime_features.name
    Type = "Feature Store"
  })
}


# --- SSM PARAMETER STORE PARA GERENCIAMENTO DE ESTADO ---

resource "aws_ssm_parameter" "processing_state" {
  name  = "/${var.project_name}/processing/last-processed-timestamp"
  type  = "String"
  value = var.initial_timestamp

  description = "Timestamp do último processamento realizado pelo Lambda de processamento"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-processing-state"
    Type = "SSM Parameter"
  })
}

# --- IAM ROLE PARA A LAMBDA DE PROCESSAMENTO ---

resource "aws_iam_role" "processing_lambda_role" {
  name = "${var.project_name}-processing-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-processing-lambda-role"
    Type = "IAM Role"
  })
}

# --- IAM POLICY PARA A LAMBDA DE PROCESSAMENTO ---

resource "aws_iam_role_policy" "processing_lambda_policy" {
  name = "${var.project_name}-processing-lambda-policy"
  role = aws_iam_role.processing_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::${var.s3_bucket_name}/processed/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.realtime_features.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan"
        ]
        Resource = "arn:aws:dynamodb:*:*:table/${var.label_history_table_name}"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:PutParameter"
        ]
        Resource = aws_ssm_parameter.processing_state.arn
      }
    ]
  })
}

# --- FUNÇÃO LAMBDA DE PROCESSAMENTO ---

data "archive_file" "processing_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../src/processing"
  output_path = "${path.module}/lambda_artifacts/processing_lambda.zip"
}

resource "aws_lambda_function" "processing_lambda" {
  function_name = "${var.project_name}-processing-lambda"
  role          = aws_iam_role.processing_lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  
  filename         = data.archive_file.processing_lambda_zip.output_path
  source_code_hash = data.archive_file.processing_lambda_zip.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  layers = [aws_lambda_layer_version.pandas_layer.arn]

  environment {
    variables = {
      DATA_LAKE_BUCKET              = var.s3_bucket_name
      DYNAMODB_TABLE_NAME           = aws_dynamodb_table.realtime_features.name
      DYNAMODB_LABEL_HISTORY_TABLE  = var.label_history_table_name
      SSM_PARAMETER_NAME            = aws_ssm_parameter.processing_state.name
      TIME_WINDOW                   = var.time_window_hours
      PREDICTION_HORIZON_HOURS      = var.prediction_horizon_hours
      PROCESSING_LAG_HOURS          = var.processing_lag_hours
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-processing-lambda"
    Type = "Lambda Function"
  })

  depends_on = [
    aws_iam_role_policy.processing_lambda_policy,
    aws_lambda_layer_version.pandas_layer
  ]
}

# --- EVENTBRIDGE SCHEDULER ---

resource "aws_cloudwatch_event_rule" "processing_schedule" {
  name                = "${var.project_name}-processing-schedule"
  description         = "Trigger processing lambda for feature engineering"
  schedule_expression = var.processing_schedule_expression

  tags = merge(var.tags, {
    Name = "${var.project_name}-processing-schedule"
  })
}

resource "aws_cloudwatch_event_target" "processing_target" {
  rule      = aws_cloudwatch_event_rule.processing_schedule.name
  target_id = "ProcessingLambdaTarget"
  arn       = aws_lambda_function.processing_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge_processing" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processing_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.processing_schedule.arn
}

# --- CLOUDWATCH LOG GROUP ---

resource "aws_cloudwatch_log_group" "processing_lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.processing_lambda.function_name}"
  retention_in_days = 14

  tags = merge(var.tags, {
    Name = "${var.project_name}-processing-lambda-logs"
    Type = "CloudWatch Log Group"
  })
}
