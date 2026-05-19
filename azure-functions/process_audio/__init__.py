"""
Azure Function: process_audio
Gatilho: Event Grid — dispara quando um novo arquivo aparece no container audio-uploads.
Ação: Baixa o áudio, transcreve via Azure AI Speech (pt-BR), grava o JSON da transcrição
      no container transcripts.
"""

import json
import logging
import os
import tempfile

import azure.cognitiveservices.speech as speechsdk
import azure.functions as func
from azure.storage.blob import BlobServiceClient


def main(event: func.EventGridEvent) -> None:
    data = event.get_json()
    blob_url: str = data.get("url", "")

    if "audio-uploads" not in blob_url:
        logging.info("Não é um blob de audio-uploads — ignorando.")
        return

    blob_name = blob_url.split("/audio-uploads/")[-1]
    logging.info(f"Processando blob de áudio: {blob_name}")

    conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    speech_key = os.environ["AZURE_SPEECH_KEY"]
    speech_region = os.environ["AZURE_SPEECH_REGION"]

    blob_svc = BlobServiceClient.from_connection_string(conn_str)

    # Baixar áudio
    audio_data = (
        blob_svc.get_blob_client("audio-uploads", blob_name)
        .download_blob()
        .readall()
    )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    # Transcrever (pt-BR)
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = "pt-BR"
    audio_config = speechsdk.AudioConfig(filename=tmp_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        transcript_text = result.text
    else:
        logging.warning(f"Reconhecimento de fala falhou: {result.reason}")
        transcript_text = ""

    # Gravar JSON da transcrição no container 'transcripts'
    transcript_blob_name = blob_name.rsplit(".", 1)[0] + ".json"
    transcript_payload = json.dumps(
        {
            "original_audio": blob_name,
            "transcript": transcript_text,
            "language": "pt-BR",
        },
        ensure_ascii=False,
    ).encode("utf-8")

    blob_svc.get_blob_client("transcripts", transcript_blob_name).upload_blob(
        transcript_payload, overwrite=True
    )

    logging.info(f"Transcrição gravada: {transcript_blob_name}  ({len(transcript_text)} caracteres)")
