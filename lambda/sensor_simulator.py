import json
import random
import time
from datetime import datetime, timezone
import boto3
import logging

# Configuração de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cliente IoT Core
iot_client = boto3.client('iot-data')

# Configurações do simulador
SENSOR_COUNT = 5  # Número de sensores por execução
MQTT_TOPIC = "sensores/fabrica/dados"

def generate_sensor_data(sensor_id: str) -> dict:
    """Gera dados simulados de sensores industriais"""
    now = datetime.now(timezone.utc)
    
    # Simula diferentes tipos de sensores industriais
    sensor_types = {
        "temp": {"min": 20, "max": 80, "unit": "°C"},
        "pressure": {"min": 0.5, "max": 2.5, "unit": "bar"},
        "vibration": {"min": 0, "max": 10, "unit": "mm/s"},
        "humidity": {"min": 30, "max": 90, "unit": "%"},
        "flow": {"min": 0, "max": 100, "unit": "L/min"}
    }
    
    # Seleciona tipo de sensor baseado no ID
    sensor_type = list(sensor_types.keys())[int(sensor_id) % len(sensor_types)]
    config = sensor_types[sensor_type]
    
    # Gera valor com pequena variação aleatória
    base_value = random.uniform(config["min"], config["max"])
    noise = random.uniform(-0.1, 0.1) * (config["max"] - config["min"])
    value = round(base_value + noise, 2)
    
    return {
        "sensor_id": f"sensor_{sensor_id}",
        "sensor_type": sensor_type,
        "value": value,
        "unit": config["unit"],
        "timestamp": now.isoformat(),
        "location": f"fabrica_zona_{random.randint(1, 3)}",
        "status": "active" if random.random() > 0.05 else "warning",  # 5% chance de warning
        "metadata": {
            "factory_id": "fabrica_001",
            "line_id": f"linha_{random.randint(1, 5)}",
            "operator_id": f"op_{random.randint(100, 999)}"
        }
    }

def publish_to_iot_core(payload: dict) -> bool:
    """Publica dados no IoT Core via MQTT"""
    try:
        response = iot_client.publish(
            topic=MQTT_TOPIC,
            qos=1,
            payload=json.dumps(payload, separators=(',', ':'))
        )
        logger.info(f"Published to IoT Core: {response['ResponseMetadata']['HTTPStatusCode']}")
        return True
    except Exception as e:
        logger.error(f"Error publishing to IoT Core: {str(e)}")
        return False

def handler(event, context):
    """Função principal do Lambda simulador"""
    logger.info("Starting sensor data simulation")
    
    try:
        # Gera dados para múltiplos sensores
        all_sensor_data = []
        successful_publishes = 0
        
        for i in range(SENSOR_COUNT):
            sensor_data = generate_sensor_data(str(i + 1))
            all_sensor_data.append(sensor_data)
            
            # Publica cada sensor individualmente no IoT Core
            if publish_to_iot_core(sensor_data):
                successful_publishes += 1
                
            # Pequeno delay entre publicações para simular comportamento real
            time.sleep(0.1)
        
        logger.info(f"Generated {len(all_sensor_data)} sensor readings")
        logger.info(f"Successfully published {successful_publishes}/{len(all_sensor_data)} to IoT Core")
        
        return {
            "statusCode": 200,
            "body": {
                "message": "Sensor data simulation completed",
                "sensors_generated": len(all_sensor_data),
                "successful_publishes": successful_publishes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in sensor simulation: {str(e)}")
        return {
            "statusCode": 500,
            "body": {
                "error": str(e),
                "message": "Sensor simulation failed"
            }
        }
