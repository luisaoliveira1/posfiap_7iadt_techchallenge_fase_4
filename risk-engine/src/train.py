"""
Treina um pipeline StandardScaler → LogisticRegression sobre os scores de saída do modelo NLP.
Entrada:  risk-engine/data/train_risk.csv  (gerado por nlp-model/scripts/generate_risk_training_data.py)
Saída:    risk-engine/models/risk_model.joblib

Execução: python -m src.train  (a partir do diretório risk-engine/)
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.schema import FEATURE_COLUMNS, LABELS

DATA_CSV = Path("data/train_risk.csv")
MODELS_DIR = Path("models")


def main() -> None:
    if not DATA_CSV.exists():
        raise FileNotFoundError(
            f"{DATA_CSV} não encontrado. Execute 'make gen-risk-data' primeiro."
        )

    print(f"Carregando {DATA_CSV}...")
    df = pd.read_csv(DATA_CSV)
    print(f"Shape: {df.shape}")
    print(f"Distribuição de rótulos:\n{df['risk_level'].value_counts()}")

    X = df[FEATURE_COLUMNS].values
    y = df["risk_level"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    print(f"\nTreino: {len(X_train)} | Teste: {len(X_test)}")

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        )),
    ])
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    print("\n=== Relatório de Classificação ===")
    print(classification_report(y_test, y_pred))
    print("=== Matriz de Confusão ===")
    print(confusion_matrix(y_test, y_pred, labels=LABELS))

    MODELS_DIR.mkdir(exist_ok=True)
    bundle = {
        "pipeline": pipe,
        "feature_columns": FEATURE_COLUMNS,
        "class_names": list(pipe.classes_),
    }
    joblib.dump(bundle, MODELS_DIR / "risk_model.joblib")
    print(f"\nModelo salvo em {MODELS_DIR}/risk_model.joblib")


def train_risk_model(df: "pd.DataFrame") -> dict:
    """
    Chamado pelo endpoint /admin/retrain.
    """
    X = df[FEATURE_COLUMNS].values
    y = df["risk_level"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X_train, y_train)

    MODELS_DIR.mkdir(exist_ok=True)
    bundle = {"pipeline": pipe, "feature_columns": FEATURE_COLUMNS, "class_names": list(pipe.classes_)}
    joblib.dump(bundle, MODELS_DIR / "risk_model.joblib")
    return bundle


if __name__ == "__main__":
    main()
