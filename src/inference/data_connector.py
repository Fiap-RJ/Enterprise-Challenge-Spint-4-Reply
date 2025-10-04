import os
from typing import Dict, Any, Optional
import boto3
import pandas as pd
from datetime import datetime
import requests

# Configuração dos clientes AWS - Usará automaticamente as credenciais do AWS CLI
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

DYNAMODB_TABLE = 'MachineFeatureStore'
S3_BUCKET = 'seu-bucket-de-dados'

# Configuração da API (opcional, pode ser hardcoded se preferir)
PREDICTION_API_URL = os.getenv('PREDICTION_API_URL', 'mock')

def get_feature_store_data() -> pd.DataFrame:
    """
    Busca dados da Feature Store no DynamoDB.
    Retorna um DataFrame do Pandas com os dados das máquinas.
    """
    try:
        table_name = os.getenv('DYNAMODB_TABLE', 'MachineFeatureStore')
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response.get('Items', [])
        
        # Converte para DataFrame
        df = pd.DataFrame(items)
        
        # Converte tipos de dados se necessário
        if 'timestamp_processamento' in df.columns:
            df['timestamp_processamento'] = pd.to_datetime(df['timestamp_processamento'])
        
        return df
        
    except Exception as e:
        print(f"Erro ao acessar DynamoDB: {str(e)}")
        return pd.DataFrame()

def get_prediction_from_api(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Obtém previsão da API de inferência.
    
    Args:
        features: Dicionário com as features da máquina
    
    Retorna:
        Dicionário com o resultado da predição
    """
    try:
        if PREDICTION_API_URL.lower() == 'mock':
            return get_mock_prediction(features)
            
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {PREDICTION_API_KEY}'
        }
        
        response = requests.post(
            PREDICTION_API_URL,
            json=features,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"Erro ao chamar API de previsão: {str(e)}")
        return get_mock_prediction(features)  # Fallback para mock em caso de erro

def get_mock_prediction(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simula a resposta da API de inferência.
    Pode ser facilmente substituída por uma chamada real à API.
    """
    try:        
        machine_id = features.get("machine_id", "ID_DESCONHECIDO")
        vib_media_5h = features.get("vib_media_5h", 0)
        temp_max_24h = features.get("temp_max_24h", 0)
        
        # Lógica de simulação baseada no documento
        if vib_media_5h > 4.5 or temp_max_24h > 90:
            probability = 0.92
            alert_status = "CRÍTICO"
        elif vib_media_5h > 3.5 or temp_max_24h > 80:
            probability = 0.75
            alert_status = "ALERTA"
        else:
            probability = 0.10
            alert_status = "NORMAL"
            
        return {
            "machine_id": machine_id,
            "probability": probability,
            "alert_status": alert_status,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock"  # Indica que é um dado simulado
        }
        
    except Exception as e:
        print(f"Erro na previsão mock: {str(e)}")
        return {
            "machine_id": features.get("machine_id", "ID_DESCONHECIDO"),
            "probability": 0.0,
            "alert_status": "ERRO",
            "error": str(e),
            "source": "mock_error"
        }

get_prediction = get_prediction_from_api