import json
import os
from urllib.parse import urlparse

import boto3

s3_client = boto3.client("s3")
sm_client = boto3.client("sagemaker")


# ----------------------- Helpers ----------------------- #


def _parse_s3_uri(s3_uri: str):
    """Converte uma S3 URI (s3://bucket/key) em (bucket, key)."""
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"URI inválida: {s3_uri}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


def _download_evaluation_metrics(s3_uri: str) -> dict:
    """Baixa evaluation.json do S3 e retorna seu conteúdo como dict."""
    bucket, key = _parse_s3_uri(s3_uri)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    data = json.loads(content)
    return data.get("metrics", data)  # suporta formato direto ou {"metrics": {...}}


def _register_model(
    model_artifacts_uri: str,
    inference_image_uri: str,
    model_package_group: str,
    auc_score: float,
):
    """Cria um pacote de modelo no SageMaker Model Registry."""
    response = sm_client.create_model_package(
        ModelPackageGroupName=model_package_group,
        ModelPackageDescription=f"Modelo com AUC={auc_score:.4f}",
        InferenceSpecification={
            "Containers": [
                {
                    "Image": inference_image_uri,
                    "ModelDataUrl": model_artifacts_uri,
                }
            ],
            "SupportedContentTypes": ["text/csv"],
            "SupportedResponseMIMETypes": ["text/csv"],
        },
        ModelApprovalStatus="Approved",
    )
    return response["ModelPackageArn"]


# ----------------------- Lambda Handler ----------------------- #


def lambda_handler(event, context):  # noqa: D401, ANN001
    """Avalia métricas do modelo e registra no Model Registry, se aprovado.

    Espera evento no formato:
        {
          "EvaluationMetricsUri": "s3://.../evaluation.json",
          "ModelArtifactsUri": "s3://.../model.tar.gz",
          "InferenceImageUri": "<image_uri>",
          "ModelPackageGroupName": "<group_name>",
          "MinimumAucScore": 0.9
        }
    """

    metrics_uri = event["EvaluationMetricsUri"]
    model_uri = event["ModelArtifactsUri"]
    image_uri = event["InferenceImageUri"]
    group_name = event["ModelPackageGroupName"]
    min_auc = float(event["MinimumAucScore"])

    # 1. Carregar métricas
    metrics = _download_evaluation_metrics(metrics_uri)
    model_auc = float(metrics.get("auc"))

    if model_auc >= min_auc:
        # 2a. Aprovar e registrar modelo
        model_package_arn = _register_model(model_uri, image_uri, group_name, model_auc)
        result = {
            "status": "APPROVED",
            "model_auc": model_auc,
            "model_package_arn": model_package_arn,
        }
        print(
            f"Modelo aprovado com AUC={model_auc:.4f}. Registrado sob ARN {model_package_arn}"
        )
    else:
        # 2b. Rejeitar modelo
        message = f"AUC de {model_auc:.4f} é inferior ao mínimo de {min_auc:.4f}"
        result = {
            "status": "REJECTED",
            "model_auc": model_auc,
            "message": message,
        }
        print(message)

    return result
