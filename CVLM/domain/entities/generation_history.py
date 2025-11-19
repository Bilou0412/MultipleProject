"""
Entité GenerationHistory - Représente une génération de lettre (PDF ou texte)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GenerationHistory:
    """
    Historique des générations de lettres de motivation
    Illimité pour engagement utilisateur maximal (modèle SaaS)
    """
    id: Optional[str]
    user_id: str
    type: str  # 'pdf' ou 'text'
    
    # Informations sur l'offre d'emploi
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_url: Optional[str] = None
    
    # Informations sur la génération
    cv_filename: Optional[str] = None
    cv_id: Optional[str] = None
    file_path: Optional[str] = None  # Chemin du PDF (NULL si expiré)
    text_content: Optional[str] = None  # Contenu texte si type='text'
    
    # Statut
    status: str = 'success'  # 'success' ou 'error'
    error_message: Optional[str] = None
    
    # Dates
    created_at: Optional[datetime] = None
    file_expires_at: Optional[datetime] = None  # created_at + 90 jours pour PDFs
    
    def is_file_expired(self) -> bool:
        """Vérifie si le fichier PDF a expiré"""
        if not self.file_expires_at or self.type != 'pdf':
            return False
        return datetime.now() > self.file_expires_at
    
    def is_downloadable(self) -> bool:
        """Vérifie si le fichier est téléchargeable"""
        return (
            self.type == 'pdf' and 
            self.file_path is not None and 
            not self.is_file_expired()
        )
    
    def days_until_expiration(self) -> Optional[int]:
        """Retourne le nombre de jours avant expiration (si applicable)"""
        if not self.file_expires_at or self.type != 'pdf':
            return None
        
        delta = self.file_expires_at - datetime.now()
        return max(0, delta.days)
