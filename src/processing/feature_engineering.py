from datetime import datetime, timedelta, timezone
from typing import Dict

def calculate_features(grouped_windows: Dict, previous_machine_states: Dict) -> Dict:
    """
    Calcula as features preditivas (vib_media_5h, temp_max_24h) a partir dos
    dados agrupados, utilizando o estado anterior da máquina para cálculos stateful.

    Args:
        grouped_windows: Dicionário com os dados dos sensores já agrupados por janela de tempo.
        previous_machine_states: Dicionário contendo o último estado conhecido de cada máquina,
                                 buscado do DynamoDB.

    Returns:
        Um dicionário com as features finais calculadas para cada máquina.
    """
    final_features = {}
    print(f"Calculando features para {len(grouped_windows)} janelas de tempo...")

    # Ordena as janelas por timestamp para garantir o processamento em ordem cronológica
    sorted_windows = sorted(grouped_windows.values(), key=lambda item: item['timestamp_janela'])

    for window_data in sorted_windows:
        machine_id = window_data["machine_id"]
        # Pega o estado anterior da máquina ou cria um estado inicial vazio
        machine_state = previous_machine_states.get(machine_id, {})

        # --- Feature 1: Média Móvel Exponencial (EMA) para Vibração (vib_media_5h) ---
        last_avg_vibration = machine_state.get("vib_media_5h", window_data.get("vibracao") or 0)
        current_vibration = window_data.get("vibracao") or last_avg_vibration
        alpha = 0.01 # Fator de suavização para uma média 'lenta'
        new_avg_vibration = (current_vibration * alpha) + (last_avg_vibration * (1 - alpha))

        # --- Feature 2: Temperatura Máxima nas últimas 24h (temp_max_24h) ---
        last_max_temp_state = machine_state.get("temp_max_24h_state", {"value": 0, "timestamp": "1970-01-01T00:00:00+00:00"})
        last_max_temp_value = last_max_temp_state["value"]
        last_max_temp_ts = datetime.fromisoformat(last_max_temp_state["timestamp"])
        current_window_ts = datetime.fromisoformat(window_data["timestamp_janela"])
        
        # Garante que ambos os timestamps sejam timezone-aware (UTC)
        if last_max_temp_ts.tzinfo is None:
            last_max_temp_ts = last_max_temp_ts.replace(tzinfo=timezone.utc)
        if current_window_ts.tzinfo is None:
            current_window_ts = current_window_ts.replace(tzinfo=timezone.utc)

        if (current_window_ts - last_max_temp_ts) > timedelta(hours=24):
            new_max_temp_value = window_data.get("temperatura") or 0
        else:
            current_temp = window_data.get("temperatura") or 0
            new_max_temp_value = max(last_max_temp_value, current_temp)

        # --- Montagem do resultado final para esta máquina ---
        final_features[machine_id] = {
            "machine_id": machine_id,
            "timestamp_processamento": datetime.now(timezone.utc).isoformat(),
            "vib_media_5h": round(new_avg_vibration, 4),
            "temp_max_24h": round(new_max_temp_value, 2)
        }

        # --- Atualiza o estado da máquina para ser salvo ou usado na próxima iteração ---
        new_max_temp_state = {"value": new_max_temp_value, "timestamp": window_data["timestamp_janela"]}
        previous_machine_states[machine_id] = {
            "vib_media_5h": new_avg_vibration,
            "temp_max_24h_state": new_max_temp_state
        }

    print("Cálculo de features concluído.")
    return final_features