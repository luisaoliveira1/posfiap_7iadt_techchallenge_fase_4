import io
import logging
import os
from contextlib import asynccontextmanager

import httpx
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.predict import MODELS_DIR, _load_models, predict_from_text, reload_models

logger = logging.getLogger(__name__)

_retrain_state = {"running": False, "last_error": None, "last_success": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_models()
    yield


app = FastAPI(
    title="PPD NLP Model",
    description="Post-partum depression NLP classifier (Portuguese)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: str


@app.post("/predict")
def predict(req: PredictRequest):
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="text cannot be empty")
    return predict_from_text(req.text)


@app.get("/health")
def health():
    return {"status": "ok", "service": "nlp-model"}


@app.get("/admin/retrain/status")
def retrain_status():
    return {
        "running": _retrain_state["running"],
        "last_success": _retrain_state["last_success"],
        "last_error": _retrain_state["last_error"],
    }


@app.post("/admin/retrain", status_code=202)
def retrain(background_tasks: BackgroundTasks, authorization: str = Header(default=None)):
    secret = os.environ.get("RETRAIN_SECRET", "")
    if secret and authorization != f"Bearer {secret}":
        raise HTTPException(status_code=403, detail="Forbidden")
    if _retrain_state["running"]:
        raise HTTPException(status_code=409, detail="Retraining already in progress")
    background_tasks.add_task(_retrain_task)
    return {"status": "accepted", "message": "Retraining started in background"}


def _retrain_task() -> None:
    from datetime import datetime, timezone

    from src.blob_store import get_training_csv, push_models, put_risk_training_csv
    from src.train import train_models

    _retrain_state["running"] = True
    _retrain_state["last_error"] = None
    try:
        csv_bytes = get_training_csv()
        if csv_bytes:
            df = pd.read_csv(io.BytesIO(csv_bytes))
            logger.info(f"Loaded training data from blob: {len(df)} rows")
        else:
            from src.train import TRANSLATED_CSV
            if not TRANSLATED_CSV.exists():
                raise FileNotFoundError("No training data available (blob and local both missing)")
            df = pd.read_csv(TRANSLATED_CSV)
            logger.info(f"Loaded training data from local file: {len(df)} rows")

        bundle, lda, dictionary = train_models(df)

        push_models(MODELS_DIR)
        reload_models(bundle, lda, dictionary)
        logger.info("NLP model retrained and hot-reloaded.")

        label_col = "label" if "label" in df.columns else df.columns[-1]
        text_col = "text_pt" if "text_pt" in df.columns else "text"
        rows = []
        for text in df[text_col].fillna(""):
            result = predict_from_text(str(text))
            prob = result["probabilities"]
            rows.append({
                "HIGH_RISK_score": prob.get("HIGH_RISK", 0.0),
                "MONITORING_score": prob.get("MONITORING", 0.0),
                "LOW_RISK_score": prob.get("LOW_RISK", 0.0),
                "risk_level": result["risk_level"],
            })
        risk_df = pd.DataFrame(rows)
        put_risk_training_csv(risk_df.to_csv(index=False).encode())
        logger.info(f"Generated {len(risk_df)} risk training rows.")

        # Retreinando risk-engine
        risk_url = os.environ.get("RISK_ENGINE_URL", "")
        retrain_secret = os.environ.get("RETRAIN_SECRET", "")
        if risk_url:
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(
                        f"{risk_url}/admin/retrain",
                        headers={"Authorization": f"Bearer {retrain_secret}"},
                    )
                    resp.raise_for_status()
                logger.info("Risk engine retrain triggered.")
            except Exception as exc:
                logger.error(f"Failed to trigger risk engine retrain: {exc}")

        _retrain_state["last_success"] = datetime.now(timezone.utc).isoformat()

    except Exception as exc:
        logger.exception(f"Retraining failed: {exc}")
        _retrain_state["last_error"] = str(exc)
    finally:
        _retrain_state["running"] = False
