import json
import os
import tempfile
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Tuple

import boto3
import pandas as pd
from sklearn.model_selection import train_test_split

# Constantes de prefixos
PROCESSED_PREFIX = "processed/training_data"
SAGEMAKER_BASE_PREFIX = "sagemaker/training-inputs"
TARGET_TRAIN_FILE = "train.csv"
TARGET_VAL_FILE = "validation.csv"

s3_client = boto3.client("s3")


def _dates_to_process(days_back: int) -> List[datetime]:
    """Gera uma lista de datas UTC começando de hoje até days_back dias atrás (inclusivo)."""
    today = datetime.utcnow().date()
    return [today - timedelta(days=i) for i in range(days_back)]


def _build_prefix_for_date(date_obj: datetime.date) -> str:
    """Constroi o prefixo S3 para uma data específica seguindo a partição year/month/day."""
    return (
        f"{PROCESSED_PREFIX}/"
        f"year={date_obj.year}/"
        f"month={date_obj.month:02d}/"
        f"day={date_obj.day:02d}/"
    )


def _list_csv_keys(bucket: str, prefix: str) -> List[str]:
    """Lista objetos .csv sob um prefixo, retornando a lista de chaves."""
    paginator = s3_client.get_paginator("list_objects_v2")
    csv_keys: List[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".csv"):
                csv_keys.append(key)
    return csv_keys


def _load_csv_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Baixa o objeto CSV do S3 e carrega como DataFrame."""
    response = s3_client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    return pd.read_csv(BytesIO(body))


def _upload_df_to_s3(df: pd.DataFrame, bucket: str, key: str):
    """Salva DataFrame temporariamente como CSV e faz upload para S3."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        df.to_csv(tmp.name, index=False)
        tmp.flush()
        s3_client.upload_file(tmp.name, bucket, key)
    os.remove(tmp.name)


def _prepare_output_paths(bucket: str) -> Tuple[str, str, str]:
    """Gera prefixo com timestamp e devolve URIs de treino e validação."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    base_prefix = f"{SAGEMAKER_BASE_PREFIX}/{timestamp}"
    train_key = f"{base_prefix}/training/{TARGET_TRAIN_FILE}"
    val_key = f"{base_prefix}/validation/{TARGET_VAL_FILE}"
    train_uri = f"s3://{bucket}/{train_key}"
    val_uri = f"s3://{bucket}/{val_key}"
    return train_key, val_key, train_uri, val_uri


def lambda_handler(event, context):  # noqa: D401, ANN001
    """Handler principal da função Lambda.

    Espera evento no formato: {
        "S3Bucket": "nome-bucket",
        "DaysToProcess": 7
    }
    """

    bucket = event.get("S3Bucket")
    days_back = int(event.get("DaysToProcess", 1))

    if not bucket:
        raise ValueError("'S3Bucket' é obrigatório no evento de entrada.")

    print(f"Iniciando preparação com days_back={days_back} no bucket={bucket}")

    # 1. Identificar objetos CSV relevantes
    keys: List[str] = []
    for date_obj in _dates_to_process(days_back):
        prefix = _build_prefix_for_date(date_obj)
        day_keys = _list_csv_keys(bucket, prefix)
        print(f"Encontrados {len(day_keys)} arquivos em {prefix}")
        keys.extend(day_keys)

    if not keys:
        raise FileNotFoundError(
            "Nenhum arquivo .csv encontrado no intervalo de datas especificado."
        )

    # 2. Download e consolidação dos dados
    dataframes: List[pd.DataFrame] = []
    for key in keys:
        df = _load_csv_from_s3(bucket, key)
        dataframes.append(df)

    full_df = pd.concat(dataframes, ignore_index=True)
    print(
        f"DataFrame consolidado contém {len(full_df)} linhas e {len(full_df.columns)} colunas."
    )

    # 3. Embaralhar as linhas
    full_df = full_df.sample(frac=1, random_state=42).reset_index(drop=True)

    # 4. Divisão treino/validação
    train_df, val_df = train_test_split(
        full_df, test_size=0.2, random_state=42, shuffle=False
    )

    # 5. Upload dos conjuntos para S3
    train_key, val_key, train_uri, val_uri = _prepare_output_paths(bucket)
    _upload_df_to_s3(train_df, bucket, train_key)
    _upload_df_to_s3(val_df, bucket, val_key)

    print("Upload concluído:")
    print(f"  Treino -> {train_uri}")
    print(f"  Validação -> {val_uri}")

    # 6. Retornar URIs para o Step Functions
    return {
        "TrainDataUri": train_uri,
        "ValidationDataUri": val_uri,
    }
