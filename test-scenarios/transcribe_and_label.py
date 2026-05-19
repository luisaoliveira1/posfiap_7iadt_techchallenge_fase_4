"""
Transcreve todos os arquivos WAV de cenários via backend em execução,
rotula-os pelo nome do arquivo e marca cada linha como treino ou teste.
"""

import csv
import sys
from pathlib import Path

import requests

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
CORPUS_CSV    = Path("nlp-model/data/raw/scenario_corpus.csv")
API_URL       = "http://localhost:8000/api/audio/analyze"

# Cenários reservados para avaliação — nunca usados no treinamento.
HELD_OUT_STEMS = {
    "scenario_01_high_risk_ideacao",
    "scenario_06_high_risk_psicose",
    "scenario_23_high_risk_test_dissociacao",
    "scenario_32_high_risk_test_negacao",
    "scenario_33_high_risk_test_exaustao_total",
    "scenario_03_monitoring_moderado",
    "scenario_09_monitoring_pensamentos_intrusivos",
    "scenario_24_monitoring_test_conflito_casal",
    "scenario_34_monitoring_test_choro_sem_motivo",
    "scenario_35_monitoring_test_ansiedade_noturna",
    "scenario_05_low_risk",
    "scenario_12_low_risk_choro_de_alegria",
    "scenario_25_low_risk_test_autocuidado",
    "scenario_36_low_risk_test_adaptacao_identidade",
    "scenario_37_low_risk_test_cansaco_normal",
}

VOICE_SUFFIXES = {"_francesca", "_thalita", "_antonio"}

LABEL_MAP = {
    "high_risk":  "HIGH_RISK",
    "monitoring": "MONITORING",
    "low_risk":   "LOW_RISK",
}


def _base_stem(stem: str) -> str:
    """Remove o sufixo de voz para obter o nome canônico do cenário."""
    for suffix in VOICE_SUFFIXES:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _infer_label(stem: str) -> str | None:
    for key, label in LABEL_MAP.items():
        if key in stem.lower():
            return label
    return None


def _infer_split(stem: str) -> str:
    return "test" if _base_stem(stem) in HELD_OUT_STEMS else "train"


def _transcribe(wav_path: Path) -> str:
    with open(wav_path, "rb") as f:
        r = requests.post(API_URL, files={"file": (wav_path.name, f, "audio/wav")}, timeout=120)
    r.raise_for_status()
    return r.json()["transcript"]


def main() -> None:
    wavs = sorted(SCENARIOS_DIR.glob("*.wav"))
    if not wavs:
        print(f"Nenhum arquivo WAV encontrado em {SCENARIOS_DIR}")
        sys.exit(1)

    existing: dict[str, dict] = {}
    if CORPUS_CSV.exists():
        with open(CORPUS_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing[row["source"]] = row

    rows: list[dict] = []
    for wav in wavs:
        stem  = wav.stem
        label = _infer_label(stem)
        split = _infer_split(stem)

        if label is None:
            print(f"  ignorado  {wav.name}  (não foi possível inferir o rótulo)")
            continue

        if wav.name in existing:
            # Manter linha existente mas atualizar a tag de split caso tenha mudado
            row = existing[wav.name]
            row["split"] = split
            rows.append(row)
            print(f"  mantido  {wav.name}  [{split}]")
            continue

        print(f"  transcrevendo  {wav.name}  → {label} [{split}] ... ", end="", flush=True)
        try:
            transcript = _transcribe(wav)
            rows.append({"text": transcript, "label": label, "split": split, "source": wav.name})
            print(f"concluído ({len(transcript.split())} palavras)")
        except Exception as e:
            print(f"ERRO: {e}")

    if not rows:
        print("Nada para gravar.")
        return

    CORPUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "split", "source"])
        writer.writeheader()
        writer.writerows(rows)

    train = [r for r in rows if r["split"] == "train"]
    test  = [r for r in rows if r["split"] == "test"]

    print(f"\nCorpus gravado em {CORPUS_CSV}")
    print(f"  treino: {len(train)} amostras  {_dist(train)}")
    print(f"  teste:  {len(test)} amostras   {_dist(test)}")


def _dist(rows: list[dict]) -> str:
    d: dict[str, int] = {}
    for r in rows:
        d[r["label"]] = d.get(r["label"], 0) + 1
    return str(d)


if __name__ == "__main__":
    main()
