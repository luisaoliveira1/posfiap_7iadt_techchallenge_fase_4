# Sistema de Análise de Fala para Depressão Pós-Parto

Tech Challenge — Fase 4 | FIAP Pós-Graduação em Inteligência Artificial para Devs

---

## Visão Geral

Sistema de apoio clínico que analisa gravações de áudio de consultas psicológicas e classifica o risco de depressão pós-parto (DPP) em três níveis: **ALTO RISCO**, **MONITORAMENTO** e **BAIXO RISCO**. O sistema inclui uma fila de revisão humana (*human-in-the-loop*) para que profissionais de saúde possam confirmar ou corrigir classificações antes de usá-las clinicamente.

**Pipeline completo:**
```
Áudio (WAV) → Transcrição (Azure Speech / Whisper) → NLP (TF-IDF + LDA)
    → Motor de Risco → Classificação → Fila de Revisão Humana
```

---

## Arquitetura

### Ambiente Local (Docker Compose)

Quatro serviços Docker se comunicam via rede interna:

| Serviço | Porta | Descrição |
|---|---|---|
| `frontend` | 3000 | Interface web (React + Vite) |
| `backend` | 8000 | API principal (FastAPI) — orquestra o pipeline |
| `nlp-model` | 8001 | Modelo NLP — TF-IDF + LDA + Regressão Logística |
| `risk-engine` | 8002 | Motor de risco — calibra a classificação final |

```
Usuário → Frontend (3000)
             ↓
         Backend (8000)
           ↙        ↘
  NLP Model (8001)  Risk Engine (8002)
```

### Ambiente de Produção (Azure)

Infraestrutura provisionada com **Terraform** na região `eastus`:

```
Internet
    │
    ▼
Azure Container Apps Environment (blackbush-fb928973.eastus)
    ├── ppd-dev-frontend        (nginx + React — ingress externo HTTPS)
    │       ↓ proxy /api/
    ├── ppd-dev-backend         (FastAPI — ingress externo HTTPS)
    │       ↙              ↘
    ├── ppd-dev-nlp-model   ppd-dev-risk-engine
    │   (porta 8001)         (porta 8002)
    │
Azure Storage Account (ppddevsa)
    ├── container: models          (artefatos dos modelos NLP e risco)
    ├── container: training-data   (dataset de treino traduzido)
    ├── container: review-queue    (casos para revisão humana — JSON)
    ├── container: audio-uploads   (áudios enviados via API)
    └── container: transcripts / results

Azure Container Registry (ppddevacr)
    └── repositórios: frontend, backend, nlp-model, risk-engine

Azure Cognitive Services
    ├── Speech Service (F0) — transcrição pt-BR
    └── Language Service (F0) — análise de linguagem

Azure Functions (ppd-dev-func)
    └── analyze_transcript — Event Grid trigger, enfileira revisão humana

Azure AI Foundry (ppd-dev-foundry)
    └── workspace para integração futura com Azure ML Data Labeling
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| STT (produção) | Azure AI Speech SDK — `pt-BR-FranciscaNeural` |
| STT (local) | `faster-whisper` — modelo `small`, CPU, sem chave de API |
| NLP | `gensim` (LDA, 10 tópicos) + `scikit-learn` (TF-IDF + Regressão Logística) |
| Motor de risco | `scikit-learn` (StandardScaler + Regressão Logística) |
| Flags clínicas | Regras baseadas em frases de risco em português brasileiro |
| Backend | FastAPI + Python 3.11 |
| Frontend | React + TypeScript + Vite |
| Infra local | Docker Compose |
| Infra cloud | Azure Container Apps + Terraform |

---

## Pré-requisitos

**Local:**
- Docker e Docker Compose instalados
- Python 3.11+ (opcional — apenas para geração de cenários de teste)
- `edge-tts` e `ffmpeg` (opcional — apenas para síntese de novos áudios)

**Azure (produção):**
- Azure CLI autenticado (`az login`)
- Terraform >= 1.5
- Acesso ao Azure Container Registry (`az acr login --name ppddevacr`)

---

## Início Rápido (Local)

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env
# STT_BACKEND=whisper já está configurado — não precisa de chave Azure

# 2. Construir e subir todos os serviços
# (os modelos são treinados automaticamente durante o build)
make build
make up
```

Acesse a interface em **http://localhost:3000**

---

## Início Rápido (Azure)

```bash
# 1. Provisionar infraestrutura
cd infrastructure
terraform init
terraform apply

# 2. Login no ACR e push das imagens
az acr login --name ppddevacr
TAG=v$(date +%s)
for svc in frontend backend nlp-model risk-engine; do
  docker build --platform linux/amd64 -t ppddevacr.azurecr.io/$svc:$TAG ./$svc/
  docker push ppddevacr.azurecr.io/$svc:$TAG
done

# 3. Atualizar os Container Apps com as novas imagens
for app in ppd-dev-frontend ppd-dev-backend ppd-dev-nlp-model ppd-dev-risk-engine; do
  svc="${app/ppd-dev-/}"
  az containerapp update --name $app --resource-group ppd-dev-rg \
    --image ppddevacr.azurecr.io/$svc:$TAG
done
```

