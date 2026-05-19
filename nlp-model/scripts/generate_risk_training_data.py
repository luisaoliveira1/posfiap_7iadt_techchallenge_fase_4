"""
Gera dados de treinamento para o motor de risco executando o modelo NLP treinado
sobre a partição de teste (HELD-OUT) do dataset traduzido. Usar apenas dados não vistos
garante que os scores de probabilidade do NLP reflitam o desempenho no mundo real, e usar
rótulos ground-truth evita vazamento trivial de labels.

Colunas do CSV de saída:
  HIGH_RISK_score, MONITORING_score, LOW_RISK_score, risk_level

Execução: python -m scripts.generate_risk_training_data  (a partir do diretório nlp-model/)
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.predict import predict_from_text

TRANSLATED_CSV = Path("data/processed/translated.csv")
RISK_CSV = Path("../risk-engine/data/train_risk.csv")

LABEL_MAP = {0: "LOW_RISK", 1: "MONITORING", 2: "HIGH_RISK",
             "0": "LOW_RISK", "1": "MONITORING", "2": "HIGH_RISK"}


def main() -> None:
    if not TRANSLATED_CSV.exists():
        raise FileNotFoundError(f"{TRANSLATED_CSV} não encontrado. Execute 'make translate' primeiro.")

    print(f"Carregando {TRANSLATED_CSV}...")
    df = pd.read_csv(TRANSLATED_CSV)

    label_col = "label" if "label" in df.columns else df.columns[-1]
    text_col  = "text_pt" if "text_pt" in df.columns else "text"
    df = df.dropna(subset=[text_col, label_col])

    if df[label_col].iloc[0] in LABEL_MAP:
        df["risk_level_true"] = df[label_col].map(LABEL_MAP)
    else:
        df["risk_level_true"] = df[label_col]
    df = df.dropna(subset=["risk_level_true"])

    _, df_test = train_test_split(df, test_size=0.20, random_state=42, stratify=df["risk_level_true"])
    print(f"Usando {len(df_test)} amostras held-out (o modelo NLP não as viu durante o treinamento).")

    print("Gerando scores de probabilidade do NLP...")
    rows = []
    for i, (_, row) in enumerate(df_test.iterrows()):
        result = predict_from_text(str(row[text_col]))
        prob_map = result["probabilities"]
        rows.append({
            "HIGH_RISK_score":  prob_map.get("HIGH_RISK",  0.0),
            "MONITORING_score": prob_map.get("MONITORING", 0.0),
            "LOW_RISK_score":   prob_map.get("LOW_RISK",   0.0),
            "risk_level":       row["risk_level_true"],   # ground truth, não predição do NLP
        })
        if (i + 1) % 50 == 0:
            print(f"  Processados {i + 1}/{len(df_test)}...")

    out_df = pd.DataFrame(rows)
    RISK_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(RISK_CSV, index=False)
    print(f"\nDados de treinamento do motor de risco salvos em {RISK_CSV}")
    print(f"Distribuição de rótulos:\n{out_df['risk_level'].value_counts()}")


if __name__ == "__main__":
    main()
