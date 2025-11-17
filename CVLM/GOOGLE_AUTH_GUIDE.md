# Guide d'Intégration Google OAuth 2.0

## 🎯 Objectif
Permettre aux utilisateurs de se connecter avec leur compte Google et associer leurs CVs/lettres à leur compte.

## 📋 Prérequis

### 1. Créer un Projet Google Cloud
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet "CVLM"
3. Activer l'API "Google+ API" ou "Google Identity"

### 2. Configurer OAuth 2.0
1. Dans "APIs & Services" > "Credentials"
2. Créer des "OAuth 2.0 Client IDs"
3. Type d'application : "Application Web"
4. URIs de redirection autorisés :
   - `http://localhost:8000/auth/callback` (développement)
   - `https://votre-domaine.com/auth/callback` (production)
5. Récupérer `Client ID` et `Client Secret`

### 3. Configurer .env
```env
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
```

## 🔧 Implémentation

### 1. Installer les Dépendances
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 PyJWT
```

### 2. Créer le Port pour l'Authentification

**Fichier : `domain/ports/auth_service.py`**
```python
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User

class AuthService(ABC):
    @abstractmethod
    def get_authorization_url(self) -> str:
        """Génère l'URL de connexion Google"""
        pass
    
    @abstractmethod
    def authenticate_with_code(self, code: str) -> User:
        """Authentifie un utilisateur avec le code OAuth"""
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[User]:
        """Vérifie un token JWT et retourne l'utilisateur"""
        pass
    
    @abstractmethod
    def create_token(self, user: User) -> str:
        """Crée un token JWT pour un utilisateur"""
        pass
```

### 3. Créer l'Adaptateur Google OAuth

**Fichier : `infrastructure/adapters/google_oauth_service.py`**
```python
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional

from domain.ports.auth_service import AuthService
from domain.ports.user_repository import UserRepository
from domain.entities.user import User

class GoogleOAuthService(AuthService):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
        
        self.flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=['openid', 'email', 'profile']
        )
        self.flow.redirect_uri = self.redirect_uri
    
    def get_authorization_url(self) -> str:
        """Génère l'URL de connexion Google"""
        auth_url, _ = self.flow.authorization_url(prompt='consent')
        return auth_url
    
    def authenticate_with_code(self, code: str) -> User:
        """Authentifie avec le code OAuth et crée/récupère l'utilisateur"""
        # Échange le code contre des tokens
        self.flow.fetch_token(code=code)
        credentials = self.flow.credentials
        
        # Récupère les infos utilisateur depuis le token ID
        user_info = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            self.client_id
        )
        
        google_id = user_info['sub']
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        picture = user_info.get('picture')
        
        # Cherche ou crée l'utilisateur
        user = self.user_repository.get_by_google_id(google_id)
        
        if not user:
            # Nouvel utilisateur
            user = User(
                id=None,  # Sera généré par le repository
                email=email,
                google_id=google_id,
                name=name,
                profile_picture_url=picture
            )
            user = self.user_repository.create(user)
        else:
            # Mise à jour des infos
            user.name = name
            user.profile_picture_url = picture
            user = self.user_repository.update(user)
        
        return user
    
    def create_token(self, user: User) -> str:
        """Crée un JWT pour l'utilisateur"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[User]:
        """Vérifie un JWT et retourne l'utilisateur"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
            
            return self.user_repository.get_by_id(user_id)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

### 4. Ajouter les Endpoints à l'API

**Fichier : `api_server.py` (ajouts)**
```python
from fastapi import Depends, HTTPException, Header
from infrastructure.adapters.google_oauth_service import GoogleOAuthService
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository

# Initialiser le service d'authentification
user_repo = PostgresUserRepository()
auth_service = GoogleOAuthService(user_repo)

# Dépendance pour récupérer l'utilisateur authentifié
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    token = authorization.replace('Bearer ', '')
    user = auth_service.verify_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    return user

# Endpoints d'authentification
@app.get("/auth/login")
async def login():
    """Redirige vers la page de connexion Google"""
    auth_url = auth_service.get_authorization_url()
    return {"auth_url": auth_url}

@app.get("/auth/callback")
async def auth_callback(code: str):
    """Callback après connexion Google"""
    try:
        user = auth_service.authenticate_with_code(code)
        token = auth_service.create_token(user)
        
        return {
            "status": "success",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.profile_picture_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'authentification: {str(e)}")

@app.get("/auth/me")
async def get_profile(user = Depends(get_current_user)):
    """Récupère le profil de l'utilisateur connecté"""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.profile_picture_url
    }

# Exemple : Protéger un endpoint existant
@app.get("/my-cvs")
async def get_my_cvs(user = Depends(get_current_user)):
    """Liste les CVs de l'utilisateur connecté"""
    cv_repo = PostgresCvRepository()
    cvs = cv_repo.get_by_user_id(user.id)
    
    return {
        "status": "success",
        "cvs": [
            {
                "id": cv.id,
                "filename": cv.filename,
                "created_at": cv.created_at.isoformat(),
                "file_size": cv.file_size
            }
            for cv in cvs
        ]
    }
```

### 5. Extension Navigateur (JavaScript)

**Fichier : `extension/background.js` (ajouts)**
```javascript
// Stocker le token après connexion
function loginWithGoogle() {
  fetch('http://localhost:8000/auth/login')
    .then(r => r.json())
    .then(data => {
      // Ouvrir la page de connexion Google
      chrome.tabs.create({ url: data.auth_url }, (tab) => {
        // Écouter la redirection callback
        chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
          if (tabId === tab.id && info.url && info.url.includes('/auth/callback?code=')) {
            // Extraire le code
            const url = new URL(info.url);
            const code = url.searchParams.get('code');
            
            // Échanger le code contre un token
            fetch(`http://localhost:8000/auth/callback?code=${code}`)
              .then(r => r.json())
              .then(authData => {
                // Sauvegarder le token
                chrome.storage.local.set({ 
                  authToken: authData.token,
                  user: authData.user
                });
                
                chrome.tabs.remove(tabId);
                chrome.tabs.onUpdated.removeListener(listener);
              });
          }
        });
      });
    });
}

// Ajouter le token aux requêtes
function makeAuthenticatedRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get(['authToken'], (result) => {
      const headers = {
        ...options.headers,
        'Authorization': `Bearer ${result.authToken}`
      };
      
      fetch(url, { ...options, headers })
        .then(resolve)
        .catch(reject);
    });
  });
}
```

## 🧪 Test de l'Authentification

1. Lancer l'API : `uvicorn api_server:app --reload`
2. Aller sur http://localhost:8000/auth/login
3. Copier l'URL de connexion Google
4. Se connecter avec un compte Google
5. Vérifier que le token est retourné
6. Tester `/auth/me` avec le token :
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/auth/me
   ```

## 🔒 Sécurité

- **Production** : Utiliser HTTPS obligatoirement
- **JWT Secret** : Générer une clé sécurisée unique
- **Token Expiration** : Configurable (actuellement 7 jours)
- **CORS** : Restreindre aux domaines autorisés
- **Rate Limiting** : Ajouter une limite de requêtes

## 📚 Ressources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
