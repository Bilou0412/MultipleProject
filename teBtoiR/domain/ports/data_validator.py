from abc import ABC, abstractmethod

class DataValidator(ABC):
    """Valide et normalise les données d'entrée"""
    
    @abstractmethod
    def validate_riot_id(self, riot_id: str) -> bool:
        """Vérifie que le Riot ID est au format GameName#TagLine"""
        pass
    
    @abstractmethod
    def parse_riot_id(self, riot_id: str) -> tuple[str, str]:
        """Parse un Riot ID en (game_name, tag_line)"""
        pass
    
    @abstractmethod
    def validate_region(self, region: str) -> bool:
        """Vérifie que la région est supportée"""
        pass
    
    @abstractmethod
    def normalize_riot_id(self, riot_id: str) -> str:
        """Normalise le Riot ID (espaces, casse)"""
        pass