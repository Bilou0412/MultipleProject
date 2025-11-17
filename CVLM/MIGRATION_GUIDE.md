# 🚀 Migration PostgreSQL + Auth Google - Guide Complet

## ✅ Ce qui a été fait

### 1. Backend API (api_server.py)
- ✅ **Authentification Google** : Endpoint `/auth/google` pour valider les tokens Google
- ✅ **PostgreSQL** : Tous les endpoints utilisent maintenant PostgreSQL avec fallback legacy
- ✅ **User Management** : Utilisateur par défaut créé automatiquement pour la transition
- ✅ **File Storage** : Système de stockage abstrait avec LocalFileStorage
- ✅ **Rétrocompatibilité** : Le système fonctionne avec et sans PostgreSQL

### 2. Infrastructure
- ✅ **google_oauth_service.py** : Service de validation des tokens Google ID
- ✅ **auth_middleware.py** : Middleware JWT pour FastAPI
- ✅ **PostgreSQL Repositories** : User, CV, MotivationalLetter
- ✅ **LocalFileStorage** : Gestion des fichiers PDF

### 3. Configuration
- ✅ **requirements.txt** : Ajout de python-jose, google-auth, python-multipart
- ✅ **Docker Compose** : Configuration sans GOOGLE_CLIENT_SECRET
- ✅ **Makefile** : Syntaxe Docker Compose v2

## 🔧 Ce qu'il reste à faire

### Extension Chrome (en cours)
1. **generator.js** : Ajouter l'authentification Google
2. **background.js** : Gérer les tokens JWT
3. **Tester le flow complet**

## 🚀 Lancement immédiat

### Option 1 : Sans authentification (mode legacy)
```bash
make up
make init
```

Accès :
- API : http://localhost:8000
- Docs : http://localhost:8000/docs
- Streamlit : http://localhost:8501

### Option 2 : Avec PostgreSQL (recommandé)
```bash
# 1. Démarrer les services
make up

# 2. Initialiser la base de données
make init

# 3. Tester l'API
curl http://localhost:8000/health
curl http://localhost:8000/auth/me
```

### Tester l'authentification Google

```bash
# Test avec un faux token (va échouer mais montre que l'endpoint existe)
curl -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{"google_token": "fake_token"}'
```

## 📝 Endpoints disponibles

### ✅ Sans auth (fonctionne immédiatement)
- `GET /health` - Santé de l'API
- `GET /auth/me` - Utilisateur par défaut
- `POST /upload-cv` - Upload CV
- `GET /list-cvs` - Liste des CVs
- `POST /generate-cover-letter` - Génération lettre
- `DELETE /cleanup/{cv_id}` - Suppression CV

### 🔐 Avec auth (en préparation)
- `POST /auth/google` - Authentification Google (implémenté)
- Tous les endpoints ci-dessus avec token JWT dans le header

## 🔐 Flow d'authentification prévu

```
1. Extension Chrome
   └─> chrome.identity.getAuthToken()
   └─> Reçoit un token Google ID

2. Envoyer à l'API
   POST /auth/google
   Body: {"google_token": "..."}
   
3. API répond
   {
     "status": "success",
     "access_token": "JWT_TOKEN",
     "user": {
       "id": "...",
       "email": "user@example.com",
       "name": "John Doe"
     }
   }

4. Extension stocke le JWT
   chrome.storage.local.set({"jwt_token": "..."})

5. Futures requêtes
   Authorization: Bearer JWT_TOKEN
```

## 📊 Architecture actuelle

```
┌─────────────────────┐
│  Chrome Extension   │
│                     │
│  generator.js       │◄─── À ADAPTER
│  background.js      │◄─── À ADAPTER
└──────────┬──────────┘
           │
           │ HTTP
           ▼
┌─────────────────────┐
│   FastAPI (8000)    │
│                     │
│  ✅ /auth/google    │
│  ✅ /auth/me        │
│  ✅ /upload-cv      │
│  ✅ /list-cvs       │
│  ✅ /generate-...   │
└──────────┬──────────┘
           │
           ├─────────┬──────────────┐
           │         │              │
           ▼         ▼              ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │PostgreSQL│ │Google API│ │FileSystem│
    │   (DB)   │ │  (Auth)  │ │  (PDFs)  │
    └──────────┘ └──────────┘ └──────────┘
```

## 🐛 Debugging

### Vérifier que PostgreSQL fonctionne
```bash
make shell-db
# Dans le shell PostgreSQL :
\dt  # Liste les tables
SELECT * FROM users;
SELECT * FROM cvs;
```

### Logs en temps réel
```bash
make logs           # Tous les services
make logs-api       # API uniquement
make logs-db        # PostgreSQL uniquement
```

### Statut des services
```bash
make status
```

## ⚠️ Notes importantes

1. **Mode transition** : L'API fonctionne actuellement avec un utilisateur par défaut (`default@cvlm.com`)
2. **Authentification** : Les endpoints d'auth sont implémentés mais pas encore utilisés par l'extension
3. **Rétrocompatibilité** : Le système fonctionne avec l'ancien storage en mémoire ET PostgreSQL
4. **Extension Chrome** : Nécessite adaptation pour utiliser l'authentification Google

## 🎯 Prochaines étapes

1. **Tester le démarrage** : `make up && make init`
2. **Vérifier l'API** : http://localhost:8000/docs
3. **Adapter l'extension** : Ajouter l'auth Google dans generator.js
4. **Test end-to-end** : Générer une lettre depuis l'extension

## 📞 Besoin d'aide ?

Si tu rencontres des erreurs :
1. Vérifie les logs : `make logs`
2. Vérifie le fichier `.env` (doit avoir GOOGLE_CLIENT_ID, OPENAI_API_KEY, etc.)
3. Redémarre proprement : `make down && make up && make init`
