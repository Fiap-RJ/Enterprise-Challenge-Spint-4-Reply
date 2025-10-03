# =============================================================================
# MÓDULO DE INGESTÃO - ARQUITETURA MLOPS INDUSTRIAL
# =============================================================================
# Este módulo implementa o fluxo de ingestão de dados conforme documentado
# no arch-pro.md: EventBridge → Lambda Simulator → IoT Core → Lambda Ingestion → S3
# E o fluxo de self-labeling: IoT Core → Lambda Label Ingestion → DynamoDB
# =============================================================================

# --- 1. S3 DATA LAKE (BUCKET PARA DADOS BRUTOS) ---

resource "aws_s3_bucket" "data_lake" {
  bucket = var.s3_bucket_name

  tags = merge(var.tags, {
    Name        = "${var.project_name}-data-lake"
    Purpose     = "MLOps Industrial Data Lake"
  })
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- 2. DYNAMODB TABLES ---

resource "aws_dynamodb_table" "machine_state" {
  name           = var.machine_state_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "machine_id"

  attribute {
    name = "machine_id"
    type = "S"
  }

  tags = merge(var.tags, {
    Name    = var.machine_state_table_name
    Purpose = "Machine degradation state for simulation"
  })
}

resource "aws_dynamodb_table" "label_history" {
  name           = var.label_history_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "machine_id"
  range_key      = "timestamp_utc"

  attribute {
    name = "machine_id"
    type = "S"
  }

  attribute {
    name = "timestamp_utc"
    type = "S"
  }

  tags = merge(var.tags, {
    Name    = var.label_history_table_name
    Purpose = "Label history for self-labeling"
  })
}

# --- 3. IAM ROLES E POLICIES ---

resource "aws_iam_role" "simulator_role" {
  name = "${var.project_name}-simulator-role"

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
    Name = "${var.project_name}-simulator-role"
  })
}

resource "aws_iam_role_policy" "simulator_policy" {
  name = "${var.project_name}-simulator-policy"
  role = aws_iam_role.simulator_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Publish"
        ]
        Resource = [
          "arn:aws:iot:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:topic/industrial/machine/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.machine_state.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "simulator_logs" {
  role       = aws_iam_role.simulator_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "ingestion_role" {
  name = "${var.project_name}-ingestion-role"

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
    Name = "${var.project_name}-ingestion-role"
  })
}

resource "aws_iam_role_policy" "ingestion_policy" {
  name = "${var.project_name}-ingestion-policy"
  role = aws_iam_role.ingestion_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingestion_logs" {
  role       = aws_iam_role.ingestion_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "label_ingestion_role" {
  name = "${var.project_name}-label-ingestion-role"

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
    Name = "${var.project_name}-label-ingestion-role"
  })
}

resource "aws_iam_role_policy" "label_ingestion_policy" {
  name = "${var.project_name}-label-ingestion-policy"
  role = aws_iam_role.label_ingestion_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.label_history.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "label_ingestion_logs" {
  role       = aws_iam_role.label_ingestion_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- 4. LAMBDA FUNCTIONS ---

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "archive_file" "simulator_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/ingestion/sensor_simulator.py"
  output_path = "${path.module}/lambda_artifacts/simulator.zip"
}

resource "aws_lambda_function" "simulator" {
  function_name = "${var.project_name}-simulator"
  role          = aws_iam_role.simulator_role.arn
  handler       = "sensor_simulator.lambda_handler"
  runtime       = "python3.12"
  
  filename         = data.archive_file.simulator_zip.output_path
  source_code_hash = data.archive_file.simulator_zip.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      STATE_TABLE_NAME = aws_dynamodb_table.machine_state.name
      TOPIC_PREFIX     = var.mqtt_topic_prefix
    }
  }

  depends_on = [
    aws_iam_role_policy.simulator_policy,
    aws_iam_role_policy_attachment.simulator_logs
  ]

  tags = merge(var.tags, {
    Name = "${var.project_name}-simulator"
  })
}

