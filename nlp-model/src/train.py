"""
Pipeline do treinamento:
  1. Carregar dataset traduzido (data/processed/translated.csv)
  2. Identificar colunas de texto e rótulo e mapear rótulos para HIGH_RISK / MONITORING / LOW_RISK
  3. Tokenizar com pré-processamento em português
  4. Treinar LDA para features de tópicos
  5. Construir matriz combinada de TF-IDF + LDA
  6. Divisão de treino e teste (estratificado por classe)
  7. Treinar classificador LogisticRegression
  8. Avaliar no conjunto de teste
  9. Persistir todos os artefatos em models/

Execução: python -m src.train  (a partir do diretório nlp-model/)
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from src.lda_model import get_topic_features, save_lda, train_lda
from src.preprocess import preprocess, preprocess_for_tfidf

TRANSLATED_CSV = Path("data/processed/translated.csv")
MODELS_DIR = Path("models")
LABEL_MAP: dict = {}


def _infer_label_map(series: pd.Series) -> dict:
    """
    Mapeamento automaticamente os rótulos do dataset para HIGH_RISK / MONITORING / LOW_RISK.
    """
    unique = sorted(series.unique())
    print(f"\nValores únicos de rótulo no dataset: {unique}")

    known = {"HIGH_RISK", "MONITORING", "LOW_RISK"}
    if set(unique) <= {0, 1, 2}:
        mapping = {0: "LOW_RISK", 1: "MONITORING", 2: "HIGH_RISK"}
    elif set(unique) <= {"0", "1", "2"}:
        mapping = {"0": "LOW_RISK", "1": "MONITORING", "2": "HIGH_RISK"}
    elif set(unique) <= known:
        # Rótulos já estão no formato esperado — mapeamento identidade
        mapping = {lbl: lbl for lbl in unique}
    else:
        print("AVISO: rótulos não numéricos detectados. Atribuindo LOW→MONITORING→HIGH por ordem alfabética.")
        mapping = {}
        for i, lbl in enumerate(unique):
            if i == 0:
                mapping[lbl] = "LOW_RISK"
            elif i == len(unique) - 1:
                mapping[lbl] = "HIGH_RISK"
            else:
                mapping[lbl] = "MONITORING"

    print(f"Mapeamento de rótulos aplicado: {mapping}")
    return mapping


def build_feature_matrix(
    df: pd.DataFrame,
    lda,
    dictionary,
    tfidf: TfidfVectorizer | None = None,
    fit: bool = True,
) -> tuple:
    texts_clean = df["text_pt"].fillna("").apply(preprocess_for_tfidf)

    if fit:
        tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
        )
        tfidf_matrix = tfidf.fit_transform(texts_clean)
    else:
        tfidf_matrix = tfidf.transform(texts_clean)

    lda_features = np.array([
        get_topic_features(preprocess(t), lda, dictionary)
        for t in df["text_pt"].fillna("")
    ])

    X = sp.hstack([tfidf_matrix, sp.csr_matrix(lda_features)])
    return X, tfidf


def main() -> None:
    if not TRANSLATED_CSV.exists():
        raise FileNotFoundError(
            f"{TRANSLATED_CSV} não encontrado. Execute 'make translate' primeiro."
        )

    print(f"Carregando {TRANSLATED_CSV}...")
    df = pd.read_csv(TRANSLATED_CSV)
    print(f"Shape: {df.shape}")

    label_col = "label" if "label" in df.columns else df.columns[-1]
    text_col = "text_pt" if "text_pt" in df.columns else "text"
    print(f"Coluna de texto: '{text_col}', coluna de rótulo: '{label_col}'")

    label_map = _infer_label_map(df[label_col])
    df["risk_label"] = df[label_col].map(label_map)
    df = df.dropna(subset=["risk_label", text_col])

    print(f"\nDistribuição de rótulos de risco:\n{df['risk_label'].value_counts()}")

    print("\nTokenizando para o LDA...")
    tokenized = [preprocess(str(t)) for t in df[text_col]]

    print("Treinando modelo LDA...")
    lda, dictionary, _ = train_lda(tokenized)
    save_lda(lda, dictionary)

    print("Construindo matriz (TF-IDF + LDA)...")
    X, tfidf = build_feature_matrix(df.rename(columns={text_col: "text_pt"}), lda, dictionary)
    y = df["risk_label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\nTreino: {X_train.shape[0]} amostras | Teste: {X_test.shape[0]} amostras")

    print("Treinando LogisticRegression...")
    clf = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42,
        C=1.0,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\n=== Relatório de Classificação ===")
    print(classification_report(y_test, y_pred))
    print("=== Matriz de Confusão ===")
    print(confusion_matrix(y_test, y_pred, labels=["HIGH_RISK", "MONITORING", "LOW_RISK"]))

    MODELS_DIR.mkdir(exist_ok=True)
    bundle = {"classifier": clf, "tfidf": tfidf, "label_map": label_map}
    joblib.dump(bundle, MODELS_DIR / "nlp_pipeline.joblib")
    print(f"\nModelo salvo em {MODELS_DIR}/nlp_pipeline.joblib")


def train_models(df: "pd.DataFrame") -> tuple:
    """
    Treina o pipeline NLP completo sobre um DataFrame arbitrário.
    Espera as colunas 'text_pt' (ou 'text') e 'label'.
    Salva os artefatos em MODELS_DIR e retorna (bundle, lda, dictionary).
    Chamado programaticamente pelo endpoint /admin/retrain.
    """
    label_col = "label" if "label" in df.columns else df.columns[-1]
    text_col = "text_pt" if "text_pt" in df.columns else "text"

    label_map = _infer_label_map(df[label_col])
    df = df.copy().rename(columns={text_col: "text_pt"})
    df["risk_label"] = df[label_col].map(label_map)
    df = df.dropna(subset=["risk_label", "text_pt"])

    tokenized = [preprocess(str(t)) for t in df["text_pt"]]
    lda, dictionary, _ = train_lda(tokenized)
    save_lda(lda, dictionary)

    X, tfidf = build_feature_matrix(df, lda, dictionary)
    y = df["risk_label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    clf = LogisticRegression(
        max_iter=2000, class_weight="balanced", solver="lbfgs", random_state=42, C=1.0
    )
    clf.fit(X_train, y_train)

    MODELS_DIR.mkdir(exist_ok=True)
    bundle = {"classifier": clf, "tfidf": tfidf, "label_map": label_map}
    joblib.dump(bundle, MODELS_DIR / "nlp_pipeline.joblib")

    return bundle, lda, dictionary


if __name__ == "__main__":
    main()
