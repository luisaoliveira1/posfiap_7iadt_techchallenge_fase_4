"""
Review queue store backed by Azure Blob Storage.
Falls back to an in-memory dict when AZURE_BLOB_CONNECTION_STRING is unset (local dev).
Each review is a JSON blob in the 'review-queue' container.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_CONTAINER = "review-queue"

# In-memory fallback for local dev (no blob connection string)
_memory_store: dict[str, dict] = {}


def _blob_client(conn_str: str):
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(conn_str, connection_timeout=5, read_timeout=10)


def enqueue(job_id: str, record: dict, conn_str: str = "") -> None:
    payload = {**record, "review_status": "pending", "enqueued_at": datetime.now(timezone.utc).isoformat()}
    if conn_str:
        try:
            data = json.dumps(payload, ensure_ascii=False).encode()
            _blob_client(conn_str).get_blob_client(_CONTAINER, f"{job_id}.json").upload_blob(data, overwrite=True)
            logger.info(f"Review enqueued in blob: {job_id}")
            return
        except Exception as exc:
            logger.warning(f"Blob enqueue failed, using memory fallback: {exc}")
    _memory_store[job_id] = payload


def list_reviews(conn_str: str = "", status: Optional[str] = None) -> list[dict]:
    if conn_str:
        try:
            svc = _blob_client(conn_str)
            container = svc.get_container_client(_CONTAINER)
            results = []
            for blob in container.list_blobs():
                data = container.get_blob_client(blob.name).download_blob().readall()
                record = json.loads(data.decode())
                if status is None or record.get("review_status") == status:
                    results.append(record)
            return sorted(results, key=lambda r: r.get("enqueued_at", ""), reverse=True)
        except Exception as exc:
            logger.warning(f"Blob list failed, using memory fallback: {exc}")
    records = list(_memory_store.values())
    if status:
        records = [r for r in records if r.get("review_status") == status]
    return sorted(records, key=lambda r: r.get("enqueued_at", ""), reverse=True)


def get_review(job_id: str, conn_str: str = "") -> Optional[dict]:
    if conn_str:
        try:
            data = _blob_client(conn_str).get_blob_client(_CONTAINER, f"{job_id}.json").download_blob().readall()
            return json.loads(data.decode())
        except Exception:
            pass
    return _memory_store.get(job_id)


def submit_decision(job_id: str, decision: str, label: str, note: str, conn_str: str = "") -> Optional[dict]:
    record = get_review(job_id, conn_str)
    if record is None:
        return None
    record.update({
        "review_status": "reviewed",
        "reviewer_decision": decision,
        "reviewer_label": label,
        "reviewer_note": note,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    })
    if conn_str:
        try:
            data = json.dumps(record, ensure_ascii=False).encode()
            _blob_client(conn_str).get_blob_client(_CONTAINER, f"{job_id}.json").upload_blob(data, overwrite=True)
            return record
        except Exception as exc:
            logger.warning(f"Blob update failed, using memory fallback: {exc}")
    _memory_store[job_id] = record
    return record
