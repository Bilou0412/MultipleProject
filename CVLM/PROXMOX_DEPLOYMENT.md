# 🏠 DÉPLOIEMENT HOMELAB PROXMOX + GITHUB RELEASES

## 🎯 TON PLAN

✅ **Proxmox homelab** : Hébergement gratuit, contrôle total  
✅ **GitHub Releases** : Distribution extension sans Chrome Web Store  
✅ **Fichiers CRX** : Installation manuelle mais pro  

---

## 📋 PARTIE 1 : PROXMOX SETUP (1-2h)

### Prérequis Proxmox
- VM avec Ubuntu 22.04 LTS (2 CPU, 4GB RAM, 20GB disk)
- Docker + Docker Compose installés
- Reverse proxy (Nginx ou Traefik)
- Nom de domaine pointant vers ton IP publique

### Architecture recommandée
```
Internet
   ↓
[Routeur] → Port 80/443 forwarding
   ↓
[Proxmox Host]
   ↓
[VM Ubuntu] → Docker Compose
   ├── PostgreSQL (port 5432)
   ├── API FastAPI (port 8000)
   └── Nginx (port 80/443)
```

---

## 🐳 ÉTAPE 1 : Préparer Docker Production (30 min)

### 1.1 Créer docker-compose.prod.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cvlm_postgres_prod
    environment:
      POSTGRES_USER: cvlm_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Fort password !
      POSTGRES_DB: cvlm_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    networks:
      - cvlm_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cvlm_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: cvlm_api_prod
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://cvlm_user:${POSTGRES_PASSWORD}@postgres:5432/cvlm_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - FILE_STORAGE_BASE_PATH=/app/data/files
      - ENVIRONMENT=production
    volumes:
      - cvlm_files:/app/data/files
    ports:
      - "127.0.0.1:8000:8000"  # Seulement localhost
    restart: unless-stopped
    networks:
      - cvlm_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: cvlm_nginx
    depends_on:
      - api
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro  # Certbot certificates
    restart: unless-stopped
    networks:
      - cvlm_network

volumes:
  postgres_data:
  cvlm_files:

networks:
  cvlm_network:
    driver: bridge
```

### 1.2 Créer nginx/nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=gen_limit:10m rate=5r/m;

    upstream api {
        server api:8000;
    }

    # Redirection HTTP → HTTPS
    server {
        listen 80;
        server_name api.ton-domaine.com;  # ← À CHANGER
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name api.ton-domaine.com;  # ← À CHANGER

        # SSL Certificates (Let's Encrypt)
        ssl_certificate /etc/letsencrypt/live/api.ton-domaine.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.ton-domaine.com/privkey.pem;
        
        # SSL Configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # CORS (pour l'extension Chrome)
        add_header Access-Control-Allow-Origin "chrome-extension://*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        add_header Access-Control-Allow-Credentials "true" always;

        location / {
            # Rate limiting
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Rate limiting strict pour génération
        location /generate-cover-letter {
            limit_req zone=gen_limit burst=2 nodelay;
            
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout plus long pour génération
            proxy_read_timeout 120s;
        }

        # Health check sans rate limit
        location /health {
            proxy_pass http://api;
        }
    }
}
```

---

## 🔐 ÉTAPE 2 : SSL avec Let's Encrypt (15 min)

### 2.1 Installer Certbot sur Proxmox VM

```bash
# Sur ta VM Ubuntu
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Obtenir certificat SSL
sudo certbot certonly --standalone -d api.ton-domaine.com

# Renouvellement auto
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 2.2 Vérifier certificats

```bash
sudo ls -la /etc/letsencrypt/live/api.ton-domaine.com/
# Tu dois voir : fullchain.pem, privkey.pem
```

---

## 🚀 ÉTAPE 3 : Déployer sur Proxmox (30 min)

### 3.1 Créer .env.production

```bash
# Sur ta VM Proxmox
cd /home/ton-user/cvlm
nano .env.production
```

```env
# Base de données
POSTGRES_PASSWORD=un-mot-de-passe-tres-fort-123!@#

# API Keys
OPENAI_API_KEY=sk-proj-2psNxzCYWQsSwIp...
GOOGLE_CLIENT_ID=825312610018-knniccb9m2o9faooksh57k4cq3s9b9tq...
JWT_SECRET_KEY=XuOEwC6t9kIdvuGt7HHDO47mmnIlcVss9c7RcbMEBkU

