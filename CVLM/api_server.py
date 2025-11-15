"""
API FastAPI pour l'extension navigateur CVLM
Respecte l'architecture Clean Architecture existante
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import tempfile
import os
import uuid
from typing import Optional
from pathlib import Path

# Import des use cases et adapters existants
from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.Google_gemini_api import LlmGemini
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import LlmOpenAI
from infrastructure.adapters.weasyprint_generator import WeasyPrintGgenerator

# Configuration
app = FastAPI(
    title="CVLM API",
    description="API pour le générateur de lettres de motivation",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: limiter aux origines spécifiques
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dossiers pour les fichiers temporaires
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Stockage en mémoire (en production: utiliser Redis/Database)
storage = {
    "cvs": {},      # cv_id -> file_path
    "letters": {}   # letter_id -> file_path
}

# === Modèles Pydantic ===

class UploadResponse(BaseModel):
    status: str
    cv_id: str
    filename: str
    message: str

class GenerationRequest(BaseModel):
    cv_id: str
    job_url: str
    llm_provider: str = "openai"
    pdf_generator: str = "fpdf"

class GenerationResponse(BaseModel):
    status: str
    message: str
    file_id: str
    download_url: str

class ErrorResponse(BaseModel):
    detail: str

# === Endpoints ===

@app.get("/")
def root():
    """Point d'entrée de l'API"""
    return {
        "name": "CVLM API",
        "version": "1.0.0",
        "description": "Générateur de lettres de motivation",
        "endpoints": {
            "health": "GET /health",
            "upload_cv": "POST /upload-cv",
            "generate": "POST /generate-cover-letter",
            "download": "GET /download/{file_id}",
            "cleanup": "DELETE /cleanup/{cv_id}"
        }
    }

@app.get("/health")
def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "service": "CVLM API",
        "temp_dir": str(TEMP_DIR),
        "output_dir": str(OUTPUT_DIR)
    }

@app.post("/upload-cv", response_model=UploadResponse)
async def upload_cv(cv_file: UploadFile = File(...)):
    """
    Upload d'un CV (PDF uniquement)
    Retourne un ID unique pour référencer ce CV
    """
    # Validation du fichier
    if not cv_file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format PDF"
        )
    
    try:
        # Génération d'un ID unique
        cv_id = str(uuid.uuid4())
        
        # Sauvegarde du fichier
        file_path = TEMP_DIR / f"cv_{cv_id}.pdf"
        
        with open(file_path, "wb") as f:
            content = await cv_file.read()
            f.write(content)
        
        # Stockage de la référence
        storage["cvs"][cv_id] = str(file_path)
        
        return UploadResponse(
            status="success",
            cv_id=cv_id,
            filename=cv_file.filename,
            message="CV uploadé avec succès"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload: {str(e)}"
        )

@app.post("/generate-cover-letter", response_model=GenerationResponse)
async def generate_cover_letter(
    cv_id: str = Form(...),
    job_url: str = Form(...),
    llm_provider: str = Form("openai"),
    pdf_generator: str = Form("fpdf")
):
    """
    Génère une lettre de motivation
    
    Args:
        cv_id: ID du CV uploadé
        job_url: URL de l'offre d'emploi
        llm_provider: "openai" ou "gemini"
        pdf_generator: "fpdf" ou "weasyprint"
    """
    # Détermination du chemin du CV sur disque (robuste au redémarrage du serveur)
    cv_path = TEMP_DIR / f"cv_{cv_id}.pdf"

    # Si le fichier n'existe pas sur le disque, on renvoie 404
    if not cv_path.exists():
        raise HTTPException(
            status_code=404,
            detail="CV non trouvé sur le serveur. Veuillez d'abord uploader votre CV."
        )
    
    try:
        # === Instanciation des adapters (Clean Architecture) ===
        
        # Parser CV
        document_parser = Pypdf_parser()
        
        # Fetcher offre d'emploi
        job_fetcher = WelcomeToTheJungleFetcher()
        
        # Service LLM
        if llm_provider.lower() == "gemini":
            llm = LlmGemini()
        else:
            llm = LlmOpenAI()
        
        # Générateur PDF
        if pdf_generator.lower() == "weasyprint":
            pdf_gen = WeasyPrintGgenerator()
        else:
            pdf_gen = Fpdf_generator()
        
        # === Création du Use Case ===
        use_case = AnalyseCvOffer(
            job_offer_fetcher=job_fetcher,
            document_parser=document_parser,
            llm=llm,
            pdf_generator=pdf_gen
        )
        
        # === Exécution ===
        letter_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"lettre_{letter_id}.pdf"
        
        result_path = use_case.execute(
            cv_path=cv_path,
            jo_path=job_url,
            output_path=str(output_path),
            use_scraper=True
        )
        
        # Stockage de la lettre générée
        storage["letters"][letter_id] = result_path
        
        return GenerationResponse(
            status="success",
            message="Lettre de motivation générée avec succès",
            file_id=letter_id,
            download_url=f"/download/{letter_id}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération: {str(e)}"
        )

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Télécharge la lettre de motivation générée
    """
    if file_id not in storage["letters"]:
        raise HTTPException(
            status_code=404,
            detail="Fichier non trouvé"
        )
    
    file_path = storage["letters"][file_id]
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Le fichier n'existe plus sur le serveur"
        )
    
    return FileResponse(
        path=file_path,
        filename="lettre_motivation.pdf",
        media_type="application/pdf"
    )

