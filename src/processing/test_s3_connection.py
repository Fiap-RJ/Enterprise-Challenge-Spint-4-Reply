from datetime import datetime, timedelta
import json
import os
import pandas as pd

# Importa as funções que queremos testar
from s3_client import fetch_sensor_data
from data_processor import merge_sensor_events
from feature_engineering import calculate_features

# --- CONFIGURAÇÕES DO TESTE ---
BUCKET_NAME = "replyec-data-lake-20250115"

def run_processing_pipeline_test():
    """
    Executa um teste do pipeline de processamento completo: busca, agrupa e calcula features.
    """
    print(f"--- INICIANDO TESTE DO PIPELINE COMPLETO COM O BUCKET: {BUCKET_NAME} ---")

    # 1. Define o intervalo de tempo: da última hora até agora
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    print(f"Buscando dados no intervalo de {start_time.isoformat()} a {end_time.isoformat()}\n")

    try:
        # ETAPA 1: Buscar os dados
        events = fetch_sensor_data(
            bucket=BUCKET_NAME,
            start_time=start_time,
            end_time=end_time
        )
        if not events:
            print("\n[AVISO] Nenhum evento encontrado no período. Teste encerrado.")
            return
        print(f"\n[SUCESSO] Etapa 1 concluída. {len(events)} eventos encontrados.")

        # ETAPA 2: Agrupar (Merge) os dados
        grouped_data = merge_sensor_events(events)
        if not grouped_data:
            print("\n[AVISO] O merge não produziu nenhum resultado. Teste encerrado.")
            return
        print(f"\n[SUCESSO] Etapa 2 concluída. {len(grouped_data)} janelas de tempo criadas.")

        # ETAPA 3: Calcular as Features
        # Para o teste, simulamos que não há estado anterior
        previous_states = {}
        print("\nIniciando cálculo de features (sem estado anterior)...")
        final_features = calculate_features(grouped_data, previous_states)

        if final_features:
            print(f"\n[SUCESSO] Etapa 3 concluída. {len(final_features)} features de máquinas calculadas.")
            
            # --- ETAPA 4 (Simulação): Salvar resultados em um arquivo CSV ---
            # Converte o dicionário de features para um DataFrame do Pandas
            features_df = pd.DataFrame(final_features.values())
            
            # Define o caminho do arquivo de saída
            output_dir = "test_output"
            os.makedirs(output_dir, exist_ok=True) # Cria a pasta se não existir
            output_path = os.path.join(output_dir, "features_calculadas.csv")
            
            # Salva o DataFrame em um arquivo CSV
            features_df.to_csv(output_path, index=False)
            
            print(f"\n[SUCESSO] Resultados salvos em: {output_path}")
            print("--- Amostra das 3 primeiras linhas do arquivo CSV ---")
            print(features_df.head(3).to_string())

        else:
            print("\n[AVISO] O cálculo de features não produziu nenhum resultado.")

    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro durante o teste: {e}")

# --- PONTO DE ENTRADA PARA EXECUTAR O SCRIPT ---
if __name__ == "__main__":
    run_processing_pipeline_test()