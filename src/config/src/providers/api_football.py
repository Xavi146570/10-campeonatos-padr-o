import os
import time
import requests
from datetime import datetime, timedelta
from dateutil import tz

class ApiFootballError(Exception):
    pass

class ApiFootballClient:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {"x-apisports-key": self.api_key}
        
        if not self.api_key:
            raise ApiFootballError("API_FOOTBALL_KEY não configurada")

    def _make_request(self, endpoint, params=None, retries=3):
        """Faz requisição com retry automático"""
        for attempt in range(retries):
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limit atingido. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                return data.get("response", [])
                
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise ApiFootballError(f"Erro na API após {retries} tentativas: {e}")
                time.sleep((attempt + 1) * 2)
                
        raise ApiFootballError("Limite de tentativas excedido")

    def get_current_season(self, league_id):
        """Determina a temporada atual para uma liga"""
        now = datetime.now()
        # Para ligas europeias, temporada geralmente começa em julho/agosto
        if now.month >= 7:
            return now.year
        return now.year - 1

    def get_fixtures_today(self, league_id, timezone_name):
        """Busca jogos de hoje para uma liga"""
        try:
            # Converter para timezone da liga
            league_tz = tz.gettz(timezone_name)
            today = datetime.now(league_tz).date()
            
            params = {
                "league": league_id,
                "season": self.get_current_season(league_id),
                "date": today.strftime("%Y-%m-%d"),
                "timezone": timezone_name
            }
            
            fixtures = self._make_request("/fixtures", params)
            # Filtrar apenas jogos que ainda não começaram
            return [f for f in fixtures if f["fixture"]["status"]["short"] in ["NS", "TBD"]]
            
        except Exception as e:
            print(f"Erro ao buscar fixtures: {e}")
            return []

    def get_team_recent_avg_goals(self, team_id, last_n=4):
        """Calcula média de gols nos últimos N jogos de um time"""
        try:
            params = {
                "team": team_id,
                "last": last_n,
                "status": "FT"  # Apenas jogos finalizados
            }
            
            fixtures = self._make_request("/fixtures", params)
            
            if not fixtures:
                return None, 0
                
            goals_scored = []
            for fixture in fixtures:
                home_id = fixture["teams"]["home"]["id"]
                away_id = fixture["teams"]["away"]["id"]
                home_goals = fixture["goals"]["home"]
                away_goals = fixture["goals"]["away"]
                
                if home_goals is None or away_goals is None:
                    continue
                    
                if team_id == home_id:
                    goals_scored.append(home_goals)
                elif team_id == away_id:
                    goals_scored.append(away_goals)
                    
            if not goals_scored:
                return None, 0
                
            avg_goals = sum(goals_scored) / len(goals_scored)
            return round(avg_goals, 2), len(goals_scored)
            
        except Exception as e:
            print(f"Erro ao buscar stats do time {team_id}: {e}")
            return None, 0