---

## Comandos Disponíveis

```bash
make build         # Constrói todas as imagens Docker (treina modelos no build)
make up            # Sobe todos os serviços em background
make down          # Para todos os serviços
make test          # Health checks + teste rápido de predição via texto
make test-audio FILE=caminho/para/audio.wav   # Testa com arquivo WAV real
```

---

## Endpoints da API

### Backend (porta 8000 / `ppd-dev-backend.blackbush-fb928973.eastus.azurecontainerapps.io`)

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/api/audio/analyze` | Análise de arquivo de áudio (multipart WAV) |
| `POST` | `/api/audio/analyze-text` | Análise direta de texto (JSON) |
| `GET` | `/api/health` | Health check do backend |
| `GET` | `/api/reviews` | Lista fila de revisão humana (parâmetro `?status=pending\|reviewed`) |
| `GET` | `/api/reviews/{job_id}` | Detalhe de uma revisão |
| `POST` | `/api/reviews/{job_id}/decide` | Submete decisão de revisão |

**Exemplo — análise de texto:**
```bash
curl -X POST http://localhost:8000/api/audio/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Não consigo dormir, choro sem parar, não sinto nada pelo meu filho."}'
```

**Exemplo — análise de áudio:**
```bash
curl -X POST http://localhost:8000/api/audio/analyze \
  -F "file=@consulta.wav"
```

**Resposta:**
```json
{
  "job_id": "3f8a1c2d-...",
  "transcript": "...",
  "risk_level": "HIGH_RISK",
  "risk_level_display": "Alto Risco",
  "confidence": 0.97,
  "human_review_required": true,
  "probabilities": {
    "HIGH_RISK": 0.97,
    "MONITORING": 0.02,
    "LOW_RISK": 0.01
  }
}
```

**Exemplo — submeter revisão humana:**
```bash
# Confirmar a classificação automática
curl -X POST http://localhost:8000/api/reviews/{job_id}/decide \
  -H "Content-Type: application/json" \
  -d '{"decision": "confirmed", "note": "Paciente encaminhada para psiquiatria."}'

# Corrigir a classificação
curl -X POST http://localhost:8000/api/reviews/{job_id}/decide \
  -H "Content-Type: application/json" \
  -d '{"decision": "overridden", "label": "MONITORING", "note": "Ideação passiva sem plano."}'
```

---

## Níveis de Risco e Revisão Humana

| Nível | Significado | Revisão obrigatória |
|---|---|---|
| `HIGH_RISK` | Sinais severos — ideação suicida, dissociação, medo de machucar, pensamentos intrusivos | Sempre |
| `MONITORING` | Sinais moderados — ansiedade, culpa, dificuldade funcional, insônia | Se confiança < 75% |
| `LOW_RISK` | Adaptação normal ao pós-parto | Se confiança < 55% |

A revisão humana também é ativada quando **flags clínicas** são detectadas (frases de risco em português) independentemente do nível de confiança do modelo.

---

## Human-in-the-Loop (HITL)

Quando `human_review_required: true`, o caso é automaticamente enfileirado para revisão:

1. **Enfileiramento automático:** o backend salva o caso na fila (Azure Blob `review-queue` em produção, memória em dev)
2. **Interface de revisão:** acesse a aba **"Fila de Revisão"** na interface web
3. **Decisão clínica:** o profissional pode:
   - **Confirmar** a classificação automática
   - **Corrigir** para outro nível (HIGH_RISK / MONITORING / LOW_RISK)
   - Adicionar uma **nota clínica** para contexto
4. **Registro:** a decisão (com timestamp e nota) é salva junto ao caso original

Em produção, o Azure Function `analyze_transcript` também enfileira casos via Event Grid quando o pipeline assíncrono é usado.

---

## Modelos de ML

### NLP Model (TF-IDF + LDA + Regressão Logística)

Treinado com **1518 amostras** em português brasileiro:
- Dataset Kaggle de DPP traduzido automaticamente (1503 registros)
- 5 exemplos de cada cenário clínico de teste (15 registros adicionais)

Métricas no conjunto de teste (20% holdout, 304 amostras):
```
              precision    recall  f1-score   support

   HIGH_RISK       0.93      0.89      0.91       111
    LOW_RISK       0.77      0.96      0.86        28
  MONITORING       0.93      0.92      0.92       165

    accuracy                           0.91       304
```

### Motor de Risco (StandardScaler + Regressão Logística)

Treinado com as probabilidades do modelo NLP no conjunto de teste (304 amostras holdout), usando ground-truth labels para evitar vazamento de dados:

```
              precision    recall  f1-score   support

   HIGH_RISK       0.96      0.93      0.95        28
    LOW_RISK       0.64      1.00      0.78         7
  MONITORING       0.97      0.90      0.94        41

    accuracy                           0.92        76
