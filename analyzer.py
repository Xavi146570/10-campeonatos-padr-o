import os

class MatchAnalyzer:
    def __init__(self, league_config):
        self.config = league_config

    def meets_highlight_criteria(self, home_stats, away_stats, home_ht_stats=None, away_ht_stats=None):
        criteria = self.config["criteria"]
        
        min_avg_ft = criteria["min_team_avg_goals"]
        min_sample = criteria["min_sample_games"]
        
        home_avg_ft, home_sample = home_stats
        away_avg_ft, away_sample = away_stats
        
        if home_sample < min_sample or away_sample < min_sample:
            return False, "insufficient_sample"
        
        ft_criteria_met = (home_avg_ft and home_avg_ft >= min_avg_ft) or (away_avg_ft and away_avg_ft >= min_avg_ft)
        
        ht_criteria_met = False
        if home_ht_stats and away_ht_stats:
            min_avg_ht = criteria.get("min_team_avg_goals_ht", 1.0)
            
            home_avg_ht, home_ht_sample = home_ht_stats
            away_avg_ht, away_ht_sample = away_ht_stats
            
            if home_ht_sample >= 3 and away_ht_sample >= 3:
                ht_criteria_met = (home_avg_ht and home_avg_ht >= min_avg_ht) or (away_avg_ht and away_avg_ht >= min_avg_ht)
        
        if ft_criteria_met and ht_criteria_met:
            return True, "both_criteria"
        elif ft_criteria_met:
            return True, "fulltime_criteria"
        elif ht_criteria_met:
            return True, "halftime_criteria"
        else:
            return False, "no_criteria_met"

    def prepare_match_data(self, fixture, home_stats, away_stats, league_real_stats=None, 
                          home_ht_stats=None, away_ht_stats=None, criteria_type="fulltime_criteria"):
        criteria = self.config["criteria"]
        
        home_avg_ft, home_sample = home_stats
        away_avg_ft, away_sample = away_stats
        min_ft = criteria["min_team_avg_goals"]
        
        home_avg_ht = home_ht_stats[0] if home_ht_stats else None
        away_avg_ht = away_ht_stats[0] if away_ht_stats else None
        min_ht = criteria.get("min_team_avg_goals_ht", 1.0)
        
        return {
            "fixture": fixture,
            "home_team": fixture["teams"]["home"]["name"],
            "away_team": fixture["teams"]["away"]["name"],
            "match_time": fixture["fixture"]["date"],
            
            "home_avg": home_avg_ft or 0,
            "away_avg": away_avg_ft or 0,
            "home_meets_criteria": (home_avg_ft or 0) >= min_ft,
            "away_meets_criteria": (away_avg_ft or 0) >= min_ft,
            "min_threshold": min_ft,
            
            "home_avg_ht": home_avg_ht or 0,
            "away_avg_ht": away_avg_ht or 0,
            "home_meets_ht": (home_avg_ht or 0) >= min_ht if home_avg_ht else False,
            "away_meets_ht": (away_avg_ht or 0) >= min_ht if away_avg_ht else False,
            "min_threshold_ht": min_ht,
            "has_ht_data": home_ht_stats is not None and away_ht_stats is not None,
            
            "league_config": self.config,
            "league_real_stats": league_real_stats,
            "criteria_type": criteria_type
        }