# Environment
ENVIRONMENT=production
```

### 3.2 Démarrer les services

```bash
# Copier fichiers sur VM
scp -r CVLM/* user@proxmox-vm:/home/user/cvlm/

# Sur la VM
cd /home/user/cvlm
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Vérifier logs
docker compose -f docker-compose.prod.yml logs -f
```

### 3.3 Tester l'API

```bash
# Depuis ta VM
curl https://api.ton-domaine.com/health

# Depuis l'extérieur
curl https://api.ton-domaine.com/health
```

---

## 📦 PARTIE 2 : GITHUB RELEASES + CRX (1h)

### Qu'est-ce qu'un fichier CRX ?
- **CRX** = Chrome Extension (format packagé)
- Installable manuellement sans Chrome Web Store
- Signé avec une clé privée

### Limitations CRX sans Store :
⚠️ Depuis Chrome 75, Google bloque les extensions non-store en **mode normal**  
✅ **Solutions :**
1. **Mode développeur** activé (users doivent garder activé)
2. **Enterprise Policy** (pour entreprises)
3. **Unpacked extension** (dossier ZIP à décompresser)

**→ Pour Reddit, on va utiliser : ZIP unpacked (plus simple)**

---

## 📤 ÉTAPE 4 : Préparer Extension pour Production

### 4.1 Créer extension/config.js

```javascript
// Configuration de l'API selon l'environnement
const CONFIG = {
    production: {
        API_URL: 'https://api.ton-domaine.com'  // ← TON DOMAINE
    },
    development: {
        API_URL: 'http://localhost:8000'
    }
};

// Auto-détection environnement
const ENVIRONMENT = chrome.runtime.getManifest().version.includes('dev') 
    ? 'development' 
    : 'production';

const API_URL = CONFIG[ENVIRONMENT].API_URL;

// Export pour autres fichiers
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_URL };
}
```

### 4.2 Mettre à jour manifest.json

```json
{
  "manifest_version": 3,
  "name": "CVLM - Générateur de Lettre de Motivation",
  "version": "1.0.0",
  "description": "Générez automatiquement des lettres de motivation depuis les offres d'emploi en ligne",
  "permissions": [
    "activeTab",
    "storage",
    "scripting",
    "downloads",
    "identity"
  ],
  "host_permissions": [
    "https://www.welcometothejungle.com/*",
    "https://www.linkedin.com/*",
    "https://www.indeed.fr/*",
    "https://api.ton-domaine.com/*"
  ],
  "oauth2": {
    "client_id": "825312610018-knniccb9m2o9faooksh57k4cq3s9b9tq.apps.googleusercontent.com",
    "scopes": [
      "https://www.googleapis.com/auth/userinfo.email",
      "https://www.googleapis.com/auth/userinfo.profile"
    ]
  },
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  },
  "action": {
    "default_popup": "generator.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": [
        "https://www.welcometothejungle.com/*/jobs/*",
        "https://www.linkedin.com/jobs/*",
        "https://www.indeed.fr/*/viewjob*"
      ],
      "js": ["config.js", "content.js"],
      "css": ["content.css"]
    }
  ]
}
```

### 4.3 Mettre à jour generator.js

```javascript
// Remplacer ligne 1
// const API_URL = 'http://localhost:8000';

// Par :
// Charger config
const API_URL = 'https://api.ton-domaine.com';  // Production
```

### 4.4 Mettre à jour content.js

```javascript
// Remplacer ligne 3
// const API_URL = 'http://localhost:8000';

// Par :
const API_URL = 'https://api.ton-domaine.com';  // Production
```

---

## 📦 ÉTAPE 5 : Créer GitHub Release (30 min)

### 5.1 Créer script de build

```bash
#!/bin/bash
# build-extension.sh

VERSION="1.0.0"
EXTENSION_DIR="extension"
OUTPUT_DIR="releases"
OUTPUT_FILE="cvlm-extension-v${VERSION}.zip"

echo "🔨 Building CVLM Extension v${VERSION}..."

# Créer dossier releases
mkdir -p $OUTPUT_DIR

# Nettoyer ancien build
rm -f $OUTPUT_DIR/$OUTPUT_FILE

# Créer ZIP (sans node_modules, .git, etc.)
cd $EXTENSION_DIR
zip -r ../$OUTPUT_DIR/$OUTPUT_FILE . \
    -x "*.git*" \
    -x "*node_modules*" \
    -x "*.DS_Store" \
    -x "*__pycache__*"

cd ..

echo "✅ Extension packagée : $OUTPUT_DIR/$OUTPUT_FILE"
echo "📦 Taille : $(du -h $OUTPUT_DIR/$OUTPUT_FILE | cut -f1)"
```

### 5.2 Créer README pour l'extension

```markdown
# CVLM Extension - Installation

## 📥 Installation

