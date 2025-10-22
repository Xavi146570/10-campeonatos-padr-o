"""
Detector de Expected Value (EV) para Santo Graal Bot
Calcula EV, Kelly Criterion e formata notificações
"""

from typing import Dict, List, Optional
from config_santo_graal import Config


class EVDetector:
    """
    Detecta oportunidades de Expected Value positivo (EV+)
    
    Fórmula EV: (Probabilidade × Odds) - 1
    
    EV+ (≥ +5%): Apostar (value bet)
    EV- (< 0%): NÃO apostar (odds ruins)
    EV neutro (0-5%): Marginal
    """
    
    def __init__(self):
        """Inicializa o detector"""
        self.min_ev = Config.MIN_EV_PERCENT / 100  # Converter para decimal
        self.kelly_fraction = Config.KELLY_FRACTION
        self.max_stake = Config.MAX_STAKE_PERCENT / 100
        self.bankroll = Config.DEFAULT_BANKROLL
    
    def calculate_ev(self, probability: float, odds: float) -> float:
        """
        Calcula Expected Value
        
        Args:
            probability: Probabilidade em % (0-100)
            odds: Odds decimal (ex: 1.50)
        
        Returns:
            EV em decimal (ex: 0.05 = +5%)
        """
        prob_decimal = probability / 100
        ev = (prob_decimal * odds) - 1
        return ev
    
    def calculate_kelly_stake(
        self, 
        probability: float, 
        odds: float, 
        bankroll: Optional[float] = None
    ) -> float:
        """
        Calcula stake recomendado usando Kelly Criterion
        
        Fórmula: Kelly = (bp - q) / b
        Onde:
        - b = odds - 1
        - p = probabilidade de ganhar
        - q = probabilidade de perder (1 - p)
        
        Args:
            probability: Probabilidade em % (0-100)
            odds: Odds decimal
            bankroll: Banca disponível (default: Config.DEFAULT_BANKROLL)
        
        Returns:
            Stake recomendado em valor absoluto
        """
        if bankroll is None:
            bankroll = self.bankroll
        
        prob_decimal = probability / 100
        b = odds - 1
        p = prob_decimal
        q = 1 - p
        
        # Kelly completo
        kelly_full = (b * p - q) / b
        
        # Aplicar fração conservadora (25%)
        kelly_conservative = kelly_full * self.kelly_fraction
        
        # Garantir que não ultrapassa máximo permitido
        kelly_conservative = max(0, min(kelly_conservative, self.max_stake))
        
        # Calcular stake em valor absoluto
        stake = bankroll * kelly_conservative
        
        return stake
    
    def detect_ev_opportunities(
        self,
        prob_over_05: float,
        prob_over_15: float,
        over_05_odds: float,
        over_15_odds: float
    ) -> List[Dict]:
        """
        Detecta oportunidades EV+ em Over 0.5 e Over 1.5
        
        Args:
            prob_over_05: Probabilidade Over 0.5 (%)
            prob_over_15: Probabilidade Over 1.5 (%)
            over_05_odds: Odds Over 0.5
            over_15_odds: Odds Over 1.5
        
        Returns:
            Lista de oportunidades com detalhes
        """
        opportunities = []
        
        # Validar odds no range permitido
        if not (Config.MIN_ODDS_RANGE <= over_05_odds <= Config.MAX_ODDS_RANGE):
            over_05_odds = None
        
        if not (Config.MIN_ODDS_RANGE <= over_15_odds <= Config.MAX_ODDS_RANGE):
            over_15_odds = None
        
        # Analisar Over 0.5
        if over_05_odds and prob_over_05 >= Config.MIN_PROBABILITY_OVER_05:
            ev_05 = self.calculate_ev(prob_over_05, over_05_odds)
            stake_05 = self.calculate_kelly_stake(prob_over_05, over_05_odds)
            
            opportunities.append({
                'market': 'Over 0.5',
                'probability': prob_over_05,
                'odds': over_05_odds,
                'ev': ev_05,
                'ev_percent': ev_05 * 100,
                'is_ev_positive': ev_05 >= self.min_ev,
                'kelly_stake': stake_05,
                'stake_percent': (stake_05 / self.bankroll) * 100
            })
        
        # Analisar Over 1.5
        if over_15_odds and prob_over_15 >= Config.MIN_PROBABILITY_OVER_15:
            ev_15 = self.calculate_ev(prob_over_15, over_15_odds)
            stake_15 = self.calculate_kelly_stake(prob_over_15, over_15_odds)
            
            opportunities.append({
                'market': 'Over 1.5',
                'probability': prob_over_15,
                'odds': over_15_odds,
                'ev': ev_15,
                'ev_percent': ev_15 * 100,
                'is_ev_positive': ev_15 >= self.min_ev,
                'kelly_stake': stake_15,
                'stake_percent': (stake_15 / self.bankroll) * 100
            })
        
        return opportunities
    
    def format_ev_message(self, fixture: Dict, opportunity: Dict) -> str:
        """
        Formata mensagem Telegram para oportunidade EV+
        
        Args:
            fixture: Dados do jogo da API
            opportunity: Dados da oportunidade detectada
        
        Returns:
            Mensagem formatada em MarkdownV2
        """
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        league = fixture['league']['name']
        
        market = opportunity['market']
        probability = opportunity['probability']
        odds = opportunity['odds']
        ev_percent = opportunity['ev_percent']
        stake = opportunity['kelly_stake']
        stake_percent = opportunity['stake_percent']
        
        # Escapar caracteres especiais para MarkdownV2
        def escape_md(text):
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        home_escaped = escape_md(home_team)
        away_escaped = escape_md(away_team)
        league_escaped = escape_md(league)
        
        message = (
            f"🚨 *OPORTUNIDADE EV\\+* 🚨\n\n"
            f"⚽ *Jogo:* {home_escaped} vs {away_escaped}\n"
            f"🏆 *Liga:* {league_escaped}\n"
            f"📊 *Situação:* HT 0\\-0\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Mercado:* {escape_md(market)}\n"
            f"📈 *Probabilidade:* {probability:.1f}%\n"
            f"💵 *Odds:* {odds:.2f}\n"
            f"⚡ *Expected Value:* \\+{ev_percent:.1f}%\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 *RECOMENDAÇÃO KELLY:*\n"
            f"💸 *Stake:* ${stake:.2f} \\({stake_percent:.1f}% da banca\\)\n"
            f"🏦 *Base:* Banca de ${self.bankroll:.0f}\n\n"
            f"✅ *APOSTAR* \\- Value bet detectado\\!\n"
            f"🔥 Odds acima do valor justo\\!"
        )
        
        return message
    
    def format_ev_negative_message(self, fixture: Dict, opportunity: Dict) -> str:
        """
        Formata mensagem educativa para oportunidades EV- (negativas)
        
        Args:
            fixture: Dados do jogo da API
            opportunity: Dados da oportunidade (EV negativo)
        
        Returns:
            Mensagem formatada em MarkdownV2
        """
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        league = fixture['league']['name']
        
        market = opportunity['market']
        probability = opportunity['probability']
        odds = opportunity['odds']
        ev_percent = opportunity['ev_percent']
        
        # Calcular odds justas (implícitas)
        fair_odds = 100 / probability
        
        # Calcular prejuízo esperado em 100 apostas
        stake_per_bet = 10  # $10 por aposta (exemplo)
        total_staked = stake_per_bet * 100
        expected_return = (probability / 100) * odds * stake_per_bet * 100
        expected_loss = total_staked - expected_return
        
        # Escapar caracteres especiais
        def escape_md(text):
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        home_escaped = escape_md(home_team)
        away_escaped = escape_md(away_team)
        league_escaped = escape_md(league)
        
        message = (
            f"📚 *ALERTA EDUCATIVO \\- EV NEGATIVO* ⚠️\n\n"
            f"⚽ *Jogo:* {home_escaped} vs {away_escaped}\n"
            f"🏆 *Liga:* {league_escaped}\n"
            f"📊 *Situação:* HT 0\\-0\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Mercado:* {escape_md(market)}\n"
            f"📈 *Probabilidade calculada:* {probability:.1f}%\n"
            f"💵 *Odds oferecidas:* {odds:.2f}\n"
            f"⚡ *Expected Value:* {ev_percent:.1f}% \\(NEGATIVO\\)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ *POR QUE NÃO APOSTAR?*\n\n"
            f"🔢 *Matemática:*\n"
            f"• Odds justas: {fair_odds:.2f}\n"
            f"• Odds oferecidas: {odds:.2f}\n"
            f"• Diferença: {escape_md(f'{fair_odds - odds:.2f}')} pontos ABAIXO\n\n"
            f"💸 *Simulação \\(100 apostas de $10\\):*\n"
            f"• Total apostado: ${total_staked:.0f}\n"
            f"• Retorno esperado: ${expected_return:.0f}\n"
            f"• Prejuízo esperado: ${escape_md(f'-{expected_loss:.0f}')}\n\n"
            f"📉 *A longo prazo, você PERDE dinheiro\\!*\n\n"
            f"💡 *Lição:* Só aposte em EV\\+ \\(≥\\+5%\\)\\.\n"
            f"Odds ruins = Prejuízo garantido no longo prazo\\."
        )
        
        return message
    
    def compare_markets(self, opportunities: List[Dict]) -> Optional[Dict]:
        """
        Compara oportunidades e retorna a melhor (maior EV+)
        
        Args:
            opportunities: Lista de oportunidades detectadas
        
        Returns:
            Melhor oportunidade ou None
        """
        # Filtrar apenas EV+
        ev_positive = [opp for opp in opportunities if opp['is_ev_positive']]
        
        if not ev_positive:
            return None
        
        # Ordenar por EV (maior primeiro)
        ev_positive.sort(key=lambda x: x['ev'], reverse=True)
        
        return ev_positive[0]
