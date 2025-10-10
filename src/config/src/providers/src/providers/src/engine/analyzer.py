class MatchAnalyzer:
    def __init__(self, league_config):
        self.config = league_config

    def meets_highlight_criteria(self, home_stats, away_stats):
        """Verifica se o jogo atende aos critérios de destaque"""
        min_avg = self.config["criteria"]["min_team_avg_goals"]
        min_sample = self.config["criteria"]["min_sample_games"]
        
        home_avg, home_sample = home_stats
        away_avg, away_sample = away_stats
        
        # Verificar se temos dados suficientes
        if (home_sample < min_sample or away_sample < min_sample):
            return False
            
        # Pelo menos uma equipe deve ter média >= threshold
        return (home_avg and home_avg >= min_avg) or (away_avg and away_avg >= min_avg)

    def prepare_match_data(self, fixture, home_stats, away_stats):
        """Prepara dados do jogo para formatação"""
        home_avg, home_sample = home_stats
        away_avg, away_sample = away_stats
        min_threshold = self.config["criteria"]["min_team_avg_goals"]
        
        return {
            "fixture": fixture,
            "home_team": fixture["teams"]["home"]["name"],
            "away_team": fixture["teams"]["away"]["name"],
            "match_time": fixture["fixture"]["date"],
            "home_avg": home_avg or 0,
            "away_avg": away_avg or 0,
            "home_meets_criteria": (home_avg or 0) >= min_threshold,
            "away_meets_criteria": (away_avg or 0) >= min_threshold,
            "min_threshold": min_threshold,
            "league_config": self.config
        }
