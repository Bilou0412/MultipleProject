# Architecture et Évolutions - CVLM

## 🏗️ Nouvelle Architecture

Le projet a été refactorisé pour suivre les principes de **Clean Architecture** avec une séparation claire entre :

### 📦 Structure

```
CVLM/
├── domain/                      # Cœur métier (indépendant)
│   ├── entities/               # Entités du domaine
│   │   ├── user.py            # 👤 Utilisateur
│   │   ├── cv.py              # 📄 CV avec métadonnées
│   │   ├── job_offer.py       # 💼 Offre d'emploi
│   │   └── motivational_letter.py  # ✉️ Lettre de motivation
│   ├── ports/                 # Interfaces (abstractions)
│   │   ├── user_repository.py          # Interface repository User
│   │   ├── cv_repository.py            # Interface repository CV
│   │   ├── motivational_letter_repository.py
│   │   ├── file_storage.py             # Interface stockage fichiers
│   │   ├── document_parser.py          # Parser de documents
│   │   ├── llm_service.py              # Service LLM
│   │   └── pdf_generator.py            # Générateur PDF
│   └── use_cases/             # Logique métier
│       └── analyze_cv_and_offer.py
│
├── infrastructure/             # Implémentations concrètes
│   └── adapters/
│       ├── database_config.py                      # 🗄️ Configuration SQLAlchemy
│       ├── postgres_user_repository.py             # Repository User PostgreSQL
│       ├── postgres_cv_repository.py               # Repository CV PostgreSQL
│       ├── postgres_motivational_letter_repository.py
│       ├── local_file_storage.py                   # 📁 Stockage local fichiers
│       ├── pypdf_parse.py                          # Parser PyPDF
│       ├── Google_gemini_api.py                    # LLM Gemini
│       ├── open_ai_api.py                          # LLM OpenAI
│       ├── fpdf_generator.py                       # Générateur FPDF
│       └── weasyprint_generator.py                 # Générateur WeasyPrint
│
├── api_server.py               # 🚀 API FastAPI
├── streamlit_app.py            # 🎨 Interface Streamlit
├── init_database.py            # 🔧 Script initialisation DB
└── .env.example                # Configuration exemple
```

## 🆕 Nouveautés

### 1. **Gestion des Utilisateurs**
- Entité `User` avec authentification Google
- Repository PostgreSQL pour la persistance
- Préparation pour OAuth 2.0

### 2. **Base de Données PostgreSQL**
- Tables structurées : `users`, `cvs`, `motivational_letters`
- Relations entre utilisateurs, CVs et lettres
- Métadonnées complètes (timestamps, tailles, etc.)

### 3. **Séparation Stockage DB / Fichiers**
- **Base de données** : métadonnées uniquement
- **File Storage** : fichiers PDF physiques
- Interface abstraite permettant migration vers S3/Cloud

### 4. **Repositories Pattern**
- `UserRepository` : CRUD utilisateurs
- `CvRepository` : CRUD CVs par utilisateur
- `MotivationalLetterRepository` : CRUD lettres
- Facilite les tests et le changement de DB

## 🚀 Utilisation

### Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer PostgreSQL
cp .env.example .env
# Éditer .env avec vos credentials PostgreSQL
```

### Initialisation de la base

```bash
# Créer les tables
python init_database.py

# Réinitialiser la base (⚠️ supprime les données)
python init_database.py --reset
```

### Configuration PostgreSQL

1. **Installer PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Créer la base de données**
   ```sql
   sudo -u postgres psql
   CREATE DATABASE cvlm_db;
   CREATE USER cvlm_user WITH PASSWORD 'cvlm_password';
   GRANT ALL PRIVILEGES ON DATABASE cvlm_db TO cvlm_user;
   ```

3. **Configurer .env**
   ```env
   DATABASE_URL=postgresql://cvlm_user:cvlm_password@localhost:5432/cvlm_db
   ```

### Exemple d'utilisation avec persistance

```python
from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.open_ai_api import LlmOpenAI
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.local_file_storage import LocalFileStorage

