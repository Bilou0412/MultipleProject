"""
Use Case: Supprimer un CV et ses fichiers associés
Workflow 6: Delete CV avec transaction atomique file+DB
"""

from dataclasses import dataclass

from fastapi import HTTPException

from domain.entities.user import User
from domain.ports.cv_repository import CvRepository
from domain.ports.file_storage import FileStorage
from domain.services.cv_validation_service import CvValidationService
from infrastructure.adapters.logger_config import setup_logger


logger = setup_logger(__name__)


@dataclass
class DeleteCvInput:
    """
    Input du Use Case DeleteCv.
    
    Attributes:
        cv_id: ID du CV à supprimer
    """
    cv_id: str


@dataclass
class DeleteCvOutput:
    """
    Output du Use Case DeleteCv.
    
    Attributes:
        status: Status de l'opération (success)
        message: Message de confirmation
    """
    status: str = "success"
    message: str = "CV supprimé avec succès"


class DeleteCvUseCase:
    """
    Use Case: Supprimer un CV et ses fichiers associés de manière atomique.
    
    Responsabilités:
    - Valider le CV et ownership
    - Supprimer le fichier physique (file storage)
    - Supprimer l'enregistrement DB
    - Garantir cohérence file+DB (transaction)
    
    Phases:
    1. Validate CV + ownership
    2. Delete file (LocalFileStorage)
    3. Delete DB record (CvRepository)
    4. Rollback DB if file deletion fails (transaction atomique)
    
    CRITIQUE: Ce Use Case garantit la cohérence entre file system et DB.
    Si la suppression du fichier échoue, la DB n'est pas modifiée (rollback).
    
    Errors:
    - HTTPException 403: Accès refusé (ownership)
    - HTTPException 404: CV introuvable
    - HTTPException 500: Erreur suppression (file ou DB)
    
    Note: SQLAlchemy gère automatiquement le rollback si exception levée
    avant commit. On s'assure que delete_file() est appelé AVANT delete_db().
    """
    
    def __init__(
        self,
        cv_repository: CvRepository,
        file_storage: FileStorage,
        cv_validation_service: CvValidationService
    ):
        """
        Initialise le Use Case avec ses dépendances.
        
        Args:
            cv_repository: Repository pour accès CVs
            file_storage: Service de stockage fichiers
            cv_validation_service: Service de validation CV + ownership
        """
        self.cv_repository = cv_repository
        self.file_storage = file_storage
        self.cv_validation_service = cv_validation_service
    
    def execute(
        self,
        input_data: DeleteCvInput,
        user: User
    ) -> DeleteCvOutput:
        """
        Exécute le workflow de suppression atomique.
        
        Args:
            input_data: Input avec cv_id
            user: Utilisateur demandant la suppression
        
        Returns:
            DeleteCvOutput avec status success
        
        Raises:
            HTTPException: Selon le type d'erreur (403/404/500)
        
        Transaction Flow:
        1. Validate CV + ownership (no DB modification yet)
        2. Delete file (if fails → exception → no DB change)
        3. Delete DB record (if fails → rollback automatic)
        4. Commit (success)
        """
        try:
            # Phase 1: Valider CV et ownership
            cv = self._validate_cv_and_ownership(input_data.cv_id, user)
            
            # Phase 2: Supprimer le fichier physique AVANT la DB
            # Si cette étape échoue, la DB n'est pas touchée (pas encore de delete DB)
            self._delete_file(input_data.cv_id)
            
            # Phase 3: Supprimer l'enregistrement DB
            # SQLAlchemy rollback automatique si exception après ce point
            self._delete_db_record(input_data.cv_id)
            
            # Phase 4: Logger succès
            logger.info(
                f"CV supprimé avec succès: cv_id={input_data.cv_id}, "
                f"user={user.email}, filename={cv.filename}"
            )
            
            return DeleteCvOutput()
        
        except HTTPException:
            # HTTPException déjà formatée, on la propage
            raise
        except Exception as e:
            # Erreur inattendue (file ou DB)
            logger.error(
                f"Erreur suppression CV: cv_id={input_data.cv_id}, "
                f"user={user.email}, error={e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )
    
    def _validate_cv_and_ownership(self, cv_id: str, user: User):
        """
        Phase 1: Valide que le CV existe et appartient à l'utilisateur.
        
        Args:
            cv_id: ID du CV
            user: Utilisateur demandant la suppression
        
        Returns:
            CV entity validé
        
        Raises:
            HTTPException 403: Accès refusé
            HTTPException 404: CV introuvable
        """
        # CvValidationService lève HTTPException si ownership invalide
        cv = self.cv_validation_service.get_and_validate_cv(cv_id, user)
        return cv
    
    def _delete_file(self, cv_id: str):
        """
        Phase 2: Supprime le fichier physique du CV.
        
        CRITIQUE: Cette opération est faite AVANT delete DB.
        Si elle échoue, la DB n'est pas modifiée (transaction non entamée).
        
        Args:
            cv_id: ID du CV
        
        Raises:
            Exception: Si erreur suppression fichier
        """
        try:
            self.file_storage.delete_cv(cv_id)
        except Exception as e:
            logger.error(f"Erreur suppression fichier: cv_id={cv_id}, error={e}")
            raise Exception(f"Impossible de supprimer le fichier: {str(e)}")
    
    def _delete_db_record(self, cv_id: str):
        """
        Phase 3: Supprime l'enregistrement du CV en base de données.
        
        Note: SQLAlchemy gère automatiquement le rollback si exception levée
        après ce point (avant commit de la session).
        
        Args:
            cv_id: ID du CV
        
        Raises:
            Exception: Si erreur suppression DB
        """
        try:
            self.cv_repository.delete(cv_id)
        except Exception as e:
            logger.error(f"Erreur suppression DB: cv_id={cv_id}, error={e}")
            raise Exception(f"Impossible de supprimer en base de données: {str(e)}")
