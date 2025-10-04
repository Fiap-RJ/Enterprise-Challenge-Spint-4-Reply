import json
import os
from pipeline import FeaturePipeline

def lambda_handler(event, context):
    """
    Ponto de entrada limpo. Lê configurações do ambiente e instancia o pipeline.
    """
    print("--- INICIANDO PIPELINE DE PROCESSAMENTO DE FEATURES STATEFUL ---")
    try:
        # Lê configurações das variáveis de ambiente
        config = {
            "bucket_name": os.getenv("DATA_LAKE_BUCKET"),
            "features_table": os.getenv("DYNAMODB_TABLE_NAME"),
            "failures_table": os.getenv("DYNAMODB_LABEL_HISTORY_TABLE"),
            "ssm_param_name": os.getenv("SSM_PARAMETER_NAME"),
            "time_window": int(os.getenv("TIME_WINDOW", 1)),
            "prediction_horizon": int(os.getenv("PREDICTION_HORIZON_HOURS", 24)),
            "processing_lag": int(os.getenv("PROCESSING_LAG_HOURS", 25))
        }
        
        print(f"Configurações carregadas: {config}")
        
        # Instancia o pipeline com parâmetros injetados
        pipeline = FeaturePipeline(**config)
        result = pipeline.run()
        print(f"--- RESULTADO: {result} ---")
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        print(f"[ERRO FATAL] Falha na execução do pipeline: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Erro no pipeline: {str(e)}")}