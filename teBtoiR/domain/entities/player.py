from dataclasses import dataclass
from typing import List
from domain.entities.ranking import Ranking

@dataclass
class Player:
    """Représente un joueur de League of Legends"""
    puuid: str
    game_name: str      # "Faker"
    tag_line: str       # "KR1"
    region: str         # "kr", "euw", "na"
    level: int
    profile_icon_id: str
    rankings: List[Ranking]
    
    @property
    def riot_id(self) -> str:
        """Retourne le Riot ID complet: GameName#TagLine"""
        return f"{self.game_name}#{self.tag_line}"