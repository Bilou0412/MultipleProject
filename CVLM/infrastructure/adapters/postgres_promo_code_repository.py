"""
Implémentation PostgreSQL du repository PromoCode
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from domain.entities.promo_code import PromoCode
from domain.ports.promo_code_repository import PromoCodeRepository
from infrastructure.database.models import PromoCodeModel
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class PostgresPromoCodeRepository(PromoCodeRepository):
    """Repository PostgreSQL pour les codes promo"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, promo_code: PromoCode) -> PromoCode:
        """Crée un nouveau code promo"""
        db_promo = PromoCodeModel(
            code=promo_code.code,
            pdf_credits=promo_code.pdf_credits,
            text_credits=promo_code.text_credits,
            max_uses=promo_code.max_uses,
            current_uses=promo_code.current_uses,
            is_active=promo_code.is_active,
            created_at=promo_code.created_at,
            expires_at=promo_code.expires_at
        )
        self.db.add(db_promo)
        self.db.commit()
        self.db.refresh(db_promo)
        logger.info(f"Code promo créé: {promo_code.code}")
        return self._model_to_entity(db_promo)
    
    def get_by_code(self, code: str) -> Optional[PromoCode]:
        """Récupère un code promo par son code"""
        db_promo = self.db.query(PromoCodeModel).filter(
            PromoCodeModel.code == code.upper()
        ).first()
        
        if db_promo:
            return self._model_to_entity(db_promo)
        return None
    
    def get_all_active(self) -> List[PromoCode]:
        """Récupère tous les codes promo actifs"""
        db_promos = self.db.query(PromoCodeModel).filter(
            PromoCodeModel.is_active == True
        ).all()
        
        return [self._model_to_entity(db_promo) for db_promo in db_promos]
    
    def update(self, promo_code: PromoCode) -> PromoCode:
        """Met à jour un code promo"""
        db_promo = self.db.query(PromoCodeModel).filter(
            PromoCodeModel.code == promo_code.code
        ).first()
        
        if not db_promo:
            raise ValueError(f"Code promo non trouvé: {promo_code.code}")
        
        db_promo.pdf_credits = promo_code.pdf_credits
        db_promo.text_credits = promo_code.text_credits
        db_promo.max_uses = promo_code.max_uses
        db_promo.current_uses = promo_code.current_uses
        db_promo.is_active = promo_code.is_active
        db_promo.expires_at = promo_code.expires_at
        
        self.db.commit()
        self.db.refresh(db_promo)
        logger.info(f"Code promo mis à jour: {promo_code.code}")
        return self._model_to_entity(db_promo)
    
    def delete(self, code: str) -> None:
        """Supprime un code promo"""
        db_promo = self.db.query(PromoCodeModel).filter(
            PromoCodeModel.code == code
        ).first()
        
        if db_promo:
            self.db.delete(db_promo)
            self.db.commit()
            logger.info(f"Code promo supprimé: {code}")
    
    def get_all(self) -> List[PromoCode]:
        """Récupère tous les codes promo (actifs et inactifs)"""
        db_promos = self.db.query(PromoCodeModel).all()
        return [self._model_to_entity(promo) for promo in db_promos]
    
    def _model_to_entity(self, model: PromoCodeModel) -> PromoCode:
        """Convertit un modèle SQLAlchemy en entité"""
        return PromoCode(
            code=model.code,
            pdf_credits=model.pdf_credits,
            text_credits=model.text_credits,
            max_uses=model.max_uses,
            current_uses=model.current_uses,
            is_active=model.is_active,
            created_at=model.created_at,
            expires_at=model.expires_at
        )
