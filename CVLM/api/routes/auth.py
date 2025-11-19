"""
Routes d'authentification
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.models.auth import AuthTokenRequest, AuthTokenResponse, UserResponse
from api.dependencies import get_current_user, get_google_oauth_service
from domain.entities.user import User
from infrastructure.adapters.database_config import get_db
from infrastructure.adapters.google_oauth_service import GoogleOAuthService
from infrastructure.adapters.auth_middleware import create_access_token
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=AuthTokenResponse)
async def auth_google(
    request: AuthTokenRequest,
    oauth_service: GoogleOAuthService = Depends(get_google_oauth_service),
    db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur via Google OAuth
    
    Args:
        request: Token Google OAuth
        oauth_service: Service d'authentification Google
        db: Session de base de données
        
    Returns:
        AuthTokenResponse: Token JWT pour l'utilisateur
    """
    try:
        # Valider le token Google et authentifier/créer l'utilisateur
        user = await oauth_service.authenticate_user(request.token)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Token Google invalide ou email non vérifié"
            )
        
        # Créer un token JWT pour notre API
        access_token = create_access_token(user.id, user.email)
        
        logger.info(f"Utilisateur authentifié: {user.email}")
        
        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.profile_picture_url,
                pdf_credits=user.pdf_credits,
                text_credits=user.text_credits,
                is_admin=user.is_admin,
                created_at=user.created_at.isoformat()
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur auth Google: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur connecté
    
    Args:
        current_user: Utilisateur authentifié
        
    Returns:
        UserResponse: Informations de l'utilisateur
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.profile_picture_url,
        pdf_credits=current_user.pdf_credits,
        text_credits=current_user.text_credits,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at.isoformat()
    )
