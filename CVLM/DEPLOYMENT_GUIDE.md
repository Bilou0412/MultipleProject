# 🚀 Guide de Déploiement CVLM en Production

## Options de déploiement recommandées

### Option 1: Railway.app (RECOMMANDÉ - le plus simple)

**Avantages:**
- Free tier généreux (500h/mois)
- PostgreSQL inclus
- HTTPS automatique
- Deploy depuis GitHub en 1 clic

**Étapes:**
1. Créer compte sur [railway.app](https://railway.app)
2. Nouveau projet → "Deploy from GitHub"
3. Sélectionner le repo CVLM
4. Ajouter service PostgreSQL
5. Variables d'environnement:
   ```
   DATABASE_URL=<fourni par Railway>
   OPENAI_API_KEY=<votre clé>
   GOOGLE_CLIENT_ID=<votre client ID>
   JWT_SECRET_KEY=<généré aléatoirement>
   PORT=8000
   ```
6. Deploy automatique à chaque push Git

**Coût:** $5-10/mois après free tier

---

### Option 2: Render.com

**Avantages:**
- Free tier permanent (avec limites)
- PostgreSQL gratuit (90 jours de rétention)
- SSL automatique

**Étapes:**
1. Compte sur [render.com](https://render.com)
2. New → Web Service
3. Connecter GitHub repo
4. Build Command: `docker compose build api`
5. Start Command: `docker compose up api`
6. Créer PostgreSQL Database (separate service)
7. Variables d'environnement (même que Railway)

**Coût:** Gratuit (avec sleep après inactivité)

---

### Option 3: Fly.io (Pour experts)

**Avantages:**
- Très rapide (edge network)
- Free tier: 3 VMs + 3GB storage
- Contrôle total

**Étapes:**
```bash
# Installer flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Initialiser
cd CVLM
flyctl launch

# Configurer PostgreSQL
flyctl postgres create

# Variables
flyctl secrets set OPENAI_API_KEY=sk-...
flyctl secrets set GOOGLE_CLIENT_ID=...
flyctl secrets set JWT_SECRET_KEY=...

# Déployer
flyctl deploy
```

**Coût:** Gratuit (3 apps max)

---

## Configuration DNS

### Obtenir un domaine
- **Namecheap:** ~$10/an
- **Porkbun:** ~$8/an
- **Cloudflare:** au prix coûtant

### Configuration
1. Acheter domaine (ex: `cvlm.app`)
2. Dans Railway/Render/Fly:
   - Settings → Custom Domain
   - Ajouter `api.cvlm.app`
3. Dans votre registrar DNS:
   - Type: CNAME
   - Name: api
   - Value: `<fourni par la plateforme>`
   - TTL: Auto

---

## Configuration Extension Chrome

### Mettre à jour manifest.json
```json
{
  "oauth2": {
    "client_id": "NOUVEAU_CLIENT_ID.apps.googleusercontent.com",
    "scopes": [
      "https://www.googleapis.com/auth/userinfo.email",
      "https://www.googleapis.com/auth/userinfo.profile"
    ]
  },
  "host_permissions": [
    "https://api.cvlm.app/*"  // Nouveau domaine
  ]
}
```

### Mettre à jour generator.js
```javascript
const API_URL = 'https://api.cvlm.app';  // Production URL
```

---

## Configuration Google OAuth

### Créer nouvelles credentials
1. [Google Cloud Console](https://console.cloud.google.com)
2. APIs & Services → Credentials
3. Create Credentials → OAuth 2.0 Client ID
4. Application type: Web application
5. Authorized redirect URIs:
   - `https://api.cvlm.app/auth/callback` (si besoin)
6. **IMPORTANT**: Copier le Client ID
7. **Révoquer les anciennes clés** exposées sur Git

### Configurer Chrome Extension
1. Même console → Create Credentials → OAuth 2.0 Client ID
2. Application type: Chrome Extension
3. Extension ID: (obtenu après publication Chrome Web Store)
4. Copier le Client ID
5. Mettre à jour `manifest.json`

---

## Stockage de fichiers (S3)

### Option 1: Cloudflare R2 (RECOMMANDÉ)
- 10 GB gratuit/mois
- Pas de frais de sortie (egress)
- Compatible S3

```python
# Installer boto3
pip install boto3

# Configuration
import boto3
s3 = boto3.client(
    's3',
    endpoint_url='https://<account-id>.r2.cloudflarestorage.com',
    aws_access_key_id='<key>',
    aws_secret_access_key='<secret>'
)

# Upload
s3.upload_file('local.pdf', 'bucket-name', 'cvs/cv_123.pdf')
```

### Option 2: AWS S3
- Plus cher mais très fiable
- Free tier: 5 GB/mois (1 an)

### Option 3: Backblaze B2
- Moins cher que S3
- 10 GB gratuit

---

## Monitoring et Logs

### Sentry (Erreurs)
```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk
sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    traces_sample_rate=0.1
)
```

### LogTail (Logs)
- Gratuit: 1 GB/mois
- Intégration Railway/Render native

### Uptime Robot (Health checks)
- Gratuit: 50 monitors
- Ping `/health` toutes les 5 min

---

## Base de données

### Backups automatiques
```bash
# Script backup quotidien
#!/bin/bash
DATE=$(date +%Y%m%d)
docker compose exec -T postgres pg_dump -U cvlm_user cvlm_db > backup_$DATE.sql
```

### Cron job (serveur)
```bash
0 2 * * * /path/to/backup.sh
```

### Railway/Render
- Backups automatiques inclus
- Restauration en 1 clic

---

## Sécurité

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/generate-cover-letter")
@limiter.limit("5/minute")  # 5 générations/minute max
async def generate(...):
    ...
```

### CORS Restrictif
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://YOUR_EXTENSION_ID",
        "https://cvlm.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Headers de sécurité
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## Checklist finale

- [ ] Variables d'environnement configurées en production
- [ ] HTTPS actif et certificat valide
- [ ] OAuth credentials production créées
- [ ] Anciennes clés révoquées
- [ ] Extension mise à jour avec production URL
- [ ] Backups BDD configurés
- [ ] Monitoring actif (Sentry + Uptime)
- [ ] Rate limiting activé
- [ ] CORS restrictif
- [ ] Privacy Policy publiée
- [ ] Terms of Service publiés
- [ ] Tests end-to-end sur production

---

## Coûts estimés

### Option minimale (Free Tier)
- Railway/Render: **$0** (avec limites)
- Domaine: **$10/an**
- Chrome Developer: **$5 one-time**
- **Total: ~$15 première année**

### Option production stable
- Railway/Render: **$7/mois**
- S3/R2: **$0-5/mois**
- Domaine: **$10/an**
- Monitoring: **$0** (free tiers)
- **Total: ~$10-15/mois**

---

## Support et maintenance

### Après déploiement
1. Surveiller logs quotidiennement (première semaine)
2. Répondre aux issues GitHub
3. Mettre à jour dépendances mensuellement
4. Backup hebdomadaire de la BDD
5. Tester nouvelles features en staging d'abord
