"""
Wrapper para transcrição de áudio em português usando o modelo Whisper.
Lembrete: usar pip install faster-whisper
"""

import tempfile
from pathlib import Path

_model = None


def _load():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def transcribe_audio_whisper(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    model = _load()

    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    segments, _ = model.transcribe(tmp_path, language="pt", task="transcribe")
    return " ".join(seg.text for seg in segments).strip()
