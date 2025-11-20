"""
Routes pour la gestion des CVs
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from api.models.cv import CvInfo, UploadResponse, CvListResponse
from api.dependencies import get_current_user, get_upload_cv_use_case
from domain.entities.user import User
from domain.use_cases.upload_cv import UploadCvUseCase, UploadCvInput
from infrastructure.database.config import get_db
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)

router = APIRouter(tags=["CV Management"])


@router.post("/upload-cv", response_model=UploadResponse)
async def upload_cv(
    cv_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    use_case: UploadCvUseCase = Depends(get_upload_cv_use_case)
):
    """
    Upload un CV au format PDF
    
    Args:
        cv_file: Fichier PDF à uploader
        current_user: Utilisateur authentifié
        use_case: Use Case d'upload de CV
        
    Returns:
        UploadResponse: Informations sur le CV uploadé
    """
    try:
        # Lire le contenu du fichier
        content = await cv_file.read()
        
        # Créer l'input du Use Case
        input_data = UploadCvInput(
            file_content=content,
            filename=cv_file.filename,
            content_type=cv_file.content_type
        )
        
        # Exécuter le Use Case
        output = use_case.execute(input_data, current_user)
        
        logger.info(f"CV uploadé avec succès: {output.cv_id} pour {current_user.email}")
        
        return UploadResponse(
            status="success",
            message="CV uploadé avec succès",
            cv_id=output.cv_id,
            filename=output.filename,
            file_size=output.file_size
        )
        
    except ValueError as e:
        # Erreur de validation (400 Bad Request)
        logger.warning(f"Validation échouée: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except RuntimeError as e:
        # Erreur serveur (500 Internal Server Error)
        logger.error(f"Erreur upload CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        # Erreur inattendue
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload du CV")


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
