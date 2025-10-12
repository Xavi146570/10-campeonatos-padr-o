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
        
        # Otimizações
        self.request_count = 0
        self.max_requests_per_run = int(os.getenv("MAX_API_REQUESTS", "200"))
        self.request_delay = float(os.getenv("API_REQUEST_DELAY", "0.7"))
        self.cache = {}
        self.cache_durations = {
            "fixtures": 300,
            "team_stats": 7200,
            "team_ht_stats": 7200,
            "league_stats": 21600,  # 6 horas
            "season": 86400
        }
        
        if not self.api_key:
            raise ApiFootballError("API_FOOTBALL_KEY não configurada")

    def _is_cache_valid(self, timestamp, cache_type):
        duration = self.cache_durations.get(cache_type, 300)
        return (time.time() - timestamp) < duration

    def _make_request(self, endpoint, params=None, cache_type=None, cache_key=None):
        # Verificar cache
        if cache_key and cache_type:
            full_key = f"{cache_type}:{cache_key}"
            if full_key in self.cache:
                data, ts = self.cache[full_key]
                if self._is_cache_valid(ts, cache_type):
                    return data

        # Verificar limites
        if self.request_count >= self.max_requests_per_run:
            raise ApiFootballError(f"Limite de {self.max_requests_per_run} requisições atingido")

        # Rate limiting
        if self.request_count > 0:
            time.sleep(self.request_delay)

        # Fazer requisição
        for attempt in range(3):
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                self.request_count += 1
                
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    print(f"⏳ Rate limit. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json().get("response", [])
                
                # Salvar no cache
                if cache_key and cache_type:
                    self.cache[f"{cache_type}:{cache_key}"] = (data, time.time())
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise ApiFootballError(f"Erro após 3 tentativas: {e}")
                time.sleep((attempt + 1) * 2)
        
        return []

    def get_current_season(self, league_id):
        cache_key = f"season:{league_id}"
        if cache_key in self.cache:
            season, ts = self.cache[cache_key]
            if self._is_cache_valid(ts, "season"):
                return season
        
        now = datetime.now()
        european_leagues = [39, 140, 135, 78, 61, 94, 144, 203]
        
        if league_id in european_leagues:
            season = now.year if now.month >= 7 else now.year - 1
        else:
            season = now.year
            
        self.cache[cache_key] = (season, time.time())
        return season

    def get_fixtures_today(self, league_id, timezone_name):
        try:
            league_tz = tz.gettz(timezone_name)
            today = datetime.now(league_tz).date().strftime("%Y-%m-%d")
            
            params = {
                "league": league_id,
                "season": self.get_current_season(league_id),
                "date": today,
                "timezone": timezone_name
            }
            
            fixtures = self._make_request(
                "/fixtures", 
                params, 
                "fixtures", 
                f"{league_id}:{today}"
            )
            
            return [f for f in fixtures if f["fixture"]["status"]["short"] in ["NS", "TBD"]]
            
        except Exception as e:
            print(f"❌ Erro ao buscar fixtures: {e}")
            return []

    def get_teams_stats_batch(self, team_ids, last_n=4):
        """Busca stats FT para os times"""
        results = {}
        unique_teams = list(dict.fromkeys(team_ids))
        
        for team_id in unique_teams:
            try:
                cache_key = f"{team_id}:{last_n}"
                cached = self.cache.get(f"team_stats:{cache_key}")
                
                if cached and self._is_cache_valid(cached[1], "team_stats"):
                    results[team_id] = cached[0]
                    continue
                
                if self.request_count >= self.max_requests_per_run:
                    results[team_id] = (None, 0)
                    continue
                
                params = {"team": team_id, "last": last_n, "status": "FT"}
                fixtures = self._make_request("/fixtures", params, "team_stats", cache_key)
                
                if not fixtures:
                    results[team_id] = (None, 0)
                    continue
                
                goals_scored = []
                for fixture in fixtures:
                    home_id = fixture["teams"]["home"]["id"]
                    away_id = fixture["teams"]["away"]["id"]
                    home_goals = fixture["goals"]["home"] or 0
                    away_goals = fixture["goals"]["away"] or 0
                    
                    if team_id == home_id:
                        goals_scored.append(home_goals)
                    elif team_id == away_id:
                        goals_scored.append(away_goals)
                
                if goals_scored:
                    avg = round(sum(goals_scored) / len(goals_scored), 2)
                    results[team_id] = (avg, len(goals_scored))
                else:
                    results[team_id] = (None, 0)
                
            except Exception as e:
                print(f"❌ Erro team {team_id}: {e}")
                results[team_id] = (None, 0)
        
        return results

    def get_teams_ht_stats_batch(self, team_ids, last_n=4):
        """Busca stats HT para os times"""
        results = {}
        unique_teams = list(dict.fromkeys(team_ids))
        
        for team_id in unique_teams:
            try:
                cache_key = f"{team_id}:{last_n}"
                cached = self.cache.get(f"team_ht_stats:{cache_key}")
                
                if cached and self._is_cache_valid(cached[1], "team_ht_stats"):
                    results[team_id] = cached[0]
                    continue
                
                if self.request_count >= self.max_requests_per_run:
                    results[team_id] = (None, 0)
                    continue
                
                params = {"team": team_id, "last": last_n, "status": "FT"}
                fixtures = self._make_request("/fixtures", params, "team_ht_stats", cache_key)
                
                if not fixtures:
                    results[team_id] = (None, 0)
                    continue
                
                ht_totals = []
                for fixture in fixtures:
                    # Buscar gols do primeiro tempo
                    score = fixture.get("score", {})
                    halftime = score.get("halftime", {})
                    ht_home = halftime.get("home")
                    ht_away = halftime.get("away")
                    
                    if ht_home is not None and ht_away is not None:
                        ht_totals.append(ht_home + ht_away)
                
                if ht_totals:
                    avg = round(sum(ht_totals) / len(ht_totals), 2)
                    results[team_id] = (avg, len(ht_totals))
                else:
                    results[team_id] = (None, 0)
                
            except Exception as e:
                print(f"❌ Erro HT team {team_id}: {e}")
                results[team_id] = (None, 0)
        
        return results

    def get_league_real_stats(self, league_id, season):
        """Calcula estatísticas reais da liga (otimizado)"""
        try:
            # Verificar se está habilitado
            if os.getenv("ENABLE_REAL_LEAGUE_STATS", "false").lower() != "true":
                return None
            
            cache_key = f"{league_id}:{season}"
            cached = self.cache.get(f"league_stats:{cache_key}")
            
            if cached and self._is_cache_valid(cached[1], "league_stats"):
                return cached[0]
            
            # Reservar requests para outras operações
            if self.request_count >= self.max_requests_per_run - 10:
                return None
            
            # Buscar jogos dos últimos 120 dias para otimizar
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=120)
            
            params = {
                "league": league_id,
                "season": season,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "status": "FT"
            }
            
            fixtures = self._make_request("/fixtures", params, "league_stats", cache_key)
            
            if not fixtures or len(fixtures) < 30:  # Mínimo para análise confiável
                return None
            
            # Calcular estatísticas
            total_games = len(fixtures)
            total_goals = 0
            total_goals_ht = 0
            btts_count = 0
            over15_ht_count = 0
            over25_count = 0
            over35_count = 0
            
            for fixture in fixtures:
                # Gols tempo total
                home_goals = fixture["goals"]["home"] or 0
                away_goals = fixture["goals"]["away"] or 0
                match_goals = home_goals + away_goals
                total_goals += match_goals
                
                # Gols primeiro tempo
                score = fixture.get("score", {})
                halftime = score.get("halftime", {})
                home_ht = halftime.get("home") if halftime.get("home") is not None else 0
                away_ht = halftime.get("away") if halftime.get("away") is not None else 0
                match_goals_ht = home_ht + away_ht
                total_goals_ht += match_goals_ht
                
                # Contadores
                if home_goals > 0 and away_goals > 0:
                    btts_count += 1
                    
                if match_goals_ht > 1.5:
                    over15_ht_count += 1
                    
                if match_goals > 2.5:
                    over25_count += 1
                    
                if match_goals > 3.5:
                    over35_count += 1
            
            stats = {
                "total_games": total_games,
                "avg_goals_per_match": round(total_goals / total_games, 2),
                "avg_goals_ht": round(total_goals_ht / total_games, 2),
                "btts_rate": round((btts_count / total_games) * 100),
                "over15_ht_rate": round((over15_ht_count / total_games) * 100),
                "over25_rate": round((over25_count / total_games) * 100),
                "over35_rate": round((over35_count / total_games) * 100),
                "second_half_share": round(((total_goals - total_goals_ht) / total_goals) * 100) if total_goals > 0 else 50,
                "days_analyzed": 120,
                "is_real": True
            }
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Erro ao calcular stats da liga: {e}")
            return None

    def get_execution_stats(self):
        return {
            "requests_used": self.request_count,
            "max_allowed": self.max_requests_per_run,
            "cache_entries": len(self.cache),
            "efficiency": f"{((self.max_requests_per_run - self.request_count) / self.max_requests_per_run * 100):.1f}%"
        }
