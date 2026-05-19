from fastapi import APIRouter, Depends

from src.config import Settings, get_settings
from src.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)):
    """
    Verifica se o serviço de backend está funcionando
    e qual o backend está sendo utilizado para transcrição de áudio (STT).
    """
    from src.routers.audio import _effective_backend
    return HealthResponse(
        status="ok",
        service="backend",
        stt_backend=_effective_backend(settings),
    )
