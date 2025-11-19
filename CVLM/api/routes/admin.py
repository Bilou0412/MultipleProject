"""
Routes d'administration
Endpoints: /admin/stats, /admin/users, /admin/promo-codes, /admin/users/promote, etc.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import verify_admin, get_db
from api.models.admin import (
    DashboardStatsResponse,
    PromoCodeGenerateRequest,
    PromoCodeResponse,
    PromoCodeRedeemRequest,
    PromoCodeRedeemResponse,
    UserUpdateCreditsRequest,
    UserPromoteRequest
)
from api.models.auth import UserResponse
from domain.entities.user import User
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.postgres_promo_code_repository import PostgresPromoCodeRepository
from domain.services.admin_service import AdminService
from domain.services.promo_code_service import PromoCodeService
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_admin_stats(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques du dashboard admin.
    
    Args:
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        DashboardStatsResponse avec total_users, active_promo_codes, etc.
    
    Raises:
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        stats = admin_service.get_dashboard_stats()
        return DashboardStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Erreur récupération stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de tous les utilisateurs.
    
    Args:
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Liste de UserResponse
    
    Raises:
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        users = admin_service.get_all_users()
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.profile_picture_url,
                pdf_credits=user.pdf_credits,
                text_credits=user.text_credits,
                is_admin=user.is_admin,
                created_at=user.created_at.isoformat() if user.created_at else ""
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Erreur récupération utilisateurs: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des utilisateurs")


@router.get("/promo-codes", response_model=list[PromoCodeResponse])
async def get_all_promo_codes(
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les codes promo.
    
    Args:
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Liste de PromoCodeResponse
    
    Raises:
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        promo_codes = admin_service.get_all_promo_codes()
        return [
            PromoCodeResponse(
                code=promo.code,
                pdf_credits=promo.pdf_credits,
                text_credits=promo.text_credits,
                max_uses=promo.max_uses,
                current_uses=promo.current_uses,
                is_active=promo.is_active,
                expires_at=promo.expires_at.isoformat() if promo.expires_at else None
            )
            for promo in promo_codes
        ]
        
    except Exception as e:
        logger.error(f"Erreur récupération codes promo: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des codes promo")


@router.post("/promo-codes/generate", response_model=PromoCodeResponse)
async def generate_promo_code(
    data: PromoCodeGenerateRequest,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Génère un nouveau code promo (réservé aux admins).
    
    Args:
        data: Requête avec pdf_credits, text_credits, max_uses, etc.
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        PromoCodeResponse avec le code généré
    
    Raises:
        HTTPException 400: Données invalides
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        promo_repo = PostgresPromoCodeRepository(db)
        user_repo = PostgresUserRepository(db)
        promo_service = PromoCodeService(promo_repo, user_repo)
        
        promo_code = promo_service.generate_code(
            pdf_credits=data.pdf_credits,
            text_credits=data.text_credits,
            max_uses=data.max_uses,
            days_valid=data.days_valid,
            custom_code=data.custom_code
        )
        
        return PromoCodeResponse(
            code=promo_code.code,
            pdf_credits=promo_code.pdf_credits,
            text_credits=promo_code.text_credits,
            max_uses=promo_code.max_uses,
            current_uses=promo_code.current_uses,
            is_active=promo_code.is_active,
            expires_at=promo_code.expires_at.isoformat() if promo_code.expires_at else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur génération code promo: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération du code")


@router.post("/promo-codes/redeem", response_model=PromoCodeRedeemResponse)
async def redeem_promo_code(
    data: PromoCodeRedeemRequest,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Utilise un code promo pour obtenir des crédits (endpoint admin pour tests).
    
    Args:
        data: Requête avec le code promo
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        PromoCodeRedeemResponse avec les crédits ajoutés
    
    Raises:
        HTTPException 400: Code invalide ou expiré
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        promo_repo = PostgresPromoCodeRepository(db)
        user_repo = PostgresUserRepository(db)
        promo_service = PromoCodeService(promo_repo, user_repo)
        
        pdf_added, text_added = promo_service.redeem_code(data.code, admin)
        
        # Rafraîchir l'utilisateur pour avoir les nouveaux crédits
        refreshed_user = user_repo.get_by_id(admin.id)
        
        return PromoCodeRedeemResponse(
            status="success",
            message=f"Code promo appliqué ! Vous avez reçu {pdf_added} crédits PDF et {text_added} crédits texte.",
            pdf_credits_added=pdf_added,
            text_credits_added=text_added,
            new_pdf_credits=refreshed_user.pdf_credits,
            new_text_credits=refreshed_user.text_credits
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur utilisation code promo: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'utilisation du code")


@router.post("/users/promote")
async def promote_user_to_admin(
    data: UserPromoteRequest,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Donne les droits admin à un utilisateur.
    
    Args:
        data: Requête avec user_id
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès
    
    Raises:
        HTTPException 404: Utilisateur introuvable
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        user = admin_service.promote_to_admin(data.user_id)
        return {
            "status": "success",
            "message": f"{user.email} est maintenant administrateur"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur promotion admin: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la promotion")


@router.post("/users/revoke")
async def revoke_user_admin(
    data: UserPromoteRequest,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Retire les droits admin à un utilisateur.
    
    Args:
        data: Requête avec user_id
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès
    
    Raises:
        HTTPException 404: Utilisateur introuvable
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        user = admin_service.revoke_admin(data.user_id)
        return {
            "status": "success",
            "message": f"Droits admin retirés pour {user.email}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur révocation admin: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la révocation")


@router.post("/users/credits")
async def update_user_credits(
    data: UserUpdateCreditsRequest,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Modifie les crédits d'un utilisateur (add ou set).
    
    Args:
        data: Requête avec user_id, pdf_credits, text_credits, operation
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès avec nouveaux crédits
    
    Raises:
        HTTPException 400: Opération invalide
        HTTPException 404: Utilisateur introuvable
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        if data.operation == "add":
            user = admin_service.add_credits_to_user(data.user_id, data.pdf_credits, data.text_credits)
            message = f"Crédits ajoutés à {user.email}: +{data.pdf_credits} PDF, +{data.text_credits} texte"
        elif data.operation == "set":
            user = admin_service.set_credits(data.user_id, data.pdf_credits, data.text_credits)
            message = f"Crédits définis pour {user.email}: {data.pdf_credits} PDF, {data.text_credits} texte"
        else:
            raise HTTPException(status_code=400, detail="Opération invalide (doit être 'add' ou 'set')")
        
        return {
            "status": "success",
            "message": message,
            "pdf_credits": user.pdf_credits,
            "text_credits": user.text_credits
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur modification crédits: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la modification des crédits")


@router.delete("/promo-codes/{code}")
async def delete_promo_code(
    code: str,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Supprime définitivement un code promo.
    
    Args:
        code: Code promo à supprimer
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès
    
    Raises:
        HTTPException 404: Code introuvable
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        admin_service.delete_promo_code(code)
        return {
            "status": "success",
            "message": f"Code promo {code} supprimé"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur suppression code promo: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")


@router.patch("/promo-codes/{code}/toggle")
async def toggle_promo_code(
    code: str,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Active ou désactive un code promo.
    
    Args:
        code: Code promo à activer/désactiver
        admin: Utilisateur admin connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Message de succès
    
    Raises:
        HTTPException 404: Code introuvable
        HTTPException 403: Utilisateur non admin
        HTTPException 500: Erreur serveur
    """
    try:
        user_repo = PostgresUserRepository(db)
        promo_repo = PostgresPromoCodeRepository(db)
        admin_service = AdminService(user_repo, promo_repo)
        
        promo_code = promo_repo.get_by_code(code.upper())
        if not promo_code:
            raise HTTPException(status_code=404, detail=f"Code promo {code} introuvable")
        
        if promo_code.is_active:
            admin_service.deactivate_promo_code(code)
            message = f"Code promo {code} désactivé"
        else:
            admin_service.reactivate_promo_code(code)
            message = f"Code promo {code} réactivé"
        
        return {
            "status": "success",
            "message": message
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur toggle code promo: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la modification")
