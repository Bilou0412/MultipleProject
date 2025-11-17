"""
Port pour la gestion des CVs
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.cv import Cv


class CvRepository(ABC):
    """
    Interface pour la persistance des CVs
    """
    
    @abstractmethod
    def create(self, cv: Cv) -> Cv:
        """Crée un nouveau CV"""
        pass
    
    @abstractmethod
    def get_by_id(self, cv_id: str) -> Optional[Cv]:
        """Récupère un CV par son ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> List[Cv]:
        """Récupère tous les CVs d'un utilisateur"""
        pass
    
    @abstractmethod
    def update(self, cv: Cv) -> Cv:
        """Met à jour un CV"""
        pass
    
    @abstractmethod
    def delete(self, cv_id: str) -> bool:
        """Supprime un CV"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Cv]:
        """Liste tous les CVs"""
        pass
