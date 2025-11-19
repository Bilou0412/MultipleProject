"""
Service de gestion des crédits utilisateur
"""
from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from domain.exceptions import InsufficientCreditsError
from infrastructure.adapters.logger_config import setup_logger
from config.constants import ERROR_NO_PDF_CREDITS, ERROR_NO_TEXT_CREDITS

logger = setup_logger(__name__)


class CreditService:
    """Service pour gérer les crédits utilisateur"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def check_and_use_pdf_credit(self, user: User) -> None:
        """
        Vérifie et utilise un crédit PDF
        
        Raises:
            InsufficientCreditsError: Si l'utilisateur n'a plus de crédits
        """
        if not user.has_pdf_credits():
            logger.warning(f"Utilisateur {user.email} sans crédits PDF")
            raise InsufficientCreditsError("PDF", ERROR_NO_PDF_CREDITS)
        
        user.use_pdf_credit()
        self.user_repository.update(user)
        logger.info(f"Crédit PDF utilisé pour {user.email}. Restants: {user.pdf_credits}")
    
    def check_and_use_text_credit(self, user: User) -> None:
        """
        Vérifie et utilise un crédit texte
        
        Raises:
            InsufficientCreditsError: Si l'utilisateur n'a plus de crédits
        """
        if not user.has_text_credits():
            logger.warning(f"Utilisateur {user.email} sans crédits texte")
            raise InsufficientCreditsError("text", ERROR_NO_TEXT_CREDITS)
        
        user.use_text_credit()
        self.user_repository.update(user)
        logger.info(f"Crédit texte utilisé pour {user.email}. Restants: {user.text_credits}")