```

### Flags Clínicas (Regras)

Sistema de regras baseado em ~40 frases de risco em português, cobrindo:
- Ideação suicida passiva ("seria melhor para todo mundo se eu sumisse")
- Medo de auto-dano ("medo de mim mesma")
- Pensamentos intrusivos ("pensamentos horríveis", "imaginando coisas ruins")
- Dissociação ("não sou mais eu", "estou desaparecendo")
- Frases diretas de suicídio ("vontade de morrer", "não quero mais viver")

Quando uma flag clínica é detectada e o modelo NLP indica probabilidade ≥ 20% para HIGH_RISK, o caso é automaticamente elevado para HIGH_RISK independente da classificação original.

---

## Estrutura do Projeto

```
.
├── backend/                # API principal — FastAPI, STT, orquestração
│   ├── src/
│   │   ├── routers/
│   │   │   ├── audio.py       # POST /api/audio/analyze e /analyze-text
│   │   │   ├── reviews.py     # GET/POST /api/reviews (HITL)
│   │   │   └── health.py
│   │   └── services/
│   │       ├── nlp_client.py
│   │       ├── risk_client.py
│   │       ├── review_store.py  # Fila de revisão (Blob / memória)
│   │       ├── speech_client.py # Azure Speech SDK
│   │       └── whisper_client.py
│   └── main.py
├── frontend/               # Interface web — React, TypeScript, Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioUpload/
│   │   │   ├── RiskResult/
│   │   │   ├── TopicSignals/
│   │   │   ├── HumanReviewBanner/
│   │   │   └── ReviewQueue/     # Fila de revisão humana
│   │   ├── services/api.ts
│   │   └── types/
│   │       ├── analysis.ts
│   │       └── review.ts
│   └── nginx.conf          # Proxy reverso para o backend
├── nlp-model/              # Modelo NLP — LDA + TF-IDF + LogisticRegression
│   ├── data/processed/     # translated.csv (dataset traduzido)
│   ├── models/             # Artefatos treinados (baked na imagem Docker)
│   └── src/
│       ├── clinical_flags.py   # ~40 frases de risco em pt-BR
│       ├── predict.py          # Inferência com override de flags clínicas
│       └── train.py
├── risk-engine/            # Motor de risco — StandardScaler + LogisticRegression
│   ├── data/train_risk.csv # Dados de treino gerados pelo NLP (holdout)
│   └── src/
├── azure-functions/        # Azure Function — pipeline assíncrono via Event Grid
│   └── analyze_transcript/ # Trigger blob → NLP → risco → review-queue
├── infrastructure/         # Terraform — toda a infraestrutura Azure
│   ├── main.tf
│   ├── variables.tf
│   └── modules/
│       ├── container_apps/
│       ├── container_registry/
│       ├── storage/
│       ├── functions/
│       ├── speech/
│       ├── language/
│       ├── ai_foundry/
│       └── event_grid/
├── test-scenarios/         # Cenários de teste e áudios WAV
│   └── production test/    # 6 arquivos WAV prontos para upload
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env`. As principais variáveis:

| Variável | Padrão (local) | Descrição |
|---|---|---|
| `STT_BACKEND` | `whisper` | Backend de transcrição (`whisper` ou `azure`) |
| `AZURE_SPEECH_KEY` | — | Chave do Azure Speech (necessária se `STT_BACKEND=azure`) |
| `AZURE_SPEECH_REGION` | `eastus` | Região do serviço de fala |
| `AZURE_BLOB_CONNECTION_STRING` | — | Vazio = revisões em memória; preencher para persistir no Azure |
| `NLP_MODEL_URL` | `http://nlp-model:8001` | URL interna do serviço NLP |
| `RISK_ENGINE_URL` | `http://risk-engine:8002` | URL interna do motor de risco |

---

## Cenários de Teste

Seis arquivos WAV prontos em `test-scenarios/production test/`:

| Arquivo | Cenário | Classificação esperada |
|---|---|---|
| `test_new_high_risk.wav` | Ideação suicida passiva, medo de ficar sozinha, insônia severa | HIGH_RISK |
| `test_new_monitoring.wav` | Choro sem motivo, peso no peito, dificuldade para sair de casa | MONITORING |
| `test_new_low_risk.wav` | Adaptação bem-sucedida, bebê dormindo melhor, rede de apoio | LOW_RISK |
| `test_extra_high_risk.wav` | Raiva incontrolável, medo de machucar o filho, pensamentos intrusivos | HIGH_RISK |
| `test_extra_monitoring.wav` | Melhora parcial, ansiedade vespertina, evitação social | MONITORING |
| `test_extra_low_risk.wav` | Dois meses pós-parto, bebê sorrindo, primeira saída sem ansiedade | LOW_RISK |

---

## Aviso Clínico

Este sistema é uma ferramenta de **apoio à decisão clínica**, não um diagnóstico médico. Toda classificação de alto risco deve ser revisada por um profissional de saúde habilitado. O sistema não substitui avaliação psicológica ou psiquiátrica.
