import os

# 10 principais campeonatos (exceto Eredivisie)
LEAGUE_CONFIGS = {
    "ENG1": {
        "api_id": 39, "name": "Premier League", "timezone": "Europe/London",
        "criteria": {"min_team_avg_goals": 2.30, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.75, "btts_rate": 55, "over25_rate": 60, "over35_rate": 30, "second_half_share": 52},
        "peak_minutes": {"60": 16, "75": 17, "85": 22}, "peak_window": {"start": 61, "end": 75, "prob_min": 17}
    },
    "ESP1": {
        "api_id": 140, "name": "LaLiga", "timezone": "Europe/Madrid",
        "criteria": {"min_team_avg_goals": 2.20, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.65, "btts_rate": 52, "over25_rate": 55, "over35_rate": 28, "second_half_share": 54},
        "peak_minutes": {"60": 15, "75": 18, "85": 23}, "peak_window": {"start": 60, "end": 75, "prob_min": 18}
    },
    "ITA1": {
        "api_id": 135, "name": "Serie A", "timezone": "Europe/Rome",
        "criteria": {"min_team_avg_goals": 2.15, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.60, "btts_rate": 50, "over25_rate": 52, "over35_rate": 26, "second_half_share": 55},
        "peak_minutes": {"60": 14, "75": 19, "85": 24}, "peak_window": {"start": 61, "end": 75, "prob_min": 19}
    },
    "GER1": {
        "api_id": 78, "name": "Bundesliga", "timezone": "Europe/Berlin",
        "criteria": {"min_team_avg_goals": 2.40, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 3.00, "btts_rate": 58, "over25_rate": 62, "over35_rate": 35, "second_half_share": 53},
        "peak_minutes": {"60": 17, "75": 18, "85": 23}, "peak_window": {"start": 61, "end": 75, "prob_min": 18}
    },
    "FRA1": {
        "api_id": 61, "name": "Ligue 1", "timezone": "Europe/Paris",
        "criteria": {"min_team_avg_goals": 2.10, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.70, "btts_rate": 53, "over25_rate": 57, "over35_rate": 29, "second_half_share": 52},
        "peak_minutes": {"60": 15, "75": 17, "85": 22}, "peak_window": {"start": 60, "end": 75, "prob_min": 17}
    },
    "POR1": {
        "api_id": 94, "name": "Primeira Liga", "timezone": "Europe/Lisbon",
        "criteria": {"min_team_avg_goals": 2.25, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.80, "btts_rate": 56, "over25_rate": 60, "over35_rate": 31, "second_half_share": 53},
        "peak_minutes": {"60": 16, "75": 18, "85": 23}, "peak_window": {"start": 61, "end": 75, "prob_min": 18}
    },
    "BRA1": {
        "api_id": 71, "name": "Brasileirão Série A", "timezone": "America/Sao_Paulo",
        "criteria": {"min_team_avg_goals": 2.00, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.50, "btts_rate": 50, "over25_rate": 50, "over35_rate": 25, "second_half_share": 52},
        "peak_minutes": {"60": 14, "75": 16, "85": 21}, "peak_window": {"start": 60, "end": 75, "prob_min": 16}
    },
    "ARG1": {
        "api_id": 128, "name": "Liga Profesional", "timezone": "America/Argentina/Buenos_Aires",
        "criteria": {"min_team_avg_goals": 1.90, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.35, "btts_rate": 48, "over25_rate": 48, "over35_rate": 22, "second_half_share": 51},
        "peak_minutes": {"60": 13, "75": 15, "85": 20}, "peak_window": {"start": 60, "end": 75, "prob_min": 15}
    },
    "BEL1": {
        "api_id": 144, "name": "Jupiler Pro League", "timezone": "Europe/Brussels",
        "criteria": {"min_team_avg_goals": 2.35, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.90, "btts_rate": 57, "over25_rate": 59, "over35_rate": 33, "second_half_share": 54},
        "peak_minutes": {"60": 16, "75": 18, "85": 24}, "peak_window": {"start": 61, "end": 75, "prob_min": 18}
    },
    "TUR1": {
        "api_id": 203, "name": "Süper Lig", "timezone": "Europe/Istanbul",
        "criteria": {"min_team_avg_goals": 2.20, "min_sample_games": 4},
        "historical_minimums": {"avg_goals_per_match": 2.75, "btts_rate": 54, "over25_rate": 56, "over35_rate": 30, "second_half_share": 53},
        "peak_minutes": {"60": 15, "75": 17, "85": 22}, "peak_window": {"start": 60, "end": 75, "prob_min": 17}
    }
}
