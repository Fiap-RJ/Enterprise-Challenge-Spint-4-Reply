# Módulo Processing - Feature Engineering e ETL

Este módulo implementa a infraestrutura para o pipeline de processamento de dados e engenharia de features conforme descrito na arquitetura MLOps Industrial.

## Recursos Criados

### 1. Lambda Layer para Pandas
- **Recurso**: `aws_lambda_layer_version.pandas_layer`
- **Propósito**: Fornece a biblioteca `pandas` para a função Lambda de processamento
- **Arquivo**: Deve ser criado um arquivo `pandas_layer.zip` contendo a biblioteca

### 2. Tabela DynamoDB para Feature Store
- **Recurso**: `aws_dynamodb_table.realtime_features`
- **Propósito**: Armazena features em tempo real para inferência
- **Chave Primária**: `machine_id` (String)
- **Billing**: Pay-per-request

### 3. Função Lambda de Processamento
- **Recurso**: `aws_lambda_function.processing_lambda`
- **Propósito**: Executa o pipeline ETL e engenharia de features
- **Runtime**: Python 3.11
- **Layers**: Inclui o layer do pandas
- **Variáveis de Ambiente**:
  - `DATA_LAKE_BUCKET`: Nome do bucket S3 do Data Lake
  - `DYNAMODB_TABLE_NAME`: Nome da tabela DynamoDB de features
  - `TIME_WINDOW`: Janela de tempo em horas para processamento

### 4. IAM Role e Policies
- **Role**: `aws_iam_role.processing_lambda_role`
- **Permissões**:
  - CloudWatch Logs (criação e escrita)
  - S3 (leitura do Data Lake, escrita em processed/)
  - DynamoDB (escrita na tabela de features)

## Variáveis de Entrada

| Nome | Tipo | Descrição | Padrão |
|------|------|-----------|--------|
| `project_name` | string | Nome do projeto | - |
| `s3_bucket_name` | string | Nome do bucket S3 do Data Lake | - |
| `lambda_timeout` | number | Timeout da Lambda em segundos | 300 |
| `lambda_memory_size` | number | Memória da Lambda em MB | 1024 |
| `processing_schedule_expression` | string | Expressão de agendamento | "rate(6 hours)" |
| `time_window_hours` | number | Janela de tempo em horas | 6 |
| `pandas_layer_zip_path` | string | Caminho para o ZIP do layer pandas | "./lambda_artifacts/pandas_layer.zip" |
| `lambda_source_path` | string | Caminho para o ZIP da Lambda | "./lambda_artifacts/processing_lambda.zip" |
| `tags` | map(string) | Tags adicionais | {} |

## Outputs

| Nome | Descrição |
|------|-----------|
| `processing_lambda_arn` | ARN da função Lambda de processamento |
| `processing_lambda_function_name` | Nome da função Lambda |
| `realtime_features_table_name` | Nome da tabela DynamoDB |
| `realtime_features_table_arn` | ARN da tabela DynamoDB |
| `pandas_layer_arn` | ARN do Lambda Layer do pandas |
| `processing_lambda_role_arn` | ARN da IAM role da Lambda |

## Uso

```hcl
module "processing" {
  source = "./modules/processing"

  project_name    = "replyec"
  s3_bucket_name  = "replyec-data-lake-20250115"

  processing_schedule_expression = "rate(6 hours)"
  time_window_hours             = 6

  lambda_timeout     = 300
  lambda_memory_size = 1024

  pandas_layer_zip_path = "./lambda_artifacts/pandas_layer.zip"
  lambda_source_path    = "./lambda_artifacts/processing_lambda.zip"

  tags = {
    Project = "Enterprise Challenge - Reply"
    Owner   = "Fiap-RJ Team"
  }
}
```

## Pré-requisitos

1. **Arquivo pandas_layer.zip**: Deve ser criado contendo a biblioteca pandas compatível com Python 3.11
2. **Arquivo processing_lambda.zip**: Deve conter o código fonte da Lambda de processamento
3. **Bucket S3**: O bucket do Data Lake deve existir antes da execução

## Fluxo de Dados

1. **Entrada**: EventBridge Scheduler aciona a Lambda periodicamente
2. **Processamento**: Lambda lê dados brutos do S3, processa e calcula features
3. **Saída**: Features são salvas no DynamoDB (Feature Store) e no S3 (treinamento)

