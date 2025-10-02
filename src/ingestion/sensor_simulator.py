import boto3
import json
import os
import random
from datetime import datetime, timezone
from decimal import Decimal

# --- Constantes de Configuração ---

# Nomes da tabela e prefixo do tópico são lidos das variáveis de ambiente
DYNAMODB_TABLE_NAME = os.environ.get('STATE_TABLE_NAME', 'MachineState')
MQTT_TOPIC_PREFIX = os.environ.get('TOPIC_PREFIX', 'industrial/machine')

# Lista de máquinas a serem simuladas
MACHINE_IDS = [
  "PUMP-A01",
  "PUMP-A02", 
  "FAN-B01",
  "FAN-B02",
  "COMPRESSOR-C01"
]

# Thresholds de Vibração (mm/s RMS) baseados na norma ISO
VIBRATION_HEALTHY_MAX = 4.5
VIBRATION_ATTENTION_MAX = 7.1
VIBRATION_FAILURE_THRESHOLD = 7.1  # A partir daqui, consideramos "falha"
VIBRATION_CRITICAL_MAX = 11.2
VIBRATION_RESET_THRESHOLD = VIBRATION_CRITICAL_MAX * 1.30  # 130% do limite crítico

# Limites de Temperatura (°C)
TEMP_HEALTHY_BASE = 60.0
TEMP_MAX = 150.0

# --- Clientes AWS ---
# Inicializados fora do handler para reutilização em invocações "quentes"
dynamodb = boto3.resource('dynamodb')
iot_data = boto3.client('iot-data')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def get_default_state(machine_id):
    """Retorna o estado inicial saudável para uma nova máquina."""
    return {
        'machine_id': machine_id,
        'vibration_rms': round(random.uniform(2.0, 4.0), 2),
        'temperature_celsius': round(random.uniform(55.0, 65.0), 2),
        # Fator que controla a velocidade de degradação da máquina
        'degradation_factor': round(random.uniform(1.0, 1.5), 2),
        'status': 'HEALTHY',
        'last_updated_utc': datetime.now(timezone.utc).isoformat()
    }

def get_machine_state(machine_id):
    """Busca o estado atual de uma máquina no DynamoDB."""
    try:
        response = table.get_item(Key={'machine_id': machine_id})
        if 'Item' in response:
            return response['Item']
        else:
            # Se a máquina não existe na tabela, cria um estado padrão
            return get_default_state(machine_id)
    except Exception as e:
        print(f"Erro ao buscar estado para {machine_id}: {e}")
        return get_default_state(machine_id)

def update_machine_state(state):
    """Atualiza o estado de uma máquina no DynamoDB."""
    try:
        # Converte floats para Decimals para o DynamoDB
        state_decimal = json.loads(json.dumps(state), parse_float=Decimal)
        table.put_item(Item=state_decimal)
    except Exception as e:
        print(f"Erro ao atualizar estado para {state['machine_id']}: {e}")

def publish_to_iot(topic, payload):
    """Publica uma mensagem em um tópico MQTT do AWS IoT Core."""
    try:
        iot_data.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(payload)
        )
    except Exception as e:
        print(f"Erro ao publicar no tópico {topic}: {e}")

def lambda_handler(event, context):
    """
    Ponto de entrada da Lambda. Itera sobre cada máquina, simula novos dados,
    publica telemetria e eventos de falha, e atualiza o estado.
    """
    print("Iniciando ciclo de simulação...")

    for machine_id in MACHINE_IDS:
        state = get_machine_state(machine_id)
        current_vibration = float(state.get('vibration_rms', 4.0))
        current_temp = float(state.get('temperature_celsius', 60.0))
        degradation_factor = float(state.get('degradation_factor', 1.0))

        # 1. Lógica de Reset: Se a máquina atingiu o limite máximo, reseta para um estado saudável
        if current_vibration >= VIBRATION_RESET_THRESHOLD:
            print(f"Máquina {machine_id} atingiu o limite de reset. Restaurando para estado saudável.")
            new_state = get_default_state(machine_id)
            update_machine_state(new_state)
            # Pula para a próxima máquina no loop
            continue
        
        # 2. Simular Degradação Progressiva
        # O aumento é maior quanto mais perto do limite a máquina está
        vibration_increase = (random.uniform(0.1, 0.3) * degradation_factor) + (current_vibration / 20)
        new_vibration = round(current_vibration + vibration_increase, 2)
        
        # A temperatura aumenta em correlação com a vibração
        temp_increase = vibration_increase * random.uniform(3.0, 5.0)
        new_temp = min(round(current_temp + temp_increase, 2), TEMP_MAX)

        # Adiciona um pouco de ruído para realismo
        final_vibration = max(0, new_vibration + random.uniform(-0.1, 0.1))
        final_temp = max(20, new_temp + random.uniform(-0.5, 0.5))

        # 3. Publicar Telemetria (sempre)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Publica Temperatura
        temp_topic = f"{MQTT_TOPIC_PREFIX}/{machine_id}/temperature"
        temp_payload = {
            "machine_id": machine_id,
            "timestamp_utc": timestamp,
            "temperature_celsius": round(final_temp, 2)
        }
        publish_to_iot(temp_topic, temp_payload)

        # Publica Vibração
        vibration_topic = f"{MQTT_TOPIC_PREFIX}/{machine_id}/vibration"
        vibration_payload = {
            "machine_id": machine_id,
            "timestamp_utc": timestamp,
            "vibration_rms": round(final_vibration, 2)
        }
        publish_to_iot(vibration_topic, vibration_payload)
        
        print(f"Máquina {machine_id}: Vib={final_vibration:.2f} mm/s, Temp={final_temp:.2f}°C")

        # 4. Verificar Threshold e Publicar Rótulo de Falha
        if final_vibration >= VIBRATION_FAILURE_THRESHOLD:
            print(f"ALERTA: Máquina {machine_id} ultrapassou o threshold de falha!")
            failure_topic = f"{MQTT_TOPIC_PREFIX}/{machine_id}/event/failure"
            failure_payload = {
                "machine_id": machine_id,
                "timestamp_utc": timestamp,
                "codigo_evento": "FALHA_DETECTADA",
                "valor_medido": round(final_vibration, 2),
                "threshold": VIBRATION_FAILURE_THRESHOLD
            }
            publish_to_iot(failure_topic, failure_payload)
            state['status'] = 'FAILURE'
        elif final_vibration >= VIBRATION_ATTENTION_MAX:
             state['status'] = 'ATTENTION'
        else:
             state['status'] = 'HEALTHY'

        # 5. Atualizar o estado no DynamoDB para a próxima execução
        state['vibration_rms'] = final_vibration
        state['temperature_celsius'] = final_temp
        state['last_updated_utc'] = timestamp
        update_machine_state(state)

    return {
        'statusCode': 200,
        'body': json.dumps(f'Ciclo de simulação concluído para {len(MACHINE_IDS)} máquinas.')
    }