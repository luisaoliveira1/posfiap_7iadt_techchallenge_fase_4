"""
Azure Function: trigger_retrain
Gatilho: Event Grid — dispara quando o Azure ML exporta um CSV rotulado para o container labeled-data.
Ação:
  1. Baixar a exportação rotulada (CSV com colunas text_pt e label).
  2. Mescla com o CSV de treinamento acumulado em 'training-data/translated.csv'.
  3. Faz upload do CSV com a nova data de treinamento.
  4. Envia (via POST) ao endpoint /admin/retrain do modelo NLP.
     O modelo NLP retreina, gera novos dados de risco e propaga ao motor de risco.

Formato esperado da exportação do Azure ML Data Labeling:
  CSV com no mínimo duas colunas: text_pt (ou text) e label
  os valores de label devem ser HIGH_RISK, MONITORING ou LOW_RISK
"""

import io
import json
import logging
import os

import azure.functions as func
import httpx
import pandas as pd
from azure.storage.blob import BlobServiceClient


def main(event: func.EventGridEvent) -> None:
    data = event.get_json()
    blob_url: str = data.get("url", "")

    if "labeled-data" not in blob_url or not blob_url.endswith(".csv"):
        logging.info("Não é um CSV de labeled-data — ignorando.")
        return

    blob_name = blob_url.split("/labeled-data/")[-1]
    logging.info(f"Processando exportação rotulada: {blob_name}")

    conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    nlp_url = os.environ["NLP_MODEL_URL"]
    retrain_secret = os.environ.get("RETRAIN_SECRET", "")

    blob_svc = BlobServiceClient.from_connection_string(conn_str)

    labeled_bytes = blob_svc.get_blob_client("labeled-data", blob_name).download_blob().readall()
    new_df = pd.read_csv(io.BytesIO(labeled_bytes))

    # Formato do Azure ML Data Labeling: colunas Url e Label
    if "Url" in new_df.columns and "Label" in new_df.columns:
        logging.info("Detectado formato Azure ML Data Labeling — convertendo para text_pt/label.")
        rows = []
        for _, row in new_df.iterrows():
            # AmlDatastore://review_queue/texts/<uuid>.txt → texts/<uuid>.txt
            blob_path = row["Url"].split("://")[-1].split("/", 1)[-1]
            try:
                text = blob_svc.get_blob_client("review-queue", blob_path).download_blob().readall().decode("utf-8").strip()
                rows.append({"text_pt": text, "label": row["Label"]})
            except Exception as exc:
                logging.warning(f"Não foi possível ler {blob_path}: {exc}")
        new_df = pd.DataFrame(rows, columns=["text_pt", "label"])

    # Normalização de nomes das colunas
    if "text" in new_df.columns and "text_pt" not in new_df.columns:
        new_df = new_df.rename(columns={"text": "text_pt"})
    if "Label" in new_df.columns and "label" not in new_df.columns:
        new_df = new_df.rename(columns={"Label": "label"})

    required = {"text_pt", "label"}
    if not required.issubset(new_df.columns):
        logging.error(f"Exportação rotulada sem colunas obrigatórias. Encontradas: {list(new_df.columns)}")
        return

    new_df = new_df[["text_pt", "label"]].dropna()
    valid_labels = {"HIGH_RISK", "MONITORING", "LOW_RISK"}
    new_df = new_df[new_df["label"].isin(valid_labels)]
    new_df = new_df[new_df["text_pt"].str.split().str.len() >= 5]
    logging.info(f"Novas linhas rotuladas: {len(new_df)}  distribuição: {new_df['label'].value_counts().to_dict() if not new_df.empty else {}}")

    if new_df.empty:
        logging.warning("Nenhuma linha rotulada válida após filtragem — abortando retreinamento.")
        return

    try:
        existing_bytes = blob_svc.get_blob_client("training-data", "translated.csv").download_blob().readall()
        existing_df = pd.read_csv(io.BytesIO(existing_bytes))
        if "text" in existing_df.columns and "text_pt" not in existing_df.columns:
            existing_df = existing_df.rename(columns={"text": "text_pt"})
        merged_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=["text_pt"])
    except Exception:
        # Ainda não há dados de treinamento — iniciar com a exportação rotulada
        merged_df = new_df

    logging.info(f"Conjunto de treinamento mesclado: {len(merged_df)} linhas")

    merged_csv = merged_df.to_csv(index=False).encode("utf-8")
    blob_svc.get_blob_client("training-data", "translated.csv").upload_blob(merged_csv, overwrite=True)
    logging.info("training-data/translated.csv atualizado no blob.")

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{nlp_url}/admin/retrain",
                headers={"Authorization": f"Bearer {retrain_secret}"},
            )
            resp.raise_for_status()
        logging.info(f"Retreinamento do modelo NLP disparado: {resp.json()}")
    except Exception as exc:
        logging.error(f"Falha ao disparar retreinamento do modelo NLP: {exc}")
