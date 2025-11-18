"""
Port pour la gestion des utilisateurs
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.user import User


class UserRepository(ABC):
    """
    Interface pour la persistance des utilisateurs
    """
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Crée un nouvel utilisateur"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        pass
    
    @abstractmethod
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Récupère un utilisateur par son Google ID"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Met à jour un utilisateur"""
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Supprime un utilisateur"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[User]:
        """Liste tous les utilisateurs"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[User]:
        """Récupère tous les utilisateurs (alias de list_all)"""
        pass
