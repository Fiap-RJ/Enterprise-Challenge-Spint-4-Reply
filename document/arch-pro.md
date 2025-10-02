
# Documentação Consolidada da Arquitetura MLOps Industrial

Esta documentação descreve a arquitetura Serverless para a Manutenção Preditiva. O foco é a transformação de dados de sensores e rótulos de falha em Features prontas para o treinamento do modelo.

---

## 1. Arquitetura e Fluxo de Dados

A arquitetura adota um padrão robusto de **Injestão de Streaming** para os dados brutos e **Processamento em Lote (Batch)** agendado para a engenharia de features.

### Fluxos Detalhados da Solução:

1.  **Fluxo de Dados de Sensor e Rótulos (Entrada de Streaming):**
    ```
    EventBridge → Lambda Simulator → IoT Core → Lambda Ingestion → S3 (Bruto - Data Lake)
    ```
2.  **Fluxo de Feature Engineering (Processamento em Lote Agendado):**
    ```
    EventBridge Scheduler → Lambda Processor [Lê do S3 Bruto] → DynamoDB/S3 (Processado - Feature Store)
    ```
3.  **Fluxo de MLOps:**
    ```
    S3 Processado → SageMaker Training → SageMaker Endpoint
    ```

---

## 2. Contratos de Dados e Estrutura de Ativos

### 2.1 Contrato Principal de Ativos e Sensores

| Item | Padrão | Detalhes |
| :--- | :--- | :--- |
| **Ativos Simulados** | **5 Máquinas** (Ex: PUMP-A01, FAN-B02, etc.) | Usadas para generalizar o modelo. O **`machine_id`** é a chave primária. |
| **Sensores** | Vibração (RMS) e Temperatura ($^\circ C$) | Os dois indicadores principais da saúde mecânica. |
| **Tópicos MQTT** | **Três Tópicos:** Vibração, Temperatura e **Rótulo de Falha**. | Permite o roteamento de dados e eventos separadamente. |
| **Chave de Correlacão**| `machine_id` + `timestamp_utc` | Usados para unir leituras de sensores e rótulos de falha. |

---

## 2.2 Estrutura de Tópicos MQTT e Contratos de Payload

Para garantir a escalabilidade e a clareza, adotamos uma estrutura de tópicos MQTT hierárquica. Este padrão facilita o roteamento e a depuração de mensagens, além de permitir o uso de wildcards (`+`, `#`) nas regras do AWS IoT Core para capturar dados de forma eficiente.

A premissa é que cada sensor publica em seu próprio tópico, simulando um cenário real onde os dados são gerados por fontes independentes.

### Definição dos Tópicos

| Tipo de Dado | Estrutura do Tópico | Detalhes do Payload |
| :--- | :--- | :--- |
| **Leitura de Temperatura** | `industrial/machine/{machine_id}/telemetry/temperature` | Contém a leitura de temperatura em graus Celsius (`°C`) para um timestamp específico. |
| **Leitura de Vibração** | `industrial/machine/{machine_id}/telemetry/vibration` | Contém a leitura de vibração em mm/s RMS para um timestamp específico. |
| **Eventos de Falha** | `industrial/machine/{machine_id}/event/failure`| Contém o registro de um evento de falha, que servirá como rótulo para o treinamento. |


### Exemplos de Publicação

**1. Publicação de Temperatura para a Bomba PUMP-A01:**

* **Tópico:** `industrial/machine/PUMP-A01/telemetry/temperature`
* **Payload:**
    ```json
    {
      "machine_id": "PUMP-A01",
      "timestamp_utc": "2025-10-15T09:00:01.123Z",
      "temperature_celsius": 75.4
    }
    ```

**2. Publicação de Vibração para a Bomba PUMP-A01:**

* **Tópico:** `industrial/machine/PUMP-A01/telemetry/vibration`
* **Payload:**
    ```json
    {
      "machine_id": "PUMP-A01",
      "timestamp_utc": "2025-10-15T09:00:01.456Z",
      "vibration_rms": 4.2
    }
    ```

**3. Publicação de Evento de Falha para a Bomba PUMP-A01:**

