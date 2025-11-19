"""
Modèles Pydantic pour la génération de contenu
"""
from pydantic import BaseModel
from typing import Optional


class GenerationResponse(BaseModel):
    status: str
    file_id: str
    download_url: str
    letter_text: Optional[str] = None


class TextGenerationRequest(BaseModel):
    cv_id: str
    job_url: str
    text_type: str = "why_join"


class TextGenerationResponse(BaseModel):
    status: str
    text: str
