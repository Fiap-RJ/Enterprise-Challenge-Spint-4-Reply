# Nova Arquitetura: Simulação e Ingestão de Dados

## Visão Geral

Esta implementação substitui o AWS IoT Device Simulator (descontinuado) por uma solução **totalmente serverless** e **Free Tier-friendly** usando EventBridge + Lambda.

## Fluxo da Arquitetura

```
EventBridge (rate: 1 min) → Lambda Simulador → IoT Core → Lambda Ingestão → S3 Data Lake
```

## Componentes Implementados

### 1. Lambda Simulador (`sensor_simulator.py`)
- **Função**: Gera dados simulados de sensores industriais
- **Tipos de sensores**: Temperatura, Pressão, Vibração, Umidade, Fluxo
- **Frequência**: Disparado a cada 1 minuto pelo EventBridge
- **Saída**: Publica no tópico MQTT `sensores/fabrica/dados`

### 2. Lambda de Ingestão (`ingestion_processor.py`)
- **Função**: Recebe dados do IoT Core e salva em lotes no S3
- **Processamento**: Enriquecimento com metadados, bufferização e compressão
- **Saída**: Arquivos JSON Lines comprimidos em GZIP no S3

### 3. Infraestrutura (Terraform)

#### Rede
- VPC com subnets públicas e privadas
- VPC Endpoint para S3 (evita NAT Gateway)
- Security Groups com egress liberado

#### Armazenamento
- S3 Data Lake com criptografia SSE-S3
- Estrutura de partições: `raw/year=YYYY/month=MM/day=DD/hour=HH/`

#### Agendamento
- EventBridge Rule com `rate(1 minute)`
- Target configurado para Lambda Simulador

#### IoT Core
- Regra SQL: `SELECT * FROM 'sensores/fabrica/dados'`
- Target: Lambda de Ingestão

## Arquivos Criados

```
lambda/
├── sensor_simulator.py      # Lambda gerador de dados
├── ingestion_processor.py   # Lambda processador de ingestão
└── *.zip                    # Arquivos empacotados pelo Terraform

scripts/
└── main.tf                  # Infraestrutura completa

document/
├── arch.md                  # Documentação atualizada
└── update.md                # Motivação da mudança
```

## Como Aplicar

1. **Inicializar Terraform**:
   ```bash
   cd scripts/
   terraform init
   ```

2. **Aplicar Infraestrutura**:
   ```bash
   terraform apply -auto-approve
   ```

3. **Verificar Execução**:
   - CloudWatch Logs das funções Lambda
   - Arquivos no S3 Data Lake
   - Métricas do EventBridge

## Vantagens da Nova Arquitetura

- ✅ **Free Tier Friendly**: Todos os serviços no Free Tier
- ✅ **Totalmente Serverless**: Sem custos fixos
- ✅ **Alta Flexibilidade**: Controle total sobre dados simulados
- ✅ **Fácil Manutenção**: Código Python simples
- ✅ **Escalável**: Ajustável para diferentes volumes
- ✅ **Seguro**: VPC privada + VPC Endpoints

## Monitoramento

- **CloudWatch Logs**: Logs das funções Lambda
- **S3**: Verificar criação de arquivos em `raw/year=.../`
- **EventBridge**: Métricas de execução da regra
- **IoT Core**: Métricas de mensagens MQTT
