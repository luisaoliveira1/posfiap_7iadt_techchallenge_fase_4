"""
Wrapper do Azure AI Speech SDK para transcrição de áudio em português.
"""

import tempfile
import threading

import azure.cognitiveservices.speech as speechsdk

from src.config import get_settings


def transcribe_audio(audio_bytes: bytes) -> str:
    settings = get_settings()

    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    speech_config.speech_recognition_language = "pt-BR"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        tmp_path = tmp.name

        audio_config = speechsdk.AudioConfig(filename=tmp_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        segments = []
        done = threading.Event()

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                segments.append(evt.result.text)

        def on_stopped(evt):
            done.set()

        recognizer.recognized.connect(on_recognized)
        recognizer.session_stopped.connect(on_stopped)
        recognizer.canceled.connect(on_stopped)

        recognizer.start_continuous_recognition()
        done.wait(timeout=240)
        recognizer.stop_continuous_recognition()

    transcript = " ".join(segments).strip()

    if not transcript:
        raise RuntimeError("No speech detected in audio file.")

    return transcript
