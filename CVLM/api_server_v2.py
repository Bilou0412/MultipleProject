"""
API FastAPI pour l'extension navigateur CVLM avec authentification Google et PostgreSQL
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from domain.entities.user import User
from domain.entities.cv import CV
from domain.entities.motivational_letter import MotivationalLetter

from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.Google_gemini_api import LlmGemini
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import LlmOpenAI
from infrastructure.adapters.weasyprint_generator import WeasyPrintGgenerator
from infrastructure.adapters.database_config import get_db, init_database
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.postgres_cv_repository import PostgresCVRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.google_oauth_service import GoogleOAuthService
from infrastructure.adapters.auth_middleware import create_access_token, get_current_user

# Configuration
app = FastAPI(title="CVLM API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialise la base de données au démarrage de l'application"""
    try:
        init_database()
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"⚠️ Erreur initialisation DB: {e}")

# Storage pour les fichiers
FILE_STORAGE_BASE_PATH = os.getenv("FILE_STORAGE_BASE_PATH", "data/files")
file_storage = LocalFileStorage(base_path=FILE_STORAGE_BASE_PATH)

# === Dependency Injection ===

def get_user_repository(db: Session = Depends(get_db)) -> PostgresUserRepository:
    """Dependency pour récupérer le repository utilisateur"""
    return PostgresUserRepository(db)

def get_cv_repository(db: Session = Depends(get_db)) -> PostgresCVRepository:
    """Dependency pour récupérer le repository CV"""
    return PostgresCVRepository(db)

def get_letter_repository(db: Session = Depends(get_db)) -> PostgresMotivationalLetterRepository:
    """Dependency pour récupérer le repository lettres"""
    return PostgresMotivationalLetterRepository(db)

def get_google_oauth_service(
    user_repo: PostgresUserRepository = Depends(get_user_repository)
) -> GoogleOAuthService:
    """Dependency pour récupérer le service OAuth Google"""
    return GoogleOAuthService(user_repo)

def get_current_user_dependency(
    db: Session = Depends(get_db)
):
    """Wrapper pour get_current_user avec le repository"""
    user_repo = PostgresUserRepository(db)
    async def wrapper(credentials):
        return await get_current_user(credentials, user_repo)
    return wrapper

# === Modèles Pydantic ===

class CvInfo(BaseModel):
    cv_id: str
    filename: str
    upload_date: str
    file_size: int
    metadata: dict = {}

class UploadResponse(BaseModel):
    status: str
    cv_id: str
    filename: str

class CvListResponse(BaseModel):
    status: str
    cvs: list[CvInfo]

class GenerationResponse(BaseModel):
    status: str
    file_id: str
    download_url: str
    letter_text: str

class TextGenerationRequest(BaseModel):
    cv_id: Optional[str] = None
    job_url: str
    llm_provider: str = "openai"
    text_type: str = "why_join"

class TextGenerationResponse(BaseModel):
    status: str
    text: str

class AuthTokenRequest(BaseModel):
    google_token: str

class AuthTokenResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: str

# === Endpoints d'authentification ===

@app.get("/health")
def health_check():
    """Endpoint de santé de l'API"""
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/auth/google", response_model=AuthTokenResponse)
async def auth_google(
    request: AuthTokenRequest,
    oauth_service: GoogleOAuthService = Depends(get_google_oauth_service)
):
    """
    Authentifie un utilisateur via un token Google (depuis chrome.identity)
    Crée l'utilisateur s'il n'existe pas
    Retourne un JWT pour les futures requêtes
    """
    try:
        # Authentifier avec Google et créer/récupérer l'utilisateur
        user = await oauth_service.authenticate_user(request.google_token)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Token Google invalide ou email non vérifié"
            )
        
        # Créer un JWT pour l'utilisateur
        access_token = create_access_token(user.id, user.email)
        
        return AuthTokenResponse(
            status="success",
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur auth Google: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db)
):
    """
    Retourne les informations de l'utilisateur courant
    Nécessite un token JWT valide
    """
    user_repo = PostgresUserRepository(db)
    
    # Note: Cette syntaxe est un workaround pour FastAPI
    # Dans la vraie implémentation, on utiliserait Depends(get_current_user)
    from fastapi.security import HTTPBearer
    from fastapi import Security
    
    security = HTTPBearer()
    
    async def get_user(credentials = Security(security)):
        return await get_current_user(credentials, user_repo)
    
    try:
        user = await get_user()
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# === Endpoints CV ===

