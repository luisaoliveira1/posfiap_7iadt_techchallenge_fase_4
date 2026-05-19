from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.config import Settings, get_settings
from src.services import review_store

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


class ReviewDecision(BaseModel):
    """
    Decisão clínica sobre um resultado de análise realizada.
    """
    decision: Literal["confirmed", "overridden"]
    label: Optional[Literal["HIGH_RISK", "MONITORING", "LOW_RISK"]] = None
    note: str = ""


@router.post("/{job_id}/decide")
def decide(
    job_id: str,
    body: ReviewDecision,
    settings: Settings = Depends(get_settings),
):
    """
    Registra a decisão de um clínico sobre um caso específico de análise.

    O job_id identifica o resultado gerado pelo pipeline de áudio/texto.
    Se a decisão for "overridden", o label corrigido é obrigatório e será usado
    como dado de treinamento supervisionado no próximo ciclo de retreinamento do modelo.
    Retorna 404 se o job_id não for encontrado na fila de revisão.
    """
    if body.decision == "overridden" and not body.label:
        raise HTTPException(status_code=422, detail="label é obrigatório quando a decisão é 'overridden'")
    record = review_store.submit_decision(
        job_id=job_id,
        decision=body.decision,
        label=body.label or "",
        note=body.note,
        conn_str=settings.azure_blob_connection_string,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Revisão não encontrada")
    return record
