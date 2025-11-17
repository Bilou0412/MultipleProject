# CVLM - Générateur de Lettres de Motivation

[![Clean Architecture](https://img.shields.io/badge/architecture-clean-blue.svg)](ARCHITECTURE.md)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](requirements.txt)

## 🎯 Objectif

Extension navigateur pour générer automatiquement des lettres de motivation personnalisées.

**Workflow** :
1. 🔐 Connexion Google OAuth
2. 📄 Upload de votre CV  
3. 🌐 Navigation sur une offre d'emploi
4. ✨ Génération automatique de la lettre
5. 💾 Téléchargement au format PDF

---

## 🏗️ Architecture Clean

```
CVLM/
├── domain/                    # ⭐ Cœur métier (pur)
│   ├── entities/              # user, cv, motivational_letter, job_offer
│   ├── ports/                 # Interfaces (ABC)
│   └── use_cases/             # Logique métier
│
├── infrastructure/adapters/   # 🔧 Implémentations
│   ├── postgres_*_repository.py
│   ├── open_ai_api.py / google_gemini_api.py
│   ├── pypdf_parse.py
│   ├── fpdf_generator.py / weasyprint_generator.py
│   └── google_oauth_service.py
│
├── extension/                 # 🧩 Chrome Extension
│   ├── manifest.json          # Manifest v3
│   ├── generator.js           # Popup avec auth
│   └── content.js             # Injection dans pages
│
└── api_server.py              # 🚀 FastAPI
```

**Stack** : FastAPI + PostgreSQL + OAuth + OpenAI GPT + Docker

---

## ⚙️ Installation

```bash
# 1. Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# 2. Lancement
docker compose up -d

# 3. Vérification
curl http://localhost:8000/health
```

---

## 🚀 Utilisation

### Extension Chrome

1. Ouvrir `chrome://extensions/`
2. Activer "Mode développeur"
3. "Charger l'extension non empaquetée" → `extension/`
4. Se connecter avec Google
5. Uploader votre CV
6. Générer des lettres sur les offres d'emploi

---

## 📝 Conventions Clean Code

- **Classes** : PascalCase (`OpenAiLlm`, `PyPdfParser`)
- **Fonctions** : snake_case (`parse_document`, `send_to_llm`)
- **Domain** : Aucune dépendance externe
- **Ports** : Interfaces ABC avec `@abstractmethod`
- **Adapters** : Implémentent les ports

---

## 🔧 Développement

```bash
# Rebuild API
docker compose build api && docker compose up -d api

# Logs
docker compose logs -f api

# Reset complet
docker compose down -v && docker compose up -d
```

---

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Détails architecture
- [Makefile](Makefile) - Commandes utiles

---

## ✅ Fonctionnalités

- ✅ Auth Google OAuth + JWT
- ✅ Upload et stockage de CVs
- ✅ Extraction texte des PDFs  
- ✅ Génération OpenAI GPT / Gemini
- ✅ Export PDF (FPDF/WeasyPrint)
- ✅ Multi-utilisateurs
- ✅ Injection dans textareas web

---

**Version** : 1.5.0 - Clean Architecture Edition
