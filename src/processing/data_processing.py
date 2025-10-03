"""
Módulo de processamento de dados.
Contém a lógica de merge e agrupamento de eventos de sensores.
"""
from datetime import datetime, timezone
from typing import List, Dict


def merge_sensor_events(events: List[Dict]) -> Dict:
    """
    Recebe uma lista de eventos brutos (temperatura, vibração, falha) e os agrupa
    em janelas de tempo discretas (por minuto) para cada máquina.

    Args:
        events: A lista de eventos brutos lidos do S3.

    Returns:
        Um dicionário onde cada chave é uma 'machine_id' e 'janela de tempo',
        e o valor contém os dados consolidados dos sensores para essa janela.
    """
    grouped_windows = {}
    print(f"Iniciando o merge de {len(events)} eventos...")

    for event in events:
        machine_id = event.get("machine_id")
        timestamp_str = event.get("timestamp_utc") or event.get("timestamp_registro")
        
        if not (machine_id and timestamp_str):
            continue # Ignora eventos malformados

        # 1. Cria uma janela de tempo (arredondando para o minuto)
        # Remove o 'Z' e adiciona o fuso horário UTC para compatibilidade
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        dt_obj = datetime.fromisoformat(timestamp_str)
        window_dt = dt_obj.replace(second=0, microsecond=0, tzinfo=timezone.utc)
        window_str = window_dt.isoformat()

        # 2. Cria uma chave única para a máquina e a janela de tempo
        window_key = f"{machine_id}_{window_str}"

        # 3. Se a janela ainda não existe, cria uma entrada base
        if window_key not in grouped_windows:
            grouped_windows[window_key] = {
                "machine_id": machine_id,
                "timestamp_janela": window_str,
                "temperatura": None,
                "vibracao": None,
                "falha": None
            }

        # 4. Preenche a janela com os dados do evento atual
        if "temperature_celsius" in event:
            grouped_windows[window_key]['temperatura'] = event['temperature_celsius']
        elif "vibration_rms" in event:
            grouped_windows[window_key]['vibracao'] = event['vibration_rms']
        elif "codigo_evento" in event:
            grouped_windows[window_key]['falha'] = event['codigo_evento']

    print(f"{len(grouped_windows)} janelas de tempo criadas após o merge.")
    return grouped_windows
