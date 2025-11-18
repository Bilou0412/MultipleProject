# 🚀 Checklist de Mise en Production - CVLM

## ⚠️ CRITIQUE - À faire AVANT toute publication

### 1. Sécurité
- [ ] **Supprimer TOUTES les clés API du Git**
  ```bash
  git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch .env" \
    --prune-empty --tag-name-filter cat -- --all
  ```
- [ ] Ajouter `.env` au `.gitignore` (déjà fait)
- [ ] Créer `.env.example` sans valeurs réelles
- [ ] Générer nouveau `JWT_SECRET_KEY` aléatoire :
  ```python
  import secrets
  print(secrets.token_urlsafe(32))
  ```
- [ ] Restreindre CORS :
  ```python
  allow_origins=[
      "chrome-extension://YOUR_EXTENSION_ID",
      "https://yourdomain.com"
  ]
  ```
- [ ] Implémenter rate limiting (slowapi ou fastapi-limiter)
- [ ] Valider TOUS les inputs utilisateur
- [ ] Sanitiser les sorties (prévenir XSS)

### 2. Infrastructure
- [ ] **Déployer sur un serveur avec HTTPS** (Render, Railway, Fly.io)
- [ ] Configurer nom de domaine (ex: `api.cvlm.app`)
- [ ] Certificat SSL via Let's Encrypt
- [ ] Migrer fichiers vers S3/Cloudflare R2
- [ ] Setup backup PostgreSQL automatique (daily)
- [ ] Configurer logs centralisés (Sentry)
- [ ] Ajouter health check avec uptime monitoring

### 3. Extension Chrome
- [ ] **Créer compte Google Developer** ($5 one-time)
- [ ] **Rédiger Privacy Policy** (obligatoire) :
  - Quelles données collectées
  - Comment elles sont utilisées
  - Politique de suppression
  - Héberger sur un site web
- [ ] **Créer Terms of Service**
- [ ] Designer icônes professionnelles (128x128, 48x48, 16x16)
- [ ] Captures d'écran pour le store (1280x800)
- [ ] Vidéo démo (optionnel mais recommandé)
- [ ] Publier sur Chrome Web Store
- [ ] Mettre à jour `manifest.json` avec liens Privacy/ToS

### 4. Base de données
- [ ] Ajouter indexes sur colonnes fréquentes :
  ```sql
  CREATE INDEX idx_cvs_user_id ON cvs(user_id);
  CREATE INDEX idx_letters_user_id ON motivational_letters(user_id);
  CREATE INDEX idx_letters_created ON motivational_letters(created_at DESC);
  ```
- [ ] Mettre en place archivage des vieilles lettres (>6 mois)
- [ ] Limiter la taille des uploads (ex: CV < 10MB)

### 5. Code
- [ ] Ajouter validation Pydantic stricte
- [ ] Gérer erreurs OpenAI (quota, timeout, 429)
- [ ] Ajouter retry logic avec backoff exponentiel
- [ ] Implémenter circuit breaker pour APIs externes
- [ ] Logger TOUTES les erreurs (pas juste print)

---

## 🎯 RECOMMANDÉ (améliore l'expérience)

### UX
- [ ] Améliorer messages d'erreur (user-friendly)
- [ ] Ajouter progress bar pendant génération
- [ ] Toast notifications au lieu d'alerts
- [ ] Mode offline graceful (message clair)
- [ ] Tutoriel première utilisation (onboarding)

### Performance
- [ ] Cache Redis pour résultats fréquents
- [ ] CDN pour assets statiques
- [ ] Compression gzip/brotli
- [ ] Minification JS/CSS
- [ ] Lazy loading des lettres (pagination)

### Monitoring
- [ ] Dashboard analytics (Plausible/Umami)
- [ ] Tracking erreurs utilisateur
- [ ] Métriques performance (temps génération)
- [ ] Alertes Slack/Discord sur erreurs critiques

### Documentation
- [ ] README avec screenshots
- [ ] Guide d'installation détaillé
- [ ] FAQ avec cas d'usage
- [ ] Troubleshooting commun
- [ ] Changelog

---

## 📢 PRÉPARATION REDDIT

### Contenu à préparer

1. **Démo vidéo** (30-60 secondes)
   - Connexion Google
   - Upload CV
   - Génération lettre
   - Téléchargement PDF
   - Historique

2. **Screenshots** (5-7 images)
   - Interface principale
   - Liste CVs
   - Historique lettres
   - Exemple de lettre générée

3. **Post Reddit** (structure)
   ```markdown
   [Project] CVLM - AI-powered cover letter generator (Chrome Extension)
   
   🎯 What it does:
   - One-click cover letter generation from job postings
   - Uses GPT-4 to analyze CV + job offer
   - Multi-user with Google OAuth
   - Full history of generated letters
   
   🔧 Tech Stack:
   - FastAPI + PostgreSQL + Docker
   - Chrome Extension (Manifest v3)
   - Clean Architecture
   - OpenAI GPT-4 / Google Gemini
   
   🚀 Status: MVP ready, seeking early feedback
   
   [Demo Video] [Screenshots] [GitHub]
   
   Looking for feedback on:
   - UX improvements
   - Feature requests
   - Bug reports
   
   Free to use during beta!
   ```

4. **Landing page simple**
   - Description claire
   - Call-to-action
   - Privacy Policy
   - Terms of Service
   - Contact/Support

### Subreddits cibles
- r/SideProject ✅ (friendly for MVPs)
- r/AlphaAndBetaUsers ✅
- r/Entrepreneur
- r/cscareerquestions (si B2B dev jobs)
- r/JobPostings
- r/Resume

---

## 🎁 BONUS - Nice to have

- [ ] Mode dark/light theme
- [ ] Export lettres en DOCX
- [ ] Templates personnalisables
- [ ] Multi-langue (EN, ES, DE)
- [ ] Extension Firefox
- [ ] Mobile app (React Native)
- [ ] Intégration LinkedIn
- [ ] API publique pour devs

---

## ⏱️ ESTIMATION TEMPS

### Minimum Viable (1-2 semaines)
- Sécurité : 2 jours
- Deploy production : 1 jour
- Privacy Policy : 1 jour
- Chrome Store : 2 jours
- Tests end-to-end : 1 jour

### Pour lancement solide (3-4 semaines)
- + UX improvements : 3 jours
- + Monitoring : 2 jours
- + Documentation : 2 jours
- + Marketing content : 3 jours

---

## 🎯 PRIORITÉS

**AUJOURD'HUI :**
1. Supprimer clés API du Git
2. Générer nouveau JWT_SECRET
3. Créer Privacy Policy simple

**CETTE SEMAINE :**
1. Déployer sur plateforme cloud
2. Configurer HTTPS
3. Publier extension Chrome

**AVANT REDDIT :**
1. Tests complets utilisateur
2. Créer démo vidéo
3. Préparer screenshots

---

## ✅ DONE
- [x] Clean Architecture
- [x] Docker setup
- [x] Google OAuth
- [x] Multi-user support
- [x] Letter history
- [x] PDF generation
