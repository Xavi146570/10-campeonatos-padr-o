from datetime import datetime
from dateutil import tz

class MessageFormatter:
    def format_highlight_message(self, match_data):
        # Dados básicos
        home_team = match_data["home_team"]
        away_team = match_data["away_team"]
        home_avg = match_data["home_avg"]
        away_avg = match_data["away_avg"]
        
        # Configurações da liga
        config = match_data["league_config"]
        league_name = config["name"]
        min_threshold = match_data["min_threshold"]
        
        # Emojis de critério atendido
        home_emoji = "✅" if match_data["home_meets_criteria"] else ""
        away_emoji = "✅" if match_data["away_meets_criteria"] else ""
        
        # Formatação de data/hora
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
        
        # Dados históricos da liga
        hist = config["historical_minimums"]
        peaks = config["peak_minutes"]
        
        # Construir mensagem
        message = f"""🚨 JOGO EM DESTAQUE {day_label}!

⚽ {home_team} vs {away_team}
🕐 {day_label} às {time_str} ({tz_label})

📊 CRITÉRIO ATENDIDO - Médias Últimos 4 Jogos:
• {home_team}: {home_avg:.2f} gols/jogo {home_emoji}
• {away_team}: {away_avg:.2f} gols/jogo {away_emoji}
(Pelo menos uma ≥ {min_threshold:.2f})

🎯 MINUTOS DE PICO (Mínimos Históricos):
• 60': ≥{peaks['60']}% probabilidade
• 75': ≥{peaks['75']}% probabilidade  
• 85': ≥{peaks['85']}% probabilidade

📈 PADRÕES {league_name.upper()} (Mínimos dos Últimos 5 Anos):
• Média: ≥{hist['avg_goals_per_match']:.2f} gols/jogo
• BTTS: ≥{hist['btts_rate']}% | Over 2.5: ≥{hist['over25_rate']}%
• Over 3.5: ≥{hist['over35_rate']}% | 2º tempo: ≥{hist['second_half_share']}%

💡 Alto potencial ofensivo confirmado - fique atento!

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
