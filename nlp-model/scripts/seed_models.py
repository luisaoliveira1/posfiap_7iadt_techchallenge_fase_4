"""
Gera dados sintéticos de treinamento para depressão pós-parto e treina ambos os modelos localmente SEM o dataset do Kaggle.

Execução: make seed
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_HIGH_RISK = [
    "não consigo dormir estou com pensamentos ruins quero desaparecer me sinto um fracasso não sinto nada pelo meu filho estou com medo de mim mesma",
    "pensamentos suicidas não quero mais estar aqui não consigo cuidar do bebê choro todo dia sem parar estou muito mal doutora",
    "não me levanto da cama não como não tomo banho não sinto amor pelo meu filho me sinto horrível culpada fracasso total",
    "quero sumir acho que eles estariam melhor sem mim não durmo olho para o teto sem conseguir dormir estou desaparecendo",
    "não sinto nada é como se estivesse morta por dentro não me reconheço mais tenho medo de fazer algo ruim",
    "choro sem parar não sei por quê estou exausta emocionalmente não consigo sentir amor não consigo me conectar com o bebê",
    "pensamentos negativos o tempo todo me sinto inútil incompetente nunca deveria ter sido mãe não tenho forças para nada",
    "me sinto presa num buraco escuro sem saída não vejo perspectiva de melhora não quero mais viver assim",
    "isolamento total não falo com ninguém não saio de casa me recuso a ver a família não tenho energia para nada absolutamente nada",
    "alucinações ouço coisas vejo coisas tenho pesadelos toda noite não durmo há dias estou perdendo a sanidade",
    "irritabilidade extrema grito com todos tenho raiva de tudo odeio a minha vida nesse momento não me reconheço",
    "fadiga extrema não consigo me mover da cama o bebê chora eu não consigo levantar me sinto paralisada",
    "desapego total do bebê não sinto que é meu filho parece estranho para mim não consigo amamentá-lo recuso",
    "choro quando vejo o bebê não de alegria de desespero não sei como cuidar dele tenho muito medo",
    "vontade de fugir deixar tudo para trás abandonar o bebê e o marido e simplesmente desaparecer para sempre",
]

_MONITORING = [
    "às vezes estou bem às vezes choro sem motivo fico ansiosa quando saio com o bebê durmo mal mas consigo me virar",
    "apetite estranho não como direito às vezes como demais fico irritada sem razão mas ainda funciono",
    "preocupação excessiva com o bebê fico verificando se está respirando toda hora muito ansiosa mas consigo cuidar dele",
    "choro esporádico sem motivo cansaço muito grande mas consigo amamentar e cuidar do bebê com dificuldade",
    "ansiedade pós-parto fico muito preocupada algo vai acontecer com ele não consigo relaxar mas não é grave",
    "dificuldade de concentração esquece as coisas fica muito distraída mas consegue fazer as tarefas do dia",
    "alterações de humor ora está bem ora está mal chora por coisas pequenas mas recupera rápido",
    "insônia leve dificuldade de dormir mesmo quando o bebê dorme muito cansada mas funcional",
    "sentimentos de culpa quando irrita com o bebê sente que não é boa mãe mas segue em frente",
    "isolamento parcial evita sair mas ainda mantém contato com marido e família próxima",
    "irritabilidade moderada fica nervosa fácil mas consegue se controlar não grita com os outros",
    "preocupação com aparência física não se sente bem com o corpo pós-parto mas aceita o processo",
    "dias bons e dias ruins alterna entre esperança e tristeza mas a tendência geral é de melhora",
    "apoio familiar presente mas sente que é peso para todos sentimento de culpa por precisar de ajuda",
    "medo de não ser boa mãe mas tenta todos os dias faz o que pode dentro das suas limitações atuais",
]

_LOW_RISK = [
    "estou bem cansada claro mas feliz consigo amamentar o bebê está saudável meu marido ajuda muito",
    "adaptação normal ao pós-parto às vezes choro de emoção de alegria mas estou bem e feliz",
    "durmo pouco mas normal para recém-nascido estou me recuperando bem apoio da família excelente",
    "fico emocionada quando vejo meu filho sorrir é tudo muito intenso mas são emoções positivas",
    "cansaço físico normal mas psicologicamente estou muito bem conectada com o bebê amamentando bem",
    "às vezes me preocupo com coisas normais de mãe de primeira viagem mas nada que me tire o sono",
    "recuperação pós-parto tranquila bebê saudável eu saudável relacionamento com marido ótimo",
    "momentos difíceis mas passageiros consigo pedir ajuda quando preciso e aceito o apoio da família",
    "alegria em cada conquista do bebê primeira vez que sorriu primeira vez que segurou a cabeça",
    "amamentação indo bem às vezes difícil mas persistindo e tendo sucesso bebê engordando bem",
    "retomando atividades gradualmente me sentindo eu mesma de novo com energia crescendo cada dia",
    "grupo de apoio de mães me ajudou muito troco experiências sem julgamento me sinto acolhida",
    "parceiro muito presente divisão de tarefas funciona bem descansamos em turnos conseguimos nos ajudar",
    "consulta de acompanhamento tranquila sem queixas relevantes progressão normal do pós-parto",
    "satisfação com a maternidade apesar dos desafios sinto que nasci para ser mãe amo meu filho",
]


def _make_df() -> pd.DataFrame:
    rows = (
        [{"text_pt": t, "risk_label": "HIGH_RISK"} for t in _HIGH_RISK]
        + [{"text_pt": t, "risk_label": "MONITORING"} for t in _MONITORING]
        + [{"text_pt": t, "risk_label": "LOW_RISK"} for t in _LOW_RISK]
    )
    return pd.DataFrame(rows * 4).sample(frac=1, random_state=42).reset_index(drop=True)


def train_nlp_model(df: pd.DataFrame, models_dir: Path) -> None:
    from src.lda_model import save_lda, train_lda
    from src.preprocess import preprocess, preprocess_for_tfidf

    print("  Treinando LDA...")
    tokenized = [preprocess(t) for t in df["text_pt"]]
    lda, dictionary, _ = train_lda(tokenized)
    save_lda(lda, dictionary)

    from src.lda_model import get_topic_features
    import scipy.sparse as sp

    print("  Construindo matriz de features...")
    tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 2), sublinear_tf=True)
    tfidf_matrix = tfidf.fit_transform(df["text_pt"].apply(preprocess_for_tfidf))
    lda_features = np.array([
        get_topic_features(preprocess(t), lda, dictionary) for t in df["text_pt"]
    ])
    X = sp.hstack([tfidf_matrix, sp.csr_matrix(lda_features)])
    y = df["risk_label"].values

    print("  Treinando LogisticRegression...")
    clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
    clf.fit(X, y)

    models_dir.mkdir(exist_ok=True)
    joblib.dump({"classifier": clf, "tfidf": tfidf, "label_map": {}}, models_dir / "nlp_pipeline.joblib")
    print(f"  Modelo NLP salvo → {models_dir}/nlp_pipeline.joblib")


def train_risk_model(nlp_models_dir: Path, risk_dir: Path) -> None:
    from src.predict import predict_from_text

    import src.predict as pred_module
    pred_module.MODELS_DIR = nlp_models_dir
    pred_module._bundle = None
    pred_module._lda = None
    pred_module._dictionary = None

    rows = []
    all_texts = _HIGH_RISK + _MONITORING + _LOW_RISK
    all_labels = (
        ["HIGH_RISK"] * len(_HIGH_RISK)
        + ["MONITORING"] * len(_MONITORING)
        + ["LOW_RISK"] * len(_LOW_RISK)
    )

    print("  Gerando dados de treinamento do motor de risco a partir da saída do modelo NLP...")
    for text, label in zip(all_texts, all_labels):
        result = predict_from_text(text)
        prob_map = result["probabilities"]
        rows.append({
            "HIGH_RISK_score": prob_map.get("HIGH_RISK", 0.0),
            "MONITORING_score": prob_map.get("MONITORING", 0.0),
            "LOW_RISK_score": prob_map.get("LOW_RISK", 0.0),
            "risk_level": label,
        })

    risk_df = pd.DataFrame(rows * 4)
    FEATURE_COLUMNS = ["HIGH_RISK_score", "MONITORING_score", "LOW_RISK_score"]

    risk_data_dir = risk_dir / "data"
    risk_data_dir.mkdir(parents=True, exist_ok=True)
    risk_df.to_csv(risk_data_dir / "train_risk.csv", index=False)
    print(f"  Dados de treinamento do motor de risco salvos → {risk_data_dir}/train_risk.csv")

    X = risk_df[FEATURE_COLUMNS].values
    y = risk_df["risk_level"].values

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, y)

    risk_models_dir = risk_dir / "models"
    risk_models_dir.mkdir(exist_ok=True)
    bundle = {
        "pipeline": pipe,
        "feature_columns": FEATURE_COLUMNS,
        "class_names": list(pipe.classes_),
    }
    joblib.dump(bundle, risk_models_dir / "risk_model.joblib")
    print(f"  Risk Engine salvo → {risk_models_dir}/risk_model.joblib")


def main() -> None:
    nlp_dir = Path(__file__).parent.parent
    risk_dir = nlp_dir.parent / "risk-engine"

    print("=== Inicializando modelo NLP (dados sintéticos) ===")
    df = _make_df()
    print(f"  Amostras sintéticas: {len(df)}")
    train_nlp_model(df, nlp_dir / "models")

    print("\n=== Inicializando modelo do Motor de Risco ===")
    train_risk_model(nlp_dir / "models", risk_dir)

    print("\nConcluído. Execute 'make up' para iniciar todos os serviços.")


if __name__ == "__main__":
    main()
