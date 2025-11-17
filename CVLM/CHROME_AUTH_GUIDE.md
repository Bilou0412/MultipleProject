# 🔐 Authentification Google OAuth - Guide Complet

## 📋 Deux Approches Possibles

### 🎯 Approche 1 : Extension Chrome (Client-Side) ⭐ Recommandé
**Pour les extensions Chrome et applications JavaScript**

✅ **Simple** - Pas de serveur backend nécessaire  
✅ **Sécurisé** - Google gère tout via `chrome.identity`  
✅ **Pas de secret** - CLIENT_ID uniquement  

### 🎯 Approche 2 : Backend FastAPI (Server-Side)
**Pour l'API web et l'authentification serveur**

⚠️ Nécessite un Client Secret  
⚠️ Plus complexe mais plus de contrôle  

---

## 🌐 Approche 1 : Extension Chrome (Recommandé)

### Pourquoi pas de Client Secret ?

Google **n'utilise PAS de Client Secret** pour :
- ❌ Extensions Chrome
- ❌ Applications JavaScript (client-side)
- ❌ Applications mobiles natives

**Raison** : Un "secret" dans du code visible par l'utilisateur n'est pas secret ! 

### 1. Configuration Google Cloud Console

#### a) Créer un projet Google Cloud
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet : **"CVLM-Extension"**

#### b) Activer les APIs
1. Menu : **APIs & Services** > **Library**
2. Rechercher et activer : **Google+ API** ou **People API**

