# Módulo de Processamento de Features

Este módulo contém a lógica de processamento de dados para geração de features preditivas para o sistema de predição de falhas.

## Estrutura dos Arquivos

### `data_access.py`
**Responsabilidade**: Acesso a recursos externos (AWS)
- **S3**: Leitura de dados brutos e salvamento de features processadas
- **DynamoDB**: Busca de eventos de falha e salvamento de features
- **SSM**: Gerenciamento de estado do pipeline

**Funções principais**:
- `fetch_sensor_data()` - Busca dados de sensores do S3
- `save_features_to_s3()` - Salva features processadas no S3
- `fetch_failure_labels_from_dynamo()` - Busca eventos de falha do DynamoDB
- `save_features_to_dynamodb()` - Salva features no DynamoDB
- `get_ssm_parameter()` / `update_ssm_parameter()` - Gerenciamento de estado

### `data_processing.py`
**Responsabilidade**: Processamento e agrupamento de dados brutos
- Merge de eventos de sensores em janelas de tempo
- Agrupamento por máquina e timestamp

**Funções principais**:
- `merge_sensor_events()` - Agrupa eventos por máquina e janela de tempo

### `feature_engineering.py`
**Responsabilidade**: Cálculo de features preditivas e labels
- Cálculo de features stateful (média móvel, temperatura máxima)
- Adição de labels preditivas baseadas em falhas futuras

**Funções principais**:
- `calculate_features()` - Calcula features preditivas
- `add_predictive_label()` - Adiciona labels baseadas em falhas futuras

### `pipeline.py`
**Responsabilidade**: Orquestração do pipeline completo
- Coordenação das etapas ETL
- Gerenciamento de janelas de tempo
- Controle de estado do processamento

**Classe principal**:
- `FeaturePipeline` - Orquestra todo o processo de geração de features
  - Construtor recebe parâmetros via injeção de dependência
  - Não lê variáveis de ambiente diretamente (responsabilidade do lambda_handler)

### `lambda_function.py`
**Responsabilidade**: Ponto de entrada da AWS Lambda
- Lê variáveis de ambiente e injeta parâmetros na FeaturePipeline
- Handler que coordena a configuração e execução do pipeline

## Fluxo de Execução

1. **Extração**: Busca dados de sensores do S3 e eventos de falha do DynamoDB
2. **Transformação**: 
   - Agrupa eventos por janela de tempo
   - Calcula features preditivas
   - Adiciona labels baseadas em falhas futuras
3. **Carregamento**: Salva features no S3 e DynamoDB
4. **Atualização de Estado**: Atualiza parâmetro SSM para próxima execução

## Dependências

- `boto3` - Cliente AWS
- `pandas` - Manipulação de DataFrames
