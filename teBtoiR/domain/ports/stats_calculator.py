from abc import ABC, abstractmethod
from typing import List
from domain.entities.match import Match

class StatisticsCalculator(ABC):
    """Calcule les statistiques à partir des données brutes"""
    
    @abstractmethod
    def calculate_overall_stats(self, matches: List[Match], puuid: str) -> dict:
        """Calcule les statistiques globales (winrate, KDA moyen, etc.)"""
        pass
    
    @abstractmethod
    def calculate_win_rate(self, wins: int, losses: int) -> float:
        """Calcule le taux de victoire"""
        pass