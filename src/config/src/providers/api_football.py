import os
import time
import json
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
        
        # Controles de otimização
        self.request_count = 0
        self.max_requests_per_run = int(os.getenv("MAX_API_REQUESTS", "20"))
        self.request_delay = float(os.getenv("API_REQUEST_DELAY", "0.8"))
        self.cache = {}
        self.cache_durations = {
            "fixtures": 300,    # 5 minutos
            "team_stats": 7200, # 2 horas  
            "season": 86400     # 24 horas
        }
        
        if not self.api_key:
            raise ApiFootballError("API_FOOTBALL_KEY não configurada")
        
        print(f"🔧 API Client configurado: max_req={self.max_requests_per_run}, delay={self.request_delay}s")

    def _get_cache_key(self, cache_type, identifier):
        """Gera chave de cache tipada"""
        return f"{cache_type}_{identifier}_{datetime.now().strftime('%Y-%m-%d')}"

    def _is_cache_valid(self, timestamp, cache_type):
        """Verifica validade do cache por tipo"""
        duration = self.cache_durations.get(cache_type, 300)
        return (time.time() - timestamp) < duration

    def _check_quota_status(self):
        """Verifica quota disponível antes de executar"""
        try:
            response = requests.get(
                f"{self.base_url}/status", 
                headers=self.headers, 
                timeout=15
            )
            if response.status_code == 200:
                data = response.json().get("response", {})
                requests_data = data.get("requests", {})
                current = requests_data.get("current", 0)
                limit = requests_data.get("limit", 7500)
                remaining = max(0, limit - current)
                
                print(f"📊 Quota API: {current}/{limit} (restante: {remaining})")
                
                if remaining < 50:  # Margem de segurança
                    raise ApiFootballError(f"Quota baixa: apenas {remaining} requisições restantes")
                    
                return remaining
        except Exception as e:
            print(f"⚠️ Não foi possível verificar quota: {e}")
            return None

    def _make_request(self, endpoint, params=None, cache_type="default", cache_key=None):
        """Requisição otimizada com cache inteligente"""
        
        # Verificar cache primeiro
        if cache_key:
            full_cache_key = f"{cache_type}_{cache_key}"
            if full_cache_key in self.cache:
                cached_data, timestamp = self.cache[full_cache_key]
                if self._is_cache_valid(timestamp, cache_type):
                    print(f"📦 Cache hit: {cache_type}")
                    return cached_data

        # Verificar limites
        if self.request_count >= self.max_requests_per_run:
            raise ApiFootballError(f"Limite de {self.max_requests_per_run} requisições atingido")

        # Rate limiting
        if self.request_count > 0:
            time.sleep(self.request_delay)

        # Fazer requisição
        for attempt in range(3):
            try:
                print(f"🌐 API Request #{self.request_count + 1}: {endpoint}")
                
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
                data = response.json()
                api_response = data.get("response", [])
                
                # Salvar no cache se especificado
                if cache_key:
                    full_cache_key = f"{cache_type}_{cache_key}"
                    self.cache[full_cache_key] = (api_response, time.time())
                
                # Log de quota restante
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                print(f"📈 Quota restante hoje: {remaining}")
                
                return api_response
                
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise ApiFootballError(f"Falha após 3 tentativas: {e}")
                time.sleep((attempt + 1) * 2)
        
        raise ApiFootballError("Limite de tentativas excedido")

    def get_current_season(self, league_id):
        """Determina temporada com cache inteligente"""
        cache_key = f"season_{league_id}"
        
        if cache_key in self.cache:
            season, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp, "season"):
                return season
        
        now = datetime.now()
        
        # Lógica específica por região
        european_leagues = [39, 140, 135, 78, 61, 94, 144, 203]
        
        if league_id in european_leagues:
            season = now.year if now.month >= 7 else now.year - 1
        elif league_id == 71:  # Brasileirão
            season = now.year
        elif league_id == 128:  # Argentina
            season = now.year
        else:
            season = now.year
        
        # Cache da temporada
        self.cache[cache_key] = (season, time.time())
        return season

    def get_fixtures_today(self, league_id, timezone_name):
        """Busca fixtures com cache otimizado"""
        try:
            # Verificar quota antes de começar
            remaining_quota = self._check_quota_status()
            if remaining_quota is not None and remaining_quota < 20:
                print("⚠️ Quota muito baixa, abortando execução")
                return []

            league_tz = tz.gettz(timezone_name)
            today = datetime.now(league_tz).date()
            
            cache_key = f"{league_id}_{today.strftime('%Y-%m-%d')}"
            
            params = {
                "league": league_id,
                "season": self.get_current_season(league_id),
                "date": today.strftime("%Y-%m-%d"),
                "timezone": timezone_name
            }
            
            fixtures = self._make_request(
                "/fixtures", 
                params, 
                cache_type="fixtures", 
                cache_key=cache_key
            )
            
            # Filtrar apenas jogos relevantes
            valid_fixtures = [
                f for f in fixtures 
                if f["fixture"]["status"]["short"] in ["NS", "TBD"]
            ]
            
            print(f"🏆 {len(valid_fixtures)} jogos válidos encontrados")
            return valid_fixtures
            
        except Exception as e:
            print(f"❌ Erro ao buscar fixtures: {e}")
            return []

    def get_teams_stats_batch(self, team_ids, last_n=4):
        """Busca stats de múltiplos times de forma otimizada"""
        results = {}
        
        # Remover duplicatas mantendo ordem
        unique_teams = list(dict.fromkeys(team_ids))
        print(f"📊 Buscando stats para {len(unique_teams)} times únicos")
        
        for team_id in unique_teams:
            try:
                cache_key = f"{team_id}_{last_n}"
                
                # Verificar cache primeiro
                full_cache_key = f"team_stats_{cache_key}"
                if full_cache_key in self.cache:
                    cached_data, timestamp = self.cache[full_cache_key]
                    if self._is_cache_valid(timestamp, "team_stats"):
                        results[team_id] = cached_data
                        print(f"📦 Cache hit para time {team_id}")
                        continue
                
                # Verificar limite de requisições
                if self.request_count >= self.max_requests_per_run:
                    print(f"⚠️ Limite atingido. Pulando time {team_id}")
                    results[team_id] = (None, 0)
                    continue
                
                params = {
                    "team": team_id,
                    "last": last_n,
                    "status": "FT"
                }
                
                fixtures = self._make_request(
                    "/fixtures", 
                    params, 
                    cache_type="team_stats", 
                    cache_key=cache_key
                )
                
                if not fixtures:
                    results[team_id] = (None, 0)
                    continue
                
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
                
                if goals_scored:
                    avg = round(sum(goals_scored) / len(goals_scored), 2)
                    results[team_id] = (avg, len(goals_scored))
                else:
                    results[team_id] = (None, 0)
                
            except Exception as e:
                print(f"❌ Erro ao buscar stats do time {team_id}: {e}")
                results[team_id] = (None, 0)
        
        return results

    def get_execution_stats(self):
        """Retorna estatísticas da execução"""
        return {
            "requests_used": self.request_count,
            "max_allowed": self.max_requests_per_run,
            "cache_entries": len(self.cache),
            "efficiency": f"{((self.max_requests_per_run - self.request_count) / self.max_requests_per_run * 100):.1f}%"
