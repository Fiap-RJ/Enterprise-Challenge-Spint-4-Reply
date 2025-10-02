
from datetime import datetime, timedelta
import json

# Importa as funções que queremos testar
from s3_client import fetch_sensor_data
from data_processor import merge_sensor_events # <-- Importamos a nova função

# --- CONFIGURAÇÕES DO TESTE ---
BUCKET_NAME = "replyec-data-lake-20250115"

def run_s3_connection_test():
    """
    Executa um teste de ponta a ponta, buscando e agrupando dados do S3.
    """
    print(f"--- INICIANDO TESTE DE CONEXÃO E MERGE COM O BUCKET: {BUCKET_NAME} ---")

    # 1. Define o intervalo de tempo: da última hora até agora
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    print(f"Buscando dados no intervalo de {start_time.isoformat()} a {end_time.isoformat()}\\n")

    try:
        # ETAPA 1: Buscar os dados
        events = fetch_sensor_data(
            bucket=BUCKET_NAME,
            start_time=start_time,
            end_time=end_time
        )

        if not events:
            print("\\n[AVISO] A conexão funcionou, mas nenhum evento foi encontrado no período.")
            return

        print(f"\\n[SUCESSO] Etapa 1 concluída. {len(events)} eventos encontrados.")

        # ETAPA 2: Agrupar (Merge) os dados
        grouped_data = merge_sensor_events(events)

        if grouped_data:
            print(f"\\n[SUCESSO] Etapa 2 concluída. {len(grouped_data)} janelas de tempo criadas.")
            print("--- Amostra dos 3 primeiros registros agrupados ---")
            # Pega os 3 primeiros itens do dicionário para exibir
            sample = list(grouped_data.values())[:3]
            for i, item in enumerate(sample):
                print(f"Registro {i+1}: {json.dumps(item)}")
        else:
            print("\\n[AVISO] O merge não produziu nenhum resultado.")

    except Exception as e:
        print(f"\\n[ERRO] Ocorreu um erro durante o teste: {e}")
        print("Verifique suas credenciais da AWS e as permissões do IAM para acessar o bucket.")

# --- PONTO DE ENTRADA PARA EXECUTAR O SCRIPT ---
if __name__ == "__main__":
    run_s3_connection_test()