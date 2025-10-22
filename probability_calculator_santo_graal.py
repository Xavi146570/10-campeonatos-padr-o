"""
Calculador de Probabilidades para Santo Graal com EV+
Adaptado do sistema Over 1.5 para calcular probabilidades no intervalo (HT 0-0)
"""

import math
from typing import Dict, Tuple
from datetime import datetime
import config_santo_graal as config


class ProbabilityCalculatorSantoGraal:
    """
    Calcula probabilidades de Over 0.5 e Over 1.5 quando jogo está 0-0 no intervalo.
    Usa 9 indicadores ponderados + ajustes contextuais para HT.
    """
    
    def __init__(self):
        self.weights = config.PROBABILITY_WEIGHTS
        self.ht_multipliers = config.HT_0_0_MULTIPLIERS
    
    def calculate_probabilities_at_ht(
        self, 
        home_stats: Dict, 
        away_stats: Dict,
        h2h_stats: Dict,
        match_info: Dict
    ) -> Dict[str, float]:
        """
        Calcula probabilidades Over 0.5 e Over 1.5 quando jogo está 0-0 no HT.
        
        Args:
            home_stats: Estatísticas do time da casa
            away_stats: Estatísticas do time visitante
            h2h_stats: Estatísticas de confrontos diretos
            match_info: Informações contextuais do jogo
        
        Returns:
            Dict com probabilidades: {'over_0_5': float, 'over_1_5': float, 'confidence': float}
        """
        
        # Calcular gols esperados para o 2º tempo
        expected_goals_2h = self._calculate_expected_goals_2h(home_stats, away_stats)
        
        # 1. INDICADORES PRIMÁRIOS (50%)
        prob_poisson_0_5 = self._poisson_probability_over_n(expected_goals_2h, 0.5)
        prob_poisson_1_5 = self._poisson_probability_over_n(expected_goals_2h, 1.5)
        
        prob_historical_0_5 = self._historical_rate(home_stats, away_stats, 0.5)
        prob_historical_1_5 = self._historical_rate(home_stats, away_stats, 1.5)
        
        prob_recent_0_5 = self._recent_trend(home_stats, away_stats, 0.5)
        prob_recent_1_5 = self._recent_trend(home_stats, away_stats, 1.5)
        
        # 2. INDICADORES SECUNDÁRIOS (30%)
        prob_h2h_0_5, prob_h2h_1_5 = self._h2h_analysis(h2h_stats)
        
        prob_offensive = self._offensive_strength(home_stats, away_stats)
        
        prob_offensive_trend_0_5 = self._offensive_trend(home_stats, away_stats, 0.5)
        prob_offensive_trend_1_5 = self._offensive_trend(home_stats, away_stats, 1.5)
        
        # 3. INDICADORES CONTEXTUAIS (20%)
        prob_season_phase = self._season_phase_factor(match_info)
        prob_motivation = self._motivation_factor(match_info)
        prob_importance = self._match_importance(match_info)
        
        # CÁLCULO PONDERADO - OVER 0.5
        prob_over_0_5_base = (
            prob_poisson_0_5 * self.weights['poisson'] +
            prob_historical_0_5 * self.weights['historical_rate'] +
            prob_recent_0_5 * self.weights['recent_trend'] +
            prob_h2h_0_5 * self.weights['h2h'] +
            prob_offensive * self.weights['offensive_strength'] +
            prob_offensive_trend_0_5 * self.weights['offensive_trend'] +
            prob_season_phase * self.weights['season_phase'] +
            prob_motivation * self.weights['motivation'] +
            prob_importance * self.weights['match_importance']
        )
        
        # CÁLCULO PONDERADO - OVER 1.5
        prob_over_1_5_base = (
            prob_poisson_1_5 * self.weights['poisson'] +
            prob_historical_1_5 * self.weights['historical_rate'] +
            prob_recent_1_5 * self.weights['recent_trend'] +
            prob_h2h_1_5 * self.weights['h2h'] +
            prob_offensive * self.weights['offensive_strength'] +
            prob_offensive_trend_1_5 * self.weights['offensive_trend'] +
            prob_season_phase * self.weights['season_phase'] +
            prob_motivation * self.weights['motivation'] +
            prob_importance * self.weights['match_importance']
        )
        
        # APLICAR MULTIPLICADORES DE HT 0-0
        # 2º tempo tende a ser mais aberto quando está 0-0 no intervalo
        prob_over_0_5 = min(prob_over_0_5_base * self.ht_multipliers['over_0_5'], 0.98)
        prob_over_1_5 = min(prob_over_1_5_base * self.ht_multipliers['over_1_5'], 0.95)
        
        # Calcular confiança (baseada em consistência dos indicadores)
        confidence = self._calculate_confidence(
            [prob_poisson_0_5, prob_historical_0_5, prob_recent_0_5, prob_h2h_0_5],
            [prob_poisson_1_5, prob_historical_1_5, prob_recent_1_5, prob_h2h_1_5]
        )
        
        return {
            'over_0_5': round(prob_over_0_5, 4),
            'over_1_5': round(prob_over_1_5, 4),
            'confidence': round(confidence, 4),
            'expected_goals_2h': round(expected_goals_2h, 2)
        }
    
    def _calculate_expected_goals_2h(self, home_stats: Dict, away_stats: Dict) -> float:
        """
        Calcula gols esperados para o 2º tempo baseado em:
        - Média de gols/jogo dos times
        - Taxa de gols no 2º tempo historicamente
        - Ajuste para situação 0-0 no HT (times tendem a atacar mais)
        """
        home_goals_avg = home_stats.get('goals_per_game', 1.5)
        away_goals_avg = away_stats.get('goals_per_game', 1.5)
        
        # Média de gols esperados por jogo
        total_goals_avg = (home_goals_avg + away_goals_avg) / 2
        
        # Ajuste: 2º tempo costuma ter ~55% dos gols do jogo
        second_half_factor = 0.55
        
        # Ajuste adicional: quando 0-0 no HT, times atacam mais (+15%)
        ht_0_0_boost = 1.15
        
        expected_goals = total_goals_avg * second_half_factor * ht_0_0_boost
        
        return max(expected_goals, 0.8)  # Mínimo de 0.8 gols esperados
    
    def _poisson_probability_over_n(self, lambda_: float, n: float) -> float:
        """
        Calcula P(X > n) usando distribuição de Poisson.
        P(Over 0.5) = 1 - P(X ≤ 0) = 1 - e^(-λ)
        P(Over 1.5) = 1 - P(X ≤ 1) = 1 - e^(-λ) × (1 + λ)
        """
        try:
            if n == 0.5:
                # P(Over 0.5) = P(X ≥ 1)
                prob = 1 - math.exp(-lambda_)
            elif n == 1.5:
                # P(Over 1.5) = P(X ≥ 2)
                prob = 1 - (math.exp(-lambda_) * (1 + lambda_))
            else:
                prob = 0.5
            
            return max(0.01, min(0.99, prob))
        except:
            return 0.5
    
    def _historical_rate(self, home_stats: Dict, away_stats: Dict, threshold: float) -> float:
        """Taxa histórica de Over N.5 dos dois times"""
        if threshold == 0.5:
            home_rate = home_stats.get('over_0_5_rate', 0.85)
            away_rate = away_stats.get('over_0_5_rate', 0.85)
        else:  # 1.5
            home_rate = home_stats.get('over_1_5_rate', 0.70)
            away_rate = away_stats.get('over_1_5_rate', 0.70)
        
        return (home_rate + away_rate) / 2
    
    def _recent_trend(self, home_stats: Dict, away_stats: Dict, threshold: float) -> float:
        """Tendência dos últimos 5 jogos"""
        if threshold == 0.5:
            home_trend = home_stats.get('recent_over_0_5_rate', 0.80)
            away_trend = away_stats.get('recent_over_0_5_rate', 0.80)
        else:
            home_trend = home_stats.get('recent_over_1_5_rate', 0.65)
            away_trend = away_stats.get('recent_over_1_5_rate', 0.65)
        
        return (home_trend + away_trend) / 2
    
    def _h2h_analysis(self, h2h_stats: Dict) -> Tuple[float, float]:
        """Análise de confrontos diretos"""
        over_0_5 = h2h_stats.get('over_0_5_rate', 0.80)
        over_1_5 = h2h_stats.get('over_1_5_rate', 0.65)
        
        # Se não há histórico suficiente, usar valores neutros
        if h2h_stats.get('total_games', 0) < 3:
            over_0_5 = 0.75
            over_1_5 = 0.60
        
        return over_0_5, over_1_5
    
    def _offensive_strength(self, home_stats: Dict, away_stats: Dict) -> float:
        """Força ofensiva combinada dos times"""
        home_attack = home_stats.get('offensive_rating', 50) / 100
        away_attack = away_stats.get('offensive_rating', 50) / 100
        
        return (home_attack + away_attack) / 2
    
    def _offensive_trend(self, home_stats: Dict, away_stats: Dict, threshold: float) -> float:
        """Tendência ofensiva recente"""
        home_goals_last_5 = home_stats.get('goals_last_5', 6) / 5  # média
        away_goals_last_5 = away_stats.get('goals_last_5', 6) / 5
        
        avg_goals = (home_goals_last_5 + away_goals_last_5) / 2
        
        if threshold == 0.5:
            return min(avg_goals / 1.5, 0.95)  # Normalizar para 0-1
        else:
            return min(avg_goals / 2.5, 0.90)
    
    def _season_phase_factor(self, match_info: Dict) -> float:
        """
        Fase da temporada afeta quantidade de gols:
        - Início: times mais cautelosos (0.65)
        - Meio: fase consolidada (0.75)
        - Final: jogos decisivos (0.85)
        """
        games_played = match_info.get('games_played', 15)
        
        if games_played < 8:
            return 0.65
        elif games_played < 25:
            return 0.75
        else:
            return 0.85
    
    def _motivation_factor(self, match_info: Dict) -> float:
        """
        Motivação dos times (posição na tabela, objetivos):
        - Times brigando por título/vaga europeia: mais ofensivos (0.80)
        - Times no meio da tabela: neutro (0.70)
        - Times lutando contra rebaixamento: variável (0.65)
        """
        home_position = match_info.get('home_position', 10)
        away_position = match_info.get('away_position', 10)
        
        # Times no topo (1-6) ou fundo (15-20) = mais motivação
        if (home_position <= 6 or away_position <= 6):
            return 0.80
        elif (home_position >= 15 or away_position >= 15):
            return 0.70
        else:
            return 0.65
    
    def _match_importance(self, match_info: Dict) -> float:
        """
        Importância do jogo:
        - Derby/clássico: máxima intensidade (0.85)
        - Jogo normal: intensidade média (0.70)
        """
        is_derby = match_info.get('is_derby', False)
        
        if is_derby:
            return 0.85
        else:
            return 0.70
    
    def _calculate_confidence(self, indicators_0_5: list, indicators_1_5: list) -> float:
        """
        Calcula confiança baseada na consistência dos indicadores.
        Menor desvio padrão = maior confiança
        """
        try:
            # Calcular desvio padrão dos indicadores
            avg_0_5 = sum(indicators_0_5) / len(indicators_0_5)
            variance_0_5 = sum((x - avg_0_5) ** 2 for x in indicators_0_5) / len(indicators_0_5)
            std_dev_0_5 = math.sqrt(variance_0_5)
            
            avg_1_5 = sum(indicators_1_5) / len(indicators_1_5)
            variance_1_5 = sum((x - avg_1_5) ** 2 for x in indicators_1_5) / len(indicators_1_5)
            std_dev_1_5 = math.sqrt(variance_1_5)
            
            # Média dos desvios
            avg_std_dev = (std_dev_0_5 + std_dev_1_5) / 2
            
            # Converter para confiança (menor desvio = maior confiança)
            # Desvio 0 = 100% confiança, Desvio 0.3 = 40% confiança
            confidence = max(0.4, 1.0 - (avg_std_dev * 2))
            
            return confidence
        except:
            return 0.6  # Confiança padrão
