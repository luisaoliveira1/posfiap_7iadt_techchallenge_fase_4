import threading
from pathlib import Path

import joblib
import numpy as np
import scipy.sparse as sp

from src.clinical_flags import HIGH_RISK_PHRASES as _HIGH_RISK_PHRASES
from src.clinical_flags import extract_flags
from src.lda_model import get_topic_features, load_lda
from src.preprocess import preprocess, preprocess_for_tfidf

MODELS_DIR = Path("models")

_lock = threading.Lock()
_bundle = None
_lda = None
_dictionary = None


def _load_models():
    global _bundle, _lda, _dictionary
    with _lock:
        if _bundle is not None:
            return
        from src.blob_store import pull_models
        pull_models(MODELS_DIR)  # baixa a versão mais recente do blob se configurado; no-op localmente
        _bundle = joblib.load(MODELS_DIR / "nlp_pipeline.joblib")
        _lda, _dictionary = load_lda()


def reload_models(bundle, lda, dictionary) -> None:
    global _bundle, _lda, _dictionary
    with _lock:
        _bundle = bundle
        _lda = lda
        _dictionary = dictionary


def predict_from_text(text: str) -> dict:
    _load_models()

    with _lock:
        bundle = _bundle
        lda = _lda
        dictionary = _dictionary

    tokens = preprocess(text)
    tfidf_vec = bundle["tfidf"].transform([preprocess_for_tfidf(text)])
    lda_vec = np.array([get_topic_features(tokens, lda, dictionary)])
    X = sp.hstack([tfidf_vec, sp.csr_matrix(lda_vec)])

    clf = bundle["classifier"]
    risk_level = clf.predict(X)[0]
    proba = clf.predict_proba(X)[0]
    classes = list(clf.classes_)
    prob_map = {cls: float(p) for cls, p in zip(classes, proba)}

    flags = extract_flags(text)
    high_risk_flags = int(flags[:len(_HIGH_RISK_PHRASES)].sum() / 5.0)
    if high_risk_flags > 0:
        if risk_level == "LOW_RISK":
            risk_level = "MONITORING" if prob_map.get("HIGH_RISK", 0) < 0.25 else "HIGH_RISK"
        elif risk_level == "MONITORING" and prob_map.get("HIGH_RISK", 0) >= 0.25:
            risk_level = "HIGH_RISK"

    label_scores = [
        {"Name": cls, "Score": float(prob)}
        for cls, prob in zip(classes, proba)
    ]

    return {
        "risk_level": risk_level,
        "confidence": float(max(proba)),
        "label_scores": label_scores,
        "probabilities": prob_map,
        "clinical_flags_fired": high_risk_flags,
    }
