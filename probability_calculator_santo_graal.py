"""
Calculador de Probabilidades para Santo Graal Bot EV+
Sistema com 9 indicadores para calcular probabilidades Over 0.5 e Over 1.5
"""

import math
from typing import Dict, List, Tuple, Optional
from config_santo_graal import Config


class ProbabilityCalculator:
    """
    Calcula probabilidades de Over 0.5 e Over 1.5 usando 9 indicadores:
    
    Indicadores Primários (50%):
    1. Distribuição de Poisson (25%)
    2. Taxa histórica Over (15%)
    3. Tendência recente (10%)
    
    Indicadores Secundários (30%):
    4. Head-to-Head (12%)
    5. Força ofensiva (10%)
    6. Tendência ofensiva (8%)
    
    Indicadores Contextuais (20%):
    7. Fase da temporada (8%)
    8. Motivação dos times (7%)
    9. Importância do jogo (5%)
    """
    
    def __init__(self):
        """Inicializa o calculador"""
        self.weights = Config.PROBABILITY_WEIGHTS
    
    def calculate_probabilities(self, match_data: Dict) -> Tuple[float, float]:
        """
        Calcula probabilidades Over 0.5 e Over 1.5
        
        Args:
            match_data: Dicionário com dados do jogo:
                - home_stats: Estatísticas do time da casa
                - away_stats: Estatísticas do time visitante
                - h2h: Lista de confrontos diretos
                - is_ht_0x0: Boolean se está 0-0 no HT
        
        Returns:
            Tuple (prob_over_05, prob_over_15) em percentual (0-100)
        """
        home_stats = match_data.get('home_stats', {})
        away_stats = match_data.get('away_stats', {})
        h2h = match_data.get('h2h', [])
        is_ht_0x0 = match_data.get('is_ht_0x0', False)
        
        # Calcular cada indicador
        indicators = {
            'poisson': self._calculate_poisson_probability(home_stats, away_stats),
            'historical_rate': self._calculate_historical_rate(home_stats, away_stats),
            'recent_trend': self._calculate_recent_trend(home_stats, away_stats),
            'h2h': self._calculate_h2h_probability(h2h),
            'offensive_strength': self._calculate_offensive_strength(home_stats, away_stats),
            'offensive_trend': self._calculate_offensive_trend(home_stats, away_stats),
            'season_phase': self._calculate_season_phase(home_stats, away_stats),
            'motivation': self._calculate_motivation(home_stats, away_stats),
            'match_importance': self._calculate_match_importance(home_stats, away_stats),
        }
        
        # Calcular probabilidade ponderada
        prob_over_05 = sum(
            indicators[key][0] * self.weights[key] 
            for key in indicators.keys()
        )
        
        prob_over_15 = sum(
            indicators[key][1] * self.weights[key] 
            for key in indicators.keys()
        )
        
        # Aplicar multiplicadores se estiver 0-0 no HT
        if is_ht_0x0:
            prob_over_05 *= Config.HT_0X0_MULTIPLIER_OVER_05
            prob_over_15 *= Config.HT_0X0_MULTIPLIER_OVER_15
        
        # Garantir que está no range 0-100
        prob_over_05 = max(0, min(100, prob_over_05))
        prob_over_15 = max(0, min(100, prob_over_15))
        
        return prob_over_05, prob_over_15
    
    def _calculate_poisson_probability(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 1: Distribuição de Poisson (25%)
        Calcula probabilidade baseada em média de gols
        """
        try:
            # Extrair médias de gols
            home_goals = home_stats.get('goals', {}).get('for', {}).get('average', {})
            away_goals = away_stats.get('goals', {}).get('for', {}).get('average', {})
            
            home_avg = float(home_goals.get('total', 1.5))
            away_avg = float(away_goals.get('total', 1.5))
            
            # Média de gols esperados no jogo
            expected_goals = (home_avg + away_avg) / 2
            
            # Poisson: P(X > k) = 1 - P(X <= k)
            prob_0_goals = math.exp(-expected_goals)
            prob_1_goal = expected_goals * math.exp(-expected_goals)
            
            prob_over_05 = (1 - prob_0_goals) * 100
            prob_over_15 = (1 - prob_0_goals - prob_1_goal) * 100
            
            return prob_over_05, prob_over_15
        
        except Exception:
            # Fallback: valores conservadores
            return 75.0, 55.0
    
    def _calculate_historical_rate(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 2: Taxa histórica Over (15%)
        Baseado em jogos anteriores dos times
        """
        try:
            home_fixtures = home_stats.get('fixtures', {}).get('played', {}).get('total', 0)
            away_fixtures = away_stats.get('fixtures', {}).get('played', {}).get('total', 0)
            
            if home_fixtures == 0 or away_fixtures == 0:
                return 70.0, 50.0
            
            # Contar jogos com Over 0.5 e Over 1.5
            home_goals_total = home_stats.get('goals', {}).get('for', {}).get('total', {}).get('total', 0)
            away_goals_total = away_stats.get('goals', {}).get('for', {}).get('total', {}).get('total', 0)
            
            # Taxa Over 0.5 (jogos com pelo menos 1 gol)
            home_over_05_rate = (home_goals_total / home_fixtures) if home_fixtures > 0 else 0.7
            away_over_05_rate = (away_goals_total / away_fixtures) if away_fixtures > 0 else 0.7
            
            prob_over_05 = ((home_over_05_rate + away_over_05_rate) / 2) * 100
            
            # Taxa Over 1.5 (estimativa: ~70% da taxa Over 0.5)
            prob_over_15 = prob_over_05 * 0.70
            
            return prob_over_05, prob_over_15
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_recent_trend(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 3: Tendência recente (10%)
        Últimos 5 jogos dos times
        """
        try:
            # Usar forma recente (últimos 5 jogos)
            home_form = home_stats.get('form', 'WWDWW')[-5:]
            away_form = away_stats.get('form', 'WWDWW')[-5:]
            
            # W = 3 pontos, D = 1 ponto, L = 0 pontos
            def form_score(form_str):
                points = {'W': 3, 'D': 1, 'L': 0}
                return sum(points.get(c, 1) for c in form_str)
            
            home_form_score = form_score(home_form)
            away_form_score = form_score(away_form)
            
            # Times em boa forma tendem a marcar mais
            avg_form = (home_form_score + away_form_score) / 30  # Máximo 30 pontos (5W+5W)
            
            prob_over_05 = 60 + (avg_form * 30)  # Range: 60-90%
            prob_over_15 = 40 + (avg_form * 30)  # Range: 40-70%
            
            return prob_over_05, prob_over_15
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_h2h_probability(self, h2h_matches: List[Dict]) -> Tuple[float, float]:
        """
        Indicador 4: Head-to-Head (12%)
        Histórico de confrontos diretos
        """
        try:
            if not h2h_matches:
                return 70.0, 50.0
            
            total_goals = 0
            games_over_05 = 0
            games_over_15 = 0
            
            for match in h2h_matches[:10]:  # Últimos 10 confrontos
                score = match.get('score', {}).get('fulltime', {})
                home = score.get('home', 0)
                away = score.get('away', 0)
                
                if home is not None and away is not None:
                    game_goals = home + away
                    total_goals += game_goals
                    
                    if game_goals > 0:
                        games_over_05 += 1
                    if game_goals > 1:
                        games_over_15 += 1
            
            num_matches = len(h2h_matches[:10])
            
            if num_matches > 0:
                prob_over_05 = (games_over_05 / num_matches) * 100
                prob_over_15 = (games_over_15 / num_matches) * 100
            else:
                prob_over_05 = 70.0
                prob_over_15 = 50.0
            
            return prob_over_05, prob_over_15
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_offensive_strength(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 5: Força ofensiva (10%)
        Capacidade de marcar gols dos times
        """
        try:
            home_goals_avg = float(
                home_stats.get('goals', {}).get('for', {}).get('average', {}).get('total', 1.5)
            )
            away_goals_avg = float(
                away_stats.get('goals', {}).get('for', {}).get('average', {}).get('total', 1.5)
            )
            
            combined_avg = home_goals_avg + away_goals_avg
            
            # Normalizar para 0-100
            # Média alta (>3.0) = alta probabilidade
            prob_over_05 = min(95, 50 + (combined_avg * 15))
            prob_over_15 = min(85, 30 + (combined_avg * 15))
            
            return prob_over_05, prob_over_15
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_offensive_trend(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 6: Tendência ofensiva (8%)
        Se os times estão marcando mais/menos recentemente
        """
        try:
            # Comparar gols home vs away
            home_goals_home = float(
                home_stats.get('goals', {}).get('for', {}).get('average', {}).get('home', 1.5)
            )
            away_goals_away = float(
                away_stats.get('goals', {}).get('for', {}).get('average', {}).get('away', 1.5)
            )
            
            # Casa marca mais em casa + Visitante marca fora = bom sinal
            combined = home_goals_home + away_goals_away
            
            prob_over_05 = min(95, 50 + (combined * 15))
            prob_over_15 = min(85, 30 + (combined * 15))
            
            return prob_over_05, prob_over_15
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_season_phase(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 7: Fase da temporada (8%)
        Início/meio/fim da temporada afeta comportamento
        """
        try:
            home_played = home_stats.get('fixtures', {}).get('played', {}).get('total', 10)
            away_played = away_stats.get('fixtures', {}).get('played', {}).get('total', 10)
            
            avg_played = (home_played + away_played) / 2
            
            # Início temporada (< 10 jogos): times mais cautelosos
            # Meio temporada (10-25 jogos): jogos mais abertos
            # Final temporada (> 25 jogos): depende de objetivos
            
            if avg_played < 10:
                return 65.0, 45.0  # Início: mais cauteloso
            elif avg_played < 25:
                return 75.0, 55.0  # Meio: mais aberto
            else:
                return 70.0, 50.0  # Final: médio
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_motivation(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 8: Motivação dos times (7%)
        Times lutando por objetivos jogam diferente
        """
        try:
            # Baseado na posição na tabela (aproximação)
            home_rank = home_stats.get('league', {}).get('rank', 10)
            away_rank = away_stats.get('league', {}).get('rank', 10)
            
            # Times brigando por título/rebaixamento: mais intenso
            # Times meio de tabela: menos intenso
            
            avg_rank = (home_rank + away_rank) / 2
            
            if avg_rank <= 6 or avg_rank >= 15:
                # Times com objetivos claros: mais gols
                return 75.0, 55.0
            else:
                # Meio de tabela: médio
                return 70.0, 50.0
        
        except Exception:
            return 70.0, 50.0
    
    def _calculate_match_importance(
        self, 
        home_stats: Dict, 
        away_stats: Dict
    ) -> Tuple[float, float]:
        """
        Indicador 9: Importância do jogo (5%)
        Derbies, clássicos, jogos decisivos
        """
        try:
            # Simplificado: baseado na diferença de ranking
            home_rank = home_stats.get('league', {}).get('rank', 10)
            away_rank = away_stats.get('league', {}).get('rank', 10)
            
            rank_diff = abs(home_rank - away_rank)
            
            # Times equilibrados (rank_diff pequeno): jogo mais disputado
            if rank_diff <= 3:
                return 75.0, 55.0
            else:
                return 70.0, 50.0
        
        except Exception:
            return 70.0, 50.0
