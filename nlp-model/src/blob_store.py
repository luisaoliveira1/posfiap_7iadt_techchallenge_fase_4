"""
Helpers para subir no Azure Blob Storage arquivos de modelo e dados de treinamento.
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_CONN_STR = os.environ.get("AZURE_BLOB_CONNECTION_STRING", "")
_MODELS_CONTAINER = os.environ.get("MODELS_BLOB_CONTAINER", "models")
_TRAINING_CONTAINER = os.environ.get("TRAINING_DATA_CONTAINER", "training-data")

_LDA_ARTIFACT_NAMES = [
    "lda_model.gensim",
    "lda_model.gensim.expElogbeta.npy",
    "lda_model.gensim.id2word",
    "lda_model.gensim.state",
    "lda_dictionary.gensim",
]
_ALL_MODEL_BLOBS = ["nlp_pipeline.joblib"] + _LDA_ARTIFACT_NAMES


def _client():
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(_CONN_STR)


def pull_models(local_dir: Path) -> bool:
    """Baixa os artefatos mais recentes do modelo do blob para local_dir. Retorna True se encontrar algum."""
    if not _CONN_STR:
        return False
    # Se todos os artefatos já estão na imagem, ignora o download para evitar
    # sobrescrever um modelo compatível por um potencialmente incompatível.
    if all((local_dir / name).exists() for name in _ALL_MODEL_BLOBS):
        logger.info("Arquivos do modelo já presentes localmente; download do blob ignorado.")
        return True
    client = _client()
    found = False
    for name in _ALL_MODEL_BLOBS:
        try:
            data = client.get_blob_client(_MODELS_CONTAINER, f"nlp/{name}").download_blob().readall()
            local_dir.mkdir(parents=True, exist_ok=True)
            (local_dir / name).write_bytes(data)
            found = True
        except Exception:
            pass
    if found:
        logger.info("Arquivos do modelo NLP baixados do blob storage.")
    return found


def push_models(local_dir: Path) -> None:
    """Faz upload de todos os arquvos do modelo de local_dir para o blob."""
    if not _CONN_STR:
        return
    client = _client()
    for name in _ALL_MODEL_BLOBS:
        path = local_dir / name
        if path.exists():
            client.get_blob_client(_MODELS_CONTAINER, f"nlp/{name}").upload_blob(
                path.read_bytes(), overwrite=True
            )
    logger.info("Arquivos do modelo NLP enviados para o blob storage.")


def get_training_csv() -> bytes | None:
    """Baixa o CSV de treinamento (translated.csv) do blob."""
    if not _CONN_STR:
        return None
    try:
        return _client().get_blob_client(_TRAINING_CONTAINER, "translated.csv").download_blob().readall()
    except Exception as exc:
        logger.warning(f"Não foi possível baixar o CSV de treinamento: {exc}")
        return None


def put_risk_training_csv(data: bytes) -> None:
    """Faz upload do CSV de treinamento gerado para o risk engine no blob."""
    if not _CONN_STR:
        return
    _client().get_blob_client(_TRAINING_CONTAINER, "risk_train.csv").upload_blob(data, overwrite=True)
    logger.info("CSV de treinamento do risk engine enviado para o blob storage.")
