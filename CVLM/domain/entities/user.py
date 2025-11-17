"""
Entité User - Représente un utilisateur de l'application
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Représente un utilisateur avec authentification Google
    """
    id: Optional[str]
    email: str
    google_id: str
    name: str
    profile_picture_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
