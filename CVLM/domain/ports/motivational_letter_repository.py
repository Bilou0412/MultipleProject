"""
Port pour la gestion des lettres de motivation
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.motivational_letter import MotivationalLetter


class MotivationalLetterRepository(ABC):
    """
    Interface pour la persistance des lettres de motivation
    """
    
    @abstractmethod
    def create(self, letter: MotivationalLetter) -> MotivationalLetter:
        """Crée une nouvelle lettre de motivation"""
        pass
    
    @abstractmethod
    def get_by_id(self, letter_id: str) -> Optional[MotivationalLetter]:
        """Récupère une lettre par son ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> List[MotivationalLetter]:
        """Récupère toutes les lettres d'un utilisateur"""
        pass
    
    @abstractmethod
    def get_by_cv_id(self, cv_id: str) -> List[MotivationalLetter]:
        """Récupère toutes les lettres générées à partir d'un CV"""
        pass
    
    @abstractmethod
    def update(self, letter: MotivationalLetter) -> MotivationalLetter:
        """Met à jour une lettre"""
        pass
    
    @abstractmethod
    def delete(self, letter_id: str) -> bool:
        """Supprime une lettre"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[MotivationalLetter]:
        """Liste toutes les lettres"""
        pass
