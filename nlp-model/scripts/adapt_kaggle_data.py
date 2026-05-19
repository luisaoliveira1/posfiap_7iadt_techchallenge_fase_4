"""
Converts the Kaggle 'post natal data.csv' (questionnaire format) into the
text + label format expected by src/translate.py and src/train.py.

Run: python -m scripts.adapt_kaggle_data  (from nlp-model/ directory)
     OR specify the source CSV path as the first argument.
"""

import csv
import sys
from pathlib import Path

KAGGLE_CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    Path.home() / ".cache/kagglehub/datasets/parvezalmuqtadir2348"
    "/postpartum-depression/versions/1/post natal data.csv"
)
OUT_CSV = Path("data/raw/postpartum_depression.csv")

SYMPTOM_COLS = [
    "Feeling sad or Tearful",
    "Irritable towards baby & partner",
    "Trouble sleeping at night",
    "Problems concentrating or making decision",
    "Overeating or loss of appetite",
    "Feeling anxious",
    "Feeling of guilt",
    "Problems of bonding with baby",
]

# Values that count as a positive (symptomatic) response
POSITIVE_VALUES = {"yes", "sometimes", "maybe", "often", "two or more days a week"}


def _is_positive(value: str) -> bool:
    return value.strip().lower() in POSITIVE_VALUES


def _row_to_text(row: dict) -> str:
    parts = []
    for col in SYMPTOM_COLS:
        val = row.get(col, "").strip() or "no"
        parts.append(f"{col.lower()}: {val.lower()}")
    suicide = row.get("Suicide attempt", "").strip() or "no"
    parts.append(f"suicide attempt: {suicide.lower()}")
    return ". ".join(parts) + "."


def _derive_label(row: dict) -> str:
    # Suicide attempt = Yes is always HIGH_RISK
    if row.get("Suicide attempt", "").strip().lower() == "yes":
        return "HIGH_RISK"

    positive_count = sum(_is_positive(row.get(col, "")) for col in SYMPTOM_COLS)

    # Thresholds chosen so each class has meaningful sample counts:
    # 0-3 symptoms → LOW_RISK (~274 rows)
    # 4-6 symptoms → MONITORING (~1089 rows)
    # 7-8 symptoms → HIGH_RISK (~140 rows, plus suicide=Yes above)
    if positive_count >= 7:
        return "HIGH_RISK"
    elif positive_count >= 4:
        return "MONITORING"
    else:
        return "LOW_RISK"


def main() -> None:
    if not KAGGLE_CSV.exists():
        print(f"ERROR: Source CSV not found at {KAGGLE_CSV}")
        print("Download via: python3 -c \"import kagglehub; kagglehub.dataset_download('parvezalmuqtadir2348/postpartum-depression')\"")
        sys.exit(1)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    counts = {"HIGH_RISK": 0, "MONITORING": 0, "LOW_RISK": 0}
    rows_written = 0

    with open(KAGGLE_CSV, encoding="utf-8") as fin, open(OUT_CSV, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=["text", "label"])
        writer.writeheader()

        for row in reader:
            text = _row_to_text(row)
            label = _derive_label(row)
            writer.writerow({"text": text, "label": label})
            counts[label] += 1
            rows_written += 1

    print(f"Written {rows_written} rows to {OUT_CSV}")
    print(f"Label distribution: {counts}")


if __name__ == "__main__":
    main()
