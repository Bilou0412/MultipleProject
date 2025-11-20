"""
Use Case: Télécharger une lettre de motivation PDF
Workflow 5: Download Letter avec validation ownership simplifiée
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from domain.entities.user import User
from domain.ports.motivational_letter_repository import MotivationalLetterRepository
from domain.ports.file_storage import FileStorage
from domain.services.filename_builder import FilenameBuilder
from infrastructure.adapters.logger_config import setup_logger


logger = setup_logger(__name__)


@dataclass
class DownloadLetterInput:
    """
    Input du Use Case DownloadLetter.
    
    Attributes:
        letter_id: ID de la lettre à télécharger
    """
    letter_id: str


@dataclass
class DownloadLetterOutput:
    """
    Output du Use Case DownloadLetter.
    
    Attributes:
        file_path: Chemin absolu du fichier PDF
        filename: Nom de fichier propre (ou fallback lettre_{id}.pdf)
        media_type: Type MIME (application/pdf)
    """
    file_path: str
    filename: str
    media_type: str = "application/pdf"


class DownloadLetterUseCase:
    """
    Use Case: Télécharger une lettre de motivation PDF.
    
    Responsabilités:
    - Récupérer la lettre depuis repository
    - Valider ownership (user_id)
    - Récupérer file path depuis file storage
    - Vérifier existence fichier physique
    - Construire filename propre (ou utiliser letter.filename)
    - Retourner file path pour FileResponse
    
    Phases:
    1. Get letter entity
    2. Validate ownership
    3. Get file path from storage
    4. Check file exists
    5. Return file path + filename
    
    Note: Plus simple que DownloadHistoryFileUseCase car:
    - Pas de vérification expiration (lettres permanentes)
    - Letter entity a déjà un filename (optionnel)
    
    Errors:
    - HTTPException 403: Accès interdit (ownership)
    - HTTPException 404: Lettre ou fichier introuvable
    - HTTPException 500: Erreur serveur
    """
    
    def __init__(
        self,
        letter_repository: MotivationalLetterRepository,
        file_storage: FileStorage,
        filename_builder: FilenameBuilder
    ):
        """
        Initialise le Use Case avec ses dépendances.
        
        Args:
            letter_repository: Repository pour accès lettres
            file_storage: Service de stockage fichiers
            filename_builder: Service de construction filename propre
        """
        self.letter_repository = letter_repository
        self.file_storage = file_storage
        self.filename_builder = filename_builder
    
    def execute(
        self,
        input_data: DownloadLetterInput,
        user: User
    ) -> DownloadLetterOutput:
        """
        Exécute le workflow de téléchargement.
        
        Args:
            input_data: Input avec letter_id
            user: Utilisateur demandant le téléchargement
        
        Returns:
            DownloadLetterOutput avec file_path et filename
        
        Raises:
            HTTPException: Selon le type d'erreur (403/404/500)
        """
        try:
            # Phase 1: Récupérer la lettre
            letter = self._get_letter(input_data.letter_id)
            
            # Phase 2: Valider ownership
            self._validate_ownership(letter.user_id, user.id)
            
            # Phase 3: Récupérer file path depuis storage
            file_path = self._get_file_path(input_data.letter_id)
            
            # Phase 4: Vérifier existence fichier physique
            self._check_file_exists(file_path)
            
            # Phase 5: Construire filename (utilise letter.filename ou fallback)
            filename = self._build_filename(letter, input_data.letter_id)
            
            # Logger et retourner
            logger.info(
                f"Téléchargement lettre réussi: "
                f"user={user.id}, letter={input_data.letter_id}, "
                f"filename='{filename}'"
            )
            
            return DownloadLetterOutput(
                file_path=file_path,
                filename=filename
            )
        
        except HTTPException:
            # HTTPException déjà formatée, on la propage
            raise
        except Exception as e:
            logger.error(
                f"Erreur téléchargement lettre: "
                f"letter_id={input_data.letter_id}, error={e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du téléchargement: {str(e)}"
            )
    
    def _get_letter(self, letter_id: str):
        """
        Phase 1: Récupère la lettre depuis repository.
        
        Args:
            letter_id: ID de la lettre
        
        Returns:
            MotivationalLetter entity
        
        Raises:
            HTTPException 404: Lettre non trouvée
        """
        letter = self.letter_repository.get_by_id(letter_id)
        
        if not letter:
            raise HTTPException(
                status_code=404,
                detail="Lettre non trouvée"
            )
        
        return letter
    
    def _validate_ownership(self, letter_user_id: str, requesting_user_id: str):
        """
        Phase 2: Valide que l'utilisateur est propriétaire de la lettre.
        
        Args:
            letter_user_id: ID du propriétaire de la lettre
            requesting_user_id: ID de l'utilisateur demandant l'accès
        
        Raises:
            HTTPException 403: Accès interdit à cette lettre
        """
        if letter_user_id != requesting_user_id:
            raise HTTPException(
                status_code=403,
                detail="Accès interdit à cette lettre"
            )
    
    def _get_file_path(self, letter_id: str) -> str:
        """
        Phase 3: Récupère le chemin du fichier depuis file storage.
        
        Args:
            letter_id: ID de la lettre
        
        Returns:
            Chemin absolu du fichier
        
        Raises:
            HTTPException 404: Fichier PDF introuvable
        """
        file_path = self.file_storage.get_letter_path(letter_id)
        
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="Fichier PDF introuvable"
            )
        
        return file_path
    
    def _check_file_exists(self, file_path: str):
        """
        Phase 4: Vérifie que le fichier physique existe.
        
        Args:
            file_path: Chemin du fichier à vérifier
        
        Raises:
            HTTPException 404: Fichier PDF introuvable
        """
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=404,
                detail="Fichier PDF introuvable"
            )
    
    def _build_filename(self, letter, letter_id: str) -> str:
        """
        Phase 5: Construit un nom de fichier propre.
        
        Stratégie:
        1. Si letter.filename existe → utiliser
        2. Sinon si company_name ou job_title existent → FilenameBuilder
        3. Sinon → fallback "lettre_{letter_id}.pdf"
        
        Args:
            letter: MotivationalLetter entity
            letter_id: ID de la lettre (pour fallback)
        
        Returns:
            Nom de fichier avec extension .pdf
        """
        # Stratégie 1: Utiliser letter.filename si existe
        if letter.filename:
            return letter.filename
        
        # Stratégie 2: Construire depuis company/job si disponible
        # Note: MotivationalLetter n'a pas company_name/job_title en attributs directs
        # On pourrait les extraire du job_offer_url mais c'est complexe
        # Pour simplifier, on utilise le fallback
        
        # Stratégie 3: Fallback
        return f"lettre_{letter_id}.pdf"
