"""
Routes de téléchargement et nettoyage de fichiers
Endpoints: /download-letter/{letter_id}, /user/history/{history_id}/download, /cleanup/{cv_id}
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
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
    db: Session = Depends(get_db)
):
    """
    Télécharge une lettre de motivation depuis PostgreSQL.
    
    Args:
        letter_id: ID de la lettre à télécharger
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        FileResponse avec le PDF
    
    Raises:
        HTTPException 403: Accès interdit
        HTTPException 404: Lettre ou fichier introuvable
        HTTPException 500: Erreur serveur
    """
    try:
        letter_repo = PostgresMotivationalLetterRepository(db)
        letter = letter_repo.get_by_id(letter_id)
        
        if not letter:
            raise HTTPException(status_code=404, detail="Lettre non trouvée")
        
        if letter.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès interdit à cette lettre")
        
        file_path = file_storage.get_letter_path(letter_id)
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Fichier PDF introuvable")
        
        return FileResponse(
            path=file_path,
            filename=letter.filename or f"lettre_{letter_id}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement lettre: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")


@router.get("/user/history/{history_id}/download")
async def download_history_file(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Télécharge un fichier PDF depuis l'historique.
    
    Args:
        history_id: ID de l'entrée historique
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        FileResponse avec le PDF
    
    Raises:
        HTTPException 403: Accès refusé
        HTTPException 404: Entrée ou fichier introuvable
        HTTPException 410: Fichier expiré
        HTTPException 500: Erreur serveur
    """
    try:
        history_repo = PostgresGenerationHistoryRepository(db)
        history = history_repo.get_by_id(history_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Entrée introuvable")
        
        if history.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        if not history.is_downloadable():
            raise HTTPException(status_code=410, detail="Fichier expiré ou indisponible")
        
        if not os.path.exists(history.file_path):
            raise HTTPException(status_code=404, detail="Fichier physique introuvable")
        
        # Construire un nom de fichier propre
        parts = []
        if history.company_name and history.company_name.strip():
            parts.append(history.company_name.strip())
        if history.job_title and history.job_title.strip():
            parts.append(history.job_title.strip())
        
        if parts:
            filename = '_'.join(parts)
        else:
            filename = 'lettre_motivation'
        
        # Nettoyer le nom de fichier
        filename = filename.replace(' ', '_').replace('/', '_')
        # Supprimer les underscores multiples
        while '__' in filename:
            filename = filename.replace('__', '_')
        # Supprimer les underscores au début et à la fin
        filename = filename.strip('_')
        # Ajouter l'extension
        filename = filename + '.pdf'
        
        logger.info(f"Téléchargement historique: filename='{filename}', company='{history.company_name}', job='{history.job_title}'")
        
        return FileResponse(
            path=history.file_path,
            filename=filename,
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement fichier: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du téléchargement")


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
