from typing import Literal

from pydantic import BaseModel


class AnalysisResult(BaseModel):
    job_id: str
    transcript: str
    risk_level: str
    risk_level_display: str
    confidence: float
    human_review_required: bool
    probabilities: dict[str, float]
    top_signals: list[dict]
    features: dict[str, float]


class TextAnalysisRequest(BaseModel):
    text: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    stt_backend: str
