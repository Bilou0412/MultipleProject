from dataclasses import dataclass
from datetime import datetime
from typing import List
from domain.entities.player import Player
from domain.entities.champion import ChampionStatistics

@dataclass
class StatsSummary:
    """Résumé statistique complet"""
    player: Player
    total_games: int
    wins: int
    win_rate: float
    average_kda: float
    top_champions: List[ChampionStatistics]
    last_updated: datetime