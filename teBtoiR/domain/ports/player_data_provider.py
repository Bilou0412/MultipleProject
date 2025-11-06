from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.ranking import Ranking
from domain.entities.player import Player
from domain.entities.match import Match

class PlayerDataProvider(ABC):
    """Récupère les données brutes depuis la source externe (Riot API)"""
    
    @abstractmethod
    def get_player_by_riot_id(self, game_name: str, tag_line: str, region: str) -> Player:
        """Récupère l'identité du joueur par son Riot ID (GameName#TagLine)"""
        pass
    
    @abstractmethod
    def get_player_ranking(self, puuid: str, region: str) -> List[Ranking]:
        """Récupère les classements du joueur (toutes les queues)"""
        pass
    
    @abstractmethod
    def get_match_history(self, puuid: str, region: str, count: int) -> List[str]:
        """Récupère la liste des IDs des dernières parties"""
        pass
    
    @abstractmethod
    def get_match_details(self, match_id: str, region: str) -> Match:
        """Récupère les détails complets d'une partie"""
        pass
