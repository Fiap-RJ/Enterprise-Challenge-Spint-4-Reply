import pandas as pd
import numpy as np
import datetime

# --- Simulação da Feature Store (DynamoDB) ---

def get_mock_feature_store_data() -> pd.DataFrame:
    """
    Simula a busca de dados da Feature Store no DynamoDB.

    Retorna um DataFrame do Pandas com dados de 5 máquinas.
    """
    machine_ids = [f"PUMP-A0{i}" for i in range(1, 6)]
    
    # Gerando dados simulados e aleatórios para um visual dinâmico
    data = {
        "machine_id": machine_ids,
        "vib_media_5h": np.random.uniform(1.5, 5.0, size=len(machine_ids)).round(2),
        "temp_max_24h": np.random.uniform(70.0, 95.0, size=len(machine_ids)).round(2),
        "timestamp_processamento": [datetime.datetime.now().isoformat() for _ in machine_ids]
    }
    
    return pd.DataFrame(data)

# --- Simulação da API de Inferência (SageMaker Endpoint) ---

def get_mock_prediction(features: dict) -> dict:
    """
    Simula a resposta da API de inferência do SageMaker.

    Recebe um dicionário de features de uma máquina e retorna um resultado
    de predição padronizado.
    """
    machine_id = features.get("machine_id", "ID_DESCONHECIDO")
    vib_media_5h = features.get("vib_media_5h", 0)
    
    # Lógica de simulação, conforme o documento de orientação
    if vib_media_5h > 4.5:
        probability = 0.95
        alert_status = "CRÍTICO"
    elif vib_media_5h > 3.5:
        probability = 0.85
        alert_status = "ALERTA"
    else:
        probability = 0.20
        alert_status = "NORMAL"
        
    return {
        "machine_id": machine_id,
        "probability": probability,
        "alert_status": alert_status
    }