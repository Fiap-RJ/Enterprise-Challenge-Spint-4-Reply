import boto3
import pandas as pd
from io import StringIO
from datetime import datetime, timezone
from decimal import Decimal
import json
from boto3.dynamodb.conditions import Key, Attr

s3_client = boto3.client('s3')
dynamodb_resource = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm')

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
    now = datetime.now(timezone.utc)
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

def fetch_failure_labels_from_dynamo(table_name: str, start_time: datetime, end_time: datetime) -> list:
    """
    Busca eventos de falha do DynamoDB dentro de um intervalo de tempo específico.
    Esta função é usada para criar labels preditivas baseadas em falhas futuras.

    Args:
        table_name: Nome da tabela DynamoDB que contém o histórico de falhas.
        start_time: Data/hora de início para busca de falhas.
        end_time: Data/hora de fim para busca de falhas.

    Returns:
        Lista de dicionários contendo eventos de falha encontrados no período.
    """
    if not table_name:
        print("Nome da tabela de falhas não fornecido. Retornando lista vazia.")
        return []

    table = dynamodb_resource.Table(table_name)
    all_failures = []
    
    print(f"Buscando falhas na tabela {table_name} entre {start_time.isoformat()} e {end_time.isoformat()}")
    
    try:
        # Converte datetime para string ISO para comparação no DynamoDB
        start_time_str = start_time.isoformat()
        end_time_str = end_time.isoformat()
        
        # Usa scan com FilterExpression para buscar falhas no intervalo
        filter_expression = Attr('timestamp_utc').between(start_time_str, end_time_str)
        
        response = table.scan(FilterExpression=filter_expression)
        all_failures.extend(response.get('Items', []))
        
        # Lida com paginação do DynamoDB
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_failures.extend(response.get('Items', []))
        
        print(f"Encontradas {len(all_failures)} falhas no período especificado.")
        return all_failures
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar falhas no DynamoDB: {e}")
        raise

def get_ssm_parameter(parameter_name: str) -> str:
    """
    Lê um parâmetro do AWS Systems Manager Parameter Store.

    Args:
        parameter_name: Nome do parâmetro no SSM.

    Returns:
        Valor do parâmetro como string.
    """
    try:
        response = ssm_client.get_parameter(Name=parameter_name)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"[ERRO] Falha ao ler parâmetro SSM {parameter_name}: {e}")
        raise

def update_ssm_parameter(parameter_name: str, value: str) -> None:
    """
    Atualiza um parâmetro no AWS Systems Manager Parameter Store.

    Args:
        parameter_name: Nome do parâmetro no SSM.
        value: Novo valor para o parâmetro.
    """
    try:
        ssm_client.put_parameter(
            Name=parameter_name,
            Value=value,
            Type='String',
            Overwrite=True
        )
        print(f"Parâmetro SSM {parameter_name} atualizado com sucesso: {value}")
    except Exception as e:
        print(f"[ERRO] Falha ao atualizar parâmetro SSM {parameter_name}: {e}")
        raise
    