"""
Azure Function: analyze_transcript
Trigger: Event Grid — disparado quando um novo JSON aparece no container de transcripts.
Ação: Chama o modelo NLP → engine risk → grava o JSON de resultado final no container 'results'.
      Se avaliação humana é retornada, grava o caso em 'review-queue' para rotulagem clínica no Azure ML.
"""

import csv
import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import azure.functions as func
import httpx
from azure.storage.blob import BlobServiceClient

CSV_BLOB = "labeling_input.csv"
CSV_FIELDS = ["case_id", "text_pt", "predicted_label"]


def _update_labeling_csv(case_id: str, text_pt: str, predicted_label: str, blob_svc: BlobServiceClient) -> None:
    container = blob_svc.get_container_client("review-queue")
    try:
        existing = container.get_blob_client(CSV_BLOB).download_blob().readall().decode("utf-8")
        reader = csv.DictReader(io.StringIO(existing))
        rows = [r for r in reader if r.get("case_id") != case_id]
    except Exception:
        rows = []

    rows.append({"case_id": case_id, "text_pt": text_pt, "predicted_label": predicted_label})

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    container.get_blob_client(CSV_BLOB).upload_blob(buf.getvalue().encode("utf-8"), overwrite=True)
    logging.info(f"labeling_input.csv atualizado — {len(rows)} casos.")


def _enqueue_human_review(result: dict, blob_svc: BlobServiceClient) -> None:
    case_id = result.get("original_audio", str(uuid.uuid4())).replace("/", "_")
    text_pt = result.get("transcript", "")
    predicted_label = result.get("riskLevel", "")

    payload = json.dumps(
        {
            "case_id": case_id,
            "text_pt": text_pt,
            "predicted_label": predicted_label,
            "confidence": result.get("confidence"),
            "probabilities": result.get("probabilities", {}),
            "review_status": "pending",
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        },
        ensure_ascii=False,
    ).encode("utf-8")

    blob_svc.get_blob_client("review-queue", f"{case_id}.json").upload_blob(payload, overwrite=True)
    logging.info(f"Caso enfileirado para revisão humana: {case_id}.json")

    blob_svc.get_blob_client("review-queue", f"texts/{case_id}.txt").upload_blob(
        text_pt.encode("utf-8"), overwrite=True
    )

    _update_labeling_csv(case_id, text_pt, predicted_label, blob_svc)


def main(event: func.EventGridEvent) -> None:
    data = event.get_json()
    blob_url: str = data.get("url", "")

    if "transcripts" not in blob_url or not blob_url.endswith(".json"):
        logging.info("Não é um blob de transcrição — ignorando.")
        return

    blob_name = blob_url.split("/transcripts/")[-1]
    logging.info(f"Analisando transcrição: {blob_name}")

    conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    nlp_url = os.environ["NLP_MODEL_URL"]
    risk_url = os.environ["RISK_ENGINE_URL"]

    blob_svc = BlobServiceClient.from_connection_string(conn_str)

    raw = blob_svc.get_blob_client("transcripts", blob_name).download_blob().readall()
    transcript_data = json.loads(raw.decode("utf-8"))
    transcript_text = transcript_data.get("transcript", "")

    if not transcript_text.strip():
        logging.warning(f"Transcrição vazia em {blob_name} — ignorando análise.")
        return

    with httpx.Client(timeout=30) as client:
        nlp_resp = client.post(f"{nlp_url}/predict", json={"text": transcript_text})
        nlp_resp.raise_for_status()
        nlp_result = nlp_resp.json()

        risk_resp = client.post(f"{risk_url}/risk", json={"Labels": nlp_result["label_scores"]})
        risk_resp.raise_for_status()
        risk_result = risk_resp.json()

    final = {**transcript_data, **nlp_result, **risk_result}

    result_blob_name = blob_name.replace(".json", "_result.json")
    blob_svc.get_blob_client("results", result_blob_name).upload_blob(
        json.dumps(final, ensure_ascii=False).encode("utf-8"), overwrite=True
    )
    logging.info(f"Resultado gravado: {result_blob_name}")

    if risk_result.get("humanReviewRequired"):
        _enqueue_human_review(final, blob_svc)
