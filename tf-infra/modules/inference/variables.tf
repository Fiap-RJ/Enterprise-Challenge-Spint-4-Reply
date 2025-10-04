variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "inference-app"
}

variable "region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for feature store"
  type        = string
  default     = "MachineFeatureStore"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for storing application data"
  type        = string
  default     = ""
}

variable "prediction_api_url" {
  description = "URL of the prediction API (if using external service)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

variable "lambda_timeout" {
  description = "Timeout in seconds for the Lambda function"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Memory size in MB for the Lambda function"
  type        = number
  default     = 256
}

variable "python_runtime" {
  description = "Python runtime version for Lambda"
  type        = string
  default     = "python3.9"
}
