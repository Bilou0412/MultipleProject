"""
Entité PromoCode - Représente un code promotionnel
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PromoCode:
    """Code promotionnel donnant des crédits"""
    
    code: str
    pdf_credits: int
    text_credits: int
    max_uses: int  # Nombre maximum d'utilisations (0 = illimité)
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def can_be_used(self) -> bool:
        """Vérifie si le code peut être utilisé"""
        if not self.is_active:
            return False
        
        # Vérifier expiration
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        # Vérifier limite d'utilisation
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def increment_usage(self) -> None:
        """Incrémente le compteur d'utilisation"""
        self.current_uses += 1
