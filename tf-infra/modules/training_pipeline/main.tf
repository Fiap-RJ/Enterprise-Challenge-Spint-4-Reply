# =============================================================================
# MÓDULO TRAINING_PIPELINE - ORQUESTRAÇÃO DE TREINAMENTO E DEPLOY
# =============================================================================
# Este módulo cria:
#   * Camada Lambda (pandas + scikit-learn)
#   * Funções Lambda data_prep e model_evaluation
#   * Package Group do SageMaker Model Registry
#   * Roles/Policies para Lambdas, SageMaker Training Job e Step Functions
#   * State Machine Step Functions que orquestra o pipeline completo
# =============================================================================

locals {
  lambda_runtime = "python3.12"
}

# -----------------------------------------------------------------------------
# 1. LAMBDA LAYERS (CENTRALIZADAS)
# -----------------------------------------------------------------------------
# As camadas são criadas pelo módulo lambda_layers centralizado

# -----------------------------------------------------------------------------
# 2. LAMBDA FUNCTIONS
# -----------------------------------------------------------------------------
# 2.1 ZIP dos códigos

data "archive_file" "data_prep_lambda_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/training/data_prep_lambda.py"
  output_path = "${path.module}/lambda_artifacts/data_prep_lambda.zip"
}

data "archive_file" "model_eval_lambda_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/training/model_evaluation_lambda.py"
  output_path = "${path.module}/lambda_artifacts/model_eval_lambda.zip"
}

# 2.2 IAM Role genérica para Lambdas do pipeline
resource "aws_iam_role" "pipeline_lambda_role" {
  name = "${var.project_name}-pipeline-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = merge(var.tags, { Name = "${var.project_name}-pipeline-lambda-role" })
}

resource "aws_iam_role_policy" "pipeline_lambda_policy" {
  name = "${var.project_name}-pipeline-lambda-policy"
  role = aws_iam_role.pipeline_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Effect   = "Allow",
        Action   = ["sagemaker:CreateModelPackage"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "data_prep" {
  function_name = "${var.project_name}-data-prep"
  role          = aws_iam_role.pipeline_lambda_role.arn
  handler       = "data_prep_lambda.lambda_handler"
  runtime       = local.lambda_runtime

  filename         = data.archive_file.data_prep_lambda_zip.output_path
  source_code_hash = data.archive_file.data_prep_lambda_zip.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size
  layers      = [var.numpy_layer_arn, var.pandas_layer_arn, var.sklearn_layer_arn]

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name
    }
  }

  tags = merge(var.tags, { Name = "${var.project_name}-data-prep" })
}

resource "aws_lambda_function" "model_evaluation" {
  function_name = "${var.project_name}-model-evaluation"
  role          = aws_iam_role.pipeline_lambda_role.arn
  handler       = "model_evaluation_lambda.lambda_handler"
  runtime       = local.lambda_runtime

  filename         = data.archive_file.model_eval_lambda_zip.output_path
  source_code_hash = data.archive_file.model_eval_lambda_zip.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size
  layers      = [var.numpy_layer_arn, var.pandas_layer_arn, var.sklearn_layer_arn]

  environment {
    variables = {
      MODEL_PACKAGE_GROUP = "${var.project_name}-mpg"
    }
  }

  tags = merge(var.tags, { Name = "${var.project_name}-model-evaluation" })
}

# -----------------------------------------------------------------------------
# 3. SAGEMAKER RESOURCES
# -----------------------------------------------------------------------------
resource "aws_sagemaker_model_package_group" "model_group" {
  model_package_group_name        = "${var.project_name}-mpg"
  model_package_group_description = "Pacotes de modelo de manutenção preditiva"
  tags                            = merge(var.tags, { Name = "${var.project_name}-mpg" })
}

# (Endpoint inicial )
# resource "aws_sagemaker_endpoint_configuration" "initial_config" {
#   name = "${var.project_name}-endpoint-config-initial"
#   production_variants {
#     variant_name           = "AllTraffic"
#     model_name             = "placeholder" 
#     initial_instance_count = 1
#     instance_type          = "ml.m5.large"
#   }
# }