@app.post("/upload-cv", response_model=UploadResponse)
async def upload_cv(
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload un CV PDF
    Nécessite authentification
    """
    if not cv_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format PDF")
    
    try:
        # Récupérer l'utilisateur courant
        user_repo = PostgresUserRepository(db)
        cv_repo = PostgresCVRepository(db)
        
        from fastapi.security import HTTPBearer
        from fastapi import Security, Request
        
        # Pour simplifier, on crée un user par défaut en attendant l'auth complète
        # TODO: Récupérer l'utilisateur depuis le token JWT
        default_user = user_repo.find_by_email("default@cvlm.com")
        if not default_user:
            default_user = User(
                id=str(uuid.uuid4()),
                email="default@cvlm.com",
                name="Default User",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            user_repo.save(default_user)
        
        # Lire le contenu du fichier
        content = await cv_file.read()
        
        # Sauvegarder avec file_storage
        cv_id = str(uuid.uuid4())
        file_path = file_storage.save_cv(cv_id, content, cv_file.filename)
        
        # Créer l'entité CV
        cv = CV(
            id=cv_id,
            user_id=default_user.id,
            file_path=file_path,
            filename=cv_file.filename,
            upload_date=datetime.utcnow(),
            file_size=len(content),
            metadata={}
        )
        
        # Sauvegarder en base
        cv_repo.save(cv)
        
        return UploadResponse(
            status="success",
            cv_id=cv_id,
            filename=cv_file.filename
        )
    except Exception as e:
        print(f"❌ Erreur upload CV: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.get("/list-cvs", response_model=CvListResponse)
async def list_cvs(
    db: Session = Depends(get_db)
):
    """
    Liste tous les CVs de l'utilisateur courant
    Nécessite authentification
    """
    try:
        user_repo = PostgresUserRepository(db)
        cv_repo = PostgresCVRepository(db)
        
        # TODO: Récupérer l'utilisateur depuis le token JWT
        default_user = user_repo.find_by_email("default@cvlm.com")
        if not default_user:
            return CvListResponse(status="success", cvs=[])
        
        cvs = cv_repo.find_by_user_id(default_user.id)
        
        cv_infos = [
            CvInfo(
                cv_id=cv.id,
                filename=cv.filename,
                upload_date=cv.upload_date.isoformat(),
                file_size=cv.file_size,
                metadata=cv.metadata
            )
            for cv in cvs
        ]
        
        return CvListResponse(status="success", cvs=cv_infos)
    except Exception as e:
        print(f"❌ Erreur list CVs: {e}")
        return CvListResponse(status="error", cvs=[])

@app.delete("/cleanup/{cv_id}")
async def cleanup_files(
    cv_id: str,
    db: Session = Depends(get_db)
):
    """
    Supprime un CV
    Nécessite authentification
    """
    try:
        cv_repo = PostgresCVRepository(db)
        
        # Récupérer le CV
        cv = cv_repo.find_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # TODO: Vérifier que le CV appartient à l'utilisateur courant
        
        # Supprimer le fichier physique
        file_storage.delete_cv(cv_id)
        
        # Supprimer de la base
        cv_repo.delete(cv_id)
        
        return {"status": "success", "message": "CV supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur suppression CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Endpoints génération ===

@app.post("/generate-cover-letter", response_model=GenerationResponse)
async def generate_cover_letter(
    cv_id: str = Form(...),
    job_url: str = Form(...),
    llm_provider: str = Form("openai"),
    pdf_generator: str = Form("fpdf"),
    db: Session = Depends(get_db)
):
    """
    Génère une lettre de motivation
    Nécessite authentification
    """
    try:
        user_repo = PostgresUserRepository(db)
        cv_repo = PostgresCVRepository(db)
        letter_repo = PostgresMotivationalLetterRepository(db)
        
        # TODO: Récupérer l'utilisateur depuis le token JWT
        default_user = user_repo.find_by_email("default@cvlm.com")
        if not default_user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        # Récupérer le CV
        cv = cv_repo.find_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Vérifier que le CV appartient à l'utilisateur
        if cv.user_id != default_user.id:
            raise HTTPException(status_code=403, detail="Accès refusé à ce CV")
        
        # Récupérer le fichier CV
        cv_path = file_storage.get_cv_path(cv_id)
        if not cv_path or not Path(cv_path).exists():
            raise HTTPException(status_code=404, detail="Fichier CV introuvable")
        
        # Configurer les services
        document_parser = Pypdf_parser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = LlmGemini() if llm_provider.lower() == "gemini" else LlmOpenAI()
        pdf_gen = WeasyPrintGgenerator() if pdf_generator.lower() == "weasyprint" else Fpdf_generator()
        
        use_case = AnalyseCvOffer(
            job_offer_fetcher=job_fetcher,
            document_parser=document_parser,
            llm=llm,
            pdf_generator=pdf_gen,
            cv_repository=cv_repo,
            motivational_letter_repository=letter_repo,
            file_storage=file_storage
        )
        
        # Générer la lettre
        letter_id = str(uuid.uuid4())
        result_path = use_case.execute(
            cv_path=Path(cv_path),
            jo_path=job_url,
            output_path=None,  # Le use case générera le path
            use_scraper=True,
            user_id=default_user.id,
            cv_id=cv_id
        )
        
        # Extraire le texte du PDF généré
        letter_text = "Lettre générée avec succès. Consultez le PDF."
        try:
            from PyPDF2 import PdfReader
            with open(result_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                letter_text = ""
                for page in pdf_reader.pages:
                    letter_text += page.extract_text() + "\n"
                letter_text = letter_text.strip()
        except:
            pass
        
        return GenerationResponse(
            status="success",
            file_id=letter_id,
            download_url=f"/download/{letter_id}",
            letter_text=letter_text
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur génération: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")

@app.get("/download/{file_id}")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Télécharge une lettre de motivation générée
    Nécessite authentification
    """
    try:
        letter_repo = PostgresMotivationalLetterRepository(db)
        
        # Récupérer la lettre
        letter = letter_repo.find_by_id(file_id)
        if not letter:
            raise HTTPException(status_code=404, detail="Lettre non trouvée")
        
        # TODO: Vérifier que la lettre appartient à l'utilisateur courant
        
        # Récupérer le fichier
        file_path = file_storage.get_letter_path(file_id)
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Fichier introuvable")
        
        return FileResponse(
            path=file_path,
            filename=letter.filename or "lettre_motivation.pdf",
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur téléchargement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage de l'API CVLM v2.0 sur http://localhost:8000")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
