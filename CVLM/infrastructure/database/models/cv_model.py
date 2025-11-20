"""
Modèle SQLAlchemy pour les CVs
"""
from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime
from infrastructure.database.config import Base


class CvModel(Base):
    """Modèle de table pour les CVs"""
    __tablename__ = 'cvs'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    
    # Dates
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
