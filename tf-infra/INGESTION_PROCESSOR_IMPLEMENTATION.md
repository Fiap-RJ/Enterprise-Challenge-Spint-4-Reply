# Implementação do Lambda Ingestion Processor

## 📋 Resumo da Implementação

Este documento detalha a implementação do Lambda `ingestion_processor` que processa dados de telemetria do IoT Core e os salva no S3 com particionamento Hive.

## 🔧 Código Python Implementado

### **Arquivo:** `src/ingestion/ingestion_processor.py`

**Principais funcionalidades:**

1. **Extração do Tipo de Sensor:**
   ```python
   def extract_sensor_type_from_topic(mqtt_topic):
       # Extrai 'temperature' de 'industrial/machine/PUMP-A01/temperature'
       topic_parts = mqtt_topic.split('/')
       return topic_parts[-1]
   ```

2. **Geração de Chave S3 com Particionamento Hive:**
   ```python
   def generate_s3_key(sensor_type, ingestion_time):
       # Formato: raw/year=2025/month=10/day=02/hour=03/temperature_reading_1760000000123.jsonl
       year = ingestion_time.strftime('%Y')
       month = ingestion_time.strftime('%m')
       day = ingestion_time.strftime('%d')
       hour = ingestion_time.strftime('%H')
       epoch_ms = int(ingestion_time.timestamp() * 1000)
       filename = f"{sensor_type}_reading_{epoch_ms}.jsonl"
       return f"{S3_PREFIX_ROOT}/year={year}/month={month}/day={day}/hour={hour}/{filename}"
   ```

3. **Salvamento no S3:**
   ```python
   def save_telemetry_to_s3(payload, s3_key):
       jsonl_content = json.dumps(payload, separators=(',', ':'))
       s3_client.put_object(
           Bucket=S3_BUCKET_NAME,
           Key=s3_key,
           Body=jsonl_content,
           ContentType='application/json',
           ServerSideEncryption='AES256'
       )
   ```

## 🎯 Exemplo de Execução

### **Entrada:**
- **Tópico:** `industrial/machine/FAN-B02/telemetry/vibration`
- **Payload:** `{"machine_id": "FAN-B02", "timestamp_utc": "2025-10-02T03:15:00Z", "vibration_rms": 5.8}`

### **Processamento:**
1. **Tipo de Sensor:** `vibration` (extraído do tópico)
2. **Timestamp de Ingestão:** `2025-10-02 03:15:00 UTC`
3. **Chave S3:** `raw/year=2025/month=10/day=02/hour=03/vibration_reading_1760000000123.jsonl`

### **Saída:**
- **Arquivo S3:** `s3://meu-projeto-datalake/raw/year=2025/month=10/day=02/hour=03/vibration_reading_1760000000123.jsonl`
- **Conteúdo:** `{"machine_id": "FAN-B02", "timestamp_utc": "2025-10-02T03:15:00Z", "vibration_rms": 5.8, "ingestion_timestamp": "2025-10-02T03:15:00.123Z", "sensor_type": "vibration", "mqtt_topic": "industrial/machine/FAN-B02/telemetry/vibration"}`

## 🔐 Permissões IAM Necessárias

