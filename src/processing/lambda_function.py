import os
import json
from datetime import datetime, timedelta
import pandas as pd

# Importa as funções dos nossos módulos
from s3_client import fetch_sensor_data
from data_processor import merge_sensor_events
from feature_engineering import calculate_features
from aws_clients import save_features_to_s3, save_features_to_dynamodb

def lambda_handler(event, context):
    """
    Ponto de entrada principal para a função Lambda.
    Orquestra o pipeline de ETL: Extrai, Transforma e Carrega (S3 + DynamoDB).
    """
    print("--- INICIANDO PIPELINE DE PROCESSAMENTO DE FEATURES ---")

    # --- CONFIGURAÇÕES ---
    # Lê as configurações das variáveis de ambiente do Lambda
    BUCKET_NAME = os.environ.get("DATA_LAKE_BUCKET")
    DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE_NAME")

    if not (BUCKET_NAME and DYNAMODB_TABLE):
        error_message = "Variáveis de ambiente DATA_LAKE_BUCKET e DYNAMODB_TABLE_NAME devem ser definidas."
        print(f"[ERRO] {error_message}")
        return {"statusCode": 500, "body": json.dumps(error_message)}

    # Define o intervalo de tempo para processar (ex: última hora)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    try:
        # ETAPA 1: Extrair - Buscar dados brutos do S3
        events = fetch_sensor_data(BUCKET_NAME, start_time, end_time)
        if not events:
            print("Nenhum evento novo encontrado. Encerrando execução.")
            return {"statusCode": 200, "body": json.dumps("Nenhum evento novo para processar.")}

        # ETAPA 2: Transformar - Agrupar eventos por janela de tempo
        grouped_data = merge_sensor_events(events)

        # ETAPA 3: Transformar - Calcular features
        # Em um cenário real, buscaríamos o estado anterior do DynamoDB
        previous_states = {}
        final_features = calculate_features(grouped_data, previous_states)

        # ETAPA 4: Carregar - Salvar em dois destinos
        if final_features:
            # Destino 1: Salvar em S3 para treinamento
            features_df = pd.DataFrame(final_features.values())
            save_features_to_s3(features_df, BUCKET_NAME)

            # Destino 2: Salvar em DynamoDB para inferência
            save_features_to_dynamodb(final_features, DYNAMODB_TABLE)
        else:
            print("Nenhuma feature foi calculada. Nada a ser salvo.")

        print("--- PIPELINE DE PROCESSAMENTO CONCLUÍDO COM SUCESSO ---")
        return {"statusCode": 200, "body": json.dumps("Pipeline executado com sucesso!")}

    except Exception as e:
        print(f"[ERRO FATAL] Ocorreu um erro inesperado no pipeline: {e}")
        # Em um cenário real, poderíamos enviar uma notificação para o CloudWatch Alarms/SNS
        return {"statusCode": 500, "body": json.dumps(f"Erro no pipeline: {e}")}