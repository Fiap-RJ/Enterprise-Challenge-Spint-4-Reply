from diagrams import Diagram, Cluster, Edge
from diagrams.aws.ml import Sagemaker, SagemakerModel, SagemakerModel
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import Eventbridge, StepFunctions
from diagrams.aws.iot import IotCore
from diagrams.aws.storage import S3
from diagrams.onprem.client import User

with Diagram("Arquitetura MLOps para Manutenção Preditiva", show=False, filename="../assets/arquitetura_cloud_aws") as diag:

    # Fontes de entrada/saída externas ao fluxo principal
    user = User("Usuário Final")
    scheduler = Eventbridge("EventBridge Scheduler")

    # --- CLUSTERS DE COMPONENTES ---

    with Cluster("2. Armazenamento Central (Data Lake & Feature Store)") as storage_cluster:
        s3_raw = S3("S3 - Data Lake (raw)")
        s3_processed = S3("S3 - Feature Store (processed)")
        dynamo_state = Dynamodb("DynamoDB - MachineState")
        dynamo_failures = Dynamodb("DynamoDB - FailureHistory")
        dynamo_features = Dynamodb("DynamoDB - Real-time Features")

    with Cluster("1. Ingestão de Dados (Streaming)") as ingestion_cluster:
        iot_core = IotCore("IoT Core")
        simulator_lambda = Lambda("Sensor Simulator")
        ingestion_lambda = Lambda("Ingestion Processor")
        label_lambda = Lambda("Label Ingestion")

    with Cluster("3. Engenharia de Features (Batch)") as processing_cluster:
        processor_lambda = Lambda("Feature Processor")

    with Cluster("4. MLOps - Pipeline de Treinamento Orquestrado") as mlops_cluster:
        step_functions = StepFunctions("Step Functions State Machine")
        
        # Etapas dentro do pipeline
        prep_lambda = Lambda("Data Prep")
        sagemaker_training = Sagemaker("SageMaker Training Job")
        eval_lambda = Lambda("Model Evaluation")
        model_registry = SagemakerModel("Model Registry")
        sagemaker_endpoint = SagemakerModel("SageMaker Endpoint")
        
        # Aplicação de consumo
        dashboard = User("Streamlit Dashboard")

    # ---- CONEXÕES DO DIAGRAMA ----

    # 1. Conexões invisíveis para forçar o layout vertical dos clusters de trabalho
    label_lambda >> Edge(style="invis") >> processor_lambda
    processor_lambda >> Edge(style="invis") >> step_functions # O gatilho do próximo estágio é o Step Functions

    # 2. Fluxo de Ingestão de Dados
    scheduler >> simulator_lambda >> iot_core
    simulator_lambda >> dynamo_state # Interação com a tabela de estado
    iot_core >> ingestion_lambda >> s3_raw
    iot_core >> label_lambda >> dynamo_failures

    # 3. Fluxo de Engenharia de Features
    scheduler >> processor_lambda
    s3_raw >> processor_lambda # CORRIGIDO: Lê de S3 raw
    processor_lambda >> s3_processed
    processor_lambda >> dynamo_features

    # 4. Fluxo do Pipeline de Treinamento (orquestrado pelo Step Functions)
    scheduler >> step_functions # Gatilho principal do pipeline de MLOps
    step_functions >> prep_lambda >> s3_processed # Prep Lambda lê dos dados processados
    step_functions >> sagemaker_training # Step Functions inicia o treino
    s3_processed >> sagemaker_training # Treino lê os dados preparados
    sagemaker_training >> step_functions # Treino notifica o Step Functions ao terminar
    step_functions >> eval_lambda >> model_registry # Avaliação e registro do modelo
    step_functions >> sagemaker_endpoint # Deploy condicional do modelo

    # 5. Fluxo de Inferência (consumo pelo dashboard)
    user >> dashboard
    dashboard >> dynamo_features # Dashboard lê as features em tempo real
    dashboard >> sagemaker_endpoint # Dashboard envia dados para predição
    sagemaker_endpoint >> dashboard # Endpoint retorna a predição

diag