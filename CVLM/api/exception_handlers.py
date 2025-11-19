"""
Handlers d'exceptions globaux pour l'API
"""
from fastapi import Request, HTTPException
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


async def business_exception_handler(request: Request, exc: Exception):
    """
    Convertit les exceptions métier en HTTPException
    
    Args:
        request: Requête HTTP
        exc: Exception levée
        
    Raises:
        HTTPException: Exception HTTP appropriée selon le type d'exception métier
    """
    from domain.exceptions import (
        InsufficientCreditsError,
        ResourceNotFoundError,
        UnauthorizedAccessError,
        FileValidationError,
        PromoCodeError
    )
    
    # Exceptions métier → HTTPException
    if isinstance(exc, InsufficientCreditsError):
        logger.warning(f"Crédits insuffisants: {exc.message}")
        raise HTTPException(status_code=403, detail=exc.message)
    
    elif isinstance(exc, ResourceNotFoundError):
        logger.warning(f"Ressource introuvable: {exc.message}")
        raise HTTPException(status_code=404, detail=exc.message)
    
    elif isinstance(exc, UnauthorizedAccessError):
        logger.warning(f"Accès non autorisé: {exc.message}")
        raise HTTPException(status_code=403, detail=exc.message)
    
    elif isinstance(exc, FileValidationError):
        logger.warning(f"Validation fichier échouée: {exc.message}")
        raise HTTPException(status_code=400, detail=exc.message)
    
    elif isinstance(exc, PromoCodeError):
        logger.warning(f"Erreur code promo: {exc.message}")
        raise HTTPException(status_code=400, detail=exc.message)
    
    # Laisser passer les autres exceptions
    raise exc
