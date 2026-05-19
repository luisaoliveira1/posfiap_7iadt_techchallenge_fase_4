"""
Função para upload dos arquivos de modelo e dados de treinamento do risk engine para o Azure Blob Storage, e download do modelo treinado para uso na predição.
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_CONN_STR = os.environ.get("AZURE_BLOB_CONNECTION_STRING", "")
_MODELS_CONTAINER = os.environ.get("MODELS_BLOB_CONTAINER", "models")
_TRAINING_CONTAINER = os.environ.get("TRAINING_DATA_CONTAINER", "training-data")


def _client():
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(_CONN_STR)


def pull_model(local_dir: Path) -> bool:
    """Baixa risk_model.joblib do blob. Retorna True se encontrado."""
    if not _CONN_STR:
        return False
    if (local_dir / "risk_model.joblib").exists():
        logger.info("Risk Engine já presente localmente; download do blob ignorado.")
        return True
    try:
        data = _client().get_blob_client(_MODELS_CONTAINER, "risk/risk_model.joblib").download_blob().readall()
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "risk_model.joblib").write_bytes(data)
        logger.info("Risk Engine baixado do blob storage.")
        return True
    except Exception:
        return False


def push_model(local_dir: Path) -> None:
    """Faz upload de risk_model.joblib para o blob."""
    if not _CONN_STR:
        return
    path = local_dir / "risk_model.joblib"
    if path.exists():
        _client().get_blob_client(_MODELS_CONTAINER, "risk/risk_model.joblib").upload_blob(
            path.read_bytes(), overwrite=True
        )
    logger.info("Risk Engine enviado para o blob storage.")


def get_training_csv() -> bytes | None:
    """Baixa o CSV de treinamento do risk engine"""
    if not _CONN_STR:
        return None
    try:
        return _client().get_blob_client(_TRAINING_CONTAINER, "risk_train.csv").download_blob().readall()
    except Exception as exc:
        logger.warning(f"Não foi possível baixar o CSV de treinamento do risk engine: {exc}")
        return None
