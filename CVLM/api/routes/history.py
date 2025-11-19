"""
Routes de gestion de l'historique utilisateur
Endpoints: /user/history, /user/history/stats, /user/history/{id}/download, etc.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.models.history import HistoryListResponse, HistoryStatsResponse, HistoryTextResponse, HistoryEntryResponse
from domain.entities.user import User
from infrastructure.adapters.postgres_generation_history_repository import PostgresGenerationHistoryRepository
from domain.services.generation_history_service import GenerationHistoryService
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


router = APIRouter(prefix="/user/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
async def get_user_history(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    period: Optional[str] = None,  # '7', '30', '90', 'all'
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des générations de l'utilisateur avec pagination.
    
    Args:
        page: Numéro de page (défaut 1)
        per_page: Éléments par page (défaut 50)
        search: Recherche textuelle dans job_title/company_name
        type_filter: Filtre par type (pdf ou text)
        period: Période en jours (7, 30, 90, all)
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        HistoryListResponse avec items paginés et metadata
    
    Raises:
        HTTPException 500: Erreur serveur
    """
    try:
        history_repo = PostgresGenerationHistoryRepository(db)
        history_service = GenerationHistoryService(history_repo)
        
        # Convertir période en jours
        period_days = None
        if period and period != 'all':
            try:
                period_days = int(period)
            except ValueError:
                pass
        
        result = history_service.get_user_history(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            search=search,
            type_filter=type_filter,
            period_days=period_days
        )
        
        # Formater les items
        items = [
            HistoryEntryResponse(
                id=item.id,
                type=item.type,
                job_title=item.job_title,
                company_name=item.company_name,
                job_url=item.job_url,
                cv_filename=item.cv_filename,
                status=item.status,
                created_at=item.created_at.isoformat() if item.created_at else "",
                is_downloadable=item.is_downloadable(),
                is_expired=item.is_file_expired(),
                days_until_expiration=item.days_until_expiration()
            )
            for item in result["items"]
        ]
        
        return HistoryListResponse(
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"],
            items=items
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération historique: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")


@router.get("/stats", response_model=HistoryStatsResponse)
async def get_user_history_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques de génération de l'utilisateur.
    
    Args:
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        HistoryStatsResponse avec total, success_rate, etc.
    
    Raises:
        HTTPException 500: Erreur serveur
    """
    try:
        history_repo = PostgresGenerationHistoryRepository(db)
        history_service = GenerationHistoryService(history_repo)
        
        stats = history_service.get_user_stats(current_user.id)
        
        return HistoryStatsResponse(
            total=stats["total"],
            pdf_count=stats["pdf_count"],
            text_count=stats["text_count"],
            success_rate=stats["success_rate"],
            this_month=stats["this_month"],
            last_generation=stats["last_generation"].isoformat() if stats["last_generation"] else None,
            unique_companies=stats["unique_companies"]
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")


@router.get("/{history_id}/text", response_model=HistoryTextResponse)
async def get_history_text(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le contenu texte d'une génération.
    
    Args:
        history_id: ID de l'entrée historique
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        HistoryTextResponse avec le contenu texte
    
    Raises:
        HTTPException 400: Type incorrect (pas de texte)
        HTTPException 403: Accès refusé
        HTTPException 404: Entrée introuvable
        HTTPException 500: Erreur serveur
    """
    try:
        history_repo = PostgresGenerationHistoryRepository(db)
        history = history_repo.get_by_id(history_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Entrée introuvable")
        
        if history.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        if history.type != 'text':
            raise HTTPException(status_code=400, detail="Cette entrée n'est pas de type texte")
        
        return HistoryTextResponse(
            id=history.id,
            text_content=history.text_content or "",
            job_title=history.job_title,
            company_name=history.company_name,
            created_at=history.created_at.isoformat() if history.created_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération texte: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du texte")


@router.delete("/{history_id}")
async def delete_history_entry(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime une entrée de l'historique.
    
    Args:
        history_id: ID de l'entrée à supprimer
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès
    
    Raises:
        HTTPException 403: Accès refusé
        HTTPException 404: Entrée introuvable
        HTTPException 500: Erreur serveur
    """
    try:
        history_repo = PostgresGenerationHistoryRepository(db)
        history_service = GenerationHistoryService(history_repo)
        
        history_service.delete_entry(history_id, current_user.id)
        
        return {
            "status": "success",
            "message": "Entrée supprimée avec succès"
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur suppression historique: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")


@router.get("/export")
async def export_user_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exporte tout l'historique de l'utilisateur en JSON.
    
    Args:
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Fichier JSON avec tout l'historique
    
    Raises:
        HTTPException 500: Erreur serveur
    """
    try:
        history_repo = PostgresGenerationHistoryRepository(db)
        history_service = GenerationHistoryService(history_repo)
        
        export_data = history_service.export_user_history(current_user.id)
        
        return Response(
            content=str(export_data),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=cvlm_history_{datetime.now().strftime('%Y%m%d')}.json"
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur export historique: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'export")
