# Configuration Nginx pour CVLM

## Configuration actuelle

- **HTTP uniquement** (développement)
- **Port 80** pour accès externe
- Reverse proxy vers :
  - `/api/` → FastAPI (port 8000)
  - `/` → Streamlit (port 8501)

## Utilisation

### Avec Docker Compose

Le service Nginx est inclus dans `docker-compose.prod.yml` (commenté par défaut).

Pour l'activer :

1. Décommenter le service `nginx` dans `docker-compose.prod.yml`
2. Démarrer : `make prod-up`

### URLs après activation de Nginx

- Interface Streamlit : http://localhost/
- API : http://localhost/api/
- Documentation : http://localhost/docs

## Configuration SSL/HTTPS (Production)

### 1. Obtenir des certificats SSL

#### Option A : Let's Encrypt (Recommandé - Gratuit)

```bash
# Installer Certbot
sudo apt-get install certbot

# Obtenir les certificats
sudo certbot certonly --standalone -d votre-domaine.com
```

Les certificats seront dans `/etc/letsencrypt/live/votre-domaine.com/`

#### Option B : Certificats auto-signés (Développement uniquement)

```bash
# Créer le dossier SSL
mkdir -p nginx/ssl

# Générer les certificats
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

### 2. Configurer Nginx pour HTTPS

Dans `nginx/nginx.conf`, décommenter la section `server` HTTPS et adapter :

```nginx
server {
    listen 443 ssl http2;
    server_name votre-domaine.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # ... reste de la configuration
}
```

### 3. Monter les certificats dans Docker

Dans `docker-compose.prod.yml`, vérifier le volume SSL :

```yaml
nginx:
  volumes:
    - ./nginx/ssl:/etc/nginx/ssl:ro
    # OU pour Let's Encrypt :
    - /etc/letsencrypt:/etc/nginx/ssl:ro
```

### 4. Redémarrer

```bash
make prod-down
make prod-up
```

## Renouvellement SSL (Let's Encrypt)

Les certificats Let's Encrypt expirent tous les 90 jours.

### Renouvellement manuel

```bash
sudo certbot renew
docker-compose restart nginx
```

### Renouvellement automatique (Cron)

```bash
# Éditer crontab
sudo crontab -e

# Ajouter cette ligne (renouvellement tous les lundis à 3h)
0 3 * * 1 certbot renew --quiet && docker-compose restart nginx
```

## Optimisations

### Performance

- **Compression gzip** : Activée pour JSON, HTML, CSS, JS
- **Keepalive** : 65 secondes
- **Client max size** : 50MB (pour upload de PDFs)

### Sécurité (Headers HTTPS)

Lorsque SSL est activé, les headers suivants sont ajoutés :
- `Strict-Transport-Security` : Force HTTPS
- `X-Frame-Options` : Prévient clickjacking
- `X-Content-Type-Options` : Prévient MIME sniffing
- `X-XSS-Protection` : Protection XSS

### Timeouts

- **API** : 300s (5 minutes) pour les requêtes LLM longues
- **Streamlit WebSocket** : 86400s (24h) pour les connexions persistantes

## Logs

Les logs Nginx sont disponibles dans `nginx/logs/` :

```bash
# Voir les logs d'accès
tail -f nginx/logs/access.log

# Voir les erreurs
tail -f nginx/logs/error.log
```

## Dépannage

### Nginx ne démarre pas

```bash
# Tester la configuration
docker-compose exec nginx nginx -t

# Voir les logs
docker-compose logs nginx
```

### Erreur 502 Bad Gateway

- Vérifier que l'API et Streamlit sont démarrés
- Vérifier les noms des services dans upstream

```bash
docker-compose ps
```

### Streamlit WebSocket ne fonctionne pas

Vérifier que la section `/_stcore/stream` est bien configurée avec :
- `proxy_http_version 1.1`
- Headers `Upgrade` et `Connection`

## Architecture Nginx

```
                  Internet
                     │
                     ▼
              ┌──────────────┐
              │    Nginx     │
              │    :80/443   │
              └──────┬───────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   /api/docs     /api/*          /
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │  Docs   │  │   API   │  │Streamlit │
   │  :8000  │  │  :8000  │  │  :8501   │
   └─────────┘  └─────────┘  └──────────┘
```

## Références

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Streamlit + Nginx](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker#nginx-reverse-proxy)
