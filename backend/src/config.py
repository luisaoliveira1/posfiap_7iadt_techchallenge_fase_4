from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    azure_speech_key: str = ""
    azure_speech_region: str = "brazilsouth"
    azure_blob_connection_string: str = ""
    azure_blob_audio_container: str = "audio-uploads"
    azure_blob_transcript_container: str = "transcripts"
    azure_blob_results_container: str = "results"
    nlp_model_url: str = "http://nlp-model:8001"
    risk_engine_url: str = "http://risk-engine:8002"
    # STT backend: "azure" | "whisper" | "none"
    # - "azure": Azure AI Speech SDK (requer AZURE_SPEECH_KEY)
    # - "whisper": Modelo OpenAI Whisper usado localmente
    # - "none": não aceita uploads de áudio, use /analyze-text para enviar o texto diretamente
    stt_backend: str = "whisper"

    offline_mode: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
