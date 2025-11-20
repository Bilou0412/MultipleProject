"""
Service: Validation commune aux Use Cases

Ce service centralise la logique de validation partagée entre plusieurs Use Cases:
- Validation du CV (existence, appartenance à l'utilisateur)
- Vérification des crédits (SANS les décompter)

Utilisé par:
- GenerateCoverLetterUseCase
- GenerateTextUseCase
- Futurs Use Cases...

Réduit la duplication de code entre les Use Cases.
"""
from domain.entities.cv import Cv
from domain.entities.user import User
from domain.services.cv_validation_service import CvValidationService
from domain.services.credit_service import CreditService
from domain.exceptions import InsufficientCreditsError
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class UseCaseValidator:
    """
    Service helper pour validation commune aux Use Cases.
    
    Responsabilités:
    - Valider le CV (get_and_validate_cv)
    - Vérifier les crédits disponibles (has_credits)
    - Centraliser la logique de validation répétitive
    
    Pattern: Service Layer Helper
    """
    
    def __init__(
        self,
        cv_validation_service: CvValidationService,
        credit_service: CreditService
    ):
        """
        Initialise le validator avec ses dépendances.
        
        Args:
            cv_validation_service: Service de validation des CVs
            credit_service: Service de gestion des crédits
        """
        self._cv_validation = cv_validation_service
        self._credit_service = credit_service
        
        logger.debug("[UseCaseValidator] Service initialisé")
    
    def validate_cv_and_credits(
        self,
        cv_id: str,
        user: User,
        credit_type: str
    ) -> Cv:
        """
        Valide le CV et vérifie les crédits disponibles.
        
        Cette méthode combine 2 validations fréquemment utilisées ensemble:
        1. Vérifier que le CV existe et appartient à l'utilisateur
        2. Vérifier que l'utilisateur a des crédits disponibles
        
        ⚠️ IMPORTANT: Cette méthode NE décompte PAS les crédits.
        Elle vérifie seulement leur disponibilité.
        
        Args:
            cv_id: ID du CV à valider
            user: Utilisateur courant authentifié
            credit_type: Type de crédit à vérifier ('pdf' ou 'text')
        
        Returns:
            CV entité validée
        
        Raises:
            ResourceNotFoundError: Si CV introuvable ou accès refusé
            InsufficientCreditsError: Si crédits insuffisants
        
        Example:
            >>> validator = UseCaseValidator(cv_service, credit_service)
            >>> cv = validator.validate_cv_and_credits(
            ...     cv_id="123",
            ...     user=current_user,
            ...     credit_type="pdf"
            ... )
            >>> # CV validé, crédits suffisants
        """
        logger.debug(
            f"[UseCaseValidator] Validation: cv_id={cv_id}, "
            f"user={user.email}, credit_type={credit_type}"
        )
        
        # 1. Valider le CV (existence, appartenance)
        cv = self._cv_validation.get_and_validate_cv(cv_id, user)
        logger.debug(f"[UseCaseValidator] ✓ CV validé: {cv.filename}")
        
        # 2. Vérifier les crédits disponibles (SANS décompter)
        if not self._credit_service.has_credits(user, credit_type):
            credits_count = getattr(user, f"{credit_type}_credits", 0)
            
            logger.warning(
                f"[UseCaseValidator] ✗ Crédits insuffisants: "
                f"type={credit_type}, disponibles={credits_count}"
            )
            
            raise InsufficientCreditsError(
                f"Crédits {credit_type.upper()} insuffisants. "
                f"Crédits disponibles: {credits_count}"
            )
        
        logger.debug(
            f"[UseCaseValidator] ✓ Crédits suffisants: "
            f"{getattr(user, f'{credit_type}_credits', 0)} {credit_type} restants"
        )
        
        return cv
