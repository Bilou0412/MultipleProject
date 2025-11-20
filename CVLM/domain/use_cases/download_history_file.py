"""
Use Case: Télécharger un fichier PDF depuis l'historique
Workflow 4: Download History File avec validation ownership + expiration
"""

import os
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException

from domain.entities.user import User
from domain.ports.generation_history_repository import GenerationHistoryRepository
from domain.services.filename_builder import FilenameBuilder
from infrastructure.adapters.logger_config import setup_logger


logger = setup_logger(__name__)


@dataclass
class DownloadHistoryFileInput:
    """
    Input du Use Case DownloadHistoryFile.
    
    Attributes:
        history_id: ID de l'entrée historique à télécharger
    """
    history_id: str


@dataclass
class DownloadHistoryFileOutput:
    """
    Output du Use Case DownloadHistoryFile.
    
    Attributes:
        file_path: Chemin absolu du fichier PDF
        filename: Nom de fichier propre (company_job.pdf)
        media_type: Type MIME (application/pdf)
    """
    file_path: str
    filename: str
    media_type: str = "application/pdf"


class DownloadHistoryFileUseCase:
    """
    Use Case: Télécharger un fichier PDF depuis l'historique utilisateur.
    
    Responsabilités:
    - Récupérer l'entrée historique
    - Valider ownership (user_id)
    - Vérifier téléchargeable (expiration, statut)
    - Construire filename propre
    - Vérifier existence fichier physique
    - Retourner file path pour FileResponse
    
    Phases:
    1. Get history entry
    2. Validate ownership
    3. Check downloadable (expiration)
    4. Build clean filename
    5. Check file exists
    6. Return file path + filename
    
    Errors:
    - HTTPException 403: Accès refusé (ownership)
    - HTTPException 404: Entrée ou fichier introuvable
    - HTTPException 410: Fichier expiré ou indisponible
    - HTTPException 500: Erreur serveur
    """
    
    def __init__(
        self,
        history_repository: GenerationHistoryRepository,
        filename_builder: FilenameBuilder
    ):
        """
        Initialise le Use Case avec ses dépendances.
        
        Args:
            history_repository: Repository pour accès historique
            filename_builder: Service de construction filename propre
        """
        self.history_repository = history_repository
        self.filename_builder = filename_builder
    
    def execute(
        self,
        input_data: DownloadHistoryFileInput,
        user: User
    ) -> DownloadHistoryFileOutput:
        """
        Exécute le workflow de téléchargement.
        
        Args:
            input_data: Input avec history_id
            user: Utilisateur demandant le téléchargement
        
        Returns:
            DownloadHistoryFileOutput avec file_path et filename
        
        Raises:
            HTTPException: Selon le type d'erreur (403/404/410/500)
        """
        try:
            # Phase 1: Récupérer l'entrée historique
            history = self._get_history_entry(input_data.history_id)
            
            # Phase 2: Valider ownership
            self._validate_ownership(history.user_id, user.id)
            
            # Phase 3: Vérifier si téléchargeable
            self._check_downloadable(history)
            
            # Phase 4: Construire filename propre
            filename = self._build_filename(
                company_name=history.company_name,
                job_title=history.job_title
            )
            
            # Phase 5: Vérifier existence fichier physique
            file_path = self._check_file_exists(history.file_path)
            
            # Phase 6: Logger et retourner
            logger.info(
                f"Téléchargement historique réussi: "
                f"user={user.id}, history={input_data.history_id}, "
                f"filename='{filename}', company='{history.company_name}', "
                f"job='{history.job_title}'"
            )
            
            return DownloadHistoryFileOutput(
                file_path=file_path,
                filename=filename
            )
        
        except HTTPException:
            # HTTPException déjà formatée, on la propage
            raise
        except Exception as e:
            logger.error(
                f"Erreur téléchargement historique: "
                f"history_id={input_data.history_id}, error={e}"
            )
            raise HTTPException(
                status_code=500,
                detail="Erreur lors du téléchargement"
            )
    
    def _get_history_entry(self, history_id: str):
        """
        Phase 1: Récupère l'entrée historique.
        
        Args:
            history_id: ID de l'entrée
        
        Returns:
            GenerationHistory entity
        
        Raises:
            HTTPException 404: Entrée introuvable
        """
        history = self.history_repository.get_by_id(history_id)
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail="Entrée introuvable"
            )
        
        return history
    
    def _validate_ownership(self, history_user_id: str, requesting_user_id: str):
        """
        Phase 2: Valide que l'utilisateur est propriétaire de l'entrée.
        
        Args:
            history_user_id: ID du propriétaire de l'entrée
            requesting_user_id: ID de l'utilisateur demandant l'accès
        
        Raises:
            HTTPException 403: Accès refusé
        """
        if history_user_id != requesting_user_id:
            raise HTTPException(
                status_code=403,
                detail="Accès refusé"
            )
    
    def _check_downloadable(self, history):
        """
        Phase 3: Vérifie si l'entrée est téléchargeable (non expirée).
        
        Args:
            history: GenerationHistory entity
        
        Raises:
            HTTPException 410: Fichier expiré ou indisponible
        """
        if not history.is_downloadable():
            raise HTTPException(
                status_code=410,
                detail="Fichier expiré ou indisponible"
            )
    
    def _build_filename(
        self,
        company_name: Optional[str],
        job_title: Optional[str]
    ) -> str:
        """
        Phase 4: Construit un nom de fichier propre.
        
        Args:
            company_name: Nom de l'entreprise (peut être None)
            job_title: Titre du poste (peut être None)
        
        Returns:
            Nom de fichier nettoyé avec extension .pdf
            Exemple: "Google_Software_Engineer.pdf"
        """
        return self.filename_builder.build_pdf_filename(
            company_name=company_name,
            job_title=job_title
        )
    
    def _check_file_exists(self, file_path: str) -> str:
        """
        Phase 5: Vérifie que le fichier physique existe.
        
        Args:
            file_path: Chemin du fichier à vérifier
        
        Returns:
            file_path si existe
        
        Raises:
            HTTPException 404: Fichier physique introuvable
        """
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Fichier physique introuvable"
            )
        
        return file_path
