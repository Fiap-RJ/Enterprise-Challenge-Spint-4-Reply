# Infraestrutura como Código - MLOps Industrial

Esta estrutura modular do Terraform implementa a arquitetura MLOps Industrial conforme documentada no `arch-pro.md`.

## Estrutura de Diretórios

```
terraform/
├── modules/
│   └── ingestion/          # Módulo de ingestão de dados
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── main.tf                 # Configuração principal
├── variables.tf            # Variáveis da infraestrutura
├── outputs.tf              # Outputs da infraestrutura
├── terraform.tfvars        # Valores das variáveis
└── README.md               # Esta documentação
```

## Módulo de Ingestão

O módulo `ingestion` implementa o fluxo de ingestão de dados:

```
EventBridge → Lambda Simulator → IoT Core → Lambda Ingestion → S3
```

### Recursos Criados

- **S3 Data Lake**: Bucket para armazenar dados brutos
- **Lambda Simulator**: Simula dados de sensores industriais
- **Lambda Ingestion**: Processa dados do IoT Core e salva no S3
- **EventBridge**: Agenda execução do simulador
- **IoT Core Rules**: Roteia mensagens MQTT para Lambda Ingestion
- **DynamoDB**: Armazena estado de degradação das máquinas
- **IAM Roles**: Permissões necessárias para as Lambdas

### Tópicos MQTT

Conforme a arquitetura, os seguintes tópicos são utilizados:

- `industrial/machine/{machine_id/temperature`
- `industrial/machine/{machine_id/vibration`
- `industrial/machine/{machine_id}/event/failure`

## Como Usar

### 1. Configuração Inicial

```bash
cd terraform
```

### 2. Personalizar Variáveis

Edite o arquivo `terraform.tfvars` para ajustar:
- Nome do bucket S3 (deve ser único globalmente)
- Configurações de agendamento
- Parâmetros das Lambdas

### 3. Inicializar Terraform

```bash
terraform init
```

### 4. Planejar Deploy

```bash
terraform plan
```

### 5. Aplicar Infraestrutura

```bash
terraform apply
```

### 6. Verificar Outputs

```bash
terraform output
```

## Variáveis Importantes

- `s3_bucket_name`: Nome único do bucket S3
- `mqtt_topic_prefix`: Prefixo dos tópicos MQTT
- `machine_ids`: Lista de IDs das máquinas
- `simulator_schedule_expression`: Frequência de execução do simulador
- `lambda_timeout`: Timeout das funções Lambda
- `lambda_memory_size`: Memória das funções Lambda

## Próximos Passos

1. **Módulo de Processamento**: Implementar feature engineering
2. **Módulo de Treinamento**: Implementar pipeline de ML
3. **Módulo de Inferência**: Implementar endpoints de predição

## Troubleshooting

### Erro de Bucket S3 Duplicado

Se receber erro de bucket S3 já existente, altere o valor de `s3_bucket_name` no `terraform.tfvars`.

### Erro de Permissões

Verifique se as credenciais AWS estão configuradas corretamente:

```bash
aws configure list
```

### Logs das Lambdas

Para verificar logs das funções Lambda:

```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/replyec"
```
