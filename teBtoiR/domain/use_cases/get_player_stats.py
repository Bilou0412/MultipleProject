from datetime import datetime
from domain.entities.stats_summary import StatsSummary
from domain.ports.player_data_provider import PlayerDataProvider
from domain.ports.data_validator import DataValidator
from domain.ports.stats_calculator import StatisticsCalculator
from domain.ports.cache_manager import CacheManager



class GetPlayerStatsUseCase:
    """Récupère les statistiques d'un joueur"""
    
    def __init__(
        self,
        player_provider: PlayerDataProvider,
        validator: DataValidator,
        calculator: StatisticsCalculator,
        cache: CacheManager
    ):
        self.player_provider = player_provider
        self.validator = validator
        self.calculator = calculator
        self.cache = cache
    
    def execute(self, riot_id: str, region: str) -> StatsSummary:
        """Récupère et calcule les stats d'un joueur"""
        
        # 1. Valider
        if not self.validator.validate_riot_id(riot_id):
            raise ValueError(f"Riot ID invalide: {riot_id}")
        
        # 2. Parser
        game_name, tag_line = self.validator.parse_riot_id(riot_id)
        
        # 3. Cache ?
        cache_key = f"stats:{region}:{riot_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 4. Récupérer les données
        player = self.player_provider.get_player_by_riot_id(game_name, tag_line, region)
        player.rankings = self.player_provider.get_player_ranking(player.puuid, region)
        
        # 5. Récupérer les matchs
        match_ids = self.player_provider.get_match_history(player.puuid, region, 20)
        matches = [
            self.player_provider.get_match_details(mid, region) 
            for mid in match_ids
        ]
        
        # 6. Calculer les stats
        champion_stats = self.calculator.calculate_champion_stats(matches, player.puuid)
        overall = self.calculator.calculate_overall_stats(matches, player.puuid)
        
        # 7. Construire le résumé
        summary = StatsSummary(
            player=player,
            total_games=overall['total_games'],
            wins=overall['wins'],
            win_rate=overall['win_rate'],
            average_kda=overall['average_kda'],
            top_champions=champion_stats[:5],
            last_updated=datetime.now()
        )
        
        # 8. Mettre en cache
        self.cache.set(cache_key, summary, ttl=300)
        
        return summary