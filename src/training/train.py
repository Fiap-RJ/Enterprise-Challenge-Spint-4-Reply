# train.py

"""
Script de treinamento para previsão de falhas de máquinas usando XGBoost.
Foi desenhado para execução no ambiente Amazon SageMaker, obedecendo às convenções
padrão de diretórios de entrada e saída.
"""

import argparse
import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from xgboost import XGBClassifier


def parse_args():
    """Analisa argumentos de linha de comando enviados pelo SageMaker."""
    parser = argparse.ArgumentParser()

    # Hiperparâmetros principais do XGBClassifier
    parser.add_argument("--max_depth", type=int, default=5)
    parser.add_argument("--n_estimators", type=int, default=200)
    parser.add_argument("--learning_rate", type=float, default=0.1)

    # Argumentos auxiliares (SageMaker injeta esses valores automaticamente)
    parser.add_argument(
        "--model-dir",
        type=str,
        default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"),
    )
    parser.add_argument(
        "--train",
        type=str,
        default=os.environ.get("SM_CHANNEL_TRAINING", "/opt/ml/input/data/training"),
    )
    parser.add_argument(
        "--validation",
        type=str,
        default=os.environ.get(
            "SM_CHANNEL_VALIDATION", "/opt/ml/input/data/validation"
        ),
    )

    return parser.parse_args()


def load_data(directory: str):
    """Carrega um arquivo CSV chamado train.csv ou validation.csv no diretório dado."""
    csv_files = list(Path(directory).glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nenhum arquivo .csv encontrado em {directory}")
    # Assume o primeiro arquivo encontrado como entrada
    print(f"Carregando dados de {csv_files[0]}")
    return pd.read_csv(csv_files[0])


def separate_features_target(df: pd.DataFrame, target_col: str, feature_cols_to_drop: list):
    """Separa features e alvo, removendo colunas de identificação."""
    print(f"Removendo colunas que não são features: {feature_cols_to_drop}")
    
    # Valida se as colunas a serem dropadas existem no dataframe
    cols_to_drop_existing = [col for col in feature_cols_to_drop if col in df.columns]
    
    X = df.drop(columns=[target_col] + cols_to_drop_existing)
    y = df[target_col]
    
    print(f"Features utilizadas para o treinamento: {list(X.columns)}")
    
    return X, y

def train_model(X_train, y_train, args):
    """Instancia e treina o XGBClassifier com hiperparâmetros fornecidos."""
    print("Treinando modelo XGBoost...")
    model = XGBClassifier(
        max_depth=args.max_depth,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        objective="binary:logistic",
        use_label_encoder=False,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)
    print("Treinamento concluído.")
    return model


def evaluate_model(model, X_val, y_val):
    """Avalia o modelo nas métricas padrão e retorna um dicionário."""
    print("Avaliando modelo...")
    probs = model.predict_proba(X_val)[:, 1]
    preds = (probs >= 0.5).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_val, preds),
        "precision": precision_score(y_val, preds, zero_division=0),
        "recall": recall_score(y_val, preds, zero_division=0),
        "f1": f1_score(y_val, preds, zero_division=0),
        "auc": roc_auc_score(y_val, probs),
    }

    print("Métricas de avaliação:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
    return metrics


def save_metrics(metrics: dict, output_path: str):
    """Salva métricas em formato JSON compatível com SageMaker."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"metrics": metrics}, f)
    print(f"Métricas salvas em {output_path}")


def save_model(model, model_dir: str):
    """Serializa o modelo treinado usando joblib."""
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.joblib")
    joblib.dump(model, model_path)
    print(f"Modelo salvo em {model_path}")


if __name__ == "__main__":
    args = parse_args()

    print("Iniciando processo de treinamento...")

    # 1. Carregamento dos dados
    train_df = load_data(args.train)
    val_df = load_data(args.validation)

    # 2. Pré-processamento
    target_column = "falha_nas_proximas_24h"
    id_columns_to_drop = ["machine_id", "timestamp_processamento"] 
    
    X_train, y_train = separate_features_target(train_df, target_column, id_columns_to_drop)
    X_val, y_val = separate_features_target(val_df, target_column, id_columns_to_drop)

    # 3. Treinamento
    model = train_model(X_train, y_train, args)

    # 4. Avaliação
    metrics = evaluate_model(model, X_val, y_val)

    # 5. Persistência
    save_metrics(metrics, "/opt/ml/output/data/evaluation.json")
    save_model(model, args.model_dir)

    print("Pipeline concluído com sucesso.")
