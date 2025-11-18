"""
Configuration de la base de données PostgreSQL avec SQLAlchemy
"""
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Base pour les modèles SQLAlchemy
Base = declarative_base()

# Modèles de tables
class UserModel(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    google_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    profile_picture_url = Column(String, nullable=True)
    # Crédits d'essai (trial credits)
    pdf_credits = Column(Integer, nullable=False, default=10)
    text_credits = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class CvModel(Base):
    __tablename__ = 'cvs'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class MotivationalLetterModel(Base):
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
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


# Configuration de la connexion
def get_database_url():
    """
    Construit l'URL de connexion à partir des variables d'environnement
    Format: postgresql://user:password@host:port/database
    """
    return os.getenv(
        'DATABASE_URL',
        'postgresql://cvlm_user:cvlm_password@localhost:5432/cvlm_db'
    )


def create_db_engine():
    """Crée le moteur SQLAlchemy"""
    database_url = get_database_url()
    return create_engine(database_url, echo=False)


def get_session_factory():
    """Crée une factory de sessions"""
    engine = create_db_engine()
    return sessionmaker(bind=engine)


def get_db():
    """
    Dependency pour FastAPI - fournit une session de base de données
    Usage: def my_endpoint(db: Session = Depends(get_db))
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialise la base de données (crée les tables)"""
    engine = create_db_engine()
    Base.metadata.create_all(engine)
    print("✅ Base de données initialisée avec succès")


def drop_all_tables():
    """Supprime toutes les tables (utile pour les tests)"""
    engine = create_db_engine()
    Base.metadata.drop_all(engine)
    print("⚠️ Toutes les tables ont été supprimées")