data "archive_file" "ingestion_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/ingestion/ingestion_processor.py"
  output_path = "${path.module}/lambda_artifacts/ingestion.zip"
}

resource "aws_lambda_function" "ingestion" {
  function_name = "${var.project_name}-ingestion"
  role          = aws_iam_role.ingestion_role.arn
  handler       = "ingestion_processor.handler"
  runtime       = "python3.12"
  
  filename         = data.archive_file.ingestion_zip.output_path
  source_code_hash = data.archive_file.ingestion_zip.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.data_lake.bucket
      S3_PREFIX_ROOT = "raw"
    }
  }

  depends_on = [
    aws_iam_role_policy.ingestion_policy,
    aws_iam_role_policy_attachment.ingestion_logs
  ]

  tags = merge(var.tags, {
    Name = "${var.project_name}-ingestion"
  })
}

data "archive_file" "label_ingestion_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/ingestion/label_ingestion_lambda.py"
  output_path = "${path.module}/lambda_artifacts/label_ingestion.zip"
}

resource "aws_lambda_function" "label_ingestion" {
  function_name = "${var.project_name}-label-ingestion"
  role          = aws_iam_role.label_ingestion_role.arn
  handler       = "label_ingestion_lambda.lambda_handler"
  runtime       = "python3.12"
  
  filename         = data.archive_file.label_ingestion_zip.output_path
  source_code_hash = data.archive_file.label_ingestion_zip.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.label_history.name
    }
  }

  depends_on = [
    aws_iam_role_policy.label_ingestion_policy,
    aws_iam_role_policy_attachment.label_ingestion_logs
  ]

  tags = merge(var.tags, {
    Name = "${var.project_name}-label-ingestion"
  })
}

# --- 5. EVENTBRIDGE SCHEDULER ---

resource "aws_cloudwatch_event_rule" "simulator_schedule" {
  name                = "${var.project_name}-simulator-schedule"
  description         = "Trigger sensor simulator every minute"
  schedule_expression = var.simulator_schedule_expression

  tags = merge(var.tags, {
    Name = "${var.project_name}-simulator-schedule"
  })
}

resource "aws_cloudwatch_event_target" "simulator_target" {
  rule      = aws_cloudwatch_event_rule.simulator_schedule.name
  target_id = "SimulatorLambdaTarget"
  arn       = aws_lambda_function.simulator.arn
}

resource "aws_lambda_permission" "allow_eventbridge_simulator" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.simulator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.simulator_schedule.arn
}

# --- 6. IOT CORE RULES (SEPARADAS POR TIPO) ---

resource "aws_lambda_permission" "allow_iot_telemetry_invoke" {
  statement_id  = "AllowExecutionFromIoTTelemetry"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.telemetry_ingestion_rule.arn
}

resource "aws_iot_topic_rule" "telemetry_ingestion_rule" {
  name        = "${var.project_name}_telemetry_ingestion_rule"
  description = "Rule to invoke Lambda from MQTT telemetry topics (temperature, vibration)"
  enabled     = true

  sql         = "SELECT *, topic() as mqtt_topic FROM 'industrial/machine/+/+'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.ingestion.arn
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-telemetry-ingestion-rule"
  })
}

resource "aws_lambda_permission" "allow_iot_failure_invoke" {
  statement_id  = "AllowExecutionFromIoTFailure"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.label_ingestion.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.failure_ingestion_rule.arn
}

resource "aws_iot_topic_rule" "failure_ingestion_rule" {
  name        = "${var.project_name}_failure_ingestion_rule"
  description = "Rule to invoke Lambda from MQTT failure event topics"
  enabled     = true

  sql         = "SELECT * FROM 'industrial/machine/+/event/failure'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.label_ingestion.arn
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-failure-ingestion-rule"
  })
}