# Initialiser les adaptateurs
parser = Pypdf_parser()
llm = LlmOpenAI()
pdf_gen = Fpdf_generator()
fetcher = WelcomeToTheJungleFetcher()

# Repositories et stockage
cv_repo = PostgresCvRepository()
letter_repo = PostgresMotivationalLetterRepository()
file_storage = LocalFileStorage()

# Use case avec persistance
use_case = AnalyseCvOffer(
    job_offer_fetcher=fetcher,
    document_parser=parser,
    llm=llm,
    pdf_generator=pdf_gen,
    cv_repository=cv_repo,
    letter_repository=letter_repo,
    file_storage=file_storage
)

# Générer avec sauvegarde en DB
pdf_path, letter_id = use_case.execute(
    cv_path="path/to/cv.pdf",
    jo_path="https://job-url.com",
    output_path="output/letter.pdf",
    use_scraper=True,
    user_id="user-uuid",
    cv_id="cv-uuid",
    persist=True  # Active la persistance
)

print(f"Lettre générée : {pdf_path}")
print(f"ID en base : {letter_id}")
```

## 🔮 Prochaines Étapes

### 1. Authentification Google OAuth
- [ ] Intégrer `authlib` ou `google-auth-oauthlib`
- [ ] Créer endpoints `/auth/login` et `/auth/callback`
- [ ] Middleware de vérification des tokens JWT
- [ ] Gestion des sessions utilisateur

### 2. API Multi-utilisateurs
- [ ] Endpoint `/users/me` (profil utilisateur)
- [ ] Filtrage des CVs par utilisateur authentifié
- [ ] Isolation des données par utilisateur

### 3. Migrations Alembic
- [ ] Initialiser Alembic : `alembic init migrations`
- [ ] Créer première migration : `alembic revision --autogenerate -m "Initial"`
- [ ] Appliquer : `alembic upgrade head`

### 4. Stockage Cloud (Optionnel)
- [ ] Créer `S3FileStorage` implémentant `FileStorage`
- [ ] Configuration AWS S3 / GCP Storage
- [ ] Migration progressive des fichiers

### 5. Tests
- [ ] Tests unitaires des repositories
- [ ] Tests d'intégration avec DB test
- [ ] Tests E2E de l'API

## 📝 Notes Importantes

### Rétrocompatibilité
L'ancien code continue de fonctionner ! Les paramètres `cv_repository`, `letter_repository` et `file_storage` sont **optionnels**. Sans eux, le système fonctionne comme avant (sans persistance).

### Migration Progressive
1. **Phase actuelle** : Stockage mémoire (dict) fonctionne
2. **Phase 1** : Activer la persistance DB pour nouveaux utilisateurs
3. **Phase 2** : Migrer les données existantes
4. **Phase 3** : Retirer le stockage mémoire

### Variables d'Environnement
- `DATABASE_URL` : URL PostgreSQL
- `OPENAI_API_KEY` : Clé API OpenAI
- `GOOGLE_API_KEY` : Clé API Google Gemini
- `GOOGLE_CLIENT_ID` : OAuth Google
- `GOOGLE_CLIENT_SECRET` : OAuth Google
- `FILE_STORAGE_BASE_PATH` : Chemin stockage local

## 🎯 Avantages de la Nouvelle Architecture

✅ **Testabilité** : Injection de dépendances via interfaces  
✅ **Flexibilité** : Changement de DB/LLM sans toucher au domaine  
✅ **Scalabilité** : Prêt pour multi-utilisateurs  
✅ **Maintenabilité** : Séparation claire des responsabilités  
✅ **Évolutivité** : Ajout facile de nouvelles fonctionnalités  

## 🛠️ Dépendances Ajoutées

```txt
sqlalchemy==2.0.40      # ORM pour PostgreSQL
psycopg2-binary==2.9.10 # Driver PostgreSQL
alembic==1.16.1         # Migrations de schéma
```