### **Para a Role da Lambda `ingestion_processor`:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::meu-projeto-datalake/*"
    }
  ]
}
```

**Permissões implementadas no Terraform:**
- ✅ **`s3:PutObject`**: Para salvar arquivos no S3
- ✅ **Recurso específico**: Apenas no bucket do Data Lake
- ✅ **Princípio do menor privilégio**: Apenas as permissões necessárias

## 🌍 Variáveis de Ambiente

### **Variáveis Esperadas pelo Código:**

| Variável | Descrição | Exemplo | Fonte Terraform |
|----------|-----------|---------|-----------------|
| `S3_BUCKET_NAME` | Nome do bucket S3 | `meu-projeto-datalake` | `aws_s3_bucket.data_lake.bucket` |
| `S3_PREFIX_ROOT` | Prefixo raiz no S3 | `raw` | Configurável via variável |

### **Configuração no Terraform:**
```hcl
environment {
  variables = {
    S3_BUCKET_NAME = aws_s3_bucket.data_lake.bucket
    S3_PREFIX_ROOT = "raw"
  }
}
```

## 🔄 Fluxo de Dados Implementado

```
IoT Core (MQTT) → Lambda Ingestion Processor → S3 (Particionado)
```

**Detalhamento:**
1. **IoT Core** publica telemetria nos tópicos `industrial/machine/{machine_id}/telemetry/{sensor_type}`
2. **Regra IoT Core** captura mensagens e inclui o tópico: `SELECT *, topic() as mqtt_topic FROM 'industrial/machine/+/telemetry/+'`
3. **Lambda Ingestion** processa e salva no S3 com particionamento Hive
4. **S3** armazena arquivos JSON Lines particionados por data/hora

## 📊 Estrutura de Dados no S3

### **Particionamento Hive:**
```
s3://bucket/raw/
├── year=2025/
│   ├── month=01/
│   │   ├── day=15/
│   │   │   ├── hour=10/
│   │   │   │   ├── temperature_reading_1737000000123.jsonl
│   │   │   │   ├── vibration_reading_1737000000456.jsonl
│   │   │   │   └── ...
│   │   │   └── hour=11/
│   │   └── day=16/
│   └── month=02/
```

### **Formato dos Arquivos:**
- **Extensão:** `.jsonl` (JSON Lines)
- **Conteúdo:** Uma linha por arquivo com payload JSON
- **Metadados:** Inclui `ingestion_timestamp`, `sensor_type`, `mqtt_topic`

## 🚀 Configuração no Terraform

### **Mudanças Implementadas:**

1. **Empacotamento Automático:**
   ```hcl
   data "archive_file" "ingestion_zip" {
     type        = "zip"
     source_file = "${path.module}/../../src/ingestion/ingestion_processor.py"
     output_path = "${path.module}/ingestion.zip"
   }
   ```

2. **Lambda com Código Real:**
   ```hcl
   resource "aws_lambda_function" "ingestion" {
     filename         = data.archive_file.ingestion_zip.output_path
     source_code_hash = data.archive_file.ingestion_zip.output_base64sha256
     handler          = "ingestion_processor.handler"
     # ...
   }
   ```

3. **Regra IoT Core Atualizada:**
   ```hcl
   resource "aws_iot_topic_rule" "telemetry_ingestion_rule" {
     sql = "SELECT *, topic() as mqtt_topic FROM 'industrial/machine/+/telemetry/+'"
     # ...
   }
   ```

## 🧪 Teste da Implementação

### **1. Deploy da Infraestrutura:**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### **2. Verificar Lambda:**
```bash
aws lambda get-function --function-name replyec-ingestion
```

### **3. Testar com Payload Simulado:**
```bash
aws lambda invoke --function-name replyec-ingestion \
  --payload '{"machine_id": "PUMP-A01", "timestamp_utc": "2025-10-02T03:15:00Z", "temperature_celsius": 75.4, "mqtt_topic": "industrial/machine/PUMP-A01/telemetry/temperature"}' \
  response.json
```

### **4. Verificar Arquivo no S3:**
```bash
aws s3 ls s3://replyec-data-lake-20250115/raw/ --recursive
```

## ⚠️ Notas Importantes

- **Código-Fonte**: Agora usa o arquivo real `ingestion_processor.py`
- **Auto-Update**: Lambda será atualizada automaticamente quando o código mudar
- **Particionamento**: Dados organizados por data/hora para consultas eficientes
- **Formato JSON Lines**: Facilita processamento posterior com ferramentas como Spark
- **Metadados**: Inclui informações de ingestão para rastreabilidade

A implementação está completa e pronta para processar dados de telemetria em tempo real! 🎉
