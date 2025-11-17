# CVLM - Générateur de Lettres de Motivation Intelligent

## 🎯 Objectif

Application complète pour générer automatiquement des lettres de motivation personnalisées à partir :
- d'un **CV** (PDF)
- d'une **offre d'emploi** (URL ou PDF)
- en utilisant des **LLM** (OpenAI GPT, Google Gemini)

## ✨ Fonctionnalités

- 📄 **Parsing intelligent** de CVs en PDF
- 🌐 **Scraping** d'offres d'emploi (Welcome to the Jungle)
- 🤖 **LLM multi-providers** (OpenAI, Google Gemini)
- 📝 **Génération PDF** personnalisée (FPDF, WeasyPrint)
- 🗄️ **Base de données PostgreSQL** pour persistance
- 👤 **Multi-utilisateurs** (prêt pour OAuth Google)
- 🔌 **API REST** FastAPI
- 🎨 **Interface Streamlit** conviviale
- 🧩 **Extension navigateur** Chrome/Firefox

## 🏗️ Architecture

Le projet suit une **Clean Architecture** avec séparation stricte :

```
CVLM/
├── domain/              # Logique métier (indépendante)
│   ├── entities/       # Entités : User, CV, MotivationalLetter
│   ├── ports/          # Interfaces (repositories, services)
│   └── use_cases/      # Cas d'usage métier
│
├── infrastructure/     # Implémentations techniques
│   └── adapters/       # Adaptateurs (PostgreSQL, LLM, PDF, etc.)
│
├── api_server.py       # API FastAPI
├── streamlit_app.py    # Interface web
└── extension/          # Extension navigateur
```

📖 Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour plus de détails.

## ⚙️ Installation

### 1. Cloner le projet
```bash
git clone <repo-url>
cd CVLM
```

### 2. Créer un environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer PostgreSQL

```bash
# Installer PostgreSQL (si nécessaire)
sudo apt install postgresql  # Linux
brew install postgresql      # macOS

# Créer la base de données
sudo -u postgres psql
```

```sql
CREATE DATABASE cvlm_db;
CREATE USER cvlm_user WITH PASSWORD 'cvlm_password';
GRANT ALL PRIVILEGES ON DATABASE cvlm_db TO cvlm_user;
\q
```

### 5. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

Exemple de `.env` :
```env
DATABASE_URL=postgresql://cvlm_user:cvlm_password@localhost:5432/cvlm_db
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

### 6. Initialiser la base de données

```bash
python init_database.py
```

## 🚀 Utilisation

### Option 1 : Interface Streamlit (Recommandé)

```bash
streamlit run streamlit_app.py
```

Ouvrir http://localhost:8501

### Option 2 : API REST

```bash
uvicorn api_server:app --reload
```

API disponible sur http://localhost:8000  
Documentation interactive : http://localhost:8000/docs

### Option 3 : CLI

```bash
python cli_interface.py
```

### Option 4 : Extension Navigateur

1. Ouvrir Chrome/Firefox
2. Aller dans Extensions > Mode développeur
3. Charger l'extension non empaquetée depuis `extension/`
4. Naviguer sur une offre d'emploi Welcome to the Jungle
5. Cliquer sur l'icône CVLM

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture détaillée et évolutions
- [GOOGLE_AUTH_GUIDE.md](GOOGLE_AUTH_GUIDE.md) - Guide d'intégration OAuth Google
- [metodo/Methodo.md](metodo/Methodo.md) - Méthodologie du projet

## 🔧 Scripts Utiles

```bash
# Initialiser/réinitialiser la base de données
python init_database.py [--reset]

# Migrer des données existantes
python migrate_data.py

# Tests (à venir)
pytest

# Générer les migrations Alembic (à venir)
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## 🗄️ Gestion des Données

### Stockage
- **Métadonnées** : PostgreSQL (users, cvs, motivational_letters)
- **Fichiers PDF** : Système de fichiers local (`data/files/`)
- **Migration vers S3** : Possible via interface `FileStorage`

### Repositories
- `UserRepository` : Gestion des utilisateurs
- `CvRepository` : Gestion des CVs par utilisateur
- `MotivationalLetterRepository` : Gestion des lettres générées

## 🎨 Interfaces

### API Endpoints (FastAPI)

```http
# Santé de l'API
GET /health

# Upload CV
POST /upload-cv

# Liste des CVs
GET /list-cvs

# Génération de lettre
POST /generate-cover-letter
  - cv_id
  - job_url
  - llm_provider (openai|gemini)
  - pdf_generator (fpdf|weasyprint)

# Téléchargement
GET /download/{file_id}

# Génération de texte (pour extension)
POST /generate-text
```

### Streamlit Interface
- Upload de CV
- Saisie URL ou upload PDF offre d'emploi
- Choix du LLM et générateur PDF
- Génération et téléchargement

## 🔮 Roadmap

### ✅ Phase 1 - Terminée
- [x] Architecture Clean Architecture
- [x] Base de données PostgreSQL
- [x] Repositories pattern
- [x] Séparation DB / File Storage
- [x] Multi-LLM support (OpenAI, Gemini)

### 🚧 Phase 2 - En cours
- [ ] Authentification Google OAuth 2.0
- [ ] Gestion multi-utilisateurs complète
- [ ] API sécurisée avec JWT
- [ ] Migrations Alembic

### 📋 Phase 3 - À venir
- [ ] Tests unitaires et d'intégration
- [ ] Stockage S3 (optionnel)
- [ ] Interface admin
- [ ] Historique des modifications
- [ ] Export/Import de données
- [ ] Amélioration de l'extension navigateur

## 🛠️ Technologies

- **Backend** : Python 3.10+
- **Framework Web** : FastAPI
- **Interface** : Streamlit
- **Base de données** : PostgreSQL + SQLAlchemy
- **LLM** : OpenAI GPT, Google Gemini
- **PDF** : PyPDF2, FPDF2, WeasyPrint
- **Scraping** : BeautifulSoup4
- **Async** : aiohttp

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir les issues GitHub pour les tâches en cours.

## 📄 Licence

[À définir]

## 👨‍💻 Auteur

Développé avec ❤️ pour simplifier la recherche d'emploi.
