"""
Tradução do dataset de inglês para português usando Google Translate.
"""

import json
import time
from pathlib import Path

import pandas as pd
from deep_translator import GoogleTranslator

RAW_CSV = Path("data/raw/postpartum_depression.csv")
PROCESSED_DIR = Path("data/processed")
TRANSLATED_CSV = PROCESSED_DIR / "translated.csv"
CACHE_FILE = PROCESSED_DIR / "translation_cache.json"

CHAR_LIMIT = 4999
BATCH_DELAY_SECONDS = 0.3


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def translate_dataset(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    cache = _load_cache()
    translator = GoogleTranslator(source="en", target="pt")

    unique_texts = [t for t in df[text_col].unique() if t not in cache]
    print(f"Unique texts to translate: {len(unique_texts)} (cache hits: {len(df[text_col].unique()) - len(unique_texts)})")

    for i, text in enumerate(unique_texts, 1):
        truncated = text[:CHAR_LIMIT]
        try:
            cache[text] = translator.translate(truncated)
        except Exception as exc:
            print(f"  [WARN] Translation failed for text #{i}: {exc}. Keeping original.")
            cache[text] = truncated
        if i % 50 == 0:
            _save_cache(cache)
            print(f"  Translated {i}/{len(unique_texts)}...")
        time.sleep(BATCH_DELAY_SECONDS)

    _save_cache(cache)
    df["text_pt"] = df[text_col].map(cache)
    return df


if __name__ == "__main__":
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"{RAW_CSV} not found.\n"
            "Download the dataset from:\n"
            "  https://www.kaggle.com/datasets/parvezalmuqtadir2348/postpartum-depression/data\n"
            "and place the CSV at nlp-model/data/raw/postpartum_depression.csv"
        )

    print(f"Loading {RAW_CSV}...")
    df = pd.read_csv(RAW_CSV)
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Label distribution:\n{df.iloc[:, -1].value_counts()}")

    df = translate_dataset(df)
    df.to_csv(TRANSLATED_CSV, index=False)
    print(f"\nTranslated dataset saved to {TRANSLATED_CSV}")
