"""
Routes utilisateur
"""
from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from domain.entities.user import User
from config.constants import DEFAULT_PDF_CREDITS, DEFAULT_TEXT_CREDITS

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/credits")
async def get_user_credits(current_user: User = Depends(get_current_user)):
    """
    Retourne les crédits restants de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        
    Returns:
        dict: Crédits PDF et texte disponibles
    """
    return {
        "pdf_credits": current_user.pdf_credits,
        "text_credits": current_user.text_credits,
        "total_pdf_credits": DEFAULT_PDF_CREDITS,
        "total_text_credits": DEFAULT_TEXT_CREDITS
    }
