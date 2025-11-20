"""
Point d'entrée principal de l'API CVLM
Version modulaire avec routes séparées
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from infrastructure.database.config import init_database
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.logger_config import setup_logger
from config.constants import (
    CORS_ALLOWED_ORIGINS,
    CORS_ORIGIN_REGEX,
    FILE_STORAGE_BASE_PATH,
    TEMP_DIR,
    OUTPUT_DIR
)

# Import routes
from api.routes import auth, user, cv, generation, admin, history, download
from api.exception_handlers import business_exception_handler

# Logger
logger = setup_logger(__name__)

# Configuration FastAPI
app = FastAPI(
    title="CVLM API",
    version="2.0.0",
    description="API pour la génération de lettres de motivation"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Initialiser la base de données au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialise la base de données et les répertoires au démarrage"""
    try:
        init_database()
        logger.info("Base de données initialisée avec succès")
        
        # Créer les répertoires nécessaires
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        Path(FILE_STORAGE_BASE_PATH).mkdir(parents=True, exist_ok=True)
        logger.info("Répertoires de stockage initialisés")
        
    except Exception as e:
        logger.error(f"Erreur initialisation: {e}")
        raise

# Exception Handlers
@app.exception_handler(Exception)
async def handle_business_exceptions(request: Request, exc: Exception):
    """Handler global pour les exceptions métier"""
    return await business_exception_handler(request, exc)

# Enregistrer les routes
# Authentification et utilisateur
app.include_router(auth.router)
app.include_router(user.router)

# Gestion des CVs
app.include_router(cv.router)

# Génération de lettres et textes
app.include_router(generation.router)

# Administration
app.include_router(admin.router)

# Historique
app.include_router(history.router)

# Téléchargement et nettoyage
app.include_router(download.router)

# Route health check
@app.get("/health")
def health_check():
    """Vérifie que l'API est opérationnelle"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "CVLM API"
    }


# Point d'entrée pour développement
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Démarrage de l'API CVLM sur http://localhost:8000")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
