import boto3
import pandas as pd
from io import StringIO
from datetime import datetime
from decimal import Decimal
import json

s3_client = boto3.client('s3')
dynamodb_resource = boto3.resource('dynamodb')

def save_features_to_s3(features_df: pd.DataFrame, bucket: str):
    """
    Salva o DataFrame de features em um arquivo CSV no S3, seguindo a estrutura
    de particionamento por data para os dados processados.

    Args:
        features_df: DataFrame do Pandas contendo as features calculadas.
        bucket: O nome do bucket S3 de destino.
    """
    if features_df.empty:
        print("DataFrame de features está vazio. Nenhum dado será salvo no S3.")
        return

    # Converte o DataFrame para uma string CSV em memória
    csv_buffer = StringIO()
    features_df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    # Define o caminho (key) do arquivo no S3 com particionamento por data
    now = datetime.utcnow()
    s3_key = (
        f"processed/training_data/"
        f"year={now.year}/"
        f"month={now.month:02d}/"
        f"day={now.day:02d}/"
        f"features_{now.strftime('%Y%m%d_%H%M%S')}.csv"
    )

    try:
        print(f"Salvando features no S3 em: s3://{bucket}/{s3_key}")
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=csv_content,
            ContentType='text/csv'
        )
        print("Features salvas com sucesso no S3.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar features no S3: {e}")
        raise

def save_features_to_dynamodb(features_dict: dict, table_name: str):
    """
    Salva as features calculadas na tabela do DynamoDB (Feature Store).

    Args:
        features_dict: Dicionário onde as chaves são machine_id e os valores são as features.
        table_name: O nome da tabela DynamoDB de destino.
    """
    if not features_dict:
        print("Dicionário de features está vazio. Nenhum dado será salvo no DynamoDB.")
        return

    table = dynamodb_resource.Table(table_name)
    
    print(f"Iniciando salvamento de {len(features_dict)} registros na tabela {table_name}...")

    try:
        with table.batch_writer() as batch:
            for machine_id, features in features_dict.items():
                # O DynamoDB não aceita floats nativamente, então os convertemos para Decimal
                item_to_save = json.loads(json.dumps(features), parse_float=Decimal)
                batch.put_item(Item=item_to_save)
        
        print("Features salvas com sucesso no DynamoDB.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar features no DynamoDB: {e}")
        raise
    