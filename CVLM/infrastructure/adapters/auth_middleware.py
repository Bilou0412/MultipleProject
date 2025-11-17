"""
Middleware d'authentification JWT pour FastAPI
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

from domain.entities.user import User
from domain.ports.user_repository import UserRepository


# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours

security = HTTPBearer()


def create_access_token(user_id: str, email: str) -> str:
    """
    Crée un token JWT pour l'utilisateur
    
    Args:
        user_id: ID de l'utilisateur
        email: Email de l'utilisateur
        
    Returns:
        Token JWT encodé
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user_id,  # Subject = user ID
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()  # Issued at
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Décode et valide un token JWT
    
    Args:
        token: Token JWT à décoder
        
    Returns:
        Payload du token ou None si invalide
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"⚠️ Erreur décodage JWT: {e}")
        return None


def verify_access_token(token: str) -> dict:
    """
    Vérifie et décode un token JWT (lance une exception si invalide)
    
    Args:
        token: Token JWT à vérifier
        
    Returns:
        Payload du token
        
    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token invalide ou expiré: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repository: UserRepository = None
) -> User:
    """
    Dependency FastAPI pour récupérer l'utilisateur courant depuis le token JWT
    
    Args:
        credentials: Credentials HTTP Bearer
        user_repository: Repository pour récupérer l'utilisateur
        
    Returns:
        User entity
        
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Token d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token invalide: user_id manquant",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Récupérer l'utilisateur depuis la base de données
    if not user_repository:
        raise HTTPException(
            status_code=500,
            detail="User repository non configuré"
        )
    
    user = user_repository.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur non trouvé",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    user_repository: UserRepository = None
) -> Optional[User]:
    """
    Dependency FastAPI pour récupérer l'utilisateur courant (optionnel)
    Ne lève pas d'exception si pas de token
    
    Returns:
        User entity ou None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, user_repository)
    except HTTPException:
        return None