#### c) Créer un OAuth Client ID
1. Menu : **APIs & Services** > **Credentials**
2. Cliquer : **Create Credentials** > **OAuth client ID**
3. Type d'application : **Chrome Extension** (ou Web Application)
4. Nom : "CVLM Chrome Extension"
5. Origines autorisées :
   ```
   https://<extension-id>.chromiumapp.org/
   ```
   (Vous obtiendrez l'extension-id après la première installation)

6. **Copier le Client ID** généré

#### d) Configurer le manifest.json de l'extension

```json
{
  "manifest_version": 3,
  "name": "CVLM Generator",
  "version": "1.0",
  "permissions": [
    "identity",
    "storage"
  ],
  "oauth2": {
    "client_id": "825312610018-cjaamh6gf8882lut9t082jhjv9g4l0bo.apps.googleusercontent.com",
    "scopes": [
      "https://www.googleapis.com/auth/userinfo.email",
      "https://www.googleapis.com/auth/userinfo.profile"
    ]
  },
  "key": "VOTRE_CLE_PUBLIQUE_ICI"
}
```

### 2. Code de l'Extension Chrome

#### background.js - Authentification

```javascript
// Fonction de connexion avec Google
async function loginWithGoogle() {
  try {
    // Récupérer le token via chrome.identity (géré par Google)
    const token = await chrome.identity.getAuthToken({ interactive: true });
    
    console.log('✅ Token obtenu:', token);
    
    // Récupérer les infos utilisateur depuis l'API Google
    const userInfo = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(r => r.json());
    
    console.log('👤 Utilisateur:', userInfo);
    
    // Sauvegarder localement
    await chrome.storage.local.set({
      googleToken: token,
      user: {
        id: userInfo.id,
        email: userInfo.email,
        name: userInfo.name,
        picture: userInfo.picture
      }
    });
    
    return userInfo;
    
  } catch (error) {
    console.error('❌ Erreur authentification:', error);
    throw error;
  }
}

// Fonction de déconnexion
async function logout() {
  const data = await chrome.storage.local.get(['googleToken']);
  
  if (data.googleToken) {
    // Révoquer le token
    await chrome.identity.removeCachedAuthToken({ token: data.googleToken });
    
    // Nettoyer le storage
    await chrome.storage.local.remove(['googleToken', 'user']);
    
    console.log('✅ Déconnecté');
  }
}

// Vérifier si l'utilisateur est connecté
async function isAuthenticated() {
  const data = await chrome.storage.local.get(['googleToken', 'user']);
  return !!(data.googleToken && data.user);
}

// Récupérer l'utilisateur courant
async function getCurrentUser() {
  const data = await chrome.storage.local.get(['user']);
  return data.user || null;
}
```

#### popup.html - Interface utilisateur

```html
<!DOCTYPE html>
<html>
<head>
  <title>CVLM Generator</title>
  <style>
    body { width: 300px; padding: 20px; }
    .user-info { display: none; }
    .login-section { display: none; }
    img { border-radius: 50%; width: 50px; height: 50px; }
  </style>
</head>
<body>
  <!-- Section login -->
  <div id="loginSection" class="login-section">
    <h2>🔐 Connexion</h2>
    <button id="loginBtn">Se connecter avec Google</button>
  </div>
  
  <!-- Section utilisateur connecté -->
  <div id="userInfo" class="user-info">
    <h2>👤 Profil</h2>
    <img id="userPicture" src="" alt="Photo">
    <p><strong id="userName"></strong></p>
    <p id="userEmail"></p>
    <button id="logoutBtn">Se déconnecter</button>
    <hr>
    <button id="generateBtn">Générer une lettre</button>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>
```

#### popup.js - Logique du popup

```javascript
// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
  const authenticated = await chrome.runtime.sendMessage({ action: 'isAuthenticated' });
  
  if (authenticated) {
    const user = await chrome.runtime.sendMessage({ action: 'getCurrentUser' });
    showUserInfo(user);
  } else {
    showLoginSection();
  }
});

// Afficher les infos utilisateur
function showUserInfo(user) {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('userInfo').style.display = 'block';
  
  document.getElementById('userName').textContent = user.name;
  document.getElementById('userEmail').textContent = user.email;
  document.getElementById('userPicture').src = user.picture;
}

// Afficher le bouton de connexion
function showLoginSection() {
  document.getElementById('loginSection').style.display = 'block';
  document.getElementById('userInfo').style.display = 'none';
}

// Bouton de connexion
document.getElementById('loginBtn').addEventListener('click', async () => {
  try {
    const user = await chrome.runtime.sendMessage({ action: 'login' });
    showUserInfo(user);
  } catch (error) {
    alert('❌ Erreur de connexion: ' + error.message);
  }
});

// Bouton de déconnexion
document.getElementById('logoutBtn').addEventListener('click', async () => {
  await chrome.runtime.sendMessage({ action: 'logout' });
  showLoginSection();
});

// Bouton de génération (utilise l'API avec le token)
document.getElementById('generateBtn').addEventListener('click', async () => {
  const user = await chrome.runtime.sendMessage({ action: 'getCurrentUser' });
  const token = (await chrome.storage.local.get(['googleToken'])).googleToken;
  
  // Appeler votre API backend
  const response = await fetch('http://localhost:8000/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`  // Token Google
    },
    body: JSON.stringify({
      user_id: user.id,
      job_url: window.location.href
    })
  });
  
  const result = await response.json();
  console.log('✅ Lettre générée:', result);
});
```

### 3. Messages entre popup et background

#### background.js - Gestionnaire de messages

```javascript
// Écouter les messages du popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  (async () => {
    try {
      switch (request.action) {
        case 'login':
          const user = await loginWithGoogle();
          sendResponse(user);
          break;
          
        case 'logout':
          await logout();
          sendResponse({ success: true });
          break;
          
        case 'isAuthenticated':
          const authenticated = await isAuthenticated();
          sendResponse(authenticated);
          break;
          
        case 'getCurrentUser':
          const currentUser = await getCurrentUser();
          sendResponse(currentUser);
          break;
          
        default:
          sendResponse({ error: 'Action inconnue' });
      }
    } catch (error) {
      sendResponse({ error: error.message });
    }
  })();
  
  return true; // Garde le canal ouvert pour sendResponse async
});
```

---

## 🖥️ Approche 2 : Backend FastAPI (Server-Side)

### Quand l'utiliser ?

- Authentification côté serveur
- Besoin de refresh tokens
- Accès à des APIs Google sensibles

### 1. Configuration Google Cloud Console

1. Type d'application : **Application Web**
2. URIs de redirection autorisés :
   ```
   http://localhost:8000/auth/callback
   https://votre-domaine.com/auth/callback
   ```
3. **Copier le Client ID ET le Client Secret**

### 2. Configuration .env

```env
# Backend OAuth (Server-Side)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
JWT_SECRET=your-random-secret-key-here
```

### 3. Code Backend (voir GOOGLE_AUTH_GUIDE.md)

Le guide complet est dans `GOOGLE_AUTH_GUIDE.md` avec :
- Port `AuthService`
- Adaptateur `GoogleOAuthService`
- Endpoints FastAPI
- Gestion JWT

---

## 🔄 Approche Hybride (Recommandé pour Production)

### Extension Chrome → Backend

1. **Extension** : Authentification avec `chrome.identity` (sans secret)
2. **Backend** : Vérification du token Google et création JWT propre

#### Flux

```
1. User clicks "Login" dans l'extension
   ↓