# resource "aws_sagemaker_endpoint" "model_endpoint" {
#   name                 = "${var.project_name}-endpoint"
#   endpoint_config_name = aws_sagemaker_endpoint_configuration.initial_config.name
# }

# -----------------------------------------------------------------------------
# 4. STEP FUNCTIONS - ROLE & STATE MACHINE
# -----------------------------------------------------------------------------
resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-sf-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "states.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })

  tags = merge(var.tags, { Name = "${var.project_name}-sf-role" })
}

resource "aws_iam_role_policy" "step_functions_policy" {
  name = "${var.project_name}-sf-policy"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["lambda:InvokeFunction"],
        Resource = [
          aws_lambda_function.data_prep.arn,
          aws_lambda_function.model_evaluation.arn
        ]
      },
      {
        Effect   = "Allow",
        Action   = ["sagemaker:*"],
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = ["iam:PassRole"],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "events:PutRule",
          "events:DeleteRule",
          "events:PutTargets",
          "events:RemoveTargets"
        ],
        Resource = "arn:aws:events:*:*:rule/StepFunctionsGetEventsForSageMaker*"
      }
    ]
  })
}

locals {
  sf_definition = jsonencode({
    Comment = "Pipeline de Treinamento e Deploy",
    StartAt = "DataPrep",
    States = {
      DataPrep = {
        Type     = "Task",
        Resource = aws_lambda_function.data_prep.arn,
        Next     = "TrainModel"
      },
      TrainModel = {
        Type     = "Task",
        Resource = "arn:aws:states:::sagemaker:createTrainingJob.sync",
        Parameters = {
          TrainingJobName = "${var.project_name}-training-${formatdate("YYYYMMDD'T'HHmmss", timestamp())}"
          RoleArn         = var.sagemaker_training_role_arn
          AlgorithmSpecification = {
            TrainingImage     = var.training_image_uri
            TrainingInputMode = "File"
          }
          InputDataConfig = [
            {
              ChannelName = "training"
              DataSource  = { S3DataSource = { S3Uri = "$.TrainDataUri", S3DataType = "S3Prefix", S3DataDistributionType = "FullyReplicated" } }
            },
            {
              ChannelName = "validation"
              DataSource  = { S3DataSource = { S3Uri = "$.ValidationDataUri", S3DataType = "S3Prefix", S3DataDistributionType = "FullyReplicated" } }
            }
          ]
          OutputDataConfig = { S3OutputPath = "s3://${var.s3_bucket_name}/sagemaker/training-output" }
          ResourceConfig = {
            InstanceCount  = 1
            InstanceType   = "ml.m5.large"
            VolumeSizeInGB = 30
          }
          StoppingCondition = { MaxRuntimeInSeconds = 3600 }
          HyperParameters   = var.training_hyperparameters
        },
        ResultPath = "$.TrainingJob",
        Next       = "EvaluateModel"
      },
      EvaluateModel = {
        Type     = "Task",
        Resource = aws_lambda_function.model_evaluation.arn,
        Next     = "IsModelApproved"
      },
      IsModelApproved = {
        Type = "Choice",
        Choices = [
          {
            Variable     = "$.status",
            StringEquals = "APPROVED",
            Next         = "DeployModel"
          }
        ],
        Default = "FailState"
      },
      DeployModel = {
        Type     = "Task",
        Resource = "arn:aws:states:::sagemaker:createModel",
        Parameters = {
          ExecutionRoleArn = var.sagemaker_training_role_arn
          PrimaryContainer = {
            Image        = var.training_image_uri
            ModelDataUrl = "$.model_package_arn"
          }
          ModelName = "${var.project_name}-model-${formatdate("YYYYMMDD'T'HHmmss", timestamp())}"
        },
        End = true
      },
      FailState = {
        Type  = "Fail",
        Error = "ModelRejected",
        Cause = "AUC abaixo do mínimo"
      }
    }
  })
}

resource "aws_sfn_state_machine" "training_pipeline" {
  name       = "${var.project_name}-training-pipeline"
  role_arn   = aws_iam_role.step_functions_role.arn
  definition = local.sf_definition
  tags       = var.tags
}
