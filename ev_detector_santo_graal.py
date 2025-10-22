"""
Detector de Expected Value (EV+) para Santo Graal
Identifica quando odds oferecidas têm valor positivo
"""

from typing import Dict, Optional
import config_santo_graal as config


class EVDetectorSantoGraal:
    """
    Detecta oportunidades com Expected Value positivo (EV+).
    Calcula EV, Kelly Criterion e recomenda stake.
    """
    
    def __init__(self):
        self.min_ev = config.MIN_EV_PERCENTAGE
        self.kelly_fraction = config.KELLY_FRACTION
        self.max_stake = config.MAX_STAKE_PERCENTAGE
    
    def analyze_opportunity(
        self, 
        market: str,
        probability: float,
        odds: float,
        confidence: float
    ) -> Optional[Dict]:
        """
        Analisa se uma odd oferece valor positivo (EV+).
        
        Args:
            market: 'Over 0.5' ou 'Over 1.5'
            probability: Probabilidade calculada (0-1)
            odds: Odd oferecida pela casa
            confidence: Confiança no cálculo (0-1)
        
        Returns:
            Dict com análise EV ou None se não for EV+
        """
        
        # Validar odds dentro do range aceitável
        if odds < config.MIN_ODDS_RANGE or odds > config.MAX_ODDS_RANGE:
            return None
        
        # Validar probabilidade mínima
        if market == 'Over 0.5' and probability < config.MIN_PROBABILITY_OVER_0_5:
            return None
        if market == 'Over 1.5' and probability < config.MIN_PROBABILITY_OVER_1_5:
            return None
        
        # CALCULAR EXPECTED VALUE (EV)
        # EV = (Probabilidade × Odds) - 1
        ev = (probability * odds) - 1
        ev_percentage = ev * 100
        
        # Verificar se EV é positivo e atende critério mínimo
        if ev_percentage < self.min_ev:
            return None
        
        # CALCULAR KELLY STAKE
        # Kelly = (bp - q) / b
        # b = odds - 1, p = probabilidade, q = 1 - p
        kelly_stake = self._calculate_kelly(probability, odds)
        
        # Aplicar fração conservadora (25% do Kelly)
        conservative_stake = kelly_stake * self.kelly_fraction
        
        # Limitar ao máximo permitido
        recommended_stake = min(conservative_stake, self.max_stake)
        
        # AJUSTAR STAKE PELA CONFIANÇA
        # Confiança baixa = reduzir stake
        adjusted_stake = recommended_stake * confidence
        
        return {
            'market': market,
            'probability': round(probability, 4),
            'odds': odds,
            'ev': round(ev, 4),
            'ev_percentage': round(ev_percentage, 2),
            'confidence': round(confidence, 4),
            'kelly_full': round(kelly_stake, 2),
            'kelly_conservative': round(conservative_stake, 2),
            'recommended_stake': round(adjusted_stake, 2),
            'is_value_bet': True
        }
    
    def _calculate_kelly(self, probability: float, odds: float) -> float:
        """
        Calcula Kelly Criterion para gestão de banca.
        
        Kelly = (bp - q) / b
        onde:
        - b = odds decimais - 1
        - p = probabilidade de ganhar
        - q = probabilidade de perder (1 - p)
        """
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly = ((b * p) - q) / b
        
        # Kelly nunca pode ser negativo (já filtramos EV+ antes)
        # Mas por segurança, limitar entre 0 e 100%
        kelly_percentage = max(0, min(kelly * 100, 100))
        
        return kelly_percentage
    
    def compare_markets(
        self,
        over_0_5_analysis: Optional[Dict],
        over_1_5_analysis: Optional[Dict],
        over_0_5_prob: float = 0.0,
        over_1_5_prob: float = 0.0,
        over_0_5_odds: float = 0.0,
        over_1_5_odds: float = 0.0
    ) -> Dict:
        """
        Compara análises de Over 0.5 e Over 1.5 e retorna melhor oportunidade.
        Agora também retorna informações sobre EV- para fins educativos.
        
        Returns:
            Dict com melhor oportunidade ou informação que nenhuma é EV+
        """
        if not over_0_5_analysis and not over_1_5_analysis:
            # Calcular EV negativo para informação educativa
            ev_negative_info = []
            
            if over_0_5_odds > 0:
                ev_0_5 = (over_0_5_prob * over_0_5_odds) - 1
                ev_negative_info.append({
                    'market': 'Over 0.5',
                    'probability': over_0_5_prob,
                    'odds': over_0_5_odds,
                    'ev': ev_0_5,
                    'ev_percentage': ev_0_5 * 100
                })
            
            if over_1_5_odds > 0:
                ev_1_5 = (over_1_5_prob * over_1_5_odds) - 1
                ev_negative_info.append({
                    'market': 'Over 1.5',
                    'probability': over_1_5_prob,
                    'odds': over_1_5_odds,
                    'ev': ev_1_5,
                    'ev_percentage': ev_1_5 * 100
                })
            
            return {
                'has_opportunity': False,
                'message': 'Nenhum mercado apresenta EV+ no momento',
                'ev_negative_markets': ev_negative_info
            }
        
        # Se apenas um mercado é EV+
        if over_0_5_analysis and not over_1_5_analysis:
            return {
                'has_opportunity': True,
                'best_market': 'Over 0.5',
                'analysis': over_0_5_analysis,
                'alternative': None
            }
        
        if over_1_5_analysis and not over_0_5_analysis:
            return {
                'has_opportunity': True,
                'best_market': 'Over 1.5',
                'analysis': over_1_5_analysis,
                'alternative': None
            }
        
        # Ambos são EV+ - comparar qual é melhor
        # Critério: EV ajustado pela confiança
        ev_adjusted_0_5 = over_0_5_analysis['ev_percentage'] * over_0_5_analysis['confidence']
        ev_adjusted_1_5 = over_1_5_analysis['ev_percentage'] * over_1_5_analysis['confidence']
        
        if ev_adjusted_0_5 >= ev_adjusted_1_5:
            return {
                'has_opportunity': True,
                'best_market': 'Over 0.5',
                'analysis': over_0_5_analysis,
                'alternative': {
                    'market': 'Over 1.5',
                    'analysis': over_1_5_analysis
                }
            }
        else:
            return {
                'has_opportunity': True,
                'best_market': 'Over 1.5',
                'analysis': over_1_5_analysis,
                'alternative': {
                    'market': 'Over 0.5',
                    'analysis': over_0_5_analysis
                }
            }
    
    def format_ev_negative_message(self, comparison: Dict, match_info: Dict) -> str:
        """
        Formata mensagem EDUCATIVA quando jogo é HT 0-0 mas odds são EV-.
        
        Args:
            comparison: Resultado de compare_markets() com EV-
            match_info: Informações do jogo
        
        Returns:
            String formatada para Telegram (mensagem educativa)
        """
        # Emojis
        emoji_stop = '⛔'
        emoji_chart = '📉'
        emoji_info = 'ℹ️'
        emoji_learn = '🎓'
        
        message = f"{emoji_stop} **ATENÇÃO: HT 0-0 DETECTADO - ODDS SEM VALOR!**\n\n"
        message += f"**Jogo:** {match_info['home_team']} vs {match_info['away_team']}\n"
        message += f"**Liga:** {match_info['league']}\n"
        message += f"**Placar HT:** 0-0\n\n"
        
        message += f"{emoji_chart} **ANÁLISE MATEMÁTICA**\n\n"
        
        # Mostrar cada mercado com EV-
        ev_markets = comparison.get('ev_negative_markets', [])
        
        for market_info in ev_markets:
            market = market_info['market']
            prob = market_info['probability']
            odds = market_info['odds']
            ev_pct = market_info['ev_percentage']
            
            message += f"**{market}:**\n"
            message += f"• Odd oferecida: {odds}\n"
            message += f"• Probabilidade calculada: {prob*100:.1f}%\n"
            message += f"• **EV: {ev_pct:+.2f}%** ❌ (NEGATIVO)\n\n"
        
        message += f"{emoji_info} **POR QUE NÃO APOSTAR?**\n\n"
        
        # Explicação educativa
        worst_market = min(ev_markets, key=lambda x: x['ev_percentage']) if ev_markets else None
        
        if worst_market:
            prob = worst_market['probability']
            odds = worst_market['odds']
            ev_pct = worst_market['ev_percentage']
            
            message += f"Expected Value (EV) mede se uma aposta é lucrativa:\n"
            message += f"EV = (Probabilidade × Odds) - 1\n\n"
            message += f"Neste caso:\n"
            message += f"EV = ({prob:.2f} × {odds}) - 1 = {ev_pct/100:.4f}\n\n"
            message += f"**EV negativo = Prejuízo esperado a longo prazo**\n\n"
            
            # Simulação de 100 apostas
            loss_per_bet = abs(ev_pct)
            total_loss = loss_per_bet  # Perda esperada por aposta
            
            message += f"📊 **SIMULAÇÃO (100 apostas):**\n"
            message += f"Perda esperada por aposta: {loss_per_bet:.2f}%\n"
            message += f"Perda total esperada: {total_loss:.1f} unidades\n\n"
        
        message += f"{emoji_learn} **APRENDIZADO:**\n"
        message += f"O sistema calculou que as odds oferecidas\n"
        message += f"estão ABAIXO do valor justo baseado nas\n"
        message += f"probabilidades reais do jogo.\n\n"
        message += f"❌ **RECOMENDAÇÃO: NÃO APOSTAR**\n\n"
        message += f"_O bot só recomenda apostas com EV ≥ +5%_\n"
        message += f"_Isso garante lucro sustentável a longo prazo_"
        
        return message
    
    def format_opportunity_message(self, comparison: Dict, match_info: Dict) -> str:
        """
        Formata mensagem de oportunidade EV+ para notificação.
        
        Args:
            comparison: Resultado de compare_markets()
            match_info: Informações do jogo
        
        Returns:
            String formatada para Telegram
        """
        if not comparison.get('has_opportunity'):
            return comparison.get('message', 'Sem oportunidades')
        
        analysis = comparison['analysis']
        
        # Emojis para visualização
        emoji_fire = '🔥'
        emoji_chart = '📊'
        emoji_money = '💰'
        emoji_warning = '⚠️'
        
        message = f"{emoji_fire} **OPORTUNIDADE EV+ DETECTADA NO HT 0-0!**\n\n"
        message += f"**Jogo:** {match_info['home_team']} vs {match_info['away_team']}\n"
        message += f"**Liga:** {match_info['league']}\n"
        message += f"**Placar HT:** 0-0\n\n"
        
        message += f"{emoji_chart} **ANÁLISE {comparison['best_market']}**\n"
        message += f"• Odd: {analysis['odds']}\n"
        message += f"• Probabilidade: {analysis['probability']*100:.1f}%\n"
        message += f"• **EV: +{analysis['ev_percentage']:.2f}%**\n"
        message += f"• Confiança: {analysis['confidence']*100:.0f}%\n\n"
        
        message += f"{emoji_money} **GESTÃO DE BANCA**\n"
        message += f"• Kelly Completo: {analysis['kelly_full']:.1f}%\n"
        message += f"• Kelly Conservador: {analysis['kelly_conservative']:.1f}%\n"
        message += f"• **Stake Recomendado: {analysis['recommended_stake']:.1f}%**\n\n"
        
        # Se houver alternativa
        if comparison.get('alternative'):
            alt = comparison['alternative']['analysis']
            message += f"**Alternativa - {comparison['alternative']['market']}:**\n"
            message += f"Odd {alt['odds']} | EV +{alt['ev_percentage']:.1f}% | Stake {alt['recommended_stake']:.1f}%\n\n"
        
        message += f"{emoji_warning} *Gestão conservadora: usando 25% do Kelly*\n"
        message += f"*Stake ajustado pela confiança do modelo*"
        
        return message
