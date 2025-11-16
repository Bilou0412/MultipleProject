"""
API FastAPI pour l'extension navigateur CVLM
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import Optional
from pathlib import Path
import PyPDF2

from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.Google_gemini_api import LlmGemini
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import LlmOpenAI
from infrastructure.adapters.weasyprint_generator import WeasyPrintGgenerator

# Configuration
app = FastAPI(title="CVLM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

storage = {"cvs": {}, "letters": {}}

# === Modèles ===

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
    return {"status": "healthy"}

@app.post("/upload-cv", response_model=UploadResponse)
async def upload_cv(cv_file: UploadFile = File(...)):
    if not cv_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format PDF")
    
    try:
        cv_id = str(uuid.uuid4())
        file_path = TEMP_DIR / f"cv_{cv_id}.pdf"
        
        with open(file_path, "wb") as f:
            content = await cv_file.read()
            f.write(content)
        
        from datetime import datetime
        storage["cvs"][cv_id] = {
            "path": str(file_path),
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
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.get("/list-cvs", response_model=CvListResponse)
async def list_cvs():
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

@app.post("/generate-cover-letter", response_model=GenerationResponse)
async def generate_cover_letter(
    cv_id: str = Form(...),
    job_url: str = Form(...),
    llm_provider: str = Form("openai"),
    pdf_generator: str = Form("fpdf")
):
    if cv_id not in storage["cvs"]:
        raise HTTPException(status_code=404, detail="CV non trouvé. Veuillez l'uploader.")
    
    cv_path = Path(storage["cvs"][cv_id]["path"])
    if not cv_path.exists():
        raise HTTPException(status_code=404, detail="Fichier CV introuvable sur le disque.")
    
    try:
        document_parser = Pypdf_parser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = LlmGemini() if llm_provider.lower() == "gemini" else LlmOpenAI()
        pdf_gen = WeasyPrintGgenerator() if pdf_generator.lower() == "weasyprint" else Fpdf_generator()
        
        use_case = AnalyseCvOffer(
            job_offer_fetcher=job_fetcher,
            document_parser=document_parser,
            llm=llm,
            pdf_generator=pdf_gen
        )
        
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
        
        if "letters" not in storage:
            storage["letters"] = {}
        storage["letters"][letter_id] = result_path
        
        return GenerationResponse(
            status="success",
            file_id=letter_id,
            download_url=f"/download/{letter_id}",
            letter_text=letter_text
        )
    except Exception as e:
        print(f"❌ Erreur génération: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    try:
        # Vérifier que le CV est fourni et existe
        if not request.cv_id:
            raise HTTPException(status_code=400, detail="Aucun CV sélectionné. Veuillez d'abord télécharger et sélectionner un CV.")
        
        if request.cv_id not in storage["cvs"]:
            raise HTTPException(status_code=404, detail="CV non trouvé. Veuillez sélectionner un CV valide.")

        document_parser = Pypdf_parser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = LlmGemini() if request.llm_provider.lower() == "gemini" else LlmOpenAI()

        # Parse le CV (obligatoire maintenant)
        cv_path = Path(storage["cvs"][request.cv_id]["path"])
        if not cv_path.exists():
            raise HTTPException(status_code=404, detail="Fichier CV introuvable.")
        
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

@app.delete("/cleanup/{cv_id}")
async def cleanup_files(cv_id: str):
    if cv_id not in storage["cvs"]:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    cv_path = Path(storage["cvs"][cv_id]["path"])
    if cv_path.exists():
        try:
            os.remove(cv_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impossible de supprimer: {e}")
    
    del storage["cvs"][cv_id]
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage de l'API CVLM sur http://localhost:8000")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
