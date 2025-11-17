# 🏗️ Diagramme d'Architecture CVLM

## Vue d'ensemble - Clean Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERFACES UTILISATEUR                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Streamlit   │  │  FastAPI     │  │  Extension   │             │
│  │  Web UI      │  │  REST API    │  │  Navigateur  │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                          USE CASES (Domain)                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  AnalyseCvOffer                                              │   │
│  │  - execute(cv_path, jo_path, user_id, persist)              │   │
│  │  - _create_prompt()                                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼──────────────┐          ┌──────────▼──────────────┐
│   DOMAIN ENTITIES      │          │    DOMAIN PORTS         │
│  ┌──────────────────┐  │          │  ┌──────────────────┐  │
│  │ User             │  │          │  │ UserRepository   │  │
│  │ - id             │  │          │  │ CvRepository     │  │
│  │ - email          │  │          │  │ LetterRepository │  │
│  │ - google_id      │  │          │  │ FileStorage      │  │
│  └──────────────────┘  │          │  │ LlmService       │  │
│  ┌──────────────────┐  │          │  │ DocumentParser   │  │
│  │ Cv               │  │          │  │ PdfGenerator     │  │
│  │ - id, user_id    │  │          │  │ JobOfferFetcher  │  │
│  │ - file_path      │  │          │  └──────────────────┘  │
│  │ - raw_text       │  │          │     (Interfaces ABC)    │
│  └──────────────────┘  │          └─────────────────────────┘
│  ┌──────────────────┐  │
│  │MotivationalLetter│  │
│  │ - id, user_id    │  │
│  │ - cv_id          │  │
│  │ - file_path      │  │
│  └──────────────────┘  │
└────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼─────────────────────┐   ┌──────────▼───────────────────┐
│   INFRASTRUCTURE ADAPTERS     │   │   INFRASTRUCTURE ADAPTERS    │
│   (Repositories)              │   │   (Services)                 │
│  ┌─────────────────────────┐  │   │  ┌────────────────────────┐ │
│  │ PostgresUserRepository  │  │   │  │ LocalFileStorage       │ │
│  │ PostgresCvRepository    │  │   │  │ (Future: S3Storage)    │ │
│  │ PostgresLetterRepository│  │   │  └────────────────────────┘ │
│  └─────────────────────────┘  │   │  ┌────────────────────────┐ │
│                                │   │  │ LlmOpenAI              │ │
│  ┌─────────────────────────┐  │   │  │ LlmGemini              │ │
│  │ database_config.py      │  │   │  └────────────────────────┘ │
│  │ - UserModel             │  │   │  ┌────────────────────────┐ │
│  │ - CvModel               │  │   │  │ Pypdf_parser           │ │
│  │ - LetterModel           │  │   │  └────────────────────────┘ │
│  │ - SQLAlchemy config     │  │   │  ┌────────────────────────┐ │
│  └─────────────────────────┘  │   │  │ Fpdf_generator         │ │
│                                │   │  │ WeasyPrintGenerator    │ │
└────────────────────────────────┘   │  └────────────────────────┘ │
                                     │  ┌────────────────────────┐ │
                                     │  │ WelcomeToJungleFetcher │ │
                                     │  └────────────────────────┘ │
                                     └────────────────────────────────┘
                                                  │
                                     ┌────────────┴─────────────┐
                                     │                          │
                          ┌──────────▼──────────┐    ┌─────────▼─────────┐
                          │   PostgreSQL DB     │    │  File System      │
                          │  - users            │    │  data/files/      │
                          │  - cvs              │    │  - cvs/           │
                          │  - letters          │    │  - letters/       │
                          └─────────────────────┘    └───────────────────┘
```

## Flux de Données - Génération de Lettre

```
1. UPLOAD CV
   User → [Streamlit/API] → FileStorage.save_file() 
                         → CvRepository.create() → PostgreSQL
                         
2. GÉNÉRATION LETTRE
   User → [Interface] 
        ↓
   AnalyseCvOffer.execute(cv_id, job_url, user_id, persist=True)
        ↓
   CvRepository.get_by_id(cv_id) ← PostgreSQL
        ↓
   JobOfferFetcher.fetch(url) → Scraping
        ↓
   LlmService.send_to_llm(prompt) → OpenAI/Gemini API
        ↓
   PdfGenerator.create_pdf() → File System
        ↓
   FileStorage.save_file() → data/files/letters/
        ↓
   LetterRepository.create() → PostgreSQL
        ↓
   [Response] → User (path + letter_id)
