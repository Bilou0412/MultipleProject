"""
Modèle SQLAlchemy pour l'historique de génération
"""
from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
from infrastructure.database.config import Base


class GenerationHistoryModel(Base):
    """Modèle de table pour l'historique de génération"""
    __tablename__ = 'generation_history'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    type = Column(String(10), nullable=False)  # 'pdf' ou 'text'
    
    # Informations sur l'offre
    job_title = Column(String(500), nullable=True)
    company_name = Column(String(200), nullable=True)
    job_url = Column(Text, nullable=True)
    
    # Informations sur la génération
    cv_filename = Column(String(255), nullable=True)
    cv_id = Column(String, nullable=True)
    file_path = Column(String(500), nullable=True)  # NULL si expiré
    text_content = Column(Text, nullable=True)
    
    # Statut
    status = Column(String(20), nullable=False, default='success')
    error_message = Column(Text, nullable=True)
    
    # Dates
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    file_expires_at = Column(DateTime, nullable=True, index=True)
