# 🚨 CORRECTIONS OBLIGATOIRES AVANT PRODUCTION

## ❌ CRITIQUE - BLOQUANTS PRODUCTION

### 1. CORS Wildcard (DANGER)
**Fichier:** `api_server.py` ligne 40  
**Problème:** `allow_origins=["*"]` = N'IMPORTE QUI peut appeler ton API  
**Impact:** 🔴 Attaques CSRF, vols de données  
**Fix:**
```python
# AVANT (ligne 39-44)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ DANGER
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APRÈS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Pour l'extension Chrome
        "https://api.ton-domaine.com",  # Ton domaine en prod
        "http://localhost:8000"  # Dev uniquement
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 2. Aucun Rate Limiting
**Fichier:** `api_server.py`  
**Problème:** Quelqu'un peut spammer `/generate-cover-letter` → Facture OpenAI explose  
**Impact:** 🔴 Coût illimité, déni de service  
**Fix:** Ajouter `slowapi`
```bash
# Dans requirements.txt
slowapi==0.1.9

# Dans api_server.py (après ligne 35)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Sur endpoint génération (ligne 410)
@app.post("/generate-cover-letter")
@limiter.limit("5/minute")  # Max 5 lettres par minute
async def generate_cover_letter(
    request: Request,  # Ajouter ce paramètre
    ...
```

---

### 3. Console.log en Production
**Fichiers:** `extension/generator.js`, `extension/content.js`  
**Problème:** 10+ console.log exposent détails internes  
**Impact:** 🟡 Fuite d'infos, perf légère  
**Fix:** Créer système de logs conditionnel
```javascript
// Ajouter en haut de generator.js et content.js
const DEBUG = false;  // false en production
const log = DEBUG ? console.log.bind(console) : () => {};
const error = console.error.bind(console);  // Toujours logger erreurs

// Remplacer tous les console.log par log()
// Garder console.error comme error()
log('🔍 Chargement des lettres...');  // Caché en prod
error('❌ Erreur critique');  // Toujours visible
```

---

### 4. URLs Hardcodées
**Fichiers:** `extension/generator.js` (ligne 1), `extension/content.js` (ligne 3), `manifest.json` (ligne 17)  
**Problème:** `localhost:8000` hardcodé = Cassé en production  
**Impact:** 🔴 Extension ne marche pas après deploy  
**Fix:** Configuration dynamique
```javascript
// Créer extension/config.js
const CONFIG = {
    API_URL: chrome.runtime.getManifest().version.includes('dev')
        ? 'http://localhost:8000'
        : 'https://api.ton-domaine.com'
};

// Dans generator.js ligne 1
// const API_URL = 'http://localhost:8000';  // ❌ SUPPRIMER
// REMPLACER PAR:
const API_URL = CONFIG.API_URL;

// Dans content.js ligne 3 - PAREIL

// Dans manifest.json - Ajouter les deux
"host_permissions": [
    "http://localhost:8000/*",
    "https://api.ton-domaine.com/*"
]
```

---

## ⚠️ IMPORTANT - À AMÉLIORER

### 5. Print() au lieu de Logging
**Fichiers:** Tous les `.py` (50+ occurrences)  
**Problème:** `print()` = pas de niveaux, pas de fichiers, pas structuré  
**Impact:** 🟡 Debug difficile en prod  
**Fix:** Utiliser logging Python
```python
# Ajouter en haut de api_server.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cvlm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Remplacer print() par logger
print("✅ Base de données initialisée")  # Avant
logger.info("Base de données initialisée")  # Après

print(f"❌ Erreur: {e}")  # Avant
logger.error(f"Erreur: {e}", exc_info=True)  # Après
```

---

### 6. Pas de Gestion Erreurs OpenAI
**Fichier:** `api_server.py` ligne 450  
**Problème:** Si OpenAI down/rate limit → Exception non gérée  
**Impact:** 🟡 Crash API  
**Fix:**
```python
# Dans /generate-cover-letter
try:
    result = use_case.execute(...)
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    raise HTTPException(
        status_code=503,
        detail="Service OpenAI temporairement indisponible. Réessayez dans 1 minute."
    )
except Exception as e:
    logger.error(f"Erreur génération: {e}")
    raise HTTPException(status_code=500, detail="Erreur interne")
```

---

### 7. Pas de Health Check Complet
**Fichier:** `api_server.py` ligne 142  
**Problème:** `/health` retourne OK même si DB down  
**Impact:** 🟡 Monitoring invalide  
**Fix:**
```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    checks = {
        "status": "healthy",
        "version": "1.5.0",
        "database": "unknown",
        "storage": "unknown"
    }
    
    # Check DB
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    
    # Check storage
    try:
        file_storage.base_path.exists()
        checks["storage"] = "ok"
    except Exception as e:
        checks["storage"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    
    return checks
```

---

### 8. Fichier .env.backup Exposé
**Fichier:** `.env.backup` (ligne 8)  
**Problème:** Anciennes clés API dans backup  
**Impact:** 🟡 Si leak, anciennes clés exposées  
**Fix:**
```bash
# Ajouter au .gitignore
.env.backup
*.backup

# Vérifier qu'il n'est pas tracké
git rm --cached .env.backup
git commit -m "security: Remove .env.backup from tracking"
```

---

## 🔧 RECOMMANDÉ - UX/QUALITÉ

### 9. Messages Erreurs Génériques
**Fichier:** `extension/generator.js`  
**Problème:** "Erreur génération" sans contexte  
**Impact:** 🟢 User confus  
**Fix:**
```javascript
// Avant
showStatus('error', `❌ Erreur: ${error.message}`);

// Après - Traduire codes HTTP
const ERROR_MESSAGES = {
    401: "Session expirée. Reconnectez-vous.",
    403: "Accès refusé.",
    429: "Trop de requêtes. Attendez 1 minute.",
    500: "Erreur serveur. Réessayez plus tard.",
    503: "Service temporairement indisponible."
};

showStatus('error', ERROR_MESSAGES[response.status] || `Erreur ${response.status}`);
```

---

### 10. Pas de Timeout Requêtes
**Fichier:** `extension/generator.js`  
**Problème:** Fetch peut attendre indéfiniment  
**Impact:** 🟢 Extension gelée  
**Fix:**
```javascript
async function fetchWithTimeout(url, options = {}, timeout = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (err) {
        clearTimeout(timeoutId);
        if (err.name === 'AbortError') {
            throw new Error('Requête expirée (30s)');
        }
        throw err;
    }
}

// Utiliser partout
const response = await fetchWithTimeout(`${API_URL}/...`, options);
```

---

## 📋 CHECKLIST PRIORITÉS

### 🔴 CRITIQUE (À faire AVANT deploy)
- [ ] Fix CORS wildcard → origines spécifiques
- [ ] Ajouter rate limiting (5 req/min génération)
- [ ] URLs dynamiques extension (config.js)
- [ ] Supprimer .env.backup du Git

### 🟡 IMPORTANT (À faire CETTE SEMAINE)
- [ ] Console.log → debug mode conditionnel
- [ ] print() → logging avec fichier
- [ ] Gestion erreurs OpenAI
- [ ] Health check complet (DB + storage)

### 🟢 RECOMMANDÉ (Après premier deploy)
- [ ] Messages erreurs clairs
- [ ] Timeouts fetch 30s
- [ ] Monitoring Sentry
- [ ] Tests unitaires endpoints critiques

---

## ⏱️ TEMPS ESTIMÉ

| Priorité | Temps | Détail |
|----------|-------|--------|
| 🔴 Critique | **2-3h** | CORS (30min) + Rate limit (1h) + Config URLs (1h) + .gitignore (10min) |
| 🟡 Important | **2h** | Logging (1h) + Error handling (30min) + Health check (30min) |
| 🟢 Recommandé | **1h** | Messages UX (30min) + Timeouts (30min) |
| **TOTAL** | **5-6h** | Réparti sur 2-3 jours |

---

## 🎯 PLAN D'ACTION

### Aujourd'hui (2h) - CRITIQUE
```bash
# 1. CORS + Rate limiting
cd CVLM
# Je te crée les fixes

# 2. Config extension
# Je te crée config.js

# 3. Tester localement
docker compose down && docker compose up -d
# Recharger extension

# 4. Commit
git add .
git commit -m "security: Add CORS restrictions and rate limiting"
```

### Demain (2h) - IMPORTANT
```bash
# 1. Logging
# Remplacer print() par logger

# 2. Error handling
# Try/catch OpenAI

# 3. Health check
# Tester DB connectivity

# 4. Commit
git commit -m "improve: Better logging and error handling"
```

### Après-demain (1h) - POLISH
```bash
# 1. Messages UX
# 2. Timeouts
# 3. Tests finaux
# 4. Deploy Proxmox !
```

---

## 💡 CE QUI EST DÉJÀ BON

✅ Architecture Clean respectée  
✅ PostgreSQL + OAuth fonctionnels  
✅ Historique lettres  
✅ Docker setup  
✅ Clés API sécurisées (régénérées)  
✅ Extension fonctionnelle  

**Tu es à 70% prêt. Les 6h restantes te mènent à 95% production-ready.**

---

## ❓ QUELLE PRIORITÉ TU VEUX FAIRE MAINTENANT ?

**Option A** : Je te crée les fixes 🔴 CRITIQUES maintenant (2h)  
**Option B** : On fait tout d'un coup (5-6h marathon)  
**Option C** : Tu veux d'abord réviser le code toi-même  

Dis-moi et je te prépare les fichiers ! 🚀
