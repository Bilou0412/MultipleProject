"""
Port (interface) pour le repository des codes promo
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.promo_code import PromoCode


class PromoCodeRepository(ABC):
    """Interface pour la persistance des codes promo"""
    
    @abstractmethod
    def create(self, promo_code: PromoCode) -> PromoCode:
        """Crée un nouveau code promo"""
        pass
    
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[PromoCode]:
        """Récupère un code promo par son code"""
        pass
    
    @abstractmethod
    def get_all_active(self) -> List[PromoCode]:
        """Récupère tous les codes promo actifs"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[PromoCode]:
        """Récupère tous les codes promo (actifs et inactifs)"""
        pass
    
    @abstractmethod
    def update(self, promo_code: PromoCode) -> PromoCode:
        """Met à jour un code promo"""
        pass
    
    @abstractmethod
    def delete(self, code: str) -> None:
        """Supprime un code promo"""
        pass
