from abc import ABC, abstractmethod
from typing import Optional


class CacheManager(ABC):
    """Gère la mise en cache des données"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[any]:
        """Récupère des données du cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, data: any, ttl: int) -> None:
        """Stocke des données dans le cache avec une durée de vie (secondes)"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Supprime une entrée du cache"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe et est valide"""
        pass