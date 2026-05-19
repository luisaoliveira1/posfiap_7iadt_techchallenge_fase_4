import re

import nltk
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer

nltk.download("stopwords", quiet=True)
nltk.download("rslp", quiet=True)

_STOPWORDS_PT = set(stopwords.words("portuguese"))
_STEMMER = RSLPStemmer()
_NON_ALPHA = re.compile(r"[^a-záàâãéêíóôõúüç\s]")


def preprocess(text: str) -> list[str]:
    """Tokenização, remoção de stopwords em português e aplicação do stemming RSLP."""
    text = text.lower()
    text = _NON_ALPHA.sub(" ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in _STOPWORDS_PT and len(t) > 2]
    tokens = [_STEMMER.stem(t) for t in tokens]
    return tokens


def preprocess_for_tfidf(text: str) -> str:
    return " ".join(preprocess(text))
