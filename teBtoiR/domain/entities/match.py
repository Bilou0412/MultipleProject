from datetime import datetime
from dataclasses import dataclass
from domain.entities.player_match_perf import PlayerMatchPerformance

@dataclass
class Match:
    """Une partie jouée"""
    match_id: str
    game_creation: datetime
    game_duration: int
    player_performance : PlayerMatchPerformance