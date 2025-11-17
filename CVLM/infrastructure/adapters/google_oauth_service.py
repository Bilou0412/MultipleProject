"""
Service d'authentification Google OAuth pour extensions Chrome
"""
from typing import Optional
import httpx
import os
from datetime import datetime
from uuid import uuid4

from domain.entities.user import User
from domain.ports.user_repository import UserRepository


class GoogleOAuthService:
    """Service de validation des tokens Google et gestion des utilisateurs"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        
        if not self.client_id:
            raise ValueError("GOOGLE_CLIENT_ID non configuré dans les variables d'environnement")
    
    async def verify_google_token(self, token: str) -> Optional[dict]:
        """
        Vérifie un access token Google reçu de chrome.identity.getAuthToken()
        
        Args:
            token: Access token OAuth2 Google
            
        Returns:
            Dict avec les informations de l'utilisateur ou None si invalide
        """
        try:
            # Utiliser l'API Google UserInfo pour valider le token et récupérer les infos
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if response.status_code != 200:
                    print(f"⚠️ Erreur Google API: {response.status_code} - {response.text}")
                    return None
                
                user_info = response.json()
                
                return {
                    'google_id': user_info['id'],
                    'email': user_info['email'],
                    'name': user_info.get('name', ''),
                    'picture': user_info.get('picture', ''),
                    'email_verified': user_info.get('verified_email', False)
                }
            
        except Exception as e:
            print(f"❌ Erreur validation token Google: {e}")
            return None
    
    async def authenticate_user(self, google_token: str) -> Optional[User]:
        """
        Authentifie un utilisateur via son token Google
        Crée l'utilisateur s'il n'existe pas déjà
        
        Args:
            google_token: Token ID Google
            
        Returns:
            User entity ou None si authentification échouée
        """
        # Valider le token Google
        google_info = await self.verify_google_token(google_token)
        if not google_info:
            return None
        
        # Vérifier si l'email est vérifié
        if not google_info.get('email_verified', False):
            print(f"⚠️ Email non vérifié pour {google_info['email']}")
            return None
        
        # Chercher l'utilisateur par google_id
        user = self.user_repository.get_by_google_id(google_info['google_id'])
        
        if user:
            # Utilisateur existant - mettre à jour la dernière connexion
            user.updated_at = datetime.utcnow()
            user.profile_picture_url = google_info.get('picture')
            self.user_repository.update(user)
            print(f"✅ Utilisateur existant connecté: {user.email}")
            return user
        
        # Vérifier si un utilisateur existe déjà avec cet email
        user = self.user_repository.get_by_email(google_info['email'])
        
        if user:
            # Associer le google_id à l'utilisateur existant
            user.google_id = google_info['google_id']
            user.updated_at = datetime.utcnow()
            user.profile_picture_url = google_info.get('picture')
            self.user_repository.update(user)
            print(f"✅ Google ID associé à l'utilisateur existant: {user.email}")
            return user
        
        # Créer un nouvel utilisateur
        new_user = User(
            id=str(uuid4()),
            email=google_info['email'],
            google_id=google_info['google_id'],
            name=google_info['name'],
            profile_picture_url=google_info.get('picture'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.user_repository.create(new_user)
        print(f"✅ Nouvel utilisateur créé: {new_user.email}")
        return new_user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        return self.user_repository.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        return self.user_repository.get_by_email(email)
