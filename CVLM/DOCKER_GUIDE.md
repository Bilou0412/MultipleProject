# Docker Compose - Guide d'Utilisation CVLM

## 🚀 Démarrage Rapide

### 1. Configuration initiale

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos clés API
nano .env  # ou vim, code, etc.
```

Contenu minimal du `.env` :
```env
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=AIza-your-key-here
```

### 2. Lancer tous les services

```bash
# Build et démarrage
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Voir le statut
docker-compose ps
```

### 3. Accéder aux services

- **API FastAPI** : http://localhost:8000
  - Documentation : http://localhost:8000/docs
  - Redoc : http://localhost:8000/redoc

- **Streamlit UI** : http://localhost:8501

- **PostgreSQL** : `localhost:5432`
  - Database : `cvlm_db`
  - User : `cvlm_user`
  - Password : `cvlm_password`

- **PgAdmin** (en mode dev) : http://localhost:5050
  - Email : `admin@cvlm.local`
  - Password : `admin`

## 📦 Services Disponibles

### Services principaux (toujours actifs)
- `postgres` - Base de données PostgreSQL
- `api` - API FastAPI
- `streamlit` - Interface web Streamlit

### Services optionnels (profile dev)
- `pgadmin` - Administration de la base de données

```bash
# Lancer avec PgAdmin
docker-compose --profile dev up -d
```

## 🔧 Commandes Utiles

### Gestion des services

```bash
# Démarrer tous les services
docker-compose up -d

# Démarrer uniquement certains services
docker-compose up -d postgres api

# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (⚠️ perte de données)
docker-compose down -v

# Redémarrer un service spécifique
docker-compose restart api

# Voir les logs en temps réel
docker-compose logs -f api

# Voir les logs d'un service spécifique
docker-compose logs postgres
```

### Rebuild

```bash
# Rebuild après modification du code
docker-compose up -d --build

# Rebuild un service spécifique
docker-compose build api
docker-compose up -d api

# Rebuild complet (sans cache)
docker-compose build --no-cache
```

### Accès aux conteneurs

```bash
# Shell dans le conteneur API
docker-compose exec api bash

# Shell dans le conteneur PostgreSQL
docker-compose exec postgres psql -U cvlm_user -d cvlm_db

# Exécuter une commande Python dans l'API
docker-compose exec api python -c "from infrastructure.adapters.database_config import init_database; init_database()"
```

### Maintenance de la base de données

```bash
# Backup de la base
docker-compose exec postgres pg_dump -U cvlm_user cvlm_db > backup.sql

# Restaurer la base
docker-compose exec -T postgres psql -U cvlm_user cvlm_db < backup.sql

# Réinitialiser la base (⚠️ perte de données)
docker-compose exec api python init_database.py --reset
```

## 📊 Monitoring

### Vérifier la santé des services

```bash
# Status de tous les services
docker-compose ps

# Statistiques de ressources
docker stats

# Logs d'erreur uniquement
docker-compose logs --tail=50 | grep -i error
```

### Volumes et données

```bash
# Lister les volumes
docker volume ls | grep cvlm

# Inspecter un volume
docker volume inspect cvlm_postgres_data

# Taille des volumes
docker system df -v
```

## 🔍 Débogage

### Problème de connexion PostgreSQL

```bash
# Vérifier que PostgreSQL est prêt
docker-compose exec postgres pg_isready -U cvlm_user

# Tester la connexion depuis l'API
docker-compose exec api python -c "
from infrastructure.adapters.database_config import create_db_engine
engine = create_db_engine()
print('Connexion OK' if engine else 'Erreur')
"
```

### Problème de permissions fichiers

```bash
# Vérifier les permissions du dossier data
ls -la data/files/

# Corriger si nécessaire
sudo chown -R $USER:$USER data/files/
chmod -R 755 data/files/
```

### Problème de port déjà utilisé

```bash
# Vérifier quel processus utilise le port 8000
sudo lsof -i :8000

# Modifier le port dans docker-compose.yml
# ports:
#   - "8001:8000"  # Port externe modifié
```

## 🏗️ Développement

### Mode développement avec hot-reload

Le fichier `docker-compose.yml` est configuré avec `--reload` pour FastAPI et Streamlit.

Les modifications du code sont automatiquement rechargées.

### Ajouter de nouvelles dépendances

```bash
# Modifier requirements.txt localement
echo "nouvelle-lib==1.0.0" >> requirements.txt

# Rebuild les conteneurs
docker-compose up -d --build
```

### Variables d'environnement personnalisées

Créer un fichier `docker-compose.override.yml` :

```yaml
version: '3.8'

services:
  api:
    environment:
      - DEBUG=True
      - LOG_LEVEL=DEBUG
    ports:
      - "8001:8000"  # Port personnalisé
```

Ce fichier est automatiquement chargé et n'est pas versionné (dans .gitignore).

## 🚀 Production

### Configuration pour la production

Créer un `docker-compose.prod.yml` :

```yaml
version: '3.8'

services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Depuis .env sécurisé
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data  # Volume persistant
  
  api:
    restart: always
    command: uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
```

Lancer avec :
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Avec un reverse proxy (Nginx)

Ajouter au `docker-compose.prod.yml` :

```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
      - streamlit
```

## 📝 Notes

### Persistance des données

- Les données PostgreSQL sont stockées dans le volume `postgres_data`
- Les fichiers PDF sont stockés dans `./data/files` (monté en volume)
- Ces données persistent même après `docker-compose down`

### Performance

En production, considérer :
- Augmenter les workers uvicorn : `--workers 4`
- Configurer un pool de connexions PostgreSQL
- Utiliser Redis pour le cache (à ajouter)
- Mettre en place un load balancer

### Sécurité

- ⚠️ Ne jamais commiter le fichier `.env` avec les vraies clés
- Changer les passwords par défaut en production
- Utiliser des secrets Docker en production
- Activer SSL/TLS avec Nginx

## 🆘 Support

En cas de problème :

```bash
# Supprimer tous les conteneurs et recommencer
docker-compose down -v
docker-compose up -d --build

# Vérifier les logs détaillés
docker-compose logs -f --tail=100
```

Pour plus d'aide, consulter :
- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- Issues GitHub du projet