@app.delete("/cleanup/{cv_id}")
async def cleanup_files(cv_id: str):
    """
    Nettoie les fichiers temporaires associés à un CV
    """
    # Calculer le chemin même si la table en mémoire a été perdue (ex: redémarrage)
    cv_path = TEMP_DIR / f"cv_{cv_id}.pdf"

    # Supprimer le fichier s'il existe
    if cv_path.exists():
        try:
            os.remove(cv_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impossible de supprimer le fichier: {e}")

    # Supprimer l'éventuelle référence en mémoire si elle existe
    if cv_id in storage["cvs"]:
        try:
            del storage["cvs"][cv_id]
        except Exception:
            pass

    # Toujours renvoyer succès (idempotent)
    return {
        "status": "success",
        "message": "Fichiers nettoyés avec succès"
    }

@app.post("/cleanup-all")
async def cleanup_all():
    """
    Nettoie tous les fichiers temporaires (Admin)
    """
    cleaned = {"cvs": 0, "letters": 0}
    
    # Nettoyage des CVs
    for cv_id, cv_path in list(storage["cvs"].items()):
        if os.path.exists(cv_path):
            os.remove(cv_path)
        del storage["cvs"][cv_id]
        cleaned["cvs"] += 1
    
    # Nettoyage des lettres
    for letter_id, letter_path in list(storage["letters"].items()):
        if os.path.exists(letter_path):
            os.remove(letter_path)
        del storage["letters"][letter_id]
        cleaned["letters"] += 1
    
    return {
        "status": "success",
        "message": "Tous les fichiers ont été nettoyés",
        "cleaned": cleaned
    }

@app.get("/stats")
async def get_stats():
    """
    Statistiques de l'API (Admin)
    """
    return {
        "cvs_in_storage": len(storage["cvs"]),
        "letters_in_storage": len(storage["letters"]),
        "temp_dir_size": sum(
            f.stat().st_size for f in TEMP_DIR.glob("**/*") if f.is_file()
        ),
        "output_dir_size": sum(
            f.stat().st_size for f in OUTPUT_DIR.glob("**/*") if f.is_file()
        )
    }

# === Point d'entrée ===

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Démarrage de l'API CVLM...")
    print("📍 URL: http://localhost:8000")
    print("📖 Documentation: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("\n💡 Appuyez sur CTRL+C pour arrêter\n")
    
    uvicorn.run(
        "api_server:app",  # Import string pour enable reload
        host="0.0.0.0",
        port=8000,
        reload=True  # Mode dev: recharge auto
    )