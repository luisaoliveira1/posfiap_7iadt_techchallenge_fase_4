RISK_LEVELS = ["HIGH_RISK", "MONITORING", "LOW_RISK"]

RISK_LEVEL_LABELS = {
    "HIGH_RISK": "Alta chance de depressão pós-parto",
    "MONITORING": "Monitorar paciente",
    "LOW_RISK": "Baixo risco",
}

# Semantic signal names used as feature labels for the risk engine
DEPRESSION_SIGNALS = [
    "choro_frequente",
    "insonia_ou_hipersonia",
    "fadiga_extrema",
    "desinteresse_por_bebe",
    "pensamentos_negativos",
    "isolamento_social",
    "irritabilidade_ou_ansiedade",
    "dificuldade_de_concentracao",
    "mudancas_de_apetite",
    "sentimentos_de_culpa",
    "pensamentos_suicidas",
]