2. chrome.identity.getAuthToken() → Token Google
   ↓
3. Extension envoie le token à l'API
   POST /auth/verify-google-token
   Body: { token: "google-token" }
   ↓
4. API vérifie le token avec Google
   ↓
5. API crée/récupère l'utilisateur en DB
   ↓
6. API retourne un JWT propre
   Response: { jwt: "your-jwt", user: {...} }
   ↓
7. Extension utilise le JWT pour les requêtes
   Authorization: Bearer jwt
```

#### Endpoint API : Vérification du token Google

```python
# api_server.py

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

@app.post("/auth/verify-google-token")
async def verify_google_token(token_data: dict):
    """Vérifie un token Google depuis l'extension Chrome"""
    try:
        # Vérifier le token auprès de Google
        idinfo = id_token.verify_oauth2_token(
            token_data['token'],
            google_requests.Request(),
            os.getenv('GOOGLE_CLIENT_ID')
        )
        
        # Extraire les infos
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        picture = idinfo.get('picture')
        
        # Chercher ou créer l'utilisateur
        user = user_repository.get_by_google_id(google_id)
        if not user:
            user = User(
                id=None,
                email=email,
                google_id=google_id,
                name=name,
                profile_picture_url=picture
            )
            user = user_repository.create(user)
        
        # Créer un JWT propre
        jwt_token = create_jwt(user.id, user.email)
        
        return {
            "status": "success",
            "jwt": jwt_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.profile_picture_url
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Token invalide")
```

---

## 📚 Résumé

| Approche | Client Secret ? | Complexité | Cas d'usage |
|----------|----------------|------------|-------------|
| **Extension Chrome** | ❌ Non | ⭐ Simple | Extension, App mobile |
| **Backend FastAPI** | ✅ Oui | ⭐⭐ Moyen | API web, Refresh tokens |
| **Hybride** | ❌ Non (client) | ⭐⭐⭐ Avancé | Production avec JWT |

## 🎯 Recommandation pour CVLM

**Utiliser l'approche hybride** :
1. Extension Chrome avec `chrome.identity` (pas de secret)
2. Token Google envoyé à l'API
3. API vérifie et crée un JWT
4. Extension utilise le JWT pour toutes les requêtes

**Avantages** :
- ✅ Pas de secret exposé dans l'extension
- ✅ Contrôle total côté serveur
- ✅ JWT pour gérer les sessions
- ✅ Peut révoquer les accès facilement

## 🔗 Ressources

- [Chrome Identity API](https://developer.chrome.com/docs/extensions/reference/identity/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Vérification de tokens](https://developers.google.com/identity/sign-in/web/backend-auth)
