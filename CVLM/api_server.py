"""
API FastAPI pour l'extension navigateur CVLM
Version 2.0: Refactoré selon principes Clean Code
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header, Request
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from typing import Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from domain.entities.user import User
from domain.entities.cv import Cv
from domain.services.letter_generation_service import LetterGenerationService
from domain.services.credit_service import CreditService
from domain.services.cv_validation_service import CvValidationService

from infrastructure.adapters.database_config import get_db, init_database
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.google_oauth_service import GoogleOAuthService
from infrastructure.adapters.auth_middleware import create_access_token, verify_access_token
from infrastructure.adapters.pypdf_parse import PyPdfParser
from infrastructure.adapters.google_gemini_api import GoogleGeminiLlm
from infrastructure.adapters.open_ai_api import OpenAiLlm
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.logger_config import setup_logger

from config.constants import (
    CORS_ALLOWED_ORIGINS,
    CORS_ORIGIN_REGEX,
    FILE_STORAGE_BASE_PATH,
    TEMP_DIR,
    OUTPUT_DIR,
    LLM_PROVIDER_GEMINI,
    TEXT_TYPE_WHY_JOIN
)

# Logger
logger = setup_logger(__name__)

# Configuration
app = FastAPI(title="CVLM API", version="2.0.0")

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
    """Initialise la base de données au démarrage"""
    try:
        init_database()
        logger.info("Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur initialisation DB: {e}")
        raise

# Storage et répertoires
file_storage = LocalFileStorage(base_path=FILE_STORAGE_BASE_PATH)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === Dependency Injection ===

def get_user_repository(db: Session = Depends(get_db)) -> PostgresUserRepository:
    return PostgresUserRepository(db)

def get_cv_repository(db: Session = Depends(get_db)) -> PostgresCvRepository:
    return PostgresCvRepository(db)

def get_letter_repository(db: Session = Depends(get_db)) -> PostgresMotivationalLetterRepository:
    return PostgresMotivationalLetterRepository(db)

def get_google_oauth_service(
    user_repo: PostgresUserRepository = Depends(get_user_repository)
) -> GoogleOAuthService:
    return GoogleOAuthService(user_repo)

def get_or_create_default_user(db: Session) -> User:
    """Crée ou récupère l'utilisateur par défaut (transition)"""
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_email("default@cvlm.com")
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="default@cvlm.com",
            google_id="default-google-id",  # ID fictif pour l'utilisateur par défaut
            name="Default User",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user_repo.create(user)
    return user

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Extrait l'utilisateur depuis le JWT ou retourne l'utilisateur par défaut
    Compatible avec ancien système (sans JWT) et nouveau (avec JWT)
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        try:
            payload = verify_access_token(token)
            user_id = payload.get("sub")
            
            if user_id:
                user_repo = PostgresUserRepository(db)
                user = user_repo.get_by_id(user_id)
                if user:
                    logger.debug(f"Utilisateur authentifié: {user.email}")
                    return user
        except Exception as e:
            logger.warning(f"JWT invalide: {e}")
    
    # Fallback vers utilisateur par défaut
    logger.debug("Utilisation de l'utilisateur par défaut")
    return get_or_create_default_user(db)

# === Modèles ===

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
    picture: Optional[str] = None
    created_at: str

class CvInfo(BaseModel):
    cv_id: str
    filename: str
    upload_date: str
    file_size: int

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

# === Utilitaires ===

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"⚠️ Erreur extraction PDF: {e}")
        return ""

# === Endpoints ===

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}

@app.get("/user/credits")
async def get_user_credits(
    current_user: User = Depends(get_current_user)
):
    """Retourne les crédits restants de l'utilisateur"""
    from config.constants import DEFAULT_PDF_CREDITS, DEFAULT_TEXT_CREDITS
    return {
        "pdf_credits": current_user.pdf_credits,
        "text_credits": current_user.text_credits,
        "total_pdf_credits": DEFAULT_PDF_CREDITS,
        "total_text_credits": 10
    }

