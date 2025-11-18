# 🚀 PROCHAINES ÉTAPES URGENTES

## ✅ FAIT
- [x] Nouveau JWT_SECRET généré : `XuOEwC6t9kIdvuGt7HHDO47mmnIlcVss9c7RcbMEBkU`
- [x] `.env` mis à jour localement
- [x] `.env.example` créé
- [x] Backup créé : `../CVLM-backup-20251118-184531.tar.gz`

---

## 🚨 À FAIRE MAINTENANT (30 minutes)

### 1. Révoquer les anciennes clés exposées ⚠️

#### OpenAI (5 min)
```
1. Aller sur https://platform.openai.com/api-keys
2. Trouver la clé: sk-proj----W_Lx...
3. Cliquer "Revoke"
4. Créer nouvelle clé → Copier
5. Mettre à jour .env:
   OPENAI_API_KEY=sk-nouvelle-cle
```

#### Google OAuth (10 min)
```
1. Aller sur https://console.cloud.google.com/apis/credentials
2. Projet actuel: Trouver CLIENT_ID: 825312610018-ied76...
3. Supprimer les anciennes credentials OAuth 2.0
4. Créer nouveau "OAuth 2.0 Client ID"
   - Type: Application Web
   - Authorized origins: http://localhost:8000, https://api.cvlm.app
   - Authorized redirect URIs: 
     - http://localhost:8000/auth/callback
     - https://api.cvlm.app/auth/callback
5. Télécharger JSON et copier:
   - Client ID → .env GOOGLE_CLIENT_ID
   - Client ID → extension/manifest.json
```

#### Google Gemini (optionnel, 5 min)
```
1. Aller sur https://makersuite.google.com/app/apikey
2. Révoquer ancienne clé: 7V3G09_X_VUb...
3. Créer nouvelle clé → Copier
4. Mettre à jour .env:
   GOOGLE_API_KEY=nouvelle-cle
```

---

### 2. Tester localement (5 min)

```bash
# Redémarrer Docker avec nouvelles clés
docker compose down
docker compose up -d

# Tester l'auth
curl http://localhost:8000/health

# Tester génération (avec nouveau token)
# Ouvrir l'extension et se reconnecter
```

---

### 3. Commiter les fichiers de production (5 min)

```bash
# Ajouter SEULEMENT les fichiers publics
git add .env.example
git add PRODUCTION_CHECKLIST.md
git add DEPLOYMENT_GUIDE.md
git add PRIVACY_POLICY.md
git add TERMS_OF_SERVICE.md
git add WHAT_IS_MISSING.md
git add secure-for-production.sh

# NE PAS ajouter .env !!!
git status  # Vérifier que .env n'est pas listé

# Commiter
git commit -m "docs: Add production documentation and security setup"

# Pusher (SANS --force car on n'a PAS nettoyé l'historique Git)
git push origin main
```

**Note:** Le script n'a PAS réussi à nettoyer l'historique Git (`You need to run this command from the toplevel`). Ce n'est pas grave pour l'instant, on peut le faire plus tard si nécessaire.

---

## 📅 APRÈS (Planning 2-3 semaines)

### Semaine 1 : Infrastructure
- [ ] Créer compte Railway.app
- [ ] Déployer avec nouvelles clés
- [ ] Acheter domaine (api.cvlm.app)
- [ ] Configurer HTTPS

### Semaine 2 : Extension Chrome
- [ ] Payer $5 Google Developer
- [ ] Designer icônes
- [ ] Screenshots + vidéo
- [ ] Publier sur Chrome Web Store

### Semaine 3 : Reddit
- [ ] Attendre review Chrome (3-5 jours)
- [ ] Préparer post Reddit
- [ ] Publier sur r/SideProject
- [ ] Itérer sur feedback

---

## ⚠️ IMPORTANT

**NE JAMAIS COMMITER CES FICHIERS:**
- `.env` (contient les clés)
- `.env.backup` (contient anciennes clés)
- `data/` (contient données users)

**TOUJOURS VÉRIFIER:**
```bash
git status  # .env doit être dans "Untracked files"
cat .gitignore | grep .env  # Doit afficher ".env"
```

---

## 🔗 Liens utiles

- OpenAI Keys: https://platform.openai.com/api-keys
- Google Cloud Console: https://console.cloud.google.com/apis/credentials
- Google Gemini Keys: https://makersuite.google.com/app/apikey
- Railway Deploy: https://railway.app/
- Chrome Web Store: https://chrome.google.com/webstore/devconsole

---

**PROCHAINE ÉTAPE:** Régénère tes clés API (30 min), puis teste localement. Une fois validé, on passe au déploiement !
