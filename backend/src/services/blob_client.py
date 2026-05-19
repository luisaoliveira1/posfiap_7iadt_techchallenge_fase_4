import uuid
from pathlib import Path

from azure.storage.blob import BlobServiceClient

from src.config import get_settings


async def upload_audio(file_bytes: bytes, filename: str) -> str:
    settings = get_settings()
    blob_name = f"{uuid.uuid4()}_{filename}"
    client = BlobServiceClient.from_connection_string(settings.azure_blob_connection_string)
    blob = client.get_blob_client(settings.azure_blob_audio_container, blob_name)
    blob.upload_blob(file_bytes, overwrite=True)
    return blob_name
