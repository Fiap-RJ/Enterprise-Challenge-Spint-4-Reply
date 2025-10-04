"""
Módulo de pipeline de processamento de dados.
"""

from datetime import datetime, timedelta, timezone
import pandas as pd
from data_access import (
    fetch_sensor_data,
    save_features_to_s3,
    fetch_failure_labels_from_dynamo,
    save_features_to_dynamodb,
    get_ssm_parameter,
    update_ssm_parameter,
)
from data_processing import merge_sensor_events
from feature_engineering import calculate_features, add_predictive_label


class FeaturePipeline:
    def __init__(
        self,
        bucket_name: str,
        features_table: str,
        failures_table: str,
        ssm_param_name: str,
        time_window: int = 1,
        prediction_horizon: int = 24,
        processing_lag: int = 25,
    ):
        """
        Inicializa o pipeline com parâmetros injetados.

        Args:
            bucket_name: Nome do bucket S3 do data lake
            features_table: Nome da tabela DynamoDB para features
            failures_table: Nome da tabela DynamoDB para histórico de falhas
            ssm_param_name: Nome do parâmetro SSM para controle de estado
            time_window: Janela de tempo para processamento em horas (padrão: 1)
            prediction_horizon: Horizonte de predição em horas (padrão: 24)
            processing_lag: Lag de processamento em horas (padrão: 25)
        """
        self.bucket_name = bucket_name
        self.features_table = features_table
        self.failures_table = failures_table
        self.ssm_param_name = ssm_param_name
        self.time_window = time_window
        self.prediction_horizon = prediction_horizon
        self.processing_lag = processing_lag

        # Inicializa atributos que serão definidos durante a execução
        self.sensor_events = None
        self.failure_events = None
        self.final_features = None
        self.labeling_start = None
        self.labeling_end = None
        self.features_start = None
        self.features_end = None

    def _calculate_windows(self):
        """Calcula e define as janelas de tempo para a execução atual."""
        last_processed_str = get_ssm_parameter(self.ssm_param_name)
        last_processed_ts = datetime.fromisoformat(last_processed_str).replace(
            tzinfo=timezone.utc
        )

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.processing_lag)

        if last_processed_ts >= cutoff:
            print("Pipeline já está em dia. Nenhum dado novo para processar.")
            return None  # Sinaliza que não há nada a fazer

        self.features_start = last_processed_ts
        self.features_end = min(
            self.features_start + timedelta(hours=self.time_window), cutoff
        )
        self.labeling_start = self.features_end
        self.labeling_end = self.features_end + timedelta(hours=self.prediction_horizon)

        print(
            f"Janela de features: {self.features_start.isoformat()} a {self.features_end.isoformat()}"
        )
        print(
            f"Janela de labels: {self.labeling_start.isoformat()} a {self.labeling_end.isoformat()}"
        )
        return True  # Sinaliza para continuar

    def _extract(self):
        """Etapa de extração de dados."""
        self.sensor_events = fetch_sensor_data(
            self.bucket_name, self.features_start, self.features_end
        )
        self.failure_events = fetch_failure_labels_from_dynamo(
            self.failures_table, self.labeling_start, self.labeling_end
        )

    def _transform(self):
        """Etapa de transformação e cálculo de features."""
        grouped_data = merge_sensor_events(self.sensor_events)
        # Estado anterior pode ser aprimorado
        features_no_label = calculate_features(grouped_data, {})
        self.final_features = add_predictive_label(
            features_no_label, self.failure_events, self.prediction_horizon
        )

    def _load(self):
        """Etapa de carregamento dos dados para S3 e DynamoDB."""
        if not self.final_features:
            print("Nenhuma feature calculada.")
            return

        features_df = pd.DataFrame(self.final_features.values())
        save_features_to_s3(features_df, self.bucket_name)
        save_features_to_dynamodb(self.final_features, self.features_table)

    def _update_state(self):
        """Atualiza o parâmetro no SSM para a próxima execução."""
        print(f"Atualizando estado para: {self.features_end.isoformat()}")
        update_ssm_parameter(self.ssm_param_name, self.features_end.isoformat())

    def run(self):
        """Orquestra a execução do pipeline."""
        if not self._calculate_windows():
            return "Nenhum dado novo para processar."

        self._extract()
        if not self.sensor_events:
            print(
                "Nenhum evento de sensor encontrado na janela. Apenas atualizando o estado."
            )
            self._update_state()
            return "Nenhum evento de sensor para processar."

        self._transform()
        self._load()
        self._update_state()
        return "Pipeline executado com sucesso!"
