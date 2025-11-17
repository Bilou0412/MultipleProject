from domain.entities.document import Document
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MotivationalLetter(Document):
    """
    Représente une lettre de motivation avec métadonnées
    """
    id: Optional[str] = None
    user_id: Optional[str] = None
    cv_id: Optional[str] = None  # Référence au CV utilisé
    job_offer_url: Optional[str] = None
    filename: str = ""
    file_path: str = ""  # Chemin de stockage du fichier PDF
    file_size: int = 0
    raw_text: str = ""  # Texte extrait de la lettre
    llm_provider: str = "openai"  # openai, gemini, etc.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
