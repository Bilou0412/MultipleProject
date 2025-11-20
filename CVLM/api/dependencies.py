"""
Dépendances FastAPI réutilisables
"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
import uuid

from domain.entities.user import User
from infrastructure.database.config import get_db
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.postgres_promo_code_repository import PostgresPromoCodeRepository
from infrastructure.adapters.postgres_generation_history_repository import PostgresGenerationHistoryRepository
from infrastructure.adapters.auth_middleware import verify_access_token
from infrastructure.adapters.google_oauth_service import GoogleOAuthService
from infrastructure.adapters.logger_config import setup_logger

# Services
from domain.services.cv_validation_service import CvValidationService
from domain.services.credit_service import CreditService
from domain.services.letter_generation_service import LetterGenerationService
from domain.services.admin_service import AdminService
from domain.services.promo_code_service import PromoCodeService
from domain.services.generation_history_service import GenerationHistoryService
from domain.services.use_case_validator import UseCaseValidator
from domain.services.job_info_extractor import JobInfoExtractor
from domain.services.filename_builder import FilenameBuilder

# Use Cases
from domain.use_cases.generate_cover_letter import GenerateCoverLetterUseCase
from domain.use_cases.generate_text import GenerateTextUseCase
from domain.use_cases.upload_cv import UploadCvUseCase
from domain.use_cases.download_history_file import DownloadHistoryFileUseCase

logger = setup_logger(__name__)


# === Repository Factories ===

def get_user_repository(db: Session = Depends(get_db)) -> PostgresUserRepository:
    """Factory pour UserRepository"""
    return PostgresUserRepository(db)


def get_cv_repository(db: Session = Depends(get_db)) -> PostgresCvRepository:
    """Factory pour CvRepository"""
    return PostgresCvRepository(db)


def get_letter_repository(db: Session = Depends(get_db)) -> PostgresMotivationalLetterRepository:
    """Factory pour MotivationalLetterRepository"""
    return PostgresMotivationalLetterRepository(db)


def get_promo_code_repository(db: Session = Depends(get_db)) -> PostgresPromoCodeRepository:
    """Factory pour PromoCodeRepository"""
    return PostgresPromoCodeRepository(db)


def get_history_repository(db: Session = Depends(get_db)) -> PostgresGenerationHistoryRepository:
    """Factory pour GenerationHistoryRepository"""
    return PostgresGenerationHistoryRepository(db)


# === Service Factories ===

def get_cv_validation_service(
    cv_repo: PostgresCvRepository = Depends(get_cv_repository)
) -> CvValidationService:
    """Factory pour CvValidationService"""
    return CvValidationService(cv_repo)


def get_credit_service(
    user_repo: PostgresUserRepository = Depends(get_user_repository)
) -> CreditService:
    """Factory pour CreditService"""
    return CreditService(user_repo)


def get_letter_generation_service() -> LetterGenerationService:
    """Factory pour LetterGenerationService"""
    return LetterGenerationService()


def get_admin_service(
    user_repo: PostgresUserRepository = Depends(get_user_repository),
    promo_repo: PostgresPromoCodeRepository = Depends(get_promo_code_repository)
) -> AdminService:
    """Factory pour AdminService"""
    return AdminService(user_repo, promo_repo)


def get_promo_code_service(
    promo_repo: PostgresPromoCodeRepository = Depends(get_promo_code_repository),
    user_repo: PostgresUserRepository = Depends(get_user_repository)
) -> PromoCodeService:
    """Factory pour PromoCodeService"""
    return PromoCodeService(promo_repo, user_repo)


def get_history_service(
    history_repo: PostgresGenerationHistoryRepository = Depends(get_history_repository)
) -> GenerationHistoryService:
    """Factory pour GenerationHistoryService"""
    return GenerationHistoryService(history_repo)


def get_job_info_extractor() -> JobInfoExtractor:
    """Factory pour JobInfoExtractor (stateless service)"""
    return JobInfoExtractor()


def get_filename_builder() -> FilenameBuilder:
    """Factory pour FilenameBuilder (stateless service)"""
    return FilenameBuilder()


def get_use_case_validator(
    cv_validation: CvValidationService = Depends(get_cv_validation_service),
    credit_service: CreditService = Depends(get_credit_service)
) -> UseCaseValidator:
    """Factory pour UseCaseValidator (helper service)"""
    return UseCaseValidator(cv_validation, credit_service)


# === Use Case Factories ===

def get_generate_cover_letter_use_case(
    use_case_validator: UseCaseValidator = Depends(get_use_case_validator),
    job_info_extractor: JobInfoExtractor = Depends(get_job_info_extractor),
    credit_service: CreditService = Depends(get_credit_service),
    letter_generation_service: LetterGenerationService = Depends(get_letter_generation_service),
    history_service: GenerationHistoryService = Depends(get_history_service),
    letter_repository: PostgresMotivationalLetterRepository = Depends(get_letter_repository),
    user_repository: PostgresUserRepository = Depends(get_user_repository)
) -> GenerateCoverLetterUseCase:
    """Factory pour GenerateCoverLetterUseCase"""
    return GenerateCoverLetterUseCase(
        use_case_validator=use_case_validator,
        job_info_extractor=job_info_extractor,
        credit_service=credit_service,
        letter_generation_service=letter_generation_service,
        history_service=history_service,
        letter_repository=letter_repository,
        user_repository=user_repository
    )


def get_generate_text_use_case(
    use_case_validator: UseCaseValidator = Depends(get_use_case_validator),
    job_info_extractor: JobInfoExtractor = Depends(get_job_info_extractor),
    credit_service: CreditService = Depends(get_credit_service),
    history_service: GenerationHistoryService = Depends(get_history_service)
) -> GenerateTextUseCase:
    """Factory pour GenerateTextUseCase"""
    from infrastructure.adapters.pypdf_parse import PyPdfParser
    from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
    from infrastructure.adapters.google_gemini_api import GoogleGeminiLlm
    from infrastructure.adapters.open_ai_api import OpenAiLlm
    from config.constants import LLM_PROVIDER_GEMINI
    
    # Factory function pour créer le LLM service selon le provider
    def llm_service_factory(provider: str):
        """Crée le service LLM approprié selon le provider"""
        if provider.lower() == LLM_PROVIDER_GEMINI:
            return GoogleGeminiLlm()
        return OpenAiLlm()
    
    return GenerateTextUseCase(
        use_case_validator=use_case_validator,
        job_info_extractor=job_info_extractor,
        credit_service=credit_service,
        history_service=history_service,
        document_parser=PyPdfParser(),
        job_offer_fetcher=WelcomeToTheJungleFetcher(),
        llm_service_factory=llm_service_factory
    )


def get_upload_cv_use_case(
    cv_repository: PostgresCvRepository = Depends(get_cv_repository)
) -> UploadCvUseCase:
    """Factory pour UploadCvUseCase"""
    from infrastructure.adapters.pypdf_parse import PyPdfParser
    from infrastructure.adapters.local_file_storage import LocalFileStorage
    from config.constants import MAX_FILE_SIZE, FILE_STORAGE_BASE_PATH
    
    return UploadCvUseCase(
        cv_repository=cv_repository,
        document_parser=PyPdfParser(),
        file_storage=LocalFileStorage(base_path=FILE_STORAGE_BASE_PATH),
        max_file_size=MAX_FILE_SIZE,
        allowed_extensions=['.pdf']
    )


def get_download_history_file_use_case(
    history_repository: PostgresGenerationHistoryRepository = Depends(get_history_repository),
    filename_builder: FilenameBuilder = Depends(get_filename_builder)
) -> DownloadHistoryFileUseCase:
    """Factory pour DownloadHistoryFileUseCase"""
    return DownloadHistoryFileUseCase(
        history_repository=history_repository,
        filename_builder=filename_builder
    )


def get_google_oauth_service(
    user_repo: PostgresUserRepository = Depends(get_user_repository)
) -> GoogleOAuthService:
    """Factory pour GoogleOAuthService"""
    return GoogleOAuthService(user_repo)


# === User Management ===

def get_or_create_default_user(db: Session) -> User:
    """Crée ou récupère l'utilisateur par défaut (transition)"""
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_email("default@cvlm.com")
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="default@cvlm.com",
            google_id="default-google-id",
            name="Utilisateur par défaut",
            pdf_credits=10,
            text_credits=10
        )
        user_repo.create(user)
    return user


def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur authentifié depuis le token JWT
    
    Args:
        authorization: Header Authorization avec Bearer token
        db: Session de base de données
        
    Returns:
        User: Utilisateur authentifié
        
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur introuvable
    """
    try:
        # Extraire le token du header "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        
        # Vérifier et décoder le token
        payload = verify_access_token(token)
        user_id = payload.get("sub")  # "sub" = subject dans JWT standard
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Récupérer l'utilisateur
        user_repo = PostgresUserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur authentification: {e}")
        raise HTTPException(status_code=401, detail="Authentification échouée")


def verify_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur a les droits administrateur
    
    Args:
        current_user: Utilisateur authentifié
        
    Returns:
        User: Utilisateur admin
        
    Raises:
        HTTPException: Si l'utilisateur n'est pas admin
    """
    if not current_user.is_admin:
        logger.warning(f"Tentative accès admin par utilisateur non-admin: {current_user.email}")
        raise HTTPException(
            status_code=403,
            detail="Accès réservé aux administrateurs"
        )
    return current_user
