"""
Flags binárias (1=presente e 0=ausente) de frases clínicas adicionadas ao vetor de features TF-IDF + LDA.

A ordem importa — não reordenar sem retreinar o modelo.
"""

import re
import numpy as np

# Frases que indicam HIGH_RISK independentemente do contexto ao redor.
# Cobrem: ideação suicida (passiva/ativa), dano ao bebê, psicose, dissociação.
HIGH_RISK_PHRASES = [
    "não estar aqui",
    "não estivesse aqui",
    "melhor sem mim",
    "seria melhor sem mim",
    "estariam melhor sem mim",
    "quero desaparecer",
    "quero sumir",
    "não quero mais viver",
    "não quero viver",
    "vontade de morrer",
    "penso em morrer",
    "pensamentos suicidas",
    "me machucar",
    "machucar meu filho",
    "machucar o bebê",
    "fazer algo ruim",
    "ouço vozes",
    "vejo coisas",
    "ouço coisas",
    "perdendo a sanidade",
    "perco a sanidade",
    "saio do meu corpo",
    "saindo do meu corpo",
    "fora do meu corpo",
    "não me reconheço no espelho",
    "aperto meu braço",
    "abandonar o bebê",
    "pensamentos intrusivos",
    "imagem de machucar",
    "indo embora de dentro",
    # Ideação suicida passiva — indireta, mas clinicamente significativa
    "seria melhor para todo mundo",
    "seria melhor se eu",
    "melhor para todos se eu",
    "se eu simplesmente sumisse",
    "se eu desaparecesse",
    # Sinais de dissociação / despersonalização
    "não sou mais eu",
    "estou desaparecendo",
    "desaparecendo aos poucos",
    # Medo de automutilação / perda de controle
    "com medo de mim mesma",
    "com medo de mim mesmo",
    "medo de mim mesma",
    "medo de mim mesmo",
    "com medo de mim",
    # Pensamentos intrusivos sobre causar dano
    "pensamentos horríveis",
    "pensamento horrível",
    "imaginando coisas ruins",
    "coisas ruins acontecendo",
    "imagino coisas ruins",
]

# Frases que indicam MONITORING — dificuldades presentes, mas sem crise.
MONITORING_PHRASES = [
    "verificando se está respirando",
    "verifico se está respirando",
    "choro sem motivo",
    "choro sem razão",
    "não sou boa mãe",
    "não me sinto boa mãe",
    "não consigo relaxar",
    "me sinto culpada",
    "sentimento de culpa",
    "ansiedade constante",
    "dias bons e dias ruins",
]

ALL_PHRASES = HIGH_RISK_PHRASES + MONITORING_PHRASES


SCALE = 5.0


def extract_flags(text: str) -> np.ndarray:
    """Detecta frases clínicas no texto e retorna um vetor de features escalado por SCALE (padrão 5.0).
    Cada posição corresponde a uma frase de ALL_PHRASES: SCALE se presente, 0 caso contrário.
    O escalonamento garante que a regularização L2 não suprima essas features frente aos valores TF-IDF."""
    normalized = text.lower()
    return np.array([SCALE if phrase in normalized else 0 for phrase in ALL_PHRASES], dtype=np.float32)


def extract_flags_batch(texts) -> np.ndarray:
    return np.vstack([extract_flags(str(t)) for t in texts])