```

## Flux d'Authentification (Future)

```
1. LOGIN
   User clicks "Login with Google"
        ↓
   GET /auth/login → AuthService.get_authorization_url()
        ↓
   Redirect to Google OAuth
        ↓
   User authenticates
        ↓
   Google redirects to /auth/callback?code=...
        ↓
   AuthService.authenticate_with_code(code)
        ↓
   UserRepository.get_by_google_id() ou create()
        ↓
   AuthService.create_token(user) → JWT
        ↓
   Response: { token, user }

2. PROTECTED ROUTE
   Request with "Authorization: Bearer JWT"
        ↓
   Middleware: AuthService.verify_token(JWT)
        ↓
   UserRepository.get_by_id()
        ↓
   Route handler with current_user
```

## Dépendances entre Couches

```
┌──────────────────────────────────────────────────────────┐
│                   RÈGLES DE DÉPENDANCE                   │
│                                                          │
│  ✅ Infrastructure → Domain (imports autorisés)         │
│  ✅ Use Cases → Entities + Ports                        │
│  ✅ Adapters → Ports (implémentent les interfaces)      │
│                                                          │
│  ❌ Domain → Infrastructure (interdit !)                │
│  ❌ Entities → Use Cases (interdit !)                   │
│  ❌ Ports → Adapters (interdit !)                       │
│                                                          │
│  Principe : Les dépendances pointent TOUJOURS vers le   │
│             centre (Domain) via des INTERFACES           │
└──────────────────────────────────────────────────────────┘
```

## Structure de Fichiers

```
CVLM/
│
├── domain/                          # ← CŒUR (Indépendant)
│   ├── entities/
│   │   ├── user.py                 # Entité métier
│   │   ├── cv.py                   # Entité métier
│   │   ├── job_offer.py            # Entité métier
│   │   └── motivational_letter.py  # Entité métier
│   │
│   ├── ports/                       # ← INTERFACES
│   │   ├── user_repository.py      # Interface ABC
│   │   ├── cv_repository.py        # Interface ABC
│   │   ├── motivational_letter_repository.py
│   │   ├── file_storage.py         # Interface ABC
│   │   ├── llm_service.py          # Interface ABC
│   │   ├── document_parser.py      # Interface ABC
│   │   ├── pdf_generator.py        # Interface ABC
│   │   └── job_offer_fetcher.py    # Interface ABC
│   │
│   └── use_cases/                   # ← LOGIQUE MÉTIER
│       └── analyze_cv_and_offer.py
│
├── infrastructure/                  # ← IMPLÉMENTATIONS
│   └── adapters/
│       ├── database_config.py           # SQLAlchemy config
│       ├── postgres_user_repository.py  # Implémentation
│       ├── postgres_cv_repository.py    # Implémentation
│       ├── postgres_motivational_letter_repository.py
│       ├── local_file_storage.py        # Implémentation
│       ├── open_ai_api.py              # Implémentation
│       ├── Google_gemini_api.py        # Implémentation
│       ├── pypdf_parse.py              # Implémentation
│       ├── fpdf_generator.py           # Implémentation
│       ├── weasyprint_generator.py     # Implémentation
│       └── welcome_to_jungle_scraper.py # Implémentation
│
├── api_server.py                    # FastAPI app
├── streamlit_app.py                 # Streamlit UI
├── cli_interface.py                 # CLI
├── init_database.py                 # DB init script
├── migrate_data.py                  # Migration script
│
├── .env.example                     # Config template
├── requirements.txt                 # Dependencies
├── README_NEW.md                    # Documentation
├── ARCHITECTURE.md                  # Architecture doc
└── GOOGLE_AUTH_GUIDE.md            # OAuth guide
```

## Avantages de cette Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ TESTABILITÉ                                             │
│     - Mock des ports pour tests unitaires                   │
│     - Tests isolés du domaine sans DB                       │
│                                                             │
│  ✅ MAINTENABILITÉ                                          │
│     - Changements localisés dans les adaptateurs            │
│     - Domaine stable et protégé                             │
│                                                             │
│  ✅ FLEXIBILITÉ                                             │
│     - Changement de DB : nouveau repository                 │
│     - Nouveau LLM : nouvel adaptateur                       │
│     - Passage S3 : nouveau FileStorage                      │
│                                                             │
│  ✅ SCALABILITÉ                                             │
│     - PostgreSQL supporte millions d'utilisateurs           │
│     - Stockage S3 illimité                                  │
│     - Microservices possibles (séparer use cases)           │
│                                                             │
│  ✅ INDÉPENDANCE TECHNOLOGIQUE                              │
│     - Le domaine ne connaît pas PostgreSQL                  │
│     - Le domaine ne connaît pas FastAPI                     │
│     - Le domaine est pur Python                             │
└─────────────────────────────────────────────────────────────┘
```
