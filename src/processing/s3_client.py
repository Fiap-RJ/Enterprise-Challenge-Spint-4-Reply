import boto3
import json
from datetime import datetime, timedelta
from typing import List, Dict

def fetch_sensor_data(bucket: str, start_time: datetime, end_time: datetime) -> List[Dict]:
    """
    Busca todos os arquivos .jsonl de partições no S3 (raw/year=.../hour=...)
    dentro de um intervalo de tempo e retorna uma lista com todos os eventos.

    Args:
        bucket: O nome do bucket S3 (ex: 'replyec-data-lake-20250115').
        start_time: A data/hora de início para a busca.
        end_time: A data/hora de fim para a busca.

    Returns:
        Uma lista de dicionários, onde cada dicionário é um evento de sensor.
    """
    s3_client = boto3.client('s3')
    all_events = []
    
    # Itera sobre cada hora no intervalo de tempo especificado
    current_hour = start_time.replace(minute=0, second=0, microsecond=0)
    while current_hour < end_time:
        prefix = (
            f"raw/year={current_hour.year}"
            f"/month={current_hour.month:02d}"
            f"/day={current_hour.day:02d}"
            f"/hour={current_hour.hour:02d}/"
        )
        
        print(f"Buscando dados no prefixo: s3://{bucket}/{prefix}")
        
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if 'Contents' not in page:
                    continue
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.jsonl'):
                        print(f"  Lendo arquivo: {key}")
                        response = s3_client.get_object(Bucket=bucket, Key=key)
                        content = response['Body'].read().decode('utf-8')
                        events = [json.loads(line) for line in content.splitlines() if line.strip()]
                        all_events.extend(events)
        except Exception as e:
            print(f"Erro ao processar o prefixo {prefix}: {str(e)}")
        
        current_hour += timedelta(hours=1)

    print(f"Total de {len(all_events)} eventos encontrados.")
    return all_events
