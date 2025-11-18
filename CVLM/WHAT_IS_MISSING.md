# ❌ Ce qui MANQUE pour la Production et Reddit

## 🚨 CRITIQUE - À faire AVANT de publier

### 1. Sécurité (1-2 jours)
- [ ] **Supprimer TOUTES les clés API de Git** (script fourni: `./secure-for-production.sh`)
- [ ] Générer nouveau `JWT_SECRET_KEY` aléatoire
- [ ] Créer nouvelles credentials Google OAuth
- [ ] Révoquer anciennes clés exposées
- [ ] Restreindre CORS (pas de wildcard `*`)
- [ ] Implémenter rate limiting (5 req/min par utilisateur)

**Impact:** ⚠️ CRITIQUE - Vulnérabilités majeures

---

### 2. Infrastructure (2-3 jours)
- [ ] Déployer sur Railway/Render/Fly.io
- [ ] Configurer HTTPS (obligatoire pour OAuth)
- [ ] Acheter nom de domaine (ex: `api.cvlm.app`)
- [ ] Migrer fichiers vers S3/Cloudflare R2
- [ ] Setup backup PostgreSQL quotidien
- [ ] Monitoring avec Sentry + Uptime Robot

**Impact:** 🔴 BLOQUANT - OAuth ne marche pas sans HTTPS

---

### 3. Extension Chrome (3-4 jours)
- [ ] Créer compte Google Developer ($5)
- [ ] Rédiger **Privacy Policy** (obligatoire)
- [ ] Rédiger **Terms of Service**
- [ ] Designer icônes professionnelles (128x128)
- [ ] Prendre 5-7 screenshots (1280x800)
- [ ] Créer vidéo démo (30-60s)
- [ ] Publier sur Chrome Web Store

**Impact:** 🔴 BLOQUANT - Impossible de partager l'extension sans publication

---

### 4. Documentation (1 jour)
- [ ] README avec screenshots et démo
- [ ] FAQ basique
- [ ] Guide d'installation utilisateur
- [ ] Troubleshooting commun

**Impact:** 🟡 IMPORTANT - Reddit downvotera sans démo claire

---

## ✅ Ce qui est BON

- ✅ Architecture Clean respectée
- ✅ Code fonctionnel end-to-end
- ✅ Multi-user avec isolation données
- ✅ Historique lettres générées
- ✅ Google OAuth implémenté
- ✅ Docker setup complet

---

## 📊 Résumé

| Catégorie | État | Temps | Priorité |
|-----------|------|-------|----------|
| Sécurité | ❌ 20% | 1-2j | 🔴 CRITIQUE |
| Infrastructure | ❌ 10% | 2-3j | 🔴 BLOQUANT |
| Extension Chrome | ❌ 0% | 3-4j | 🔴 BLOQUANT |
| UX/Logs | ⚠️ 60% | 1j | 🟡 Important |
| Documentation | ⚠️ 40% | 1j | �� Important |
| **TOTAL** | **❌ 30%** | **8-11 jours** | |

---

## 🎯 Plan d'action RÉALISTE

### Semaine 1 : SÉCURITÉ + INFRA
**Jour 1-2:** Sécurité
- Exécuter `./secure-for-production.sh`
- Générer nouvelles clés OAuth
- Tester rate limiting

**Jour 3-4:** Infrastructure
- Déployer sur Railway (le plus simple)
- Configurer domaine + HTTPS
- Tester en production

**Jour 5:** Tests et fixes
- Tests end-to-end en production
- Corriger bugs découverts

### Semaine 2 : EXTENSION + MARKETING
**Jour 6-7:** Legal
- Rédiger Privacy Policy
- Rédiger Terms of Service
- Créer landing page simple

**Jour 8-9:** Chrome Web Store
- Payer $5
- Designer icônes
- Screenshots + vidéo démo
- Soumettre pour review (3-5 jours délai)

**Jour 10-11:** Reddit
- Préparer post
- Répondre aux questions
- Itérer sur feedback

---

## 💰 Budget minimal

| Item | Prix | Note |
|------|------|------|
| Google Developer | $5 | One-time |
| Domaine | $10/an | Namecheap/Porkbun |
| Railway free tier | $0 | 500h/mois suffit |
| **TOTAL AN 1** | **$15** | |

---

## ⏰ Timeline réaliste

- **Aujourd'hui → J+5:** Sécurité + Deploy production
- **J+6 → J+11:** Extension + Legal + Marketing
- **J+12 → J+17:** Review Chrome Web Store (attente)
- **J+18:** Publication Reddit + premiers users

**Total: ~3 semaines** pour un lancement professionnel.

---

## 🎁 Bonus (optionnel, après Reddit)

- [ ] Mode dark theme
- [ ] Export DOCX
- [ ] Templates personnalisables
- [ ] Multi-langue (EN, ES)
- [ ] Analytics anonymes
- [ ] Intégration LinkedIn

---

**TL;DR:** Il manque **8-11 jours de travail** pour un lancement production propre.
Les 3 bloquants : Sécurité (clés exposées), HTTPS (OAuth), Chrome Web Store (distribution).
