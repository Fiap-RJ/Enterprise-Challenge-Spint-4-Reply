import boto3
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import unquote


S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_PREFIX_ROOT = os.environ.get('S3_PREFIX_ROOT', 'raw')

s3_client = boto3.client('s3')

def extract_sensor_type_from_topic(mqtt_topic):
    """
    Extrai o tipo de sensor a partir do tópico MQTT.
    
    Args:
        mqtt_topic (str): Tópico MQTT (ex: 'industrial/machine/PUMP-A01/temperature')
    
    Returns:
        str: Tipo do sensor (ex: 'temperature', 'vibration')
    """
    try:
        topic_parts = mqtt_topic.split('/')
        if len(topic_parts) >= 2:
            return topic_parts[-1]
        else:
            match = re.search(r'/([^/]+)$', mqtt_topic)
            if match:
                return match.group(1)
            else:
                return 'unknown'
    except Exception as e:
        print(f"Erro ao extrair tipo de sensor do tópico '{mqtt_topic}': {e}")
        return 'unknown'

def generate_s3_key(sensor_type, ingestion_time):
    """
    Gera a chave S3 com particionamento Hive e nome de arquivo único.
    
    Args:
        sensor_type (str): Tipo do sensor
        ingestion_time (datetime): Momento da ingestão em UTC
    
    Returns:
        str: Chave S3 completa
    """
    year = ingestion_time.strftime('%Y')
    month = ingestion_time.strftime('%m')
    day = ingestion_time.strftime('%d')
    hour = ingestion_time.strftime('%H')
    
    epoch_ms = int(ingestion_time.timestamp() * 1000)
    
    filename = f"{sensor_type}_reading_{epoch_ms}.jsonl"
    
    s3_key = f"{S3_PREFIX_ROOT}/year={year}/month={month}/day={day}/hour={hour}/{filename}"
    
    return s3_key

def save_telemetry_to_s3(payload, s3_key):
    """
    Salva o payload de telemetria no S3 como arquivo JSON Lines.
    
    Args:
        payload (dict): Payload da mensagem MQTT
        s3_key (str): Chave S3 onde salvar o arquivo
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        jsonl_content = json.dumps(payload, separators=(',', ':'))
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=jsonl_content,
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        
        print(f"Telemetria salva com sucesso: s3://{S3_BUCKET_NAME}/{s3_key}")
        return True
        
    except Exception as e:
        print(f"Erro ao salvar telemetria no S3: {e}")
        return False

def process_iot_event(event):
    """
    Processa um evento do IoT Core e salva a telemetria no S3.
    
    Args:
        event (dict): Evento do IoT Core
    
    Returns:
        dict: Resultado do processamento
    """
    try:
        mqtt_topic = event.get('mqtt_topic', '')
        if not mqtt_topic:
            return {
                'statusCode': 400,
                'body': 'Tópico MQTT não encontrado no evento'
            }
        
        mqtt_topic = unquote(mqtt_topic)
        
        sensor_type = extract_sensor_type_from_topic(mqtt_topic)
        
        payload = {k: v for k, v in event.items() if k not in ['mqtt_topic', 'topic']}
        
        ingestion_time = datetime.now(timezone.utc)
        payload['ingestion_timestamp'] = ingestion_time.isoformat()
        payload['sensor_type'] = sensor_type
        payload['mqtt_topic'] = mqtt_topic
        
        s3_key = generate_s3_key(sensor_type, ingestion_time)
        
        success = save_telemetry_to_s3(payload, s3_key)
        
        if success:
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Telemetria processada com sucesso',
                    'sensor_type': sensor_type,
                    's3_key': s3_key,
                    'machine_id': payload.get('machine_id', 'unknown')
                }
            }
        else:
            return {
                'statusCode': 500,
                'body': 'Erro ao salvar telemetria no S3'
            }
            
    except Exception as e:
        print(f"Erro ao processar evento IoT: {e}")
        return {
            'statusCode': 500,
            'body': f'Erro interno: {str(e)}'
        }

def handler(event, context):
    """
    Ponto de entrada da Lambda para processamento de telemetria IoT.
    
    Args:
        event (dict): Evento do IoT Core contendo dados de telemetria
        context: Contexto da execução Lambda
    
    Returns:
        dict: Resposta da função
    """
    print(f"Iniciando processamento de telemetria...")
    print(f"Evento recebido: {json.dumps(event, indent=2)}")
    

    result = process_iot_event(event)
    
    print(f"Resultado do processamento: {json.dumps(result, indent=2)}")
    return result
