.PHONY: help install setup-extension run-api run-streamlit test clean

help:
	@echo "🚀 CVLM - Commandes disponibles"
	@echo ""
	@echo "Installation:"
	@echo "  make install          - Installer toutes les dépendances"
	@echo "  make setup-extension  - Créer la structure de l'extension"
	@echo ""
	@echo "Lancement:"
	@echo "  make run-api          - Lancer l'API (port 8000)"
	@echo "  make run-streamlit    - Lancer l'interface Streamlit"
	@echo ""
	@echo "Tests:"
	@echo "  make test             - Tester l'API"
	@echo "  make test-health      - Test rapide du health check"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            - Nettoyer les fichiers temporaires"
	@echo "  make clean-all        - Nettoyage complet"

install:
	@echo "📦 Installation des dépendances..."
	pip install -r requirements.txt
	pip install fastapi uvicorn python-multipart pydantic
	@echo "✅ Dépendances installées"

setup-extension:
	@echo "🏗️  Création de la structure de l'extension..."
	python setup_extension.py
	@echo "✅ Extension configurée"
	@echo ""
	@echo "⚠️  N'oubliez pas:"
	@echo "  1. Copier les fichiers dans extension/"
	@echo "  2. Créer les icônes dans extension/icons/"
	@echo "  3. Configurer .env avec vos clés API"

run-api:
	@echo "🚀 Lancement de l'API CVLM..."
	python api_server.py

run-streamlit:
	@echo "🚀 Lancement de l'interface Streamlit..."
	streamlit run streamlit_app.py

test:
	@echo "🧪 Tests de l'API..."
	python test_api.py

test-health:
	@echo "🔍 Test du health check..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API non accessible"

clean:
	@echo "🧹 Nettoyage des fichiers temporaires..."
	rm -rf data/temp/*
	rm -f temp_cv.pdf temp_jo.pdf lettre_motivation.pdf
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Nettoyage terminé"

clean-all: clean
	@echo "🧹 Nettoyage complet..."
	rm -rf data/output/lettre_*.pdf
	rm -rf extension/
	@echo "✅ Nettoyage complet terminé"

dev:
	@echo "🔧 Mode développement"
	@echo "Terminal 1: API"
	@echo "  make run-api"
	@echo ""
	@echo "Terminal 2: Tests"
	@echo "  make test"

.DEFAULT_GOAL := help