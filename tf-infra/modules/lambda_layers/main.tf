# =============================================================================
# MÓDULO LAMBDA_LAYERS - CAMADAS CENTRALIZADAS
# =============================================================================
# Este módulo centraliza a criação de todas as camadas Lambda compartilhadas
# =============================================================================

# --- NUMPY LAYER ---
resource "aws_lambda_layer_version" "numpy_layer" {
  filename            = "s3://${var.artifacts_s3_bucket}/${var.numpy_layer_s3_key}"
  layer_name          = "${var.project_name}-numpy-layer"
  compatible_runtimes = [var.lambda_runtime]
  description         = "Lambda Layer contendo a biblioteca numpy"
}

# --- PANDAS LAYER ---
resource "aws_lambda_layer_version" "pandas_layer" {
  filename            = "s3://${var.artifacts_s3_bucket}/${var.pandas_layer_s3_key}"
  layer_name          = "${var.project_name}-pandas-layer"
  compatible_runtimes = [var.lambda_runtime]
  description         = "Lambda Layer contendo a biblioteca pandas"
}

# --- SKLEARN LAYER ---
resource "aws_lambda_layer_version" "sklearn_layer" {
  filename            = "s3://${var.artifacts_s3_bucket}/${var.sklearn_layer_s3_key}"
  layer_name          = "${var.project_name}-sklearn-layer"
  compatible_runtimes = [var.lambda_runtime]
  description         = "Lambda Layer contendo a biblioteca scikit-learn"
}
