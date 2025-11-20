"""
Modèle SQLAlchemy pour les utilisateurs
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime
from infrastructure.database.config import Base


class UserModel(Base):
    """Modèle de table pour les utilisateurs"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    google_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    profile_picture_url = Column(String, nullable=True)
    
    # Crédits d'essai (trial credits)
    pdf_credits = Column(Integer, nullable=False, default=10)
    text_credits = Column(Integer, nullable=False, default=10)
    is_admin = Column(Boolean, nullable=False, default=False)
    
    # Dates
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
