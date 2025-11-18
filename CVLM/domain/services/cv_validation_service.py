"""
Service de validation et récupération de CV
"""
from pathlib import Path
from fastapi import HTTPException

from domain.entities.cv import Cv
from domain.entities.user import User
from domain.ports.cv_repository import CvRepository
from infrastructure.adapters.logger_config import setup_logger
from config.constants import ERROR_CV_NOT_FOUND, ERROR_CV_FILE_NOT_FOUND, ERROR_CV_ACCESS_DENIED

logger = setup_logger(__name__)


class CvValidationService:
    """Service pour valider et récupérer les CVs"""
    
    def __init__(self, cv_repository: CvRepository):
        self.cv_repository = cv_repository
    
    def get_and_validate_cv(self, cv_id: str, user: User) -> Cv:
        """
        Récupère et valide un CV
        
        Args:
            cv_id: ID du CV
            user: Utilisateur courant
        
        Returns:
            CV validé
        
        Raises:
            HTTPException: Si le CV n'existe pas, n'appartient pas à l'utilisateur,
                          ou si le fichier n'existe pas sur le disque
        """
        cv = self.cv_repository.get_by_id(cv_id)
        
        if not cv:
            logger.warning(f"CV non trouvé: {cv_id}")
            raise HTTPException(status_code=404, detail=ERROR_CV_NOT_FOUND)
        
        if cv.user_id != user.id:
            logger.warning(f"Tentative d'accès non autorisé au CV {cv_id} par {user.email}")
            raise HTTPException(status_code=403, detail=ERROR_CV_ACCESS_DENIED)
        
        cv_path = Path(cv.file_path)
        if not cv_path.exists():
            logger.error(f"Fichier CV introuvable: {cv_path}")
            raise HTTPException(status_code=404, detail=ERROR_CV_FILE_NOT_FOUND)
        
        logger.debug(f"CV validé: {cv_id} pour {user.email}")
        return cv
