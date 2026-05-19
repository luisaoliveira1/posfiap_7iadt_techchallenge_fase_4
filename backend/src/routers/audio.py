import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.config import Settings, get_settings
from src.models.schemas import AnalysisResult, TextAnalysisRequest
from src.services import nlp_client, risk_client, review_store

router = APIRouter(prefix="/api/audio", tags=["audio"])


async def _run_pipeline(transcript: str, settings: Settings) -> AnalysisResult:
    try:
        nlp_result = await nlp_client.predict(transcript)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro no modelo NLP: {exc}")

    try:
        risk_result = await risk_client.predict(nlp_result["label_scores"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro no motor de risco: {exc}")

    risk_level = risk_result["riskLevel"]
    human_review = risk_result["humanReviewRequired"]

    # Salvaguarda clínica: se o modelo NLP detectou uma frase de ALTO RISCO,
    # o resultado final não pode ser BAIXO RISCO independentemente da calibração de probabilidade.
    clinical_flags = nlp_result.get("clinical_flags_fired", 0)
    if clinical_flags > 0:
        human_review = True
        if risk_level in ("LOW_RISK", "MONITORING"):
            probs = risk_result.get("probabilities", {})
            risk_level = "HIGH_RISK" if probs.get("HIGH_RISK", 0) >= 0.20 else "MONITORING"

    _DISPLAY = {"HIGH_RISK": "Alto Risco", "MONITORING": "Monitorar paciente", "LOW_RISK": "Baixo Risco"}

    result = AnalysisResult(
        job_id=str(uuid.uuid4()),
        transcript=transcript,
        risk_level=risk_level,
        risk_level_display=_DISPLAY.get(risk_level, risk_result["riskLevelDisplay"]),
        confidence=risk_result["confidence"],
        human_review_required=human_review,
        probabilities=risk_result["probabilities"],
        top_signals=risk_result["topSignals"],
        features=risk_result["features"],
    )

    # Enfileirar todos os resultados para que clínicos possam enviar feedback independente do nível de risco.
    review_store.enqueue(
        job_id=result.job_id,
        record=result.model_dump(),
        conn_str=settings.azure_blob_connection_string,
    )

    return result


def _effective_backend(settings: Settings) -> str:
    if settings.offline_mode:
        return "none"
    return settings.stt_backend.lower()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_audio(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    """
    Recebe um arquivo de áudio WAV e retorna uma análise de risco.

    Roteamento de STT (defina STT_BACKEND no .env):
    - "whisper" (padrão): modelo Whisper local, sem necessidade de conta Azure
    - "azure": Azure AI Speech SDK (pt-BR), requer AZURE_SPEECH_KEY
    - "none": rejeita áudio — use /analyze-text
    """
    backend = _effective_backend(settings)

    if backend == "none":
        raise HTTPException(
            status_code=400,
            detail="Upload de áudio desativado (STT_BACKEND=none). Use POST /api/audio/analyze-text.",
        )

    audio_bytes = await file.read()
    filename = file.filename or "audio.wav"

    # O áudio é processado em memória, liberando assim que é transcrito por segurança
    try:
        if backend == "whisper":
            from src.services.whisper_client import transcribe_audio_whisper
            transcript = transcribe_audio_whisper(audio_bytes, filename)
        else:
            from src.services.speech_client import transcribe_audio
            transcript = transcribe_audio(audio_bytes)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro na transcrição de fala ({backend}): {exc}")
    finally:
        del audio_bytes

    if not transcript.strip():
        raise HTTPException(status_code=422, detail="Nenhuma fala detectada no arquivo de áudio.")

    return await _run_pipeline(transcript, settings)


@router.post("/analyze-text", response_model=AnalysisResult)
async def analyze_text(
    req: TextAnalysisRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Recebe a transcrição.
    Utilizado para desenvolvimento local (OFFLINE_MODE=true) e para o pipeline da Azure Function
    onde a transcrição é feita externamente.
    """
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="O texto não pode estar vazio.")
    return await _run_pipeline(req.text, settings)
