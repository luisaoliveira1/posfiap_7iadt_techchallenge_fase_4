"""
Retreina o modelo NLP e o motor de risco a partir de duas fontes de dados:
  1. Texto sintético: 45 frases por classe (HIGH_RISK, MONITORING, LOW_RISK),
     repetidas 4 vezes para totalizar 180 amostras balanceadas.
  2. Transcrições reais geradas pelo Whisper, rotuladas manualmente e registradas
     com split=train em scenario_corpus.csv — aplicando oversample de 3× para
     aumentar o peso dos dados reais frente ao texto sintético.
Após o treino, avalia o modelo nas linhas split=test do mesmo CSV (dados nunca vistos).

Execução dentro do Docker (a partir da raiz do projeto):
    docker run --rm \
      -v $(pwd)/nlp-model/data:/app/data \
      -v $(pwd)/nlp-model/models:/app/models \
      -v $(pwd)/nlp-model/scripts:/app/scripts \
      -v $(pwd)/risk-engine:/risk-engine \
      -e PYTHONPATH=/app \
      posfiap_7iadt_techchallenge_fase4-nlp-model \
      python scripts/retrain_with_scenarios.py
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SCENARIO_CSV = Path("data/raw/scenario_corpus.csv")
MODELS_DIR   = Path("models")
OVERSAMPLE   = 3

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


def _seed_df() -> pd.DataFrame:
    rows = (
        [{"text": t, "label": "HIGH_RISK"}  for t in _HIGH_RISK]
        + [{"text": t, "label": "MONITORING"} for t in _MONITORING]
        + [{"text": t, "label": "LOW_RISK"}   for t in _LOW_RISK]
    )
    return pd.DataFrame(rows * 4)  # 180 amostras


def _build_features(df: pd.DataFrame, lda, dictionary, tfidf=None, fit=True):
    from src.lda_model import get_topic_features
    from src.preprocess import preprocess, preprocess_for_tfidf

    texts = df["text"].fillna("")
    clean = texts.apply(preprocess_for_tfidf)

    if fit:
        tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 2), sublinear_tf=True)
        X_tfidf = tfidf.fit_transform(clean)
    else:
        X_tfidf = tfidf.transform(clean)

    lda_feats = np.array([
        get_topic_features(preprocess(t), lda, dictionary)
        for t in texts
    ])
    return sp.hstack([X_tfidf, sp.csr_matrix(lda_feats)]), tfidf


def main() -> None:
    from src.lda_model import save_lda, train_lda
    from src.preprocess import preprocess

    seed = _seed_df()
    print(f"Corpus semente : {len(seed)} amostras")

    train_scenario = pd.DataFrame()
    test_scenario  = pd.DataFrame()

    if SCENARIO_CSV.exists():
        corpus = pd.read_csv(SCENARIO_CSV)
        train_scenario = corpus[corpus["split"] == "train"][["text", "label"]]
        test_scenario  = corpus[corpus["split"] == "test"][["text", "label"]]
        print(f"Cenários   : {len(train_scenario)} treino  |  {len(test_scenario)} teste (held-out)")
    else:
        print(f"Corpus de cenários não encontrado em {SCENARIO_CSV} — usando apenas a semente")

    train_df = pd.concat(
        [seed] + [train_scenario] * OVERSAMPLE,
        ignore_index=True,
    ).sample(frac=1, random_state=42)

    print(f"\nConjunto de treino: {len(train_df)} amostras")
    print(train_df["label"].value_counts().to_string())

    print("\nTreinando LDA ...")
    tokenized = [preprocess(t) for t in train_df["text"]]
    lda, dictionary, _ = train_lda(tokenized)
    save_lda(lda, dictionary)

    X_train, tfidf = _build_features(train_df, lda, dictionary, fit=True)
    y_train = train_df["label"].values

    print("Treinando por regressão logística ...")
    clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
    clf.fit(X_train, y_train)

    print("\n=== Validação cruzada 5-fold (conjunto de treino) ===")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
    cv_results = cross_validate(
        cv_clf, X_train, y_train, cv=cv,
        scoring=["accuracy", "f1_macro", "f1_weighted"],
        return_train_score=False,
    )
    for metric, key in [("Acurácia", "test_accuracy"), ("F1 macro", "test_f1_macro"), ("F1 ponderado", "test_f1_weighted")]:
        scores = cv_results[key]
        print(f"  {metric:14s}: {scores.mean():.3f} ± {scores.std():.3f}  (folds: {', '.join(f'{s:.2f}' for s in scores)})")

    # Esses 15 cenários nunca foram usados durante o treinamento
    if not test_scenario.empty:
        print("\n=== Avaliação no conjunto de teste held-out ===")
        X_test, _ = _build_features(test_scenario, lda, dictionary, tfidf=tfidf, fit=False)
        y_test = test_scenario["label"].values
        y_pred = clf.predict(X_test)
        labels = ["HIGH_RISK", "MONITORING", "LOW_RISK"]
        print(classification_report(y_test, y_pred, labels=labels, zero_division=0))
        print("Matriz de confusão (linhas=real, colunas=predito):")
        print(confusion_matrix(y_test, y_pred, labels=labels))
    else:
        print("\n(Sem cenários de teste — avaliação held-out ignorada)")

    # Salvando modelo NLP
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"classifier": clf, "tfidf": tfidf, "label_map": {}}, MODELS_DIR / "nlp_pipeline.joblib")
    print(f"\nModelo NLP salvo → {MODELS_DIR}/nlp_pipeline.joblib")

    #Retreino de risk engine
    from src.predict import predict_from_text
    import src.predict as pred_module
    pred_module.MODELS_DIR = MODELS_DIR
    pred_module._bundle = pred_module._lda = pred_module._dictionary = None

    print("\nGerando dados de treinamento do motor de risco ...")
    risk_rows = []
    for text, label in zip(train_df["text"], train_df["label"]):
        result  = predict_from_text(text)
        prob    = result["probabilities"]
        risk_rows.append({
            "HIGH_RISK_score":  prob.get("HIGH_RISK",  0.0),
            "MONITORING_score": prob.get("MONITORING", 0.0),
            "LOW_RISK_score":   prob.get("LOW_RISK",   0.0),
            "risk_level": label,
        })

    risk_df = pd.DataFrame(risk_rows)
    FEAT    = ["HIGH_RISK_score", "MONITORING_score", "LOW_RISK_score"]

    risk_dir = Path("/risk-engine")
    (risk_dir / "data").mkdir(parents=True, exist_ok=True)
    risk_df.to_csv(risk_dir / "data" / "train_risk.csv", index=False)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(risk_df[FEAT].values, risk_df["risk_level"].values)

    (risk_dir / "models").mkdir(exist_ok=True)
    joblib.dump(
        {"pipeline": pipe, "feature_columns": FEAT, "class_names": list(pipe.classes_)},
        risk_dir / "models" / "risk_model.joblib",
    )
    print(f"Risk Engine salvo → {risk_dir}/models/risk_model.joblib")
    print("\nConcluído. Reinicie os containers: docker restart <nlp-model> <risk-engine>")


if __name__ == "__main__":
    main()
