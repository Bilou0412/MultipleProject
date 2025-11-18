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
    Système de crédits : 10 crédits PDF + 10 crédits texte pour la version d'essai
    """
    id: Optional[str]
    email: str
    google_id: str
    name: str
    profile_picture_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Crédits d'essai (trial credits)
    pdf_credits: int = 10  # Nombre de lettres PDF générables
    text_credits: int = 10  # Nombre de générations de texte
    is_admin: bool = False  # Droit administrateur pour gérer les codes promo et utilisateurs
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def has_pdf_credits(self) -> bool:
        """Vérifie si l'utilisateur a encore des crédits PDF"""
        return self.pdf_credits > 0
    
    def has_text_credits(self) -> bool:
        """Vérifie si l'utilisateur a encore des crédits texte"""
        return self.text_credits > 0
    
    def use_pdf_credit(self) -> bool:
        """Utilise un crédit PDF. Retourne True si succès."""
        if self.has_pdf_credits():
            self.pdf_credits -= 1
            return True
        return False
    
    def use_text_credit(self) -> bool:
        """Utilise un crédit texte. Retourne True si succès."""
        if self.has_text_credits():
            self.text_credits -= 1
            return True
        return False
