"""
Use Case: Upload et parsing d'un CV

Ce use case orchestre le workflow complet d'upload d'un CV:
- Validation du fichier (taille, type, contenu)
- Parsing et extraction du texte
- Sauvegarde en storage et base de données
- Gestion transactionnelle avec cleanup

Architecture: Hexagonal (Use Case Pattern)
Author: System
Date: 2025-11-20
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from domain.entities.user import User
from domain.entities.cv import Cv
from domain.ports.cv_repository import CvRepository
from domain.ports.document_parser import DocumentParser
from domain.ports.file_storage import FileStorage
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


# ==================== INPUT/OUTPUT DATA CLASSES ====================

@dataclass
class UploadCvInput:
    """Données d'entrée pour l'upload de CV."""
    file_content: bytes
    filename: str
    content_type: Optional[str] = None


@dataclass
class UploadCvOutput:
    """Résultat de l'upload de CV."""
    cv_id: str
    filename: str
    file_size: int
    file_path: str
    text_extracted: bool
    text_length: int


# ==================== USE CASE ====================

class UploadCvUseCase:
    """
    Use Case: Upload et traitement d'un CV.
    
    Responsabilités:
    - Validation du fichier (taille, type, intégrité)
    - Extraction du texte via parser
    - Sauvegarde du fichier en storage
    - Sauvegarde des métadonnées en DB
    - Cleanup en cas d'erreur (suppression fichier)
    
    Gestion transactionnelle:
    - Sauvegarde fichier AVANT DB
    - Suppression fichier si échec DB
    - Rollback complet en cas d'erreur
    
    Pattern: Use Case orchestrant plusieurs services domain
    """
    
    def __init__(
        self,
        cv_repository: CvRepository,
        document_parser: DocumentParser,
        file_storage: FileStorage,
        max_file_size: int,
        allowed_extensions: list[str]
    ):
        """
        Initialise le use case avec ses dépendances injectées.
        
        Args:
            cv_repository: Repository pour la persistance des CVs
            document_parser: Parser pour extraire le texte des PDFs
            file_storage: Service de stockage des fichiers
            max_file_size: Taille maximale autorisée en bytes
            allowed_extensions: Liste des extensions autorisées (ex: ['.pdf'])
        """
        self._cv_repo = cv_repository
        self._parser = document_parser
        self._storage = file_storage
        self._max_file_size = max_file_size
        self._allowed_extensions = allowed_extensions
        
        logger.info("[Use Case] UploadCvUseCase initialisé")
    
    def execute(
        self,
        input_data: UploadCvInput,
        current_user: User
    ) -> UploadCvOutput:
        """
        Exécute le workflow complet d'upload de CV.
        
        Workflow:
        1. Validation du fichier (taille, type, extension)
        2. Parsing et extraction du texte
        3. Sauvegarde du fichier en storage
        4. Sauvegarde des métadonnées en DB
        5. Cleanup si erreur
        
        Args:
            input_data: Données du fichier à uploader
            current_user: Utilisateur courant authentifié
        
        Returns:
            UploadCvOutput avec les informations du CV uploadé
        
        Raises:
            ValueError: Si validation du fichier échoue
            RuntimeError: Si erreur de parsing, storage ou DB
        """
        logger.info(f"[Use Case] Début upload CV pour utilisateur {current_user.email}")
        logger.info(f"[Use Case] Fichier: {input_data.filename}, taille: {len(input_data.file_content)} bytes")
        
        cv_id = None
        file_path = None
        
        try:
            # ==================== PHASE 1: VALIDATION ====================
            self._validate_file(input_data)
            logger.info(f"[Use Case] ✓ Validation fichier OK")
            
            # ==================== PHASE 2: PARSING ====================
            raw_text = self._extract_text(input_data)
            logger.info(f"[Use Case] ✓ Texte extrait - {len(raw_text)} caractères")
            
            # ==================== PHASE 3: SAUVEGARDE STORAGE ====================
            cv_id = str(uuid.uuid4())
            file_path = self._save_to_storage(cv_id, input_data)
            logger.info(f"[Use Case] ✓ Fichier sauvegardé: {file_path}")
            
            # ==================== PHASE 4: SAUVEGARDE DB ====================
            cv_entity = self._create_cv_entity(
                cv_id=cv_id,
                user=current_user,
                input_data=input_data,
                file_path=file_path,
                raw_text=raw_text
            )
            
            saved_cv = self._cv_repo.create(cv_entity)
            logger.info(f"[Use Case] ✓ CV sauvegardé en DB: {saved_cv.id}")
            
            # ==================== SUCCÈS ====================
            logger.info(f"[Use Case] ✅ Upload CV réussi: {cv_id} pour {current_user.email}")
            
            return UploadCvOutput(
                cv_id=saved_cv.id,
                filename=saved_cv.filename,
                file_size=saved_cv.file_size,
                file_path=file_path,
                text_extracted=bool(raw_text and raw_text.strip()),
                text_length=len(raw_text) if raw_text else 0
            )
            
        except ValueError as e:
            # Erreur de validation (attendue)
            logger.error(f"[Use Case] ❌ Erreur validation: {e}")
            raise
            
        except Exception as e:
            # Erreur inattendue: cleanup nécessaire
            logger.error(f"[Use Case] ❌ Erreur upload CV: {e}", exc_info=True)
            
            # Cleanup: supprimer le fichier si créé
            if file_path and Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                    logger.debug(f"[Use Case] Fichier nettoyé: {file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"[Use Case] Erreur nettoyage: {cleanup_error}")
            
            raise RuntimeError(f"Erreur lors de l'upload du CV: {str(e)}")
    
    # ==================== MÉTHODES PRIVÉES ====================
    
    def _validate_file(self, input_data: UploadCvInput) -> None:
        """
        Valide le fichier uploadé.
        
        Args:
            input_data: Données du fichier
        
        Raises:
            ValueError: Si validation échoue
        """
        # Vérifier la taille
        if len(input_data.file_content) > self._max_file_size:
            raise ValueError(
                f"Fichier trop volumineux. Maximum autorisé: "
                f"{self._max_file_size / (1024 * 1024):.1f} MB"
            )
        
        # Vérifier l'extension
        file_ext = Path(input_data.filename).suffix.lower()
        if file_ext not in self._allowed_extensions:
            raise ValueError(
                f"Type de fichier non autorisé. Extensions autorisées: "
                f"{', '.join(self._allowed_extensions)}"
            )
        
        # Vérifier que le fichier n'est pas vide
        if len(input_data.file_content) == 0:
            raise ValueError("Le fichier est vide")
    
    def _extract_text(self, input_data: UploadCvInput) -> str:
        """
        Extrait le texte du CV (best effort).
        
        Args:
            input_data: Données du fichier
        
        Returns:
            Texte extrait (chaîne vide si échec)
        """
        try:
            # Sauvegarder temporairement pour le parser
            temp_path = Path("/tmp") / f"temp_{uuid.uuid4()}.pdf"
            temp_path.write_bytes(input_data.file_content)
            
            try:
                raw_text = self._parser.parse_document(input_path=str(temp_path))
                return raw_text if raw_text else ""
            finally:
                # Nettoyer le fichier temporaire
                if temp_path.exists():
                    temp_path.unlink()
                    
        except Exception as e:
            logger.warning(f"[Use Case] ⚠️  Erreur extraction texte (non bloquant): {e}")
            return ""  # Best effort: continuer même si extraction échoue
    
    def _save_to_storage(self, cv_id: str, input_data: UploadCvInput) -> str:
        """
        Sauvegarde le fichier en storage.
        
        Args:
            cv_id: ID unique du CV
            input_data: Données du fichier
        
        Returns:
            Chemin relatif du fichier sauvegardé
        
        Raises:
            RuntimeError: Si erreur de sauvegarde
        """
        try:
            file_path = self._storage.save_cv(
                cv_id=cv_id,
                content=input_data.file_content,
                filename=input_data.filename
            )
            return file_path
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
    
    def _create_cv_entity(
        self,
        cv_id: str,
        user: User,
        input_data: UploadCvInput,
        file_path: str,
        raw_text: str
    ) -> Cv:
        """
        Crée l'entité CV.
        
        Args:
            cv_id: ID unique du CV
            user: Utilisateur propriétaire
            input_data: Données du fichier
            file_path: Chemin du fichier sauvegardé
            raw_text: Texte extrait
        
        Returns:
            Entité Cv
        """
        return Cv(
            id=cv_id,
            user_id=user.id,
            file_path=file_path,
            filename=input_data.filename,
            file_size=len(input_data.file_content),
            raw_text=raw_text,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
