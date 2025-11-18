"""
Service de gestion des codes promotionnels
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException

from domain.entities.promo_code import PromoCode
from domain.entities.user import User
from domain.ports.promo_code_repository import PromoCodeRepository
from domain.ports.user_repository import UserRepository
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class PromoCodeService:
    """Service pour gérer les codes promotionnels"""
    
    def __init__(
        self,
        promo_code_repository: PromoCodeRepository,
        user_repository: UserRepository
    ):
        self.promo_code_repo = promo_code_repository
        self.user_repo = user_repository
    
    def generate_code(
        self,
        pdf_credits: int = 0,
        text_credits: int = 0,
        max_uses: int = 0,
        days_valid: Optional[int] = None,
        custom_code: Optional[str] = None
    ) -> PromoCode:
        """
        Génère un nouveau code promo
        
        Args:
            pdf_credits: Nombre de crédits PDF à donner
            text_credits: Nombre de crédits texte à donner
            max_uses: Nombre max d'utilisations (0 = illimité)
            days_valid: Nombre de jours de validité (None = illimité)
            custom_code: Code personnalisé (sinon généré automatiquement)
        
        Returns:
            PromoCode créé
        """
        # Générer ou valider le code
        if custom_code:
            code = custom_code.upper().strip()
            # Vérifier que le code n'existe pas déjà
            existing = self.promo_code_repo.get_by_code(code)
            if existing:
                raise ValueError(f"Le code {code} existe déjà")
        else:
            code = self._generate_random_code()
        
        # Calculer la date d'expiration
        expires_at = None
        if days_valid:
            expires_at = datetime.utcnow() + timedelta(days=days_valid)
        
        # Créer le code promo
        promo_code = PromoCode(
            code=code,
            pdf_credits=pdf_credits,
            text_credits=text_credits,
            max_uses=max_uses,
            current_uses=0,
            is_active=True,
            expires_at=expires_at
        )
        
        created = self.promo_code_repo.create(promo_code)
        logger.info(
            f"Code promo généré: {code} "
            f"(PDF: {pdf_credits}, Text: {text_credits}, Max: {max_uses})"
        )
        return created
    
    def redeem_code(self, code: str, user: User) -> tuple[int, int]:
        """
        Utilise un code promo pour un utilisateur
        
        Args:
            code: Code promo à utiliser
            user: Utilisateur qui utilise le code
        
        Returns:
            Tuple (crédits PDF ajoutés, crédits texte ajoutés)
        
        Raises:
            HTTPException: Si le code est invalide, expiré ou épuisé
        """
        # Récupérer le code
        promo_code = self.promo_code_repo.get_by_code(code.upper())
        
        if not promo_code:
            logger.warning(f"Code promo inexistant: {code}")
            raise HTTPException(status_code=404, detail="Code promo invalide")
        
        # Vérifier si le code peut être utilisé
        if not promo_code.can_be_used():
            if not promo_code.is_active:
                reason = "désactivé"
            elif promo_code.expires_at and datetime.utcnow() > promo_code.expires_at:
                reason = "expiré"
            else:
                reason = "épuisé"
            
            logger.warning(f"Code promo {code} {reason} pour {user.email}")
            raise HTTPException(
                status_code=400,
                detail=f"Ce code promo est {reason}"
            )
        
        # Ajouter les crédits à l'utilisateur
        user.pdf_credits += promo_code.pdf_credits
        user.text_credits += promo_code.text_credits
        self.user_repo.update(user)
        
        # Incrémenter l'utilisation du code
        promo_code.increment_usage()
        self.promo_code_repo.update(promo_code)
        
        logger.info(
            f"Code promo {code} utilisé par {user.email} "
            f"(+{promo_code.pdf_credits} PDF, +{promo_code.text_credits} text)"
        )
        
        return (promo_code.pdf_credits, promo_code.text_credits)
    
    def deactivate_code(self, code: str) -> None:
        """Désactive un code promo"""
        promo_code = self.promo_code_repo.get_by_code(code.upper())
        
        if not promo_code:
            raise ValueError(f"Code promo non trouvé: {code}")
        
        promo_code.is_active = False
        self.promo_code_repo.update(promo_code)
        logger.info(f"Code promo désactivé: {code}")
    
    def _generate_random_code(self, length: int = 8) -> str:
        """Génère un code aléatoire"""
        # Utiliser lettres majuscules et chiffres (éviter confusion 0/O, 1/I)
        alphabet = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Vérifier unicité
        if self.promo_code_repo.get_by_code(code):
            return self._generate_random_code(length)  # Retry
        
        return code
