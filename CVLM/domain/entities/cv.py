from domain.entities.document import Document
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Cv(Document):
    """
    Représente un CV avec métadonnées pour la persistance
    """
    id: Optional[str] = None
    user_id: Optional[str] = None
    filename: str = ""
    file_path: str = ""  # Chemin de stockage du fichier
    file_size: int = 0
    raw_text: str = ""  # Texte extrait du CV
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
