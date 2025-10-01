# Plano de Projeto: Simulação e Ingestão de Dados

Este plano cobre a primeira fase da sua pipeline MLOps: gerar dados simulados de sensores industriais e ingeri-los no **Data Lake (S3)** de forma segura e econômica, utilizando a arquitetura Free Tier (**EventBridge → Lambda (Simulador) → IoT Core → Lambda (Processador) → S3**).

---

## I. Arquitetura de Referência (Simulador Serverless)

| Camada | Serviço AWS | Função |
| :--- | :--- | :--- |
| **Agendamento** | Amazon EventBridge | Regra de agendamento que dispara a função Lambda simuladora a cada minuto. |
| **Geração** | AWS Lambda (Simulador) | Função *serverless* que gera dados simulados de sensores e publica no IoT Core via MQTT. |
| **Entrada** | AWS IoT Core | *Broker* de mensagens que recebe dados e os encaminha via Regra. |
| **Processamento** | AWS Lambda (Processador) | Função *serverless* para receber os dados do IoT e salvá-los em **lotes (*batch*)** no S3. |
| **Armazenamento** | Amazon S3 | **Data Lake** para armazenar os dados brutos e *datasets* processados. |

---

## II. Etapas do Projeto e Tarefas

### Etapa 1: Provisionamento da Infraestrutura de Rede e Storage (IaC)

| Tarefa | Serviço/Ferramenta | Descrição |
| :--- | :--- | :--- |
| 1.1 | **Terraform** | Inicializar o projeto Terraform e a VPC. |
| 1.2 | **Terraform/VPC** | Criar a **VPC**, Subnets Públicas, Subnets Privadas, IGW e Route Tables. |
| 1.3 | **Terraform/S3** | Criar o **S3 Data Lake** com criptografia padrão (SSE-S3). |
| 1.4 | **Terraform/IAM** | Criar os **IAM Roles** para os Lambdas (incluindo permissões para S3, IoT Core e CloudWatch Logs). |
| 1.5 | **Terraform/SG** | Criar os **Security Groups** para os Lambdas, permitindo tráfego de saída (outbound). |

### Etapa 2: Desenvolvimento do Código Lambda de Simulação

| Tarefa | Serviço/Ferramenta | Descrição |
| :--- | :--- | :--- |
| 2.1 | **Python/Boto3** | Desenvolver o *script* Lambda (`sensor_simulator.py`). Deve gerar dados simulados de sensores industriais (temperatura, pressão, vibração, etc.). | 
| 2.2 | **Python/Boto3** | Implementar a lógica de publicação no IoT Core: conectar ao MQTT e publicar no tópico `sensores/fabrica/dados`. |
| 2.3 | **Terraform/Lambda** | Empacotar o código Lambda (`.zip`) e provisionar a função simuladora. |

### Etapa 3: Desenvolvimento do Código Lambda de Ingestão

| Tarefa | Serviço/Ferramenta | Descrição |
| :--- | :--- | :--- |
| 3.1 | **Python/Boto3** | Desenvolver o *script* Lambda (`ingestion_processor.py`). Deve receber eventos do IoT, adicionar metadados (timestamp de ingestão) e criar um *buffer*. | 
| 3.2 | **Python/Boto3** | Implementar a lógica de escrita no S3: salvar os dados em **lote** no S3, utilizando a estrutura de pastas baseada em data (**ex:** `raw/year=YYYY/month=MM/`). |
| 3.3 | **Terraform/Lambda** | Empacotar o código Lambda (`.zip`) e provisionar a função, associando-a ao **IAM Role** e às **Subnets Privadas** (VPC Config). |

### Etapa 4: Configuração do Agendamento (EventBridge)

| Tarefa | Serviço/Ferramenta | Descrição |
| :--- | :--- | :--- |
| 4.1 | **Terraform/EventBridge** | Criar a **EventBridge Rule** com agendamento (`rate(1 minute)`) para disparar o Lambda simulador. |
| 4.2 | **Terraform/EventBridge** | Configurar o **Target** da regra para invocar o Lambda simulador. |

### Etapa 5: Configuração da Ingestão de Streaming (IoT Core)

| Tarefa | Serviço/Ferramenta | Descrição |
| :--- | :--- | :--- |
| 5.1 | **Terraform/IoT** | Criar a **IoT Rule** com a *query* SQL: `SELECT * FROM 'sensores/fabrica/dados'`. |
| 5.2 | **Terraform/Lambda** | Adicionar a permissão (`aws_lambda_permission`) para que o **IoT Core** possa invocar o Lambda processador. |

### Etapa 6: Teste e Validação

| Tarefa | Serviço/Ferramenta | Descrição |
| :--- | :--- | :--- |
| 6.1 | **EventBridge** | Verificar se a regra está disparando o Lambda simulador a cada minuto. |
| 6.2 | **CloudWatch Logs** | Monitorar os *logs* dos Lambdas para verificar a execução e diagnosticar erros. |
| 6.3 | **Amazon S3** | Validar se os arquivos estão sendo criados no *bucket* do S3 com a estrutura de pastas correta e se o conteúdo JSON está intacto. |

---

## III. Boas Práticas e Segurança (Checklist)

| Prática | Detalhe de Implementação | Justificativa |
| :--- | :--- | :--- |
| **Princípio do Privilégio Mínimo** | Os **IAM Roles** dos Lambdas têm apenas as permissões mínimas necessárias (S3, IoT, Logs). | Minimiza o risco de segurança em caso de comprometimento das funções. |
| **Isolamento de Rede (VPC)** | O **AWS Lambda (Processador)** é configurado nas **Subnets Privadas** da VPC. | Garante que o tráfego da função permaneça privado e controlado pela rede da AWS. |
| **Criptografia em Repouso** | S3 Data Lake com **SSE-S3** ativada. | Proteção básica e automática dos dados armazenados (obrigatório em ambiente de produção). |
| **VPC Endpoints** | Recomendado para o S3 e DynamoDB (futuro) para permitir o acesso do Lambda sem sair da rede privada. | Evita a necessidade de NAT Gateway (economizando custos) e aumenta a segurança. |
| **Simulador Serverless** | Substitui o AWS IoT Device Simulator (descontinuado) por uma solução totalmente *Free Tier-friendly*. | Economia de custos e maior controle sobre a geração de dados. |

---

## IV. Vantagens da Nova Arquitetura

| Vantagem | Descrição |
| :--- | :--- |
| **Free Tier Friendly** | Todos os serviços utilizados estão no Free Tier da AWS. |
| **Totalmente Serverless** | Não há custos fixos de infraestrutura. |
| **Alta Flexibilidade** | Controle total sobre o formato e frequência dos dados simulados. |
| **Fácil Manutenção** | Código Python simples e bem documentado. |
| **Escalabilidade** | Pode ser facilmente ajustado para diferentes volumes de dados. |