* **Tópico:** `industrial/machine/PUMP-A01/event/failure`
* **Payload:**
    ```json
    {
      "machine_id": "PUMP-A01",
      "timestamp_utc": "2025-10-15T09:30:00Z",
      "codigo_evento": "FALHA_VIBRACAO_ELEVADA"
    }
## 3. Módulo de Geração e Ingestão de Rótulos (Self-Labeling)

Esta abordagem faz com que o **Lambda Simulator** seja a única fonte de verdade para dados e rótulos, simplificando o controle da simulação.

### 3.1 Geração de Rótulo de Falha no Simulator

* **Lógica:** O Lambda Simulator usa o estado persistente de degradação da máquina (no DynamoDB) e as leituras simuladas de Vibração/Temperatura para determinar quando uma falha ocorre (ex: `vib_rms_eixo_x > 5.0`).
* **Publicação:** Quando o limite de falha é atingido, o Simulator publica uma mensagem de alerta no tópico dedicado, **além** de publicar os dados de sensor daquele ciclo.

**Tópico e Payload de Rótulo de Falha (Exemplo de Entrada de Evento):**

| Tópico | Payload (Exemplo) |
| :--- | :--- |
|`industrial/machine/PUMP-A01/event/failure` | `{"machine_id": "PUMP-A01", "timestamp_utc": "2025-10-15T09:00:00Z", "codigo_evento": "FALHA_DETECTADA"}` |

### 3.2 O Papel do Lambda Ingestion

O **Lambda Ingestion** tem um papel simplificado: é um *proxy* que recebe todas as mensagens (Vibração, Temperatura) do IoT Core e as salva imediatamente no S3.

| Item | Fluxo | Responsabilidade |
| :--- | :--- | :--- |
| **IoT Core Rules**| Roteiam todas as mensagens dos **três tópicos** (Vibração, Temperatura) para o `Lambda Ingestion`. |
| **Lambda Ingestion**| Recebe o evento e escreve o JSON bruto no S3. Não faz processamento. | **Destino:** S3 (Data Lake) no prefixo `raw/`. |

---

## 4. Módulo de Feature Engineering e Feature Store

### 4.1 Lambda Processor

O `Lambda Processor` é acionado periodicamente via **EventBridge Scheduler** (ex: a cada 6 horas) e realiza o processamento em lote dos dados brutos que se acumularam no S3.

| Função | Detalhe |
| :--- | :--- |
| **Extração (E)** | Lê o lote de arquivos JSON Lines do S3 (`raw/`). Após o processamento bem-sucedido, os arquivos são movidos para um prefixo de arquivamento (ex: `archive/`) para evitar reprocessamento. |
| **Junção de Dados**| **Correlaciona** as leituras de Vibração, Temperatura e Rótulos usando a técnica de **Janelas de Tempo (Tumbling Windows)**. Como os timestamps nunca são idênticos, os eventos são agrupados em pequenas janelas fixas (ex: 1 segundo) com base em `machine_id` e um timestamp "arredondado", permitindo a sincronização dos diferentes sensores. |
| **Feature Engineering**| Calcula *features* preditivas (média móvel, desvio padrão) dentro das janelas de tempo e cria o **Rótulo Final** para o treinamento. |

### 4.2 Feature Store (DynamoDB)

O DynamoDB serve como repositório de Features de **Baixa Latência**, otimizado para a inferência em tempo real.

| Tabela | Chave Primária | Conteúdo |
| :--- | :--- | :--- |
| **`MachineFeatureStore`** | `machine_id` | Armazena as *features* prontas (ex: `vib_media_5h`, `temp_max_24h`). |
| **`FalhaHistory`** | `machine_id` + `timestamp_utc` | Armazena o histórico dos eventos de falha (os Rótulos). Usado para o *joining* na fase de treinamento. |

### 4.3 Dataset de Treinamento

O `Lambda Processor` também salva o dataset final, pronto para o ML:

* **Localização:** S3 (`s3://<bucket>/processed/training_data/`).
* **Conteúdo:** Tabela de Features + Coluna de Rótulo.

| Coluna | Exemplo de Valor | Fonte |
| :--- | :--- | :--- |
| `vib_media_5h` | 4.85 | Feature Engineering |
| `temp_max_24h` | 78.1 | Feature Engineering |
| **`LABEL_FALHA_7D`** | 1 (Sim) ou 0 (Não) | Criado ao **unir** as *Features* de hoje com um Rótulo de Falha que ocorreu nos próximos 7 dias. |

### 4.4 Orquestração Avançada (Próximos Passos)

Para o escopo atual, o `Lambda Processor` centraliza a lógica de ETL. Em um cenário de produção com mais etapas (validação, múltiplos enriquecimentos, etc.), o fluxo de processamento poderia ser orquestrado com o **AWS Step Functions**. Isso transformaria o processo em um workflow mais resiliente, visual e com melhor tratamento de erros, servindo como uma evolução natural da arquitetura.

---

## 5. Módulo de Dashboard e Inferência

### Streamlit App (Interface do Usuário)

O Frontend é o consumidor final das *Features* e dos resultados.

| Fonte de Dados | Consumo | Propósito |
| :--- | :--- | :--- |
| **DynamoDB** | Leitura direta (`boto3`) da `MachineFeatureStore`. | Exibir o status de saúde e as Features atuais. |
| **API de Inferência**| Mock local (inicialmente) ou SageMaker Endpoint. | Retorna a **probabilidade de falha**. Esta probabilidade é usada para colorir e alertar o usuário. |


### Extra
-   Temperatura → **°C** entre **20 e 150**.
-   Vibração → **mm/s RMS** com valores **entre 0 e 10**, simulando falhas quando passa de **7–8 mm/s**.
	- Normas ISO (como **ISO 10816 / ISO 20816**) definem limites em **mm/s RMS** para indicar condição da máquina:

	-   Até **4,5 mm/s RMS** → bom.
	-   **4,5 – 7,1 mm/s RMS** → atenção.
	-   **7,1 – 11,2 mm/s RMS** → condição insatisfatória.
	-   Acima de **11,2 mm/s RMS** → crítico.
