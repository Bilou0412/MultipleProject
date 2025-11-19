"""
Port (interface) pour le repository d'historique des générations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from domain.entities.generation_history import GenerationHistory


class GenerationHistoryRepository(ABC):
    """Interface pour la persistance de l'historique des générations"""
    
    @abstractmethod
    def create(self, history: GenerationHistory) -> GenerationHistory:
        """Crée une nouvelle entrée dans l'historique"""
        pass
    
    @abstractmethod
    def get_by_id(self, history_id: str) -> Optional[GenerationHistory]:
        """Récupère une entrée par son ID"""
        pass
    
    @abstractmethod
    def get_user_history(
        self, 
        user_id: str, 
        page: int = 1, 
        per_page: int = 50,
        search: Optional[str] = None,
        type_filter: Optional[str] = None,
        period_days: Optional[int] = None
    ) -> Dict:
        """
        Récupère l'historique d'un utilisateur avec pagination et filtres
        Retourne: {total, page, per_page, pages, items}
        """
        pass
    
    @abstractmethod
    def get_user_stats(self, user_id: str) -> Dict:
        """Récupère les statistiques d'un utilisateur"""
        pass
    
    @abstractmethod
    def update(self, history: GenerationHistory) -> GenerationHistory:
        """Met à jour une entrée (pour régénération)"""
        pass
    
    @abstractmethod
    def delete(self, history_id: str) -> None:
        """Supprime une entrée de l'historique"""
        pass
    
    @abstractmethod
    def get_expired_files(self) -> List[GenerationHistory]:
        """Récupère les entrées avec fichiers expirés (pour cleanup)"""
        pass
    
    @abstractmethod
    def get_all_with_pagination(
        self,
        page: int = 1,
        per_page: int = 50,
        user_filter: Optional[str] = None
    ) -> Dict:
        """Récupère tout l'historique (admin) avec pagination"""
        pass
