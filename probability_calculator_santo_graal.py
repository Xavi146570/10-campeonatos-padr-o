"""
Calculadora de Probabilidades para Santo Graal Bot
Usa 9 indicadores ponderados para calcular Over 0.5 e Over 1.5
"""

import requests
import config_santo_graal as config

class ProbabilityCalculator:
    """Calcula probabilidades Over 0.5 e Over 1.5 usando 9 indicadores."""
    
    def __init__(self):
        self.api_key = config.API_FOOTBALL_KEY
        self.base_url = config.API_FOOTBALL_BASE_URL
        
        # Pesos dos indicadores (total = 100%)
        self.weights = {
            'poisson': 0.25,           # 25%
            'historical_rate': 0.15,   # 15%
            'recent_trend': 0.10,      # 10%
            'h2h': 0.12,               # 12%
            'offensive_strength': 0.10, # 10%
            'offensive_trend': 0.08,    # 8%
            'season_phase': 0.08,       # 8%
            'motivation': 0.07,         # 7%
            'match_importance': 0.05    # 5%
        }
    
    def calculate_probabilities(self, home_team_id, away_team_id, league_id):
        """
        Calcula probabilidades Over 0.5 e Over 1.5 para o 2º tempo.
        
        Args:
            home_team_id (int): ID do time da casa
            away_team_id (int): ID do time visitante
            league_id (int): ID da liga
        
        Returns:
            dict: {'over_05': float, 'over_15': float} ou None se erro
        """
        try:
            # 1. Buscar dados dos times
            home_stats = self._get_team_stats(home_team_id, league_id)
            away_stats = self._get_team_stats(away_team_id, league_id)
            
            if not home_stats or not away_stats:
                return None
            
            # 2. Buscar dados H2H
            h2h_data = self._get_h2h_data(home_team_id, away_team_id)
            
            # 3. Calcular indicadores
            indicators = {
                'poisson': self._calculate_poisson(home_stats, away_stats),
                'historical_rate': self._calculate_historical_rate(home_stats, away_stats),
                'recent_trend': self._calculate_recent_trend(home_stats, away_stats),
                'h2h': self._calculate_h2h(h2h_data),
                'offensive_strength': self._calculate_offensive_strength(home_stats, away_stats),
                'offensive_trend': self._calculate_offensive_trend(home_stats, away_stats),
                'season_phase': self._calculate_season_phase(),
                'motivation': self._calculate_motivation(home_stats, away_stats),
                'match_importance': self._calculate_match_importance(league_id)
            }
            
            # 4. Calcular probabilidades ponderadas
            prob_over_05 = sum(indicators[key] * self.weights[key] for key in indicators.keys())
            prob_over_15 = prob_over_05 * 0.75  # Over 1.5 é ~75% do Over 0.5
            
            return {
                'over_05': round(prob_over_05, 2),
                'over_15': round(prob_over_15, 2)
            }
        
        except Exception as e:
            print(f"❌ Erro ao calcular probabilidades: {e}")
            return None
    
    def _get_team_stats(self, team_id, league_id):
        """Busca estatísticas de um time na API."""
        url = f"{self.base_url}/teams/statistics"
        headers = {'x-apisports-key': self.api_key}
        params = {
            'team': team_id,
            'league': league_id,
            'season': config.SEASON
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=config.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results', 0) > 0:
                return data['response']
            return None
        
        except Exception as e:
            print(f"❌ Erro ao buscar stats do time {team_id}: {e}")
            return None
    
    def _get_h2h_data(self, home_team_id, away_team_id):
        """Busca histórico de confrontos diretos."""
        url = f"{self.base_url}/fixtures/headtohead"
        headers = {'x-apisports-key': self.api_key}
        params = {
            'h2h': f"{home_team_id}-{away_team_id}",
            'last': 5
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=config.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results', 0) > 0:
                return data['response']
            return []
        
        except Exception as e:
            print(f"❌ Erro ao buscar H2H: {e}")
            return []
    
    # ============================================
    # INDICADORES (Simplificados - Mock Data)
    # ============================================
    
    def _calculate_poisson(self, home_stats, away_stats):
        """Probabilidade baseada em distribuição de Poisson."""
        # Simplificado: retorna 70% como base
        return 70.0
    
    def _calculate_historical_rate(self, home_stats, away_stats):
        """Taxa histórica de gols marcados."""
        return 65.0
    
    def _calculate_recent_trend(self, home_stats, away_stats):
        """Tendência recente (últimos 5 jogos)."""
        return 72.0
    
    def _calculate_h2h(self, h2h_data):
        """Análise de confrontos diretos."""
        if not h2h_data:
            return 60.0
        
        # Calcular média de gols nos últimos H2H
        total_goals = sum(
            fixture['goals']['home'] + fixture['goals']['away']
            for fixture in h2h_data
        )
        avg_goals = total_goals / len(h2h_data) if h2h_data else 0
        
        # Converter para probabilidade
        if avg_goals >= 2.5:
            return 75.0
        elif avg_goals >= 1.5:
            return 65.0
        else:
            return 55.0
    
    def _calculate_offensive_strength(self, home_stats, away_stats):
        """Força ofensiva combinada."""
        return 68.0
    
    def _calculate_offensive_trend(self, home_stats, away_stats):
        """Tendência ofensiva recente."""
        return 70.0
    
    def _calculate_season_phase(self):
        """Fase da temporada (início/meio/fim)."""
        return 65.0
    
    def _calculate_motivation(self, home_stats, away_stats):
        """Nível de motivação dos times."""
        return 70.0
    
    def _calculate_match_importance(self, league_id):
        """Importância do jogo (liga, competição)."""
        # Champions League = mais importante
        if league_id == 2:
            return 80.0
        # Top 5 ligas europeias
        elif league_id in [39, 140, 78, 135, 61]:
            return 75.0
        else:
            return 70.0

if __name__ == "__main__":
    # Teste
    calc = ProbabilityCalculator()
    print("✅ ProbabilityCalculator inicializado")
    
    # Teste de cálculo (mock)
    probs = calc.calculate_probabilities(33, 50, 39)  # Manchester United vs Manchester City
    if probs:
        print(f"📊 Probabilidades:")
        print(f"   Over 0.5: {probs['over_05']}%")
        print(f"   Over 1.5: {probs['over_15']}%")
