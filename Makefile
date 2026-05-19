.PHONY: translate train-nlp gen-risk-data train-risk train-all seed up down build test test-audio help

PYTHON := python3
NLP_DIR := nlp-model
RISK_DIR := risk-engine

help:
	@echo "Sistema de Análise de Depressão Pós-Parto"
	@echo ""
	@echo "Início rápido (sem dataset do Kaggle):"
	@echo "  make seed             Treina ambos os modelos com dados sintéticos (~30s) e então 'make up'"
	@echo ""
	@echo "Pipeline completo de treinamento com dataset do Kaggle (executar em ordem):"
	@echo "  make translate        Traduz o dataset do Kaggle EN→PT (com cache, seguro para re-executar)"
	@echo "  make train-nlp        Treina o modelo NLP (TF-IDF + LDA + LogisticRegression)"
	@echo "  make gen-risk-data    Gera o CSV de treinamento do motor de risco a partir da saída do modelo NLP"
	@echo "  make train-risk       Treina o motor de risco (StandardScaler + LogisticRegression)"
	@echo "  make train-all        Executa as 4 etapas acima em sequência"
	@echo ""
	@echo "Docker:"
	@echo "  make build            Constrói todas as imagens Docker"
	@echo "  make up               Inicia todos os serviços"
	@echo "  make down             Para todos os serviços"
	@echo ""
	@echo "Testes:"
	@echo "  make test             Executa verificações de saúde + teste rápido de predição"
	@echo "  make test-audio FILE=caminho/para/audio.wav   Testa com um arquivo de áudio real"

seed:
	@echo ">>> Inicializando modelos com dados sintéticos (sem dataset do Kaggle)..."
	cd $(NLP_DIR) && $(PYTHON) -m scripts.seed_models
	@echo ">>> Concluído. Execute 'make up' para iniciar todos os serviços."

translate:
	@echo ">>> Traduzindo dataset (deduplicação + cache em disco)..."
	cd $(NLP_DIR) && $(PYTHON) -m src.translate

train-nlp:
	@echo ">>> Treinando modelo NLP..."
	cd $(NLP_DIR) && $(PYTHON) -m src.train

gen-risk-data:
	@echo ">>> Gerando dados de treinamento do motor de risco..."
	cd $(NLP_DIR) && $(PYTHON) -m scripts.generate_risk_training_data

train-risk:
	@echo ">>> Treinando motor de risco..."
	cd $(RISK_DIR) && $(PYTHON) -m src.train

train-all: translate train-nlp gen-risk-data train-risk
	@echo ">>> Todos os modelos treinados com sucesso."

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Serviços iniciando... frontend: http://localhost:3000  backend: http://localhost:8000"

down:
	docker-compose down

test:
	@echo ">>> Verificações de saúde..."
	@curl -sf http://localhost:8001/health | $(PYTHON) -m json.tool && echo " Modelo NLP: OK" || echo " Modelo NLP: FALHA"
	@curl -sf http://localhost:8002/health | $(PYTHON) -m json.tool && echo " Motor de risco: OK" || echo " Motor de risco: FALHA"
	@curl -sf http://localhost:8000/api/health | $(PYTHON) -m json.tool && echo " Backend: OK" || echo " Backend: FALHA"
	@echo ""
	@echo ">>> Teste rápido de análise de texto..."
	@curl -sf -X POST http://localhost:8000/api/audio/analyze-text \
	  -H "Content-Type: application/json" \
	  -d '{"text": "Doutora não consigo dormir fico chorando sem parar não sinto nada pelo meu filho estou com medo de mim mesma"}' | $(PYTHON) -m json.tool

test-audio:
	@if [ -z "$(FILE)" ]; then echo "Uso: make test-audio FILE=caminho/para/audio.wav"; exit 1; fi
	@echo ">>> Enviando $(FILE) para análise..."
	@curl -sf -X POST http://localhost:8000/api/audio/analyze \
	  -F "file=@$(FILE)" | $(PYTHON) -m json.tool
