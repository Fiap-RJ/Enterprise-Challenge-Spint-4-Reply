import os
import json
from datetime import datetime, timedelta, timezone
import pandas as pd

# Importa as funções dos nossos módulos
from s3_client import fetch_sensor_data
from data_processor import merge_sensor_events
from feature_engineering import calculate_features
from aws_clients import (
    save_features_to_s3, 
    save_features_to_dynamodb, 
    fetch_failure_labels_from_dynamo,
    get_ssm_parameter,
    update_ssm_parameter
)

def add_predictive_label(features_dict: dict, future_failures: list, prediction_horizon_hours: int) -> dict:
    """
    Adiciona a label preditiva às features com base em falhas futuras.
    """
    failing_machines = {event['machine_id'] for event in future_failures}
    labeled_features = {}
    label_name = f"falha_nas_proximas_{prediction_horizon_hours}h"

    for machine_id, features in features_dict.items():
        features[label_name] = 1 if machine_id in failing_machines else 0
        labeled_features[machine_id] = features
        
    return labeled_features

def lambda_handler(event, context):
    """
    Ponto de entrada principal para a função Lambda stateful.
    Orquestra o pipeline de ETL com gerenciamento de estado e labels preditivas.
    """
    print("--- INICIANDO PIPELINE DE PROCESSAMENTO DE FEATURES STATEFUL ---")

    # --- CONFIGURAÇÕES ---
    # Lê as configurações das variáveis de ambiente do Lambda
    BUCKET_NAME = os.environ.get("DATA_LAKE_BUCKET")
    DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE_NAME")
    DYNAMODB_LABEL_HISTORY_TABLE = os.environ.get("DYNAMODB_LABEL_HISTORY_TABLE")
    SSM_PARAMETER_NAME = os.environ.get("SSM_PARAMETER_NAME")
    TIME_WINDOW = int(os.environ.get("TIME_WINDOW", 4))  # Janela de processamento em horas
    PREDICTION_HORIZON_HOURS = int(os.environ.get("PREDICTION_HORIZON_HOURS", 24))  # Horizonte de predição
    PROCESSING_LAG_HOURS = int(os.environ.get("PROCESSING_LAG_HOURS", 24))  # Lag de processamento

    # Validação das variáveis de ambiente obrigatórias
    required_vars = {
        "DATA_LAKE_BUCKET": BUCKET_NAME,
        "DYNAMODB_TABLE_NAME": DYNAMODB_TABLE,
        "DYNAMODB_LABEL_HISTORY_TABLE": DYNAMODB_LABEL_HISTORY_TABLE,
        "SSM_PARAMETER_NAME": SSM_PARAMETER_NAME
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        error_message = f"Variáveis de ambiente obrigatórias não definidas: {', '.join(missing_vars)}"
        print(f"[ERRO] {error_message}")
        return {"statusCode": 500, "body": json.dumps(error_message)}

    try:
        # --- GERENCIAMENTO DE ESTADO ---
        # Lê o último timestamp processado do SSM Parameter Store
        print(f"Lendo estado anterior do parâmetro SSM: {SSM_PARAMETER_NAME}")
        last_processed_timestamp_str = get_ssm_parameter(SSM_PARAMETER_NAME)
        last_processed_timestamp = datetime.fromisoformat(last_processed_timestamp_str)
        
        # Garante que o timestamp seja timezone-aware (UTC)
        if last_processed_timestamp.tzinfo is None:
            last_processed_timestamp = last_processed_timestamp.replace(tzinfo=timezone.utc)
        
        # Calcula as janelas de tempo com base no estado anterior
        current_time = datetime.now(timezone.utc)
        
        # Aplica o lag de processamento para garantir que temos dados completos
        processing_cutoff = current_time - timedelta(hours=PROCESSING_LAG_HOURS)
        
        # Verifica se já processamos até o ponto de corte
        if last_processed_timestamp >= processing_cutoff:
            print(f"Pipeline já processou dados até {last_processed_timestamp.isoformat()}. "
                  f"Aguardando mais dados (cutoff: {processing_cutoff.isoformat()})")
            return {"statusCode": 200, "body": "Nenhum dado novo para processar."}
        
        # Define as janelas de tempo para features e labels
        features_start_time = last_processed_timestamp
        features_end_time = min(features_start_time + timedelta(hours=TIME_WINDOW), processing_cutoff)
        
        # Janela para buscar labels de falha (período futuro em relação às features)
        labeling_start_time = features_end_time
        labeling_end_time = features_end_time + timedelta(hours=PREDICTION_HORIZON_HOURS)
        
        print(f"Janela de features: {features_start_time.isoformat()} a {features_end_time.isoformat()}")
        print(f"Janela de labels: {labeling_start_time.isoformat()} a {labeling_end_time.isoformat()}")

        # --- ETAPA 1: Extrair dados de sensores para features ---
        print("ETAPA 1: Buscando dados de sensores para cálculo de features...")
        sensor_events = fetch_sensor_data(BUCKET_NAME, features_start_time, features_end_time)
        if not sensor_events:
            print("Nenhum evento de sensor encontrado na janela de features. Atualizando estado.")
            update_ssm_parameter(SSM_PARAMETER_NAME, features_end_time.isoformat())
            return {"statusCode": 200, "body": "Nenhum evento de sensor para processar."}

        # --- ETAPA 2: Extrair labels de falha para predição ---
        print("ETAPA 2: Buscando labels de falha para predição...")
        failure_events = fetch_failure_labels_from_dynamo(DYNAMODB_LABEL_HISTORY_TABLE, labeling_start_time, labeling_end_time)

        # --- ETAPA 3: Transformar - Agrupar eventos de sensores ---
        print("ETAPA 3: Agrupando eventos de sensores por janela de tempo...")
        grouped_sensor_data = merge_sensor_events(sensor_events)

        # --- ETAPA 4: Transformar - Calcular features preditivas ---
        print("ETAPA 4: Calculando features preditivas...")
        # Em um cenário real, buscaríamos o estado anterior do DynamoDB
        previous_machine_states = {}
        features_without_labels = calculate_features(grouped_sensor_data, previous_machine_states)

        # --- ETAPA 5: Adicionar labels preditivas ---
        print("ETAPA 5: Adicionando labels preditivas...")
        final_features = add_predictive_label(
            features_without_labels, 
            failure_events, 
            PREDICTION_HORIZON_HOURS
        )

        # --- ETAPA 6: Carregar - Salvar em dois destinos ---
        if final_features:
            print("ETAPA 6: Salvando features com labels preditivas...")
            
            # Destino 1: Salvar em S3 para treinamento
            features_df = pd.DataFrame(final_features.values())
            save_features_to_s3(features_df, BUCKET_NAME)

            # Destino 2: Salvar em DynamoDB para inferência
            save_features_to_dynamodb(final_features, DYNAMODB_TABLE)
            
            # --- ATUALIZAR ESTADO APENAS EM CASO DE SUCESSO ---
            print("Atualizando estado no SSM Parameter Store...")
            update_ssm_parameter(SSM_PARAMETER_NAME, features_end_time.isoformat())
            
            print(f"--- PIPELINE STATEFUL CONCLUÍDO COM SUCESSO ---")
            print(f"Próxima execução processará a partir de: {features_end_time.isoformat()}")
            return {"statusCode": 200, "body": json.dumps("Pipeline stateful executado com sucesso!")}
        else:
            print("Nenhuma feature foi calculada. Atualizando estado mesmo assim.")
            update_ssm_parameter(SSM_PARAMETER_NAME, features_end_time.isoformat())
            return {"statusCode": 200, "body": "Nenhuma feature calculada, mas estado atualizado."}

    except Exception as e:
        print(f"[ERRO FATAL] Ocorreu um erro inesperado no pipeline stateful: {e}")
        print("Estado NÃO será atualizado para permitir reprocessamento na próxima execução.")
        # Em um cenário real, poderíamos enviar uma notificação para o CloudWatch Alarms/SNS
        return {"statusCode": 500, "body": json.dumps(f"Erro no pipeline stateful: {e}")}