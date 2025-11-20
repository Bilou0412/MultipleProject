"""
Modèle SQLAlchemy pour les lettres de motivation
"""
from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime
from infrastructure.database.config import Base


class MotivationalLetterModel(Base):
    """Modèle de table pour les lettres de motivation"""
    __tablename__ = 'motivational_letters'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    cv_id = Column(String, nullable=True, index=True)
    job_offer_url = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    llm_provider = Column(String, nullable=False, default='openai')
    
    # Dates
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
