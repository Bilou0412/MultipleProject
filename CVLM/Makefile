# Makefile pour CVLM - Commandes simplifiées
.PHONY: help build up down restart logs shell db-shell test clean init migrate

# Couleurs pour les messages
BLUE=\033[0;34m
GREEN=\033[0;32m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Affiche cette aide
	@echo "$(BLUE)CVLM - Commandes disponibles :$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ===== DOCKER =====

build: ## Build les images Docker
	@echo "$(BLUE)🔨 Build des images Docker...$(NC)"
	docker compose build

up: ## Démarre tous les services
	@echo "$(BLUE)🚀 Démarrage des services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Services démarrés !$(NC)"
	@echo "$(BLUE)API:$(NC) http://localhost:8000"
	@echo "$(BLUE)Streamlit:$(NC) http://localhost:8501"
	@echo "$(BLUE)Docs:$(NC) http://localhost:8000/docs"

up-dev: ## Démarre avec PgAdmin (mode développement)
	@echo "$(BLUE)🚀 Démarrage mode développement...$(NC)"
	docker compose --profile dev up -d
	@echo "$(GREEN)✅ Services démarrés !$(NC)"
	@echo "$(BLUE)API:$(NC) http://localhost:8000"
	@echo "$(BLUE)Streamlit:$(NC) http://localhost:8501"
	@echo "$(BLUE)PgAdmin:$(NC) http://localhost:5050"

down: ## Arrête tous les services
	@echo "$(BLUE)⏹️  Arrêt des services...$(NC)"
	docker compose down

restart: ## Redémarre tous les services
	@echo "$(BLUE)🔄 Redémarrage des services...$(NC)"
	docker compose restart

rebuild: ## Rebuild et redémarre tous les services
	@echo "$(BLUE)🔨 Rebuild complet...$(NC)"
	docker compose down
	docker compose up -d --build
	@echo "$(GREEN)✅ Services redémarrés !$(NC)"

logs: ## Affiche les logs en temps réel
	docker compose logs -f

logs-api: ## Logs de l'API uniquement
	docker compose logs -f api

logs-db: ## Logs de PostgreSQL uniquement
	docker compose logs -f postgres

status: ## Affiche le statut des services
	@echo "$(BLUE)📊 Statut des services :$(NC)"
	docker compose ps

# ===== ACCÈS AUX CONTENEURS =====

shell: ## Shell dans le conteneur API
	docker compose exec api bash

shell-db: ## Shell dans PostgreSQL
	docker compose exec postgres psql -U cvlm_user -d cvlm_db

# ===== BASE DE DONNÉES =====

init: ## Initialise la base de données
	@echo "$(BLUE)🔧 Initialisation de la base de données...$(NC)"
	docker compose exec api python init_database.py
	@echo "$(GREEN)✅ Base initialisée !$(NC)"

init-reset: ## Réinitialise la base (⚠️ supprime les données)
	@echo "$(RED)⚠️  ATTENTION : Cela va supprimer toutes les données !$(NC)"
	@read -p "Continuer ? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose exec api python init_database.py --reset; \
		echo "$(GREEN)✅ Base réinitialisée !$(NC)"; \
	fi

migrate: ## Migre les données existantes vers la DB
	@echo "$(BLUE)🔄 Migration des données...$(NC)"
	docker compose exec api python migrate_data.py

backup: ## Backup de la base de données
	@echo "$(BLUE)💾 Backup de la base...$(NC)"
	docker compose exec postgres pg_dump -U cvlm_user cvlm_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup créé !$(NC)"

restore: ## Restaure la base depuis backup.sql
	@if [ ! -f backup.sql ]; then \
		echo "$(RED)❌ Fichier backup.sql introuvable$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)📥 Restauration de la base...$(NC)"
	docker compose exec -T postgres psql -U cvlm_user cvlm_db < backup.sql
	@echo "$(GREEN)✅ Base restaurée !$(NC)"

# ===== DÉVELOPPEMENT =====

install: ## Installe les dépendances localement (pour IDE)
	pip install -r requirements.txt

install-dev: ## Installe les dépendances de développement
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Lance les tests
	@echo "$(BLUE)🧪 Exécution des tests...$(NC)"
	docker compose exec api pytest tests/ -v

test-local: ## Lance les tests localement
	pytest tests/ -v

lint: ## Vérifie le code avec flake8
	@echo "$(BLUE)🔍 Vérification du code...$(NC)"
	docker compose exec api flake8 domain/ infrastructure/ --max-line-length=120

format: ## Formate le code avec black
	@echo "$(BLUE)✨ Formatage du code...$(NC)"
	docker compose exec api black domain/ infrastructure/

# ===== NETTOYAGE =====

clean: ## Nettoie les conteneurs, volumes et images
	@echo "$(RED)⚠️  Nettoyage complet...$(NC)"
	docker compose down -v
	docker system prune -f
	@echo "$(GREEN)✅ Nettoyage terminé !$(NC)"

clean-data: ## Supprime les données persistées (⚠️ perte de données)
	@echo "$(RED)⚠️  ATTENTION : Suppression des données !$(NC)"
	@read -p "Continuer ? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/files/*; \
		docker volume rm cvlm_postgres_data 2>/dev/null || true; \
		echo "$(GREEN)✅ Données supprimées !$(NC)"; \
	fi

clean-logs: ## Supprime les logs
	@echo "$(BLUE)🧹 Suppression des logs...$(NC)"
	rm -rf logs/*.log
	@echo "$(GREEN)✅ Logs supprimés !$(NC)"

# ===== PRODUCTION =====

prod-build: ## Build pour la production
	@echo "$(BLUE)🏭 Build production...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Démarre en mode production
	@echo "$(BLUE)🚀 Démarrage production...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Production démarrée !$(NC)"

prod-down: ## Arrête la production
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# ===== UTILITAIRES =====

check-env: ## Vérifie que le fichier .env existe
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ Fichier .env introuvable$(NC)"; \
		echo "$(BLUE)Copier .env.example vers .env et le configurer$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✅ Fichier .env trouvé$(NC)"; \
	fi

health: ## Vérifie la santé des services
	@echo "$(BLUE)🏥 Vérification de la santé...$(NC)"
	@curl -s http://localhost:8000/health | jq . || echo "$(RED)API non accessible$(NC)"

watch-logs: ## Logs avec filtrage des erreurs
	docker compose logs -f | grep -i --color=always -E "error|warning|exception|$$"

stats: ## Statistiques des conteneurs
	docker stats --no-stream

# ===== DÉVELOPPEMENT LOCAL (sans Docker) =====

local-db: ## Démarre uniquement PostgreSQL (pour dev local)
	docker compose up -d postgres
	@echo "$(GREEN)✅ PostgreSQL démarré sur localhost:5432$(NC)"

local-api: ## Lance l'API localement
	uvicorn api_server:app --reload

local-streamlit: ## Lance Streamlit localement
	streamlit run streamlit_app.py

local-stop: ## Arrête les services Docker
	docker compose down

.DEFAULT_GOAL := help
