"""
Configuration de la base de données PostgreSQL avec SQLAlchemy
Contient uniquement la configuration (Base, engine, sessions)
Les modèles sont maintenant dans infrastructure/database/models/
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)

# Base pour les modèles SQLAlchemy
Base = declarative_base()


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
    # Import des modèles pour que SQLAlchemy les connaisse
    from infrastructure.database.models import (
        UserModel, CvModel, MotivationalLetterModel, 
        PromoCodeModel, GenerationHistoryModel
    )
    
    engine = create_db_engine()
    Base.metadata.create_all(engine)
    logger.info("Base de données initialisée avec succès")


def drop_all_tables():
    """Supprime toutes les tables (utile pour les tests)"""
    engine = create_db_engine()
    Base.metadata.drop_all(engine)
    logger.warning("Toutes les tables ont été supprimées")
