from diagrams import Diagram, Cluster, Edge
from diagrams.aws.ml import SagemakerTrainingJob, SagemakerModel, Sagemaker
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import Eventbridge
from diagrams.aws.iot import IotCore
from diagrams.aws.storage import S3
from diagrams.onprem.client import User

with Diagram("Arquitetura MLOps para Manutenção Preditiva", show=False, filename="arquitetura_cloud_aws") as diag:

    user = User("Usuário Final")
    scheduler = Eventbridge("EventBridge Scheduler")

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

    with Cluster("4. MLOps - Treinamento e Inferência") as mlops_cluster:
        sagemaker_training = Sagemaker("SageMaker Training")
        sagemaker_endpoint = SagemakerModel("SageMaker Endpoint")
        dashboard = User("Streamlit Dashboard")

    label_lambda >> Edge(style="invis") >> processor_lambda
    processor_lambda >> Edge(style="invis") >> sagemaker_training

    scheduler >> simulator_lambda >> iot_core
    simulator_lambda >> dynamo_state
    iot_core >> ingestion_lambda >> s3_raw
    iot_core >> label_lambda >> dynamo_failures

    scheduler >> processor_lambda
    processor_lambda >> s3_processed
    processor_lambda >> dynamo_features
    processor_lambda >> s3_raw

    s3_processed >> sagemaker_training >> sagemaker_endpoint

    user >> dashboard
    dashboard >> dynamo_features
    dashboard >> sagemaker_endpoint
    sagemaker_endpoint >> dashboard

diag