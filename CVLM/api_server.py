"""
API FastAPI pour l'extension navigateur CVLM
Version 1.5: Support PostgreSQL + Auth Google (rétrocompatible)
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import Optional
from pathlib import Path
import PyPDF2
from datetime import datetime
from sqlalchemy.orm import Session

from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from domain.entities.user import User
from domain.entities.cv import Cv

from infrastructure.adapters.pypdf_parse import PyPdfParser
from infrastructure.adapters.google_gemini_api import GoogleGeminiLlm
from infrastructure.adapters.fpdf_generator import FpdfGenerator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import OpenAiLlm
from infrastructure.adapters.weasyprint_generator import WeasyPrintGenerator
from infrastructure.adapters.database_config import get_db, init_database
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.google_oauth_service import GoogleOAuthService
from infrastructure.adapters.auth_middleware import create_access_token, verify_access_token

# Configuration
app = FastAPI(title="CVLM API", version="1.5.0")

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
    """Initialise la base de données au démarrage"""
    try:
        init_database()
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"⚠️ Erreur initialisation DB (mode fallback): {e}")

# Storage pour les fichiers
FILE_STORAGE_BASE_PATH = os.getenv("FILE_STORAGE_BASE_PATH", "data/files")
file_storage = LocalFileStorage(base_path=FILE_STORAGE_BASE_PATH)

# Legacy storage (fallback)
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

storage = {"cvs": {}, "letters": {}}

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
    Extrait l'utilisateur depuis le JWT (si fourni) ou retourne l'utilisateur par défaut
    Compatible avec l'ancien système (pas de JWT) et le nouveau (avec JWT)
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
                    return user
        except Exception as e:
            print(f"⚠️ JWT invalide: {e}")
    
    # Fallback vers utilisateur par défaut
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
    return {"status": "healthy", "version": "1.5.0"}

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
        
        # Legacy storage (pour compatibilité)
        storage["cvs"][cv_id] = {
            "path": file_path,
            "filename": cv_file.filename,
            "upload_date": datetime.now().isoformat(),
            "file_size": len(content)
        }
        
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
        print(f"⚠️ Erreur PostgreSQL, fallback legacy: {e}")
        # Fallback legacy
        cvs = []
        for cv_id, cv_data in storage["cvs"].items():
            cv_path = Path(cv_data["path"])
            if cv_path.exists():
                cvs.append(CvInfo(
                    cv_id=cv_id,
                    filename=cv_data["filename"],
                    upload_date=cv_data["upload_date"],
                    file_size=cv_data["file_size"]
                ))
        return CvListResponse(status="success", cvs=cvs)

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
    try:
        # Récupérer le CV depuis PostgreSQL
        cv_repo = PostgresCvRepository(db)
        cv = cv_repo.get_by_id(cv_id)
        
        # Vérifier que le CV appartient à l'utilisateur
        if cv and cv.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès interdit à ce CV")
        
        if not cv:
            # Fallback legacy
            if cv_id not in storage["cvs"]:
                raise HTTPException(status_code=404, detail="CV non trouvé")
            cv_path = Path(storage["cvs"][cv_id]["path"])
        else:
            cv_path = Path(cv.file_path)
        
        if not cv_path.exists():
            raise HTTPException(status_code=404, detail="Fichier CV introuvable")
        
        # Services LLM et PDF
        document_parser = PyPdfParser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = GoogleGeminiLlm() if llm_provider.lower() == "gemini" else OpenAiLlm()
        pdf_gen = WeasyPrintGenerator() if pdf_generator.lower() == "weasyprint" else FpdfGenerator()
        
        use_case = AnalyseCvOffer(
            job_offer_fetcher=job_fetcher,
            document_parser=document_parser,
            llm=llm,
            pdf_generator=pdf_gen
        )
        
        # Générer la lettre
        letter_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"lettre_{letter_id}.pdf"
        
        result_path = use_case.execute(
            cv_path=cv_path,
            jo_path=job_url,
            output_path=str(output_path),
            use_scraper=True
        )
        
        letter_text = extract_text_from_pdf(result_path)
        if not letter_text:
            letter_text = "Lettre générée. Consultez le PDF."
        
        # Sauvegarder dans PostgreSQL
        try:
            from domain.entities.motivational_letter import MotivationalLetter
            letter_repo = PostgresMotivationalLetterRepository(db)
            file_storage = LocalFileStorage()
            
            # Lire le contenu du PDF
            with open(result_path, 'rb') as f:
                pdf_content = f.read()
            
            # Sauvegarder le fichier via le storage
            file_path = file_storage.save_letter(
                letter_id=letter_id,
                content=pdf_content,
                filename=f"lettre_{letter_id}.pdf"
            )
            
            # Créer l'entité MotivationalLetter
            letter = MotivationalLetter(
                id=letter_id,
                user_id=current_user.id,
                cv_id=cv_id,
                job_offer_url=job_url,
                filename=f"lettre_{letter_id}.pdf",
                file_path=file_path,
                file_size=len(pdf_content),
                raw_text=letter_text,
                llm_provider=llm_provider
            )
            
            # Sauvegarder en base
            letter_repo.create(letter)
            print(f"✅ Lettre sauvegardée en base: {letter_id}")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde PostgreSQL: {e}")
            # Continue même si la sauvegarde échoue
        
        # Stocker dans legacy storage (pour compatibilité)
        if "letters" not in storage:
            storage["letters"] = {}
        storage["letters"][letter_id] = result_path
        
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


@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    request: TextGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Vérifier que le CV est fourni et existe
        if not request.cv_id:
            raise HTTPException(status_code=400, detail="Aucun CV sélectionné. Veuillez d'abord télécharger et sélectionner un CV.")
        
        # Récupérer le CV depuis PostgreSQL
        cv_repo = PostgresCvRepository(db)
        cv = cv_repo.get_by_id(request.cv_id)
        
        # Vérifier que le CV appartient à l'utilisateur
        if cv and cv.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès interdit à ce CV")
        
        if not cv:
            # Fallback vers legacy storage si besoin
            if request.cv_id not in storage["cvs"]:
                raise HTTPException(status_code=404, detail="CV non trouvé. Veuillez sélectionner un CV valide.")
            cv_path = Path(storage["cvs"][request.cv_id]["path"])
        else:
            cv_path = Path(cv.file_path)

        if not cv_path.exists():
            raise HTTPException(status_code=404, detail="Fichier CV introuvable.")

        document_parser = PyPdfParser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = GoogleGeminiLlm() if request.llm_provider.lower() == "gemini" else OpenAiLlm()
        
        cv_text = document_parser.parse_document(input_path=str(cv_path))

        job_offer_text = ""
        try:
            job_offer_text = job_fetcher.fetch(url=request.job_url)
        except Exception:
            pass

        if request.text_type == "why_join":
            prompt = f"Vous êtes un assistant expert en communication RH.\n\nContexte (CV) :\n{cv_text}\n\nOffre d'emploi :\n{job_offer_text}\n\nTâche : Rédigez une réponse concise (3-6 phrases) à la question : 'Expliquez-nous pourquoi vous souhaitez nous rejoindre.' Utilisez un ton professionnel et motivé. Ne fournissez que le texte de la réponse, sans préambule ni signature."
        else:
            prompt = f"Vous êtes un assistant expert.\n\nContexte (CV) :\n{cv_text}\n\nOffre d'emploi :\n{job_offer_text}\n\nTâche : Rédigez un court paragraphe adapté à l'offre."

        generated = llm.send_to_llm(prompt)
        return TextGenerationResponse(status="success", text=generated)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur génération texte: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    if "letters" not in storage or file_id not in storage["letters"]:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    file_path = storage["letters"][file_id]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Le fichier n'existe plus")
    
    return FileResponse(path=file_path, filename="lettre_motivation.pdf", media_type="application/pdf")

@app.get("/download-letter/{letter_id}")
async def download_letter(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Télécharge une lettre de motivation depuis PostgreSQL"""
    try:
        letter_repo = PostgresMotivationalLetterRepository(db)
        file_storage = LocalFileStorage()
        
        # Récupérer la lettre depuis la base
        letter = letter_repo.get_by_id(letter_id)
        
        if not letter:
            raise HTTPException(status_code=404, detail="Lettre non trouvée")
        
        # Vérifier que la lettre appartient à l'utilisateur
        if letter.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès interdit à cette lettre")
        
        # Récupérer le chemin du fichier
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
        print(f"❌ Erreur téléchargement lettre: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")

@app.delete("/cleanup/{cv_id}")
async def cleanup_files(
    cv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cv_repo = PostgresCvRepository(db)
        cv = cv_repo.get_by_id(cv_id)
        
        # Vérifier que le CV appartient à l'utilisateur
        if cv and cv.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès interdit à ce CV")
        
        if cv:
            # Supprimer le fichier physique
            try:
                file_storage.delete_cv(cv_id)
            except:
                # Si file_storage échoue, essayer legacy
                if cv_id in storage["cvs"]:
                    cv_path = Path(storage["cvs"][cv_id]["path"])
                    if cv_path.exists():
                        os.remove(cv_path)
            
            # Supprimer de PostgreSQL
            cv_repo.delete(cv_id)
        
        # Supprimer du legacy storage
        if cv_id in storage["cvs"]:
            del storage["cvs"][cv_id]
        
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
