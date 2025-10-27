"""
EV Detector para Santo Graal Bot - Modo Best Available
Calcula Expected Value e formata mensagens TOP 2 com odd justa visível
"""

import config_santo_graal as config

class EVDetector:
    """Detector de Expected Value com formatação Best Available."""
    
    def __init__(self):
        self.min_ev = config.MIN_EV_POSITIVE
        self.kelly_fraction = config.KELLY_FRACTION
        self.best_available_mode = config.ENABLE_BEST_AVAILABLE_MODE
        self.best_available_count = config.BEST_AVAILABLE_COUNT
    
    def calculate_ev(self, probability, odds):
        """
        Calcula Expected Value.
        
        Args:
            probability (float): Probabilidade do evento (0-100)
            odds (float): Odd oferecida pela casa de apostas
        
        Returns:
            float: EV em decimal (ex: 0.15 = +15%)
        """
        prob_decimal = probability / 100
        ev = (prob_decimal * odds) - 1
        return ev
    
    def calculate_kelly(self, probability, odds):
        """
        Calcula stake recomendado usando Kelly Criterion (conservador 25%).
        
        Args:
            probability (float): Probabilidade do evento (0-100)
            odds (float): Odd oferecida
        
        Returns:
            float: Percentual do bankroll a apostar (0-100)
        """
        prob_decimal = probability / 100
        q = 1 - prob_decimal  # Probabilidade de perder
        b = odds - 1  # Ganho líquido por unidade apostada
        
        # Kelly = (bp - q) / b
        kelly = ((b * prob_decimal) - q) / b
        
        # Aplicar fração conservadora (25%)
        conservative_kelly = kelly * self.kelly_fraction
        
        # Limitar entre 0% e 25%
        return max(0, min(conservative_kelly * 100, 25))
    
    def calculate_fair_odds(self, probability):
        """
        Calcula a odd justa baseada na probabilidade.
        
        Args:
            probability (float): Probabilidade do evento (0-100)
        
        Returns:
            float: Odd justa
        """
        return 100 / probability if probability > 0 else 0
    
    def escape_markdown(self, text):
        """Escapa caracteres especiais para MarkdownV2."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def format_best_available_message(self, opportunities):
        """
        Formata mensagem para TOP jogos disponíveis (Modo Best Available).
        
        Args:
            opportunities (list): Lista de dicionários com oportunidades ranqueadas
                Cada dict contém: fixture, league_name, market, probability, 
                                  offered_odds, ev, kelly, timestamp, rank
        
        Returns:
            str: Mensagem formatada em MarkdownV2
        """
        if not opportunities:
            return None
        
        # Pegar apenas TOP N jogos
        top_opportunities = opportunities[:self.best_available_count]
        
        # Header
        msg = "🏆 *SANTO GRAAL \\- TOP OPORTUNIDADES* 🏆\n\n"
        
        for idx, opp in enumerate(top_opportunities, 1):
            fixture = opp['fixture']
            league_name = opp['league_name']
            market = opp['market']
            probability = opp['probability']
            offered_odds = opp['offered_odds']
            ev = opp['ev']
            kelly = opp['kelly']
            timestamp = opp['timestamp']
            
            # Calcular odd justa e distância
            fair_odds = self.calculate_fair_odds(probability)
            odds_diff = offered_odds - fair_odds
            odds_diff_percent = (odds_diff / fair_odds) * 100
            
            # Emoji de ranking
            rank_emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉"
            
            # Emoji de status EV
            if ev >= self.min_ev:
                ev_emoji = "✅ EV\\+"
                ev_color = "verde"
            else:
                ev_emoji = "⚠️ EV\\-"
                ev_color = "amarelo"
            
            # Escapar textos
            home_team = self.escape_markdown(fixture['teams']['home']['name'])
            away_team = self.escape_markdown(fixture['teams']['away']['name'])
            league_escaped = self.escape_markdown(league_name)
            status = self.escape_markdown(fixture['fixture']['status']['short'])
            
            # Linha de separação
            msg += f"{rank_emoji} *OPORTUNIDADE \\#{idx}* {rank_emoji}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Jogo
            msg += f"⚽ *{home_team} vs {away_team}*\n"
            msg += f"🏆 {league_escaped}\n"
            msg += f"⏱️ Status: *{status}* \\| Score: *{fixture['goals']['home']}\\-{fixture['goals']['away']}*\n\n"
            
            # Mercado
            msg += f"📊 *Mercado*: {self.escape_markdown(market)}\n\n"
            
            # Análise
            msg += f"🎯 *Probabilidade*: {probability:.1f}%\n"
            msg += f"💰 *Odd Oferecida*: {offered_odds:.2f}\n"
            msg += f"⚖️ *Odd Justa*: {fair_odds:.2f}\n"
            
            # Distância das odds
            if odds_diff > 0:
                msg += f"📈 *Distância*: \\+{odds_diff:.2f} \\({odds_diff_percent:+.1f}%\\) 🟢\n"
            else:
                msg += f"📉 *Distância*: {odds_diff:.2f} \\({odds_diff_percent:.1f}%\\) 🔴\n"
            
            msg += f"\n{ev_emoji} *Expected Value*: {ev*100:+.2f}%\n"
            msg += f"💵 *Kelly Stake*: {kelly:.2f}% do bankroll\n\n"
            
            # Recomendação
            if ev >= self.min_ev and offered_odds > fair_odds:
                msg += "✅ *RECOMENDAÇÃO*: APOSTAR \\(EV\\+ e Odd acima da justa\\)\n"
            elif ev >= 0:
                msg += "⚠️ *RECOMENDAÇÃO*: NEUTRO \\(EV próximo de zero\\)\n"
            else:
                msg += "❌ *RECOMENDAÇÃO*: PASSAR \\(EV negativo\\)\n"
            
            msg += f"🕒 Timestamp: {self.escape_markdown(timestamp)}\n"
            msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Footer
        msg += f"📌 *Total de oportunidades analisadas*: {len(opportunities)}\n"
        msg += f"🎯 *Mostrando TOP {len(top_opportunities)} melhores*\n\n"
        msg += "_Sistema Best Available \\- Sempre mostra as melhores opções disponíveis_"
        
        return msg
    
    def format_ev_message(self, fixture, league_name, market, probability, offered_odds, ev, kelly, timestamp):
        """
        Formata mensagem de EV (modo legado - mantido para compatibilidade).
        
        Args:
            fixture (dict): Dados da partida da API
            league_name (str): Nome da liga
            market (str): Mercado (Over 0.5 ou Over 1.5)
            probability (float): Probabilidade calculada (0-100)
            offered_odds (float): Odd oferecida pela casa de apostas
            ev (float): Expected Value calculado
            kelly (float): Stake recomendado (0-100)
            timestamp (str): Horário da análise
        
        Returns:
            str: Mensagem formatada em MarkdownV2
        """
        # Calcular odd justa
        fair_odds = self.calculate_fair_odds(probability)
        odds_diff = offered_odds - fair_odds
        odds_diff_percent = (odds_diff / fair_odds) * 100
        
        # Determinar emoji e mensagem
        if ev >= self.min_ev:
            emoji = "✅"
            ev_status = "EV\\+"
            recommendation = "APOSTAR"
        else:
            emoji = "⚠️"
            ev_status = "EV\\-"
            recommendation = "PASSAR \\(Educativo\\)"
        
        # Escapar caracteres especiais
        home_team = self.escape_markdown(fixture['teams']['home']['name'])
        away_team = self.escape_markdown(fixture['teams']['away']['name'])
        league_escaped = self.escape_markdown(league_name)
        market_escaped = self.escape_markdown(market)
        status = self.escape_markdown(fixture['fixture']['status']['short'])
        
        # Construir mensagem
        msg = f"{emoji} *SANTO GRAAL \\- {ev_status}* {emoji}\n\n"
        msg += f"⚽ *{home_team} vs {away_team}*\n"
        msg += f"🏆 {league_escaped}\n"
        msg += f"⏱️ Status: *{status}* \\| Score: *{fixture['goals']['home']}\\-{fixture['goals']['away']}*\n\n"
        msg += f"📊 *Mercado*: {market_escaped}\n"
        msg += f"🎯 *Probabilidade*: {probability:.1f}%\n"
        msg += f"💰 *Odd Oferecida*: {offered_odds:.2f}\n"
        msg += f"⚖️ *Odd Justa*: {fair_odds:.2f}\n"
        
        if odds_diff > 0:
            msg += f"📈 *Distância*: \\+{odds_diff:.2f} \\({odds_diff_percent:+.1f}%\\) 🟢\n\n"
        else:
            msg += f"📉 *Distância*: {odds_diff:.2f} \\({odds_diff_percent:.1f}%\\) 🔴\n\n"
        
        msg += f"💵 *Expected Value*: {ev*100:+.2f}%\n"
        msg += f"📈 *Kelly Stake*: {kelly:.2f}% do bankroll\n\n"
        msg += f"✅ *RECOMENDAÇÃO*: {self.escape_markdown(recommendation)}\n"
        msg += f"🕒 {self.escape_markdown(timestamp)}"
        
        return msg

if __name__ == "__main__":
    # Teste
    detector = EVDetector()
    print(f"✅ EV Detector inicializado")
    print(f"Modo Best Available: {detector.best_available_mode}")
    print(f"TOP jogos: {detector.best_available_count}")
    
    # Teste de cálculo
    prob = 65.0
    odds = 1.75
    ev = detector.calculate_ev(prob, odds)
    kelly = detector.calculate_kelly(prob, odds)
    fair = detector.calculate_fair_odds(prob)
    
    print(f"\n📊 Teste de Cálculo:")
    print(f"Probabilidade: {prob}%")
    print(f"Odd Oferecida: {odds}")
    print(f"Odd Justa: {fair:.2f}")
    print(f"EV: {ev*100:+.2f}%")
    print(f"Kelly: {kelly:.2f}%")
