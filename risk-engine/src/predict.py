import threading
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.schema import FEATURE_COLUMNS, LABELS, RISK_LEVEL_DISPLAY

MODELS_DIR = Path("models")

_lock = threading.Lock()
_bundle = None


def _load_model():
    global _bundle
    with _lock:
        if _bundle is not None:
            return
        from src.blob_store import pull_model
        pull_model(MODELS_DIR)
        _bundle = joblib.load(MODELS_DIR / "risk_model.joblib")


def reload_model(bundle) -> None:
    """Substitui o modelo recém-treinado sem reiniciar o processo."""
    global _bundle
    with _lock:
        _bundle = bundle


def predict_risk(labels: list[dict]) -> dict:
    """
    labels: [{"Name": "HIGH_RISK", "Score": 0.85}, ...]
    Retorna: riskLevel, confidence, probabilities, humanReviewRequired, topSignals
    """
    _load_model()

    with _lock:
        bundle = _bundle

    score_map = {item["Name"]: item["Score"] for item in labels}
    feature_row = {col: score_map.get(col.replace("_score", ""), 0.0) for col in FEATURE_COLUMNS}
    X = pd.DataFrame([feature_row])[FEATURE_COLUMNS].values

    pipe = bundle["pipeline"]
    class_names = bundle["class_names"]

    risk_level = pipe.predict(X)[0]
    proba = pipe.predict_proba(X)[0]
    confidence = float(np.max(proba))

    probabilities = {cls: float(p) for cls, p in zip(class_names, proba)}

    if risk_level == "HIGH_RISK":
        human_review = True
    elif risk_level == "MONITORING":
        human_review = confidence < 0.75
    else:
        human_review = confidence < 0.55

    top_signals = sorted(
        [{"label": name, "score": score} for name, score in score_map.items()],
        key=lambda x: x["score"],
        reverse=True,
    )[:5]

    return {
        "riskLevel": risk_level,
        "riskLevelDisplay": RISK_LEVEL_DISPLAY.get(risk_level, risk_level),
        "confidence": confidence,
        "probabilities": probabilities,
        "humanReviewRequired": human_review,
        "topSignals": top_signals,
        "features": feature_row,
    }
