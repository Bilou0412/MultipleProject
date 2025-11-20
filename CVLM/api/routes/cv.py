"""
Routes pour la gestion des CVs
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import uuid

from api.models.cv import CvInfo, UploadResponse, CvListResponse
from api.dependencies import get_current_user
from domain.entities.user import User
from domain.entities.cv import Cv
from infrastructure.database.config import get_db
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.pypdf_parse import PyPdfParser
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.logger_config import setup_logger
from config.constants import (
    MAX_FILE_SIZE,
    ALLOWED_MIME_TYPES,
    ERROR_FILE_TOO_LARGE,
    ERROR_INVALID_FILE_TYPE,
    FILE_STORAGE_BASE_PATH
)

logger = setup_logger(__name__)

router = APIRouter(tags=["CV Management"])

# Storage
file_storage = LocalFileStorage(base_path=FILE_STORAGE_BASE_PATH)


@router.post("/upload-cv", response_model=UploadResponse)
async def upload_cv(
    cv_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload un CV au format PDF
    
    Args:
        cv_file: Fichier PDF à uploader
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        UploadResponse: Informations sur le CV uploadé
    """
    # ✅ Validation extension
    if not cv_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail=ERROR_INVALID_FILE_TYPE)
    
    try:
        cv_repo = PostgresCvRepository(db)
        document_parser = PyPdfParser()
        
        content = await cv_file.read()
        
        # ✅ Validation taille
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=ERROR_FILE_TOO_LARGE)
        
        # ✅ Validation type MIME
        if cv_file.content_type and cv_file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail=ERROR_INVALID_FILE_TYPE)
        
        cv_id = str(uuid.uuid4())
        
        # Sauvegarder le fichier
        file_path = file_storage.save_cv(cv_id, content, cv_file.filename)
        
        # Extraire le texte du PDF
        try:
            raw_text = document_parser.parse_document(input_path=file_path)
        except Exception as e:
            logger.warning(f"Erreur extraction texte: {e}")
            raw_text = ""
        
        # Créer l'entité CV
        cv = Cv(
            id=cv_id,
            user_id=current_user.id,
            file_path=file_path,
            filename=cv_file.filename,
            file_size=len(content),
            raw_text=raw_text,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Sauvegarder en base
        cv_repo.create(cv)
        
        logger.info(f"CV uploadé: {cv_id} pour {current_user.email}")
        
        return UploadResponse(
            status="success",
            cv_id=cv_id,
            filename=cv_file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")


@router.get("/list-cvs", response_model=CvListResponse)
async def list_cvs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste tous les CVs de l'utilisateur connecté
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        CvListResponse: Liste des CVs
    """
    try:
        cv_repo = PostgresCvRepository(db)
        
        # Récupérer uniquement les CVs de l'utilisateur connecté
        cvs = cv_repo.get_by_user_id(current_user.id)
        
        cv_infos = [
            CvInfo(
                cv_id=cv.id,
                filename=cv.filename,
                upload_date=cv.created_at.isoformat(),
                file_size=cv.file_size
            )
            for cv in cvs if Path(cv.file_path).exists()
        ]
        
        return CvListResponse(status="success", cvs=cv_infos)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des CVs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des CVs: {str(e)}"
        )
