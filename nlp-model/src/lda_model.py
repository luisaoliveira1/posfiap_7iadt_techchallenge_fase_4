"""
Wrapper Gensim LDA para extração de distribuições de tópicos latentes em
conversas sobre depressão pós-parto.
"""

from pathlib import Path

from gensim import corpora
from gensim import models as gensim_models

NUM_TOPICS = 10
MODELS_DIR = Path("models")


def train_lda(tokenized_docs: list[list[str]]) -> tuple:
    """
    Treina o modelo LDA e retorna (lda, dictionary, corpus).
    filter_extremes remove tokens que aparecem em menos de 3 documentos ou em mais de 85% deles.
    """
    dictionary = corpora.Dictionary(tokenized_docs)
    dictionary.filter_extremes(no_below=3, no_above=0.85)
    corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]

    lda = gensim_models.LdaModel(
        corpus,
        id2word=dictionary,
        num_topics=NUM_TOPICS,
        passes=15,
        random_state=42,
        alpha="auto",
        eta="auto",
    )
    return lda, dictionary, corpus


def get_topic_features(tokens: list[str], lda, dictionary) -> list[float]:
    bow = dictionary.doc2bow(tokens)
    topic_dist = lda.get_document_topics(bow, minimum_probability=0.0)
    return [prob for _, prob in sorted(topic_dist, key=lambda x: x[0])]


def save_lda(lda, dictionary) -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    lda.save(str(MODELS_DIR / "lda_model.gensim"))
    dictionary.save(str(MODELS_DIR / "lda_dictionary.gensim"))
    print(f"Modelo LDA salvo em {MODELS_DIR}/")


def load_lda() -> tuple:
    lda = gensim_models.LdaModel.load(str(MODELS_DIR / "lda_model.gensim"))
    dictionary = corpora.Dictionary.load(str(MODELS_DIR / "lda_dictionary.gensim"))
    return lda, dictionary