1. **Télécharger** : [cvlm-extension-v1.0.0.zip](https://github.com/Bilou0412/MultipleProject/releases/latest)

2. **Extraire** le fichier ZIP dans un dossier

3. **Ouvrir Chrome** et aller sur `chrome://extensions/`

4. **Activer le mode développeur** (coin supérieur droit)

5. **Cliquer sur "Charger l'extension non empaquetée"**

6. **Sélectionner** le dossier extrait

7. **C'est prêt !** L'icône CVLM apparaît dans la barre d'outils

## ⚠️ Important

- Garder le **mode développeur activé**
- Ne **pas supprimer** le dossier extrait
- L'extension reste fonctionnelle après redémarrage Chrome

## 🔄 Mise à jour

1. Télécharger nouvelle version
2. Extraire dans le même dossier (écraser)
3. Chrome → Extensions → Cliquer "🔄 Recharger"

## 🐛 Problèmes ?

- Vérifier que l'API est accessible : https://api.ton-domaine.com/health
- Vérifier les permissions dans chrome://extensions/
- Consulter les logs : F12 dans le popup de l'extension
```

### 5.3 Builder et tester

```bash
chmod +x build-extension.sh
./build-extension.sh

# Tester le ZIP
unzip -t releases/cvlm-extension-v1.0.0.zip
```

### 5.4 Créer GitHub Release

```bash
# Commiter les changements
git add extension/ build-extension.sh
git commit -m "feat: Production-ready extension with configurable API URL"
git push origin main

# Créer tag
git tag -a v1.0.0 -m "Release v1.0.0 - First production release"
git push origin v1.0.0

# Sur GitHub.com :
# 1. Releases → "Create a new release"
# 2. Tag : v1.0.0
# 3. Title : "CVLM v1.0.0 - First Release"
# 4. Description : Copier README installation
# 5. Uploader : releases/cvlm-extension-v1.0.0.zip
# 6. Publish release
```

---

## 🎯 ÉTAPE 6 : Mettre à jour Google OAuth (10 min)

```
1. Google Cloud Console → APIs & Credentials
2. Modifier OAuth Client ID
3. Authorized JavaScript origins → Ajouter :
   https://api.ton-domaine.com
4. Authorized redirect URIs → Ajouter :
   https://api.ton-domaine.com/auth/callback
5. Sauvegarder
```

---

## ✅ CHECKLIST FINALE

### Infrastructure Proxmox
- [ ] VM Ubuntu avec Docker
- [ ] Port forwarding 80/443 sur routeur
- [ ] Domaine pointant vers IP publique
- [ ] Certificat SSL Let's Encrypt
- [ ] Docker Compose production lancé
- [ ] Nginx reverse proxy configuré
- [ ] Health check accessible depuis internet

### Extension
- [ ] API_URL changé en production
- [ ] manifest.json mis à jour
- [ ] Google OAuth configuré pour domaine
- [ ] Extension testée localement
- [ ] ZIP créé avec build-extension.sh
- [ ] GitHub Release publiée

### Sécurité
- [ ] Rate limiting activé (nginx)
- [ ] HTTPS forcé (redirection 80→443)
- [ ] CORS configuré pour extensions Chrome
- [ ] .env.production non commité
- [ ] Backups PostgreSQL configurés

---

## 🚀 POST-DÉPLOIEMENT

### Monitoring gratuit
```bash
# Uptime Robot : https://uptimerobot.com/ (gratuit)
# Créer monitor HTTP(S)
# URL : https://api.ton-domaine.com/health
# Interval : 5 minutes
# Alert : Email si down
```

### Backups automatiques PostgreSQL
```bash
# Crontab sur VM
crontab -e

# Backup quotidien à 2h du matin
0 2 * * * docker exec cvlm_postgres_prod pg_dump -U cvlm_user cvlm_db > /home/user/cvlm/backups/cvlm_$(date +\%Y\%m\%d).sql

# Nettoyer backups > 30 jours
0 3 * * * find /home/user/cvlm/backups/ -name "cvlm_*.sql" -mtime +30 -delete
```

---

## 📊 COÛT FINAL

| Item | Prix | Note |
|------|------|------|
| Proxmox Homelab | €0 | Tu as déjà |
| Électricité | ~€5-10/mois | Selon VM |
| Domaine | ~€10/an | Namecheap/OVH |
| SSL | €0 | Let's Encrypt gratuit |
| **TOTAL** | **~€5-10/mois** | vs $10-20 cloud |

---

## 🎬 NEXT : POST REDDIT

Une fois tout déployé :

1. **Tester end-to-end** : Installation extension → Génération lettre
2. **Préparer assets** : Screenshots, GIF démo
3. **Rédiger post Reddit** :
   ```markdown
   [Show Reddit] CVLM - Générateur automatique de lettres de motivation
   
   Self-hosted, open-source, propulsé par GPT-4.
   
   🔗 GitHub : github.com/Bilou0412/MultipleProject
   📥 Download : [Releases](link)
   🎥 Demo : [GIF]
   
   Tech stack : FastAPI + PostgreSQL + Chrome Extension + Proxmox
   ```
4. **Poster sur** : r/SideProject, r/selfhosted, r/opensource

---

**Tu veux que je commence par quoi ?**

A. Créer les fichiers Docker production  
B. Préparer l'extension pour production  
C. Script de build + GitHub Release  
D. Guide complet installation Proxmox
