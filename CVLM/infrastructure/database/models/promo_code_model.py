"""
Modèle SQLAlchemy pour les codes promo
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime
from infrastructure.database.config import Base


class PromoCodeModel(Base):
    """Modèle de table pour les codes promo"""
    __tablename__ = 'promo_codes'
    
    code = Column(String, primary_key=True)
    pdf_credits = Column(Integer, nullable=False, default=0)
    text_credits = Column(Integer, nullable=False, default=0)
    max_uses = Column(Integer, nullable=False, default=0)  # 0 = illimité
    current_uses = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Dates
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=True)
