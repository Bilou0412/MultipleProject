# CVLM - Générateur de Lettres de Motivation# CVLM - Générateur de Lettres de Motivation



[![Clean Architecture](https://img.shields.io/badge/architecture-clean-blue.svg)](ARCHITECTURE.md)[![Clean Architecture](https://img.shields.io/badge/architecture-clean-blue.svg)](ARCHITECTURE.md)

[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](requirements.txt)[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](requirements.txt)



> Extension navigateur + API pour générer automatiquement des lettres de motivation personnalisées à partir de CVs et d'offres d'emploi.## 🎯 Objectif



---Extension navigateur pour générer automatiquement des lettres de motivation personnalisées.



## 🎯 Vue d'ensemble**Workflow** :

1. 🔐 Connexion Google OAuth

**Workflow utilisateur** :2. 📄 Upload de votre CV  

1. 🔐 Connexion Google OAuth (authentification sécurisée)3. 🌐 Navigation sur une offre d'emploi

2. 📄 Upload du CV au format PDF4. ✨ Génération automatique de la lettre

3. 🌐 Navigation sur une offre d'emploi (Welcome to the Jungle)5. 💾 Téléchargement au format PDF

4. ✨ Génération automatique de la lettre (LLM + PDF)

5. 💾 Téléchargement ou injection directe dans formulaire---



**Technologies** : FastAPI + PostgreSQL 16 + OpenAI GPT-4 + Docker + Chrome Extension## 🏗️ Architecture Clean



---```

CVLM/

## 🏗️ Architecture Clean├── domain/                    # ⭐ Cœur métier (pur)

│   ├── entities/              # user, cv, motivational_letter, job_offer

```│   ├── ports/                 # Interfaces (ABC)

CVLM/│   └── use_cases/             # Logique métier

├── api/                       # 🚀 API modulaire FastAPI│

│   ├── main.py                # Point d'entrée├── infrastructure/adapters/   # 🔧 Implémentations

│   ├── routes/                # 7 modules de routes│   ├── postgres_*_repository.py

│   ├── models/                # Pydantic schemas│   ├── open_ai_api.py / google_gemini_api.py

│   └── dependencies.py        # Injection de dépendances│   ├── pypdf_parse.py

││   ├── fpdf_generator.py / weasyprint_generator.py

├── domain/                    # ⭐ Cœur métier (logique pure)│   └── google_oauth_service.py

│   ├── entities/              # user, cv, motivational_letter│

│   ├── ports/                 # Interfaces (ABC)├── extension/                 # 🧩 Chrome Extension

│   ├── services/              # Services métier│   ├── manifest.json          # Manifest v3

│   └── use_cases/             # Cas d'usage│   ├── generator.js           # Popup avec auth

││   └── content.js             # Injection dans pages

├── infrastructure/adapters/   # 🔧 Implémentations techniques│

│   ├── postgres_*_repository.py  # Persistance DB└── api_server.py              # 🚀 FastAPI

│   ├── open_ai_api.py            # LLM OpenAI```

│   ├── google_gemini_api.py      # LLM Gemini

│   ├── pypdf_parse.py            # Parser PDF**Stack** : FastAPI + PostgreSQL + OAuth + OpenAI GPT + Docker

│   ├── fpdf_generator.py         # Génération PDF

│   └── google_oauth_service.py   # OAuth Google---

│

├── extension/                 # 🧩 Extension Chrome (Manifest v3)## ⚙️ Installation

│   ├── manifest.json

│   ├── generator.html/js      # Popup principale```bash

│   ├── content.js             # Injection dans pages# 1. Configuration

│   └── admin.html/js          # Dashboard admincp .env.example .env

│# Éditer .env avec vos clés API

└── config/                    # ⚙️ Configuration

    ├── constants.py           # Constantes# 2. Lancement

    └── logger_config.py       # Logging centralisédocker compose up -d

```

# 3. Vérification

**Principes respectés** :curl http://localhost:8000/health

- ✅ **Clean Architecture** : Domain indépendant de l'infrastructure```

- ✅ **SOLID** : Responsabilité unique, Dependency Inversion

- ✅ **DRY** : Pas de duplication, code réutilisable---

- ✅ **Dependency Injection** : Testabilité maximale

## 🚀 Utilisation

---

### Extension Chrome

## ⚡ Installation Rapide

1. Ouvrir `chrome://extensions/`

### Prérequis2. Activer "Mode développeur"

- Docker + Docker Compose3. "Charger l'extension non empaquetée" → `extension/`

- Clés API : OpenAI, Google OAuth4. Se connecter avec Google

5. Uploader votre CV

### Configuration6. Générer des lettres sur les offres d'emploi



```bash---

# 1. Copier la configuration

cp .env.example .env## 📝 Conventions Clean Code



# 2. Éditer .env avec vos clés API- **Classes** : PascalCase (`OpenAiLlm`, `PyPdfParser`)

nano .env- **Fonctions** : snake_case (`parse_document`, `send_to_llm`)

- **Domain** : Aucune dépendance externe

# Variables requises :- **Ports** : Interfaces ABC avec `@abstractmethod`

# - OPENAI_API_KEY=sk-...- **Adapters** : Implémentent les ports

# - GOOGLE_CLIENT_ID=...

# - GOOGLE_CLIENT_SECRET=...---

# - JWT_SECRET=... (généré automatiquement)

```## 🔧 Développement



### Lancement```bash

# Rebuild API

```bashdocker compose build api && docker compose up -d api

# Démarrer l'API + PostgreSQL

docker compose up -d# Logs

docker compose logs -f api

# Vérifier la santé

curl http://localhost:8000/health# Reset complet

# {"status":"healthy","version":"2.0.0"}docker compose down -v && docker compose up -d

```

# Voir les logs

docker compose logs -f api---

```

## 📚 Documentation

**C'est prêt !** L'API tourne sur `http://localhost:8000` 🚀

- [ARCHITECTURE.md](ARCHITECTURE.md) - Détails architecture

---- [Makefile](Makefile) - Commandes utiles



## 📱 Extension Chrome---



### Installation## ✅ Fonctionnalités

1. Ouvrir `chrome://extensions/`

2. Activer **"Mode développeur"** (toggle en haut à droite)- ✅ Auth Google OAuth + JWT

3. Cliquer **"Charger l'extension non empaquetée"**- ✅ Upload et stockage de CVs

4. Sélectionner le dossier `extension/`- ✅ Extraction texte des PDFs  

- ✅ Génération OpenAI GPT / Gemini

### Utilisation- ✅ Export PDF (FPDF/WeasyPrint)

1. Cliquer sur l'icône CVLM dans la barre d'outils- ✅ Multi-utilisateurs

2. Se connecter avec Google- ✅ Injection dans textareas web

3. Uploader son CV (PDF, max 10MB)

4. Naviguer sur une offre d'emploi---

5. Générer la lettre (bouton "Générer")

6. Télécharger ou injecter dans le formulaire**Version** : 1.5.0 - Clean Architecture Edition


---

## 🔐 API Endpoints

### Authentification
- `POST /auth/google` - Connexion Google OAuth
- `GET /auth/me` - Informations utilisateur

### Gestion CVs
- `POST /upload-cv` - Upload CV (PDF, 10MB max)
- `GET /list-cvs` - Liste des CVs
- `DELETE /cleanup/{cv_id}` - Suppression CV

### Génération
- `POST /generate-cover-letter` - Lettre PDF (1 crédit PDF)
- `POST /generate-text` - Texte motivation (1 crédit texte)
- `GET /list-letters` - Liste des lettres générées

### Historique
- `GET /user/history` - Historique avec pagination
- `GET /user/history/stats` - Statistiques utilisateur
- `GET /user/history/{id}/download` - Télécharger PDF

### Administration (is_admin=true)
- `GET /admin/stats` - Dashboard statistiques
- `GET /admin/users` - Liste utilisateurs
- `POST /admin/users/credits` - Modifier crédits
- `GET /admin/promo-codes` - Gestion codes promo

**Documentation complète** : `http://localhost:8000/docs` (Swagger UI)

---

## 🔧 Développement

### Commandes Docker

```bash
# Rebuild après modification code
docker compose build api
docker compose up -d api

# Voir les logs en temps réel
docker compose logs -f api

# Accéder au shell du container
docker compose exec api bash

# Reset complet (⚠️ supprime la DB)
docker compose down -v
docker compose up -d
```

### Structure Modulaire

L'API est organisée en **7 modules indépendants** :

```python
# api/routes/
auth.py        # Authentification (2 endpoints)
user.py        # Utilisateur (1 endpoint)
cv.py          # Gestion CVs (3 endpoints)
generation.py  # Génération lettres (3 endpoints)
admin.py       # Administration (10 endpoints)
history.py     # Historique (6 endpoints)
download.py    # Téléchargement (2 endpoints)
```

Chaque module est **autonome** et **testable** indépendamment.

---

## 🎨 Conventions de Code

### Nommage
- **Classes** : `PascalCase` (`OpenAiLlm`, `PostgresCvRepository`)
- **Fonctions** : `snake_case` (`parse_document`, `send_to_llm`)
- **Constantes** : `UPPER_SNAKE_CASE` (`MAX_FILE_SIZE`, `DEFAULT_PDF_CREDITS`)
- **Fichiers** : `snake_case.py` (`cv_repository.py`, `promo_code_service.py`)

### Clean Architecture
- **domain/** : Aucune dépendance externe (pure Python)
- **ports/** : Interfaces ABC avec `@abstractmethod`
- **adapters/** : Implémentent les ports (PostgreSQL, OpenAI, etc.)
- **api/** : Couche HTTP (FastAPI, Pydantic)

### Logging
```python
# ✅ BON
from config.logger_config import logger
logger.info("CV uploaded successfully")
logger.error(f"Error generating letter: {error}")

# ❌ MAUVAIS
print("CV uploaded")  # Ne pas utiliser print()
```

---

## 📊 Fonctionnalités

### Utilisateur
- ✅ Authentification Google OAuth 2.0
- ✅ JWT tokens (7 jours de validité)
- ✅ Upload CV multi-format (validation 10MB)
- ✅ Historique des générations (pagination)
- ✅ Statistiques personnelles (success rate, total)
- ✅ Export historique (JSON)

### Génération
- ✅ LLM multi-provider (OpenAI GPT-4, Google Gemini)
- ✅ PDF generator multi-backend (FPDF, WeasyPrint)
- ✅ Scraping offres d'emploi (Welcome to the Jungle)
- ✅ Extraction texte PDF (PyPDF)
- ✅ Personnalisation lettre par LLM
- ✅ Injection directe dans formulaires web

### Administration
- ✅ Dashboard statistiques (users, générations)
- ✅ Gestion utilisateurs (crédits, droits admin)
- ✅ Codes promo (création, activation, suppression)
- ✅ RBAC (Role-Based Access Control)
- ✅ Audit logs

### Technique
- ✅ Clean Architecture (domain/ports/adapters)
- ✅ SOLID principles respectés
- ✅ Dependency Injection (testabilité)
- ✅ Exception handling centralisé
- ✅ Logging structuré
- ✅ Docker multi-container
- ✅ PostgreSQL 16 avec indexes
- ✅ CORS configuré

---

## 📚 Documentation Technique

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture détaillée, diagrammes, patterns
- **[.env.example](.env.example)** - Variables d'environnement
- **Swagger UI** - `http://localhost:8000/docs` (interactive)
- **ReDoc** - `http://localhost:8000/redoc` (documentation)

---

## 🔒 Sécurité

- ✅ JWT tokens avec expiration (7 jours)
- ✅ Google OAuth sécurisé (client credentials)
- ✅ Validation stricte uploads (size, MIME type)
- ✅ RBAC pour endpoints admin
- ✅ Secrets en variables d'environnement
- ✅ CORS configuré (origins whitelist)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ⚠️ Rate limiting (à implémenter)

---

## 🚀 Roadmap

### Court terme
- [ ] Tests unitaires (70%+ coverage)
- [ ] Rate limiting (slowapi)
- [ ] Monitoring Prometheus

### Moyen terme
- [ ] Cache Redis (CVs parsés)
- [ ] Background tasks (Celery)
- [ ] CI/CD (GitHub Actions)

### Long terme
- [ ] Support LinkedIn scraping
- [ ] Export multi-formats (DOCX, TXT)
- [ ] Templates lettres personnalisables

---

## 📄 Licence

**Propriétaire** - Usage interne uniquement

---

## 🤝 Contact

**Développeur** : Clean Architecture Team  
**Version** : 2.0.0  
**Dernière mise à jour** : Novembre 2025

---

**🎉 Prêt à générer des lettres de motivation automatiquement !**
