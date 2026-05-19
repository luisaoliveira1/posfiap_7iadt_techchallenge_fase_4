"""
Gera áudio WAV a partir de arquivos .txt de cenários usando Microsoft Edge TTS (gratuito, sem chave de API).
"""

import asyncio
import re
import subprocess
import sys
from pathlib import Path

import edge_tts

SCENARIOS_DIR = Path(__file__).parent / "scenarios"

HELD_OUT_STEMS = {
    "scenario_01_high_risk_ideacao",
    "scenario_03_monitoring_moderado",
    "scenario_05_low_risk",
    "scenario_06_high_risk_psicose",
    "scenario_09_monitoring_pensamentos_intrusivos",
    "scenario_12_low_risk_choro_de_alegria",
    "scenario_23_high_risk_test_dissociacao",
    "scenario_24_monitoring_test_conflito_casal",
    "scenario_25_low_risk_test_autocuidado",
    "scenario_32_high_risk_test_negacao",
    "scenario_33_high_risk_test_exaustao_total",
    "scenario_34_monitoring_test_choro_sem_motivo",
    "scenario_35_monitoring_test_ansiedade_noturna",
    "scenario_36_low_risk_test_adaptacao_identidade",
    "scenario_37_low_risk_test_cansaco_normal",
}

VOICES = {
    "francesca": "pt-BR-FranciscaNeural",
    "thalita":   "pt-BR-ThalitaMultilingualNeural",
    "antonio":   "pt-BR-AntonioNeural",
}
DEFAULT_VOICE = "pt-BR-FranciscaNeural"

RATE_BY_CLASS = {
    "high_risk":  "-15%",
    "monitoring": "-5%",
    "low_risk":   "+5%",
}


def _clean_text(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _rate_for(stem: str) -> str:
    stem = stem.lower()
    for key, rate in RATE_BY_CLASS.items():
        if key in stem:
            return rate
    return "0%"


async def _synthesise(text: str, voice: str, rate: str, out_wav: Path) -> None:
    if out_wav.exists():
        print(f"  ignorado  {out_wav.name}")
        return

    tmp_audio = out_wav.with_suffix(".tmp")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(tmp_audio))

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp_audio), "-ar", "16000", "-ac", "1", str(out_wav)],
            check=True, capture_output=True,
        )
        if tmp_audio.exists():
            tmp_audio.unlink()
        print(f"  concluído  {out_wav.name}  (voz={voice}, velocidade={rate})")
    except FileNotFoundError:
        if tmp_audio.exists():
            tmp_audio.rename(out_wav)
        print(f"  concluído  {out_wav.name}  (ffmpeg não encontrado, arquivo pode não ser WAV válido)")
    except subprocess.CalledProcessError:
        if tmp_audio.exists():
            tmp_audio.rename(out_wav)
            print(f"  concluído  {out_wav.name}  (erro no ffmpeg, arquivo pode não ser WAV válido)")
        else:
            print(f"  FALHA  {out_wav.name}  (erro no ffmpeg, sem arquivo de fallback)")


async def generate_single(txt_path: Path, voice: str) -> None:
    text = _clean_text(txt_path.read_text(encoding="utf-8"))
    rate = _rate_for(txt_path.stem)
    out_wav = txt_path.with_suffix(".wav")
    await _synthesise(text, voice, rate, out_wav)


async def generate_multi_voice(txt_path: Path) -> None:
    if txt_path.stem in HELD_OUT_STEMS:
        print(f"  ignorado  {txt_path.stem}  (cenário de teste held-out, mantendo WAV original)")
        return

    text = _clean_text(txt_path.read_text(encoding="utf-8"))
    rate = _rate_for(txt_path.stem)

    for alias, voice in VOICES.items():
        out_wav = SCENARIOS_DIR / f"{txt_path.stem}_{alias}.wav"
        await _synthesise(text, voice, rate, out_wav)


async def main(paths: list[Path], multi_voice: bool, voice: str) -> None:
    for p in paths:
        if multi_voice:
            await generate_multi_voice(p)
        else:
            await generate_single(p, voice)


if __name__ == "__main__":
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]

    multi_voice = "--multi-voice" in flags
    voice_flag  = next((f for f in flags if f.startswith("--voice=")), None)
    voice = voice_flag.split("=", 1)[1] if voice_flag else DEFAULT_VOICE

    paths = [Path(a) for a in args] if args else sorted(SCENARIOS_DIR.glob("*.txt"))

    if not paths:
        print(f"Nenhum arquivo .txt encontrado em {SCENARIOS_DIR}")
        sys.exit(1)

    mode = "multi-voz (apenas cenários de treino)" if multi_voice else f"voz única ({voice})"
    print(f"Gerando {len(paths)} cenário(s) — {mode}")
    asyncio.run(main(paths, multi_voice, voice))
    print("Concluído.")
