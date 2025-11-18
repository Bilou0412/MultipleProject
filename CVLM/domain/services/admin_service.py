"""
Service d'administration pour gérer les utilisateurs et codes promo
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from domain.entities.user import User
from domain.entities.promo_code import PromoCode
from domain.ports.user_repository import UserRepository
from domain.ports.promo_code_repository import PromoCodeRepository
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class AdminService:
    """Service pour les opérations d'administration"""
    
    def __init__(self, user_repo: UserRepository, promo_code_repo: PromoCodeRepository):
        self.user_repo = user_repo
        self.promo_code_repo = promo_code_repo
    
    # === Gestion des utilisateurs ===
    
    def get_all_users(self) -> List[User]:
        """Récupère tous les utilisateurs"""
        logger.info("Récupération de tous les utilisateurs")
        return self.user_repo.get_all()
    
    def promote_to_admin(self, user_id: str) -> User:
        """Donne les droits admin à un utilisateur"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"Utilisateur {user_id} introuvable")
        
        user.is_admin = True
        self.user_repo.update(user)
        logger.info(f"Utilisateur {user.email} promu admin")
        return user
    
    def revoke_admin(self, user_id: str) -> User:
        """Retire les droits admin à un utilisateur"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"Utilisateur {user_id} introuvable")
        
        user.is_admin = False
        self.user_repo.update(user)
        logger.info(f"Droits admin retirés pour {user.email}")
        return user
    
    def add_credits_to_user(self, user_id: str, pdf_credits: int, text_credits: int) -> User:
        """Ajoute des crédits à un utilisateur"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"Utilisateur {user_id} introuvable")
        
        user.pdf_credits += pdf_credits
        user.text_credits += text_credits
        self.user_repo.update(user)
        logger.info(f"Crédits ajoutés à {user.email}: +{pdf_credits} PDF, +{text_credits} texte")
        return user
    
    def set_credits(self, user_id: str, pdf_credits: int, text_credits: int) -> User:
        """Définit les crédits d'un utilisateur (remplace les anciens)"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"Utilisateur {user_id} introuvable")
        
        user.pdf_credits = pdf_credits
        user.text_credits = text_credits
        self.user_repo.update(user)
        logger.info(f"Crédits définis pour {user.email}: {pdf_credits} PDF, {text_credits} texte")
        return user
    
    # === Gestion des codes promo ===
    
    def get_all_promo_codes(self) -> List[PromoCode]:
        """Récupère tous les codes promo"""
        logger.info("Récupération de tous les codes promo")
        return self.promo_code_repo.get_all()
    
    def get_active_promo_codes(self) -> List[PromoCode]:
        """Récupère uniquement les codes actifs"""
        logger.info("Récupération des codes promo actifs")
        return self.promo_code_repo.get_all_active()
    
    def deactivate_promo_code(self, code: str) -> PromoCode:
        """Désactive un code promo"""
        promo_code = self.promo_code_repo.get_by_code(code.upper())
        if not promo_code:
            raise ValueError(f"Code promo {code} introuvable")
        
        promo_code.is_active = False
        self.promo_code_repo.update(promo_code)
        logger.info(f"Code promo {code} désactivé")
        return promo_code
    
    def reactivate_promo_code(self, code: str) -> PromoCode:
        """Réactive un code promo"""
        promo_code = self.promo_code_repo.get_by_code(code.upper())
        if not promo_code:
            raise ValueError(f"Code promo {code} introuvable")
        
        promo_code.is_active = True
        self.promo_code_repo.update(promo_code)
        logger.info(f"Code promo {code} réactivé")
        return promo_code
    
    def delete_promo_code(self, code: str) -> None:
        """Supprime définitivement un code promo"""
        self.promo_code_repo.delete(code.upper())
        logger.info(f"Code promo {code} supprimé")
    
    # === Statistiques ===
    
    def get_dashboard_stats(self) -> Dict:
        """Récupère les statistiques pour le dashboard admin"""
        users = self.user_repo.get_all()
        promo_codes = self.promo_code_repo.get_all()
        active_promos = self.promo_code_repo.get_all_active()
        
        total_pdf_credits = sum(user.pdf_credits for user in users)
        total_text_credits = sum(user.text_credits for user in users)
        total_promo_uses = sum(promo.current_uses for promo in promo_codes)
        
        stats = {
            "total_users": len(users),
            "total_admins": sum(1 for user in users if user.is_admin),
            "total_pdf_credits": total_pdf_credits,
            "total_text_credits": total_text_credits,
            "total_promo_codes": len(promo_codes),
            "active_promo_codes": len(active_promos),
            "total_promo_redemptions": total_promo_uses,
        }
        
        logger.info(f"Statistiques dashboard: {stats}")
        return stats
