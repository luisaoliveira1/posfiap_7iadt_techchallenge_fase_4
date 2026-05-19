import io
import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.predict import MODELS_DIR, _load_model, predict_risk, reload_model

logger = logging.getLogger(__name__)

_retrain_state = {"running": False, "last_error": None, "last_success": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    yield


app = FastAPI(
    title="PPD Risk Engine",
    description="Classificador de risco de depressão pós-parto",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LabelScore(BaseModel):
    Name: str
    Score: Annotated[float, Field(ge=0.0, le=1.0)]


class RiskRequest(BaseModel):
    Labels: list[LabelScore]


@app.post("/risk")
def risk(req: RiskRequest):
    labels = [{"Name": l.Name, "Score": l.Score} for l in req.Labels]
    return predict_risk(labels)


@app.get("/health")
def health():
    return {"status": "ok", "service": "risk-engine"}


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
        raise HTTPException(status_code=403, detail="Acesso negado")
    if _retrain_state["running"]:
        raise HTTPException(status_code=409, detail="Retreinamento já em andamento")
    background_tasks.add_task(_retrain_task)
    return {"status": "accepted", "message": "Retreinamento do motor de risco iniciado em segundo plano"}


def _retrain_task() -> None:
    from datetime import datetime, timezone

    from src.blob_store import get_training_csv, push_model
    from src.train import DATA_CSV, train_risk_model

    _retrain_state["running"] = True
    _retrain_state["last_error"] = None
    try:
        csv_bytes = get_training_csv()
        if csv_bytes:
            df = pd.read_csv(io.BytesIO(csv_bytes))
            logger.info(f"Dados de treinamento do motor de risco carregados do blob: {len(df)} linhas")
        else:
            if not DATA_CSV.exists():
                raise FileNotFoundError("Nenhum dado de treinamento disponível (blob e arquivo local ausentes)")
            df = pd.read_csv(DATA_CSV)
            logger.info(f"Dados de treinamento do motor de risco carregados do arquivo local: {len(df)} linhas")

        bundle = train_risk_model(df)
        push_model(MODELS_DIR)
        reload_model(bundle)
        logger.info("Motor de risco retreinado e recarregado.")

        _retrain_state["last_success"] = datetime.now(timezone.utc).isoformat()

    except Exception as exc:
        logger.exception(f"Falha no retreinamento do motor de risco: {exc}")
        _retrain_state["last_error"] = str(exc)
    finally:
        _retrain_state["running"] = False
