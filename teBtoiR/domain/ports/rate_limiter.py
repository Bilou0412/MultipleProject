from abc import ABC, abstractmethod

class RateLimiter(ABC):
    """Gère les limitations de requêtes vers l'API externe"""
    
    @abstractmethod
    def can_make_request(self, endpoint: str) -> bool:
        """Vérifie si une requête peut être effectuée"""
        pass
    
    @abstractmethod
    def record_request(self, endpoint: str) -> None:
        """Enregistre qu'une requête a été effectuée"""
        pass
    
    @abstractmethod
    def get_time_until_next_available(self, endpoint: str) -> int:
        """Retourne le temps d'attente (secondes) avant la prochaine requête"""
        pass