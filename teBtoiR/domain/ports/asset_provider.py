from abc import ABC, abstractmethod

class AssetProvider(ABC):
    """Fournit les URLs des ressources visuelles"""
    
    @abstractmethod
    def get_champion_icon_url(self, champion_name: str) -> str:
        """Récupère l'URL de l'icône d'un champion"""
        pass
    
    @abstractmethod
    def get_rank_icon_url(self, tier: str, division: str) -> str:
        """Récupère l'URL de l'icône de rang"""
        pass
    
    @abstractmethod
    def get_profile_icon_url(self, icon_id: str) -> str:
        """Récupère l'URL de l'icône de profil"""
        pass
