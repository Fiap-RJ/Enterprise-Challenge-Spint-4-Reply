O **AWS IoT Device Simulator** foi descontinuado pela AWS.  

A melhor alternativa é voltar ao uso do **AWS Lambda** para simular a publicação de dados no **IoT Core**. É a solução mais **econômica** e **simples** de gerenciar.

-----

## Opção Recomendada (Free Tier Friendly): AWS Lambda + EventBridge

Esta opção mantém sua arquitetura *serverless* e não adiciona custos fixos. Ela substitui a interface visual do Device Simulator por código Python simples.

### 1\. Novo Fluxo

A arquitetura de Simulação e Ingestão fica da seguinte forma:

**Novo Fluxo:** **Amazon EventBridge** $\rightarrow$ **AWS Lambda (Simulador)** $\rightarrow$ **AWS IoT Core** $\rightarrow$ **AWS Lambda (Processador)** $\rightarrow$ **S3**

### 2\. Funções do Novo Lambda (Simulador)

Você precisará de uma nova função Lambda que faça o trabalho que o *Device Simulator* fazia:

| Serviço | Função | Detalhes |
| :--- | :--- | :--- |
| **Amazon EventBridge** | **Agendador** | Cria uma regra de agendamento (`cron` ou `rate`) para disparar a função Lambda (ex: a cada 1 minuto). |
| **AWS Lambda (Simulador)** | **Gerador de Dados** | A função contém código Python que: <br> a) Gera o **payload JSON** dos sensores (valores aleatórios). <br> b) Usa o SDK **Boto3** para se conectar ao **AWS IoT Core** e publicar a mensagem no tópico MQTT (`sensores/fabrica/dados`). |

### 3\. Ajustes no Terraform (A Serem Adicionados)

Você precisará de blocos Terraform para provisionar esse novo "Simulador Serverless":

1.  **IAM Role para o Novo Lambda:** Um *Role* que permita ao Lambda fazer `logs:PutLogEvents` e, crucialmente, **publicar no IoT Core** (`iot:Publish`).
2.  **AWS Lambda Function:** Onde seu código Python gerador de dados será executado.
3.  **EventBridge Rule:** Uma regra que define a frequência de disparo (`rate(1 minute)`).
4.  **EventBridge Target:** Conecta a regra ao novo Lambda.

**Vantagem:** Totalmente *Free Tier-friendly*, alta flexibilidade (você controla o formato do *payload* diretamente no código), e é uma excelente prática de programação em nuvem.

-----