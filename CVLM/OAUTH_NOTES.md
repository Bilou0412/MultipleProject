# 🔑 Configuration OAuth - Notes Importantes

## ❌ Pourquoi pas de Client Secret pour l'extension Chrome ?

### Explication

Google **ne fournit PAS de Client Secret** pour :
- ❌ **Extensions Chrome** (code visible dans le navigateur)
- ❌ **Applications JavaScript** côté client
- ❌ **Applications mobiles natives**

### Raison de Sécurité

Un "Client Secret" dans du code accessible par l'utilisateur **n'est pas secret** !

```javascript
// ❌ MAUVAIS - Le secret serait visible dans le code
const clientSecret = "GOCSPX-abc123...";  // ⚠️ N'importe qui peut le voir !
```

### Solutions Google

Google utilise plutôt :
1. **PKCE** (Proof Key for Code Exchange)
2. **chrome.identity API** pour les extensions
3. **Vérification du domaine/extension ID**

---

## ✅ Configuration Actuelle

### Extension Chrome
```json
// manifest.json
{
  "permissions": ["identity"],
  "oauth2": {
    "client_id": "825312610018-cjaamh6gf8882lut9t082jhjv9g4l0bo.apps.googleusercontent.com",
    "scopes": [
      "https://www.googleapis.com/auth/userinfo.email",
      "https://www.googleapis.com/auth/userinfo.profile"
    ]
  }
}
```

**✅ CLIENT_ID uniquement - C'est normal !**

### Backend FastAPI (Optionnel)

Si vous avez besoin d'authentification côté serveur :

```.env
# Pour l'API backend (application web serveur)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here  # Uniquement pour le serveur !
```

---

## 🔄 Deux Types d'OAuth Client

### 1. Chrome Extension / JavaScript App

**Type** : Extension Chrome ou Application JavaScript  
**Client Secret** : ❌ Aucun  
**Sécurité** : Gérée par Google via `chrome.identity`

**Configuration Google Cloud** :
```
Type d'application : Extension Chrome
Origines JavaScript autorisées : 
  - chrome-extension://YOUR_EXTENSION_ID
```

### 2. Application Web (Server-Side)

**Type** : Application Web  
**Client Secret** : ✅ Oui (gardé côté serveur)  
**Sécurité** : Le secret n'est jamais exposé au client

**Configuration Google Cloud** :
```
Type d'application : Application Web
URIs de redirection autorisés :
  - http://localhost:8000/auth/callback
  - https://votre-domaine.com/auth/callback
```

---

## 🎯 Architecture Recommandée pour CVLM

### Approche Hybride Sécurisée

```
┌─────────────────────────────────────────────────────┐
│                Extension Chrome                     │
│                                                     │
│  1. chrome.identity.getAuthToken()                 │
│     ↓                                               │
│  2. Token Google obtenu (PAS DE SECRET NÉCESSAIRE) │
│     ↓                                               │
│  3. Envoyer token à l'API backend                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                API Backend (FastAPI)                │
│                                                     │
│  4. Vérifier le token avec Google                  │
│     (utilise CLIENT_ID pour vérifier)              │
│     ↓                                               │
│  5. Créer/récupérer utilisateur en DB              │
│     ↓                                               │
│  6. Générer un JWT propre                          │
│     ↓                                               │
│  7. Retourner JWT à l'extension                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                Extension Chrome                     │
│                                                     │
│  8. Stocker JWT                                     │
│  9. Utiliser JWT pour toutes les requêtes API     │
│     Authorization: Bearer JWT                       │
└─────────────────────────────────────────────────────┘
```

### Avantages

✅ **Pas de secret exposé** dans l'extension  
✅ **Contrôle total** de l'authentification côté serveur  
✅ **JWT** pour gérer les sessions et permissions  
✅ **Révocation** possible des accès  
✅ **Sécurité** maximale  

---

## 📝 Configuration du Projet

### Variables d'Environnement (.env)

```env
# Extension Chrome - CLIENT_ID uniquement
GOOGLE_CLIENT_ID=825312610018-cjaamh6gf8882lut9t082jhjv9g4l0bo.apps.googleusercontent.com

# Backend API - SECRET uniquement si auth serveur (optionnel)
# GOOGLE_CLIENT_SECRET=GOCSPX-...

# JWT pour les sessions internes
JWT_SECRET=change-this-in-production
```

### Fichiers Modifiés

- ✅ `extension/manifest.json` - Ajout `identity` permission et `oauth2` config
- ✅ `.env.example` - Clarifié la différence CLIENT_ID vs SECRET
- ✅ `CHROME_AUTH_GUIDE.md` - Guide complet avec exemples de code

---

## 🔗 Ressources

- [Chrome Identity API](https://developer.chrome.com/docs/extensions/reference/identity/)
- [OAuth 2.0 pour Client-Side Apps](https://developers.google.com/identity/protocols/oauth2/javascript-implicit-flow)
- [PKCE Flow](https://oauth.net/2/pkce/)
- [Google OAuth Best Practices](https://developers.google.com/identity/protocols/oauth2/web-server#security-considerations)

---

## 💡 TL;DR

- **Extension Chrome** : Utilise `chrome.identity` avec CLIENT_ID uniquement (✅ NORMAL)
- **Backend API** : Peut utiliser CLIENT_ID + SECRET pour auth serveur (optionnel)
- **Pas de secret dans le code client** = bonne pratique de sécurité Google
- **Architecture hybride recommandée** : Extension obtient token → API vérifie et crée JWT

**Le CLIENT_ID seul dans l'extension est PARFAITEMENT SÉCURISÉ et c'est la méthode recommandée par Google !** ✅
