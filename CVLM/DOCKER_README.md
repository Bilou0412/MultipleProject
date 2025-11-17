# 🐳 Docker - Guide Rapide

## Démarrage Ultra-Rapide

```bash
# 1. Configurer
cp .env.example .env
# Éditer .env avec vos clés API

# 2. Démarrer (avec Makefile)
make up

# OU sans Makefile
docker-compose up -d
```

**C'est tout !** 🎉

Les services sont disponibles :
- API : http://localhost:8000
- Streamlit : http://localhost:8501
- Docs API : http://localhost:8000/docs

## Commandes Essentielles (avec Makefile)

```bash
make help          # Voir toutes les commandes
make up            # Démarrer les services
make down          # Arrêter les services
make logs          # Voir les logs
make restart       # Redémarrer
make rebuild       # Rebuild après modif code
make shell         # Shell dans le conteneur
make init          # Initialiser la DB
make backup        # Backup de la DB
```

## Commandes Essentielles (sans Makefile)

```bash
docker-compose up -d              # Démarrer
docker-compose down               # Arrêter
docker-compose logs -f            # Logs
docker-compose restart            # Redémarrer
docker-compose up -d --build      # Rebuild
docker-compose exec api bash      # Shell
docker-compose exec api python init_database.py  # Init DB
```

## Architecture Docker

```
┌─────────────────────────────────────────┐
│         Docker Compose                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │ PostgreSQL  │◄───│  API FastAPI │  │
│  │  :5432      │    │    :8000     │  │
│  └─────────────┘    └──────────────┘  │
│         ▲                  ▲           │
│         │                  │           │
│  ┌──────┴──────────────────┴────────┐ │
│  │      Streamlit  :8501            │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  PgAdmin  :5050  (optionnel)    │ │
│  └──────────────────────────────────┘ │
│                                        │
└────────────────────────────────────────┘
```

## Volumes & Persistance

- `postgres_data` : Données PostgreSQL (volume Docker)
- `./data/files` : Fichiers PDF uploadés (bind mount)
- `./logs` : Logs de l'application (bind mount)

**Les données persistent après `docker-compose down`** ✅

## Développement

### Hot Reload activé
Les modifications du code sont automatiquement rechargées (FastAPI et Streamlit).

### Mode développement avec PgAdmin
```bash
make up-dev
# ou
docker-compose --profile dev up -d
```
Accès PgAdmin : http://localhost:5050

### Ajouter une dépendance
```bash
# 1. Modifier requirements.txt
echo "nouvelle-lib==1.0.0" >> requirements.txt

# 2. Rebuild
make rebuild
```

## Production

```bash
# Build production
make prod-build

# Démarrer en production
make prod-up

# Arrêter
make prod-down
```

Différences en production :
- Workers multiples (4) pour l'API
- Logs niveau INFO
- Limites de ressources CPU/RAM
- Volumes système persistants
- Restart automatique

## Dépannage

### Services ne démarrent pas
```bash
# Vérifier les logs
make logs

# Vérifier le statut
make status

# Redémarrer tout
make down
make up
```

### Problème de base de données
```bash
# Vérifier que PostgreSQL est prêt
docker-compose exec postgres pg_isready -U cvlm_user

# Réinitialiser la DB
make init-reset
```

### Problème de port
Si le port 8000 ou 8501 est déjà utilisé, modifier `docker-compose.yml` :
```yaml
ports:
  - "8001:8000"  # Port externe modifié
```

### Nettoyage complet
```bash
# Supprimer tout (conteneurs, volumes, images)
make clean

# Redémarrer proprement
make up
```

## Structure des Fichiers Docker

```
CVLM/
├── docker-compose.yml          # Config développement
├── docker-compose.prod.yml     # Config production
├── Dockerfile.api              # Image API
├── Dockerfile.streamlit        # Image Streamlit
├── docker-entrypoint.sh        # Script d'init
├── init_db.sql                 # Init PostgreSQL
├── .dockerignore               # Fichiers exclus
├── Makefile                    # Commandes simplifiées
└── DOCKER_GUIDE.md            # Ce fichier
```

## Sécurité

### En développement
- ✅ Passwords par défaut OK pour le dev local
- ✅ .env non versionné (dans .gitignore)

### En production
- ⚠️ **CHANGER tous les passwords**
- ⚠️ Utiliser des variables d'environnement sécurisées
- ⚠️ Activer SSL/TLS (Nginx + Let's Encrypt)
- ⚠️ Configurer un firewall
- ⚠️ Limiter les ressources (CPU/RAM)

## Ressources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Guide détaillé
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture du projet

## Aide

```bash
# Voir toutes les commandes Makefile
make help

# Voir les logs en temps réel
make logs

# État de santé de l'API
make health
```

**Support** : Voir les issues GitHub du projet
