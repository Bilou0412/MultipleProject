"""
Routes de téléchargement et nettoyage de fichiers
Endpoints: /download-letter/{letter_id}, /user/history/{history_id}/download, /cleanup/{cv_id}
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, get_download_history_file_use_case, get_download_letter_use_case
from domain.entities.user import User
from domain.services.cv_validation_service import CvValidationService
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.postgres_generation_history_repository import PostgresGenerationHistoryRepository
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


router = APIRouter(prefix="", tags=["download"])
file_storage = LocalFileStorage()


@router.get("/download-letter/{letter_id}")
async def download_letter(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    use_case = Depends(get_download_letter_use_case)
):
    """
    Télécharge une lettre de motivation depuis PostgreSQL.
    
    Args:
        letter_id: ID de la lettre à télécharger
        current_user: Utilisateur connecté (injecté)
        use_case: Use case de téléchargement (injecté)
    
    Returns:
        FileResponse avec le PDF
    
    Raises:
        HTTPException 403: Accès interdit
        HTTPException 404: Lettre ou fichier introuvable
        HTTPException 500: Erreur serveur
    """
    # Créer l'input du use case
    from domain.use_cases.download_letter import DownloadLetterInput
    
    input_data = DownloadLetterInput(letter_id=letter_id)
    
    # Exécuter le use case (orchestration complète)
    output = use_case.execute(input_data, current_user)
    
    # Retourner la réponse
    return FileResponse(
        path=output.file_path,
        filename=output.filename,
        media_type=output.media_type
    )


@router.get("/user/history/{history_id}/download")
async def download_history_file(
    history_id: str,
    current_user: User = Depends(get_current_user),
    use_case = Depends(get_download_history_file_use_case)
):
    """
    Télécharge un fichier PDF depuis l'historique.
    
    Args:
        history_id: ID de l'entrée historique
        current_user: Utilisateur connecté (injecté)
        use_case: Use case de téléchargement (injecté)
    
    Returns:
        FileResponse avec le PDF
    
    Raises:
        HTTPException 403: Accès refusé
        HTTPException 404: Entrée ou fichier introuvable
        HTTPException 410: Fichier expiré
        HTTPException 500: Erreur serveur
    """
    # Créer l'input du use case
    from domain.use_cases.download_history_file import DownloadHistoryFileInput
    
    input_data = DownloadHistoryFileInput(history_id=history_id)
    
    # Exécuter le use case (orchestration complète)
    output = use_case.execute(input_data, current_user)
    
    # Retourner la réponse
    return FileResponse(
        path=output.file_path,
        filename=output.filename,
        media_type=output.media_type
    )


@router.delete("/cleanup/{cv_id}")
async def cleanup_files(
    cv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un CV et ses fichiers associés.
    
    Args:
        cv_id: ID du CV à supprimer
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès
    
    Raises:
        HTTPException 403: Accès refusé
        HTTPException 404: CV introuvable
        HTTPException 500: Erreur serveur
    """
    try:
        cv_validation_service = CvValidationService(PostgresCvRepository(db))
        cv = cv_validation_service.get_and_validate_cv(cv_id, current_user)
        
        # Supprimer fichier et base de données
        file_storage.delete_cv(cv_id)
        cv_repo = PostgresCvRepository(db)
        cv_repo.delete(cv_id)
        
        logger.info(f"CV supprimé: {cv_id} par {current_user.email}")
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression: {e}")
        raise HTTPException(status_code=500, detail=str(e))