@app.post("/auth/google", response_model=AuthTokenResponse)
async def auth_google(
    request: AuthTokenRequest,
    oauth_service: GoogleOAuthService = Depends(get_google_oauth_service)
):
    """
    Authentifie un utilisateur via un token Google (depuis chrome.identity)
    Crée l'utilisateur s'il n'existe pas, retourne un JWT
    """
    try:
        user = await oauth_service.authenticate_user(request.google_token)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Token Google invalide ou email non vérifié"
            )
        
        access_token = create_access_token(user.id, user.email)
        
        return AuthTokenResponse(
            status="success",
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.profile_picture_url,
                "created_at": user.created_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur auth Google: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Retourne les infos de l'utilisateur connecté"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.profile_picture_url,
        created_at=current_user.created_at.isoformat()
    )

@app.post("/upload-cv", response_model=UploadResponse)
async def upload_cv(
    cv_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not cv_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format PDF")
    
    try:
        cv_repo = PostgresCvRepository(db)
        document_parser = PyPdfParser()
        
        content = await cv_file.read()
        cv_id = str(uuid.uuid4())
        
        # Sauvegarder le fichier
        file_path = file_storage.save_cv(cv_id, content, cv_file.filename)
        
        # Extraire le texte du PDF
        try:
            raw_text = document_parser.parse_document(input_path=file_path)
        except Exception as e:
            print(f"⚠️ Erreur extraction texte: {e}")
            raw_text = ""
        
        # Créer l'entité CV pour l'utilisateur connecté
        cv = Cv(
            id=cv_id,
            user_id=current_user.id,
            file_path=file_path,
            filename=cv_file.filename,
            file_size=len(content),
            raw_text=raw_text,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Sauvegarder en base
        cv_repo.create(cv)
        
        return UploadResponse(
            status="success",
            cv_id=cv_id,
            filename=cv_file.filename
        )
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.get("/list-cvs", response_model=CvListResponse)
async def list_cvs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cv_repo = PostgresCvRepository(db)
        
        # Récupérer uniquement les CVs de l'utilisateur connecté
        cvs = cv_repo.get_by_user_id(current_user.id)
        
        cv_infos = [
            CvInfo(
                cv_id=cv.id,
                filename=cv.filename,
                upload_date=cv.created_at.isoformat(),
                file_size=cv.file_size
            )
            for cv in cvs if Path(cv.file_path).exists()
        ]
        
        return CvListResponse(status="success", cvs=cv_infos)
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des CVs: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des CVs: {str(e)}")

@app.get("/list-letters")
async def list_letters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Liste toutes les lettres générées par l'utilisateur"""
    try:
        letter_repo = PostgresMotivationalLetterRepository(db)
        cv_repo = PostgresCvRepository(db)
        
        # Récupérer toutes les lettres de l'utilisateur
        letters = letter_repo.get_by_user_id(current_user.id)
        
        letter_infos = []
        for letter in letters:
            # Récupérer le CV associé
            cv = cv_repo.get_by_id(letter.cv_id) if letter.cv_id else None
            
            letter_infos.append({
                "letter_id": letter.id,
                "filename": letter.filename or "lettre_motivation.pdf",
                "cv_filename": cv.filename if cv else "CV supprimé",
                "job_offer_url": letter.job_offer_url or "",
                "created_at": letter.created_at.isoformat(),
                "file_size": letter.file_size,
                "llm_provider": letter.llm_provider
            })
        
        # Trier par date décroissante (plus récent en premier)
        letter_infos.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "success",
            "letters": letter_infos,
            "total": len(letter_infos)
        }
    except Exception as e:
        print(f"❌ Erreur liste lettres: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des lettres: {str(e)}")

@app.post("/generate-cover-letter", response_model=GenerationResponse)
async def generate_cover_letter(
    cv_id: str = Form(...),
    job_url: str = Form(...),
    llm_provider: str = Form("openai"),
    pdf_generator: str = Form("fpdf"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Génère une lettre de motivation en PDF"""
    try:
        # Services
        cv_validation_service = CvValidationService(PostgresCvRepository(db))
        credit_service = CreditService(PostgresUserRepository(db))
        letter_service = LetterGenerationService()
        
        # Valider le CV
        cv = cv_validation_service.get_and_validate_cv(cv_id, current_user)
        
        # Vérifier et utiliser un crédit (lève une exception si pas de crédit)
        credit_service.check_and_use_pdf_credit(current_user)
        
        # Générer la lettre
        letter_id, pdf_path, letter_text = letter_service.generate_letter_pdf(
            cv=cv,
            job_url=job_url,
            llm_provider=llm_provider,
            pdf_generator=pdf_generator,
            user=current_user
        )
        
        # Sauvegarder en base de données
        try:
            letter = letter_service.save_letter_to_storage(
                letter_id=letter_id,
                pdf_path=pdf_path,
                cv_id=cv_id,
                job_url=job_url,
                letter_text=letter_text,
                llm_provider=llm_provider,
                user=current_user
            )
            
            letter_repo = PostgresMotivationalLetterRepository(db)
            letter_repo.create(letter)
            
        except Exception as e:
            logger.warning(f"Erreur sauvegarde lettre en base: {e}")
        
        return GenerationResponse(
            status="success",
            file_id=letter_id,
            download_url=f"/download-letter/{letter_id}",
            letter_text=letter_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération lettre: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    data: TextGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Génère un texte de motivation personnalisé"""
    try:
        # Validation
        if not data.cv_id:
            raise HTTPException(
                status_code=400,
                detail="Aucun CV sélectionné. Veuillez d'abord télécharger et sélectionner un CV."
            )
        
        # Services
        cv_validation_service = CvValidationService(PostgresCvRepository(db))
        credit_service = CreditService(PostgresUserRepository(db))
        
        # Valider le CV et vérifier crédit
        cv = cv_validation_service.get_and_validate_cv(data.cv_id, current_user)
        credit_service.check_and_use_text_credit(current_user)
        
        # Parser et fetcher
        document_parser = PyPdfParser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = GoogleGeminiLlm() if data.llm_provider.lower() == LLM_PROVIDER_GEMINI else OpenAiLlm()
        
        cv_text = document_parser.parse_document(input_path=str(cv.file_path))
        
        job_offer_text = ""
        try:
            job_offer_text = job_fetcher.fetch(url=data.job_url)
        except Exception as e:
            logger.warning(f"Erreur fetch offre d'emploi: {e}")
        
        # Créer le prompt
        prompt = _build_text_generation_prompt(cv_text, job_offer_text, data.text_type)
        
        # Générer
        generated_text = llm.send_to_llm(prompt)
        logger.info(f"Texte généré pour {current_user.email}")
        
        return TextGenerationResponse(status="success", text=generated_text)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération texte: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_text_generation_prompt(cv_text: str, job_offer_text: str, text_type: str) -> str:
    """Construit le prompt pour la génération de texte"""
    if text_type == TEXT_TYPE_WHY_JOIN:
        return (
            f"Vous êtes un assistant expert en communication RH.\n\n"
            f"Contexte (CV) :\n{cv_text}\n\n"
            f"Offre d'emploi :\n{job_offer_text}\n\n"
            f"Tâche : Rédigez une réponse concise (3-6 phrases) à la question : "
            f"'Expliquez-nous pourquoi vous souhaitez nous rejoindre.' "
            f"Utilisez un ton professionnel et motivé. Ne fournissez que le texte de la réponse, "
            f"sans préambule ni signature."
        )
    return (
        f"Vous êtes un assistant expert.\n\n"
        f"Contexte (CV) :\n{cv_text}\n\n"
        f"Offre d'emploi :\n{job_offer_text}\n\n"
        f"Tâche : Rédigez un court paragraphe adapté à l'offre."
    )


@app.get("/download-letter/{letter_id}")
async def download_letter(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Télécharge une lettre de motivation depuis PostgreSQL"""
    try:
        letter_repo = PostgresMotivationalLetterRepository(db)
        letter = letter_repo.get_by_id(letter_id)
        
        if not letter:
            raise HTTPException(status_code=404, detail="Lettre non trouvée")
        
        if letter.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès interdit à cette lettre")
        
        file_path = file_storage.get_letter_path(letter_id)
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Fichier PDF introuvable")
        
        return FileResponse(
            path=file_path,
            filename=letter.filename or f"lettre_{letter_id}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement lettre: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")


@app.delete("/cleanup/{cv_id}")
async def cleanup_files(
    cv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime un CV et ses fichiers associés"""
    try:
        cv_validation_service = CvValidationService(PostgresCvRepository(db))
        cv = cv_validation_service.get_and_validate_cv(cv_id, current_user)
        
        # Supprimer fichier et base de données
        file_storage.delete_cv(cv_id)
        cv_repo = PostgresCvRepository(db)
        cv_repo.delete(cv_id)
        
        logger.info(f"CV supprimé: {cv_id} par {current_user.email}")
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage de l'API CVLM sur http://localhost:8000")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
