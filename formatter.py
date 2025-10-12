from datetime import datetime
from dateutil import tz
import os

class MessageFormatter:
    def format_highlight_message(self, match_data):
        """Formata mensagem completa com dados reais e padrões HT"""
        # Dados básicos
        home_team = match_data["home_team"]
        away_team = match_data["away_team"]
        home_avg = match_data["home_avg"]
        away_avg = match_data["away_avg"]
        
        # Configurações
        config = match_data["league_config"]
        league_name = config["name"]
        min_threshold = match_data["min_threshold"]
        
        # Stats reais da liga (se disponíveis)
        league_stats = match_data.get("league_real_stats")
        hist = config["historical_minimums"]
        peaks = config["peak_minutes"]
        
        # Controles de exibição
        show_peak_minutes = os.getenv("SHOW_PEAK_MINUTES", "true").lower() == "true"
        show_league_stats = os.getenv("SHOW_LEAGUE_STATS", "true").lower() == "true"
        show_ht_patterns = os.getenv("SHOW_HT_PATTERNS", "true").lower() == "true"
        
        # Emojis
        home_emoji = "✅" if match_data["home_meets_criteria"] else ""
        away_emoji = "✅" if match_data["away_meets_criteria"] else ""
        
        # Data/hora
        match_datetime = datetime.fromisoformat(
            match_data["match_time"].replace("Z", "+00:00")
        )
        league_tz = tz.gettz(config["timezone"])
        local_time = match_datetime.astimezone(league_tz)
        
        now_local = datetime.now(league_tz)
        if local_time.date() == now_local.date():
            day_label = "HOJE"
        else:
            day_label = local_time.strftime("%d/%m")
            
        time_str = local_time.strftime("%H:%M")
        tz_label = self._get_timezone_label(config["timezone"])
        
        # Construir mensagem
        message = f"""🚨 JOGO EM DESTAQUE {day_label}!

⚽ {home_team} vs {away_team}
🕐 {day_label} às {time_str} ({tz_label})

📊 CRITÉRIO ATENDIDO - Médias Últimos 4 Jogos:
• {home_team}: {home_avg:.2f} gols/jogo {home_emoji}
• {away_team}: {away_avg:.2f} gols/jogo {away_emoji}
(Pelo menos uma ≥ {min_threshold:.2f})"""

        # Seção HT (se habilitada e dados disponíveis)
        if show_ht_patterns and match_data.get("has_ht_data"):
            home_avg_ht = match_data["home_avg_ht"]
            away_avg_ht = match_data["away_avg_ht"]
            min_ht = match_data["min_threshold_ht"]
            
            home_emoji_ht = "🎯" if match_data["home_meets_ht"] else ""
            away_emoji_ht = "🎯" if match_data["away_meets_ht"] else ""
            
            message += f"""

🕐 PRIMEIRO TEMPO - Médias Últimos 4 Jogos:
• {home_team}: {home_avg_ht:.2f} gols HT {home_emoji_ht}
• {away_team}: {away_avg_ht:.2f} gols HT {away_emoji_ht}
(Critério HT: ≥ {min_ht:.2f})"""

        # Minutos de pico (se habilitado)
        if show_peak_minutes:
            message += f"""

🎯 MINUTOS DE PICO (Referência Histórica):
• 60': ≥{peaks['60']}% probabilidade
• 75': ≥{peaks['75']}% probabilidade  
• 85': ≥{peaks['85']}% probabilidade"""

        # Padrões da liga (se habilitado)
        if show_league_stats:
            # Usar dados reais se disponíveis, senão usar históricos
            if league_stats and league_stats.get("is_real"):
                stats_title = f"DADOS REAIS {league_name.upper()} (Últimos {league_stats['days_analyzed']} dias)"
                games_info = f" - {league_stats['total_games']} jogos"
                
                avg_goals = league_stats["avg_goals_per_match"]
                avg_goals_ht = league_stats["avg_goals_ht"]
                btts_rate = league_stats["btts_rate"]
                over15_ht = league_stats["over15_ht_rate"]
                over25_rate = league_stats["over25_rate"]
                over35_rate = league_stats["over35_rate"]
                sh_share = league_stats["second_half_share"]
            else:
                stats_title = f"PADRÕES {league_name.upper()} (Referência Histórica)"
                games_info = ""
                
                avg_goals = hist["avg_goals_per_match"]
                avg_goals_ht = round(avg_goals * 0.44, 2)  # Estimativa: ~44% dos gols no HT
                btts_rate = hist["btts_rate"]
                over15_ht = hist["over15_ht_rate"]
                over25_rate = hist["over25_rate"]
                over35_rate = hist["over35_rate"]
                sh_share = hist["second_half_share"]
            
            message += f"""

📈 {stats_title}{games_info}:
• Média: {avg_goals:.2f} gols/jogo | HT: {avg_goals_ht:.2f} gols/jogo
• BTTS: {btts_rate}% | Over 2.5: {over25_rate}% | Over 3.5: {over35_rate}%
• Over 1.5 HT: {over15_ht}% | 2º tempo: {sh_share}% dos gols"""

        # Rodapé
        data_source = "dados reais confirmam" if league_stats and league_stats.get("is_real") else "padrões sugerem"
        message += f"""

💡 {data_source.capitalize()} alto potencial ofensivo - fique atento!

📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}"""

        return message

    def _get_timezone_label(self, timezone_str):
        labels = {
            "Europe/London": "Londres", "Europe/Madrid": "Madrid", "Europe/Rome": "Roma",
            "Europe/Berlin": "Berlim", "Europe/Paris": "Paris", "Europe/Lisbon": "Lisboa",
            "Europe/Brussels": "Bruxelas", "Europe/Istanbul": "Istambul",
            "America/Sao_Paulo": "Brasília", "America/Argentina/Buenos_Aires": "Buenos Aires"
        }
        return labels.get(timezone_str, timezone_str.split("/")[-1])
