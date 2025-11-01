"""
Santo Graal Bot - Versão Corrigida e Melhorada
Bot que detecta jogos 0-0 e envia alertas com odd justa para gol no 2º tempo
"""

import requests
import time
import json
import hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

import config_santo_graal as config
from probability_calculator_santo_graal import ProbabilityCalculator
from ev_detector_santo_graal import EVDetector

# ========================
# CONFIGURAÇÃO DE LOGGING
# ========================
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# ========================
# HTTP SERVER (RENDER)
# ========================
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler para health check do Render."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        payload = {
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "name": "Santo Graal Bot - Versão Corrigida"
        }
        self.wfile.write(json.dumps(payload).encode("utf-8"))
    
    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP

def start_http_server():
    """Inicia servidor HTTP em background."""
    server = HTTPServer(('0.0.0.0', config.HTTP_PORT), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"🌐 HTTP server started on port {config.HTTP_PORT}")

# ========================
# SANTO GRAAL BOT
# ========================
class SantoGraalBot:
    """Bot principal com alertas 0-0 e análise de oportunidades."""
    
    def __init__(self):
        # .strip() previne problemas com %0A no token/chat_id
        self.api_key = (config.API_FOOTBALL_KEY or "").strip()
        self.telegram_token = (config.TELEGRAM_BOT_TOKEN or "").strip()
        self.chat_id = (config.TELEGRAM_CHAT_ID or "").strip()
        self.base_url = config.API_FOOTBALL_BASE_URL
        
        self.prob_calculator = ProbabilityCalculator()
        self.ev_detector = EVDetector()
        
        self.leagues = config.LEAGUES
        self.smart_mode_config = config.SMART_MODE_CONFIG
        
        self.best_available_mode = getattr(config, "ENABLE_BEST_AVAILABLE_MODE", True)
        self.best_available_count = getattr(config, "BEST_AVAILABLE_COUNT", 2)
        
        # Cache para evitar duplicados
        self.immediate_alerts_sent = set()  # Para alertas 0-0: (fixture_id, status)
        self.notified_opportunities = set()  # Para oportunidades: opportunity_hash
        
        logger.info("✅ Santo Graal Bot inicializado")
        logger.info(f"🎯 Modo Best Available: {'ATIVO' if self.best_available_mode else 'DESATIVADO'}")
        logger.info(f"📊 TOP {self.best_available_count} jogos por ciclo")
    
    def get_active_leagues(self):
        """Retorna ligas ativas baseado no Smart Mode (horário UTC)."""
        current_hour = datetime.utcnow().hour
        
        for period, config_data in self.smart_mode_config.items():
            start_hour, end_hour = config_data['hours']
            
            # Tratamento para período que cruza meia-noite
            if start_hour > end_hour:  # Ex: 21h-03h
                if current_hour >= start_hour or current_hour < end_hour:
                    logger.info(f"⏰ Smart Mode: {period} ({start_hour}h-{end_hour}h UTC)")
                    return config_data['active_leagues'], config_data['check_interval']
            else:
                if start_hour <= current_hour < end_hour:
                    logger.info(f"⏰ Smart Mode: {period} ({start_hour}h-{end_hour}h UTC)")
                    return config_data['active_leagues'], config_data['check_interval']
        
        # Fallback
        logger.warning("⚠️ Smart Mode fallback - usando configuração padrão")
        return list(self.leagues.keys())[:10], 180
    
    def get_all_live_fixtures_and_filter(self, active_league_names):
        """Busca todos os jogos ao vivo e filtra pelas ligas ativas."""
        url = f"{self.base_url}/fixtures"
        headers = {'x-apisports-key': self.api_key}
        
        # Season dinâmica
        current_year = datetime.now().year
        season = current_year if datetime.now().month >= 8 else current_year - 1
        
        params = {
            'live': 'all',
            'timezone': 'UTC'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=config.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            all_fixtures = data.get('response', [])
            
            # Filtrar por ligas ativas
            active_ids = {self.leagues[name] for name in active_league_names if name in self.leagues}
            filtered = [f for f in all_fixtures if f['league']['id'] in active_ids]
            
            logger.info(f"📡 Live global: {len(all_fixtures)} | Filtrados: {len(filtered)}")
            
            # DEBUG: Mostrar jogos por liga
            for league_name in active_league_names:
                if league_name in self.leagues:
                    league_id = self.leagues[league_name]
                    league_fixtures = [f for f in filtered if f['league']['id'] == league_id]
                    if league_fixtures:
                        logger.info(f"🏆 {league_name}: {len(league_fixtures)} jogos")
                        
                        # Mostrar detalhes dos primeiros 3 jogos
                        for i, fixture in enumerate(league_fixtures[:3]):
                            status = fixture['fixture']['status']['short']
                            home_score = fixture['goals']['home']
                            away_score = fixture['goals']['away']
                            home_team = fixture['teams']['home']['name']
                            away_team = fixture['teams']['away']['name']
                            
                            logger.info(f"   🎮 {home_team} vs {away_team}")
                            logger.info(f"      Status: {status} | Placar: {home_score}-{away_score}")
                            
                            if status in ['HT', '1H', '2H'] and home_score == 0 and away_score == 0:
                                logger.info(f"      🚨 CANDIDATO 0-0 DETECTADO!")
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar fixtures live: {e}")
            return []
    
    def is_game_0x0(self, fixture):
        """Verifica se o jogo está 0-0 em status válido (HT, 1H, 2H)."""
        status = fixture['fixture']['status']['short']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        valid_statuses = ['HT', '1H', '2H']
        
        if status in valid_statuses and home_score == 0 and away_score == 0:
            logger.info(f"✅ 0-0 detectado ({status}): {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            return True
        return False
    
    def get_multipliers(self, status):
        """Retorna multiplicadores baseados no status do jogo."""
        if status == 'HT':
            return (
                getattr(config, 'HALFTIME_0X0_MULTIPLIER_OVER_05', 1.4),
                getattr(config, 'HALFTIME_0X0_MULTIPLIER_OVER_15', 1.3)
            )
        elif status == '2H':
            return (
                getattr(config, 'SECOND_HALF_0X0_MULTIPLIER_OVER_05', 1.2),
                getattr(config, 'SECOND_HALF_0X0_MULTIPLIER_OVER_15', 1.1)
            )
        else:  # 1H ou outros
            return (1.4, 1.3)
    
    def send_immediate_0x0_alert(self, fixture, league_name):
        """Envia alerta imediato quando detecta 0-0 com odd justa para gol no 2º tempo."""
        fixture_id = fixture['fixture']['id']
        status = fixture['fixture']['status']['short']
        
        # Evitar alertas duplicados por (fixture_id, status)
        alert_key = (fixture_id, status)
        if alert_key in self.immediate_alerts_sent:
            return False
        
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        
        # Calcular odd justa específica para gol no 2º tempo
        probs = self.prob_calculator.calculate_probabilities(
            fixture['teams']['home']['id'],
            fixture['teams']['away']['id'],
            fixture['league']['id']
        )
        
        if not probs:
            logger.warning(f"⚠️ Não conseguiu calcular probabilidades para {home_team} vs {away_team}")
            return False
        
        # Aplicar multiplicadores
        mult_05, _ = self.get_multipliers(status)
        prob_goal_2h = min(probs['over_05'] * mult_05, 99.9)
        fair_odds_2h = 100 / prob_goal_2h
        
        # Preparar mensagem
        status_emoji = "⏸️" if status == "HT" else "⚽" if status == "2H" else "🕐"
        status_info = {
            "HT": ("INTERVALO", "Todo o 2º tempo por jogar"),
            "2H": ("2º TEMPO", "Parte do 2º tempo restante"),
            "1H": ("1º TEMPO", "Ainda no 1º tempo")
        }
        status_text, time_info = status_info.get(status, (status, "Status específico"))
        
        message = f"""{status_emoji} <b>ALERTA 0-0 DETECTADO</b>

🎯 <b>{home_team} vs {away_team}</b>
🏆 Liga: {league_name}
📊 Status: {status_text} (resultado 0-0)
⏱️ Situação: {time_info}

🎲 <b>ODD JUSTA p/ GOL NO 2ºT: {fair_odds_2h:.2f}</b>
📈 Probabilidade calculada: {prob_goal_2h:.1f}%

💡 <b>AÇÃO RECOMENDADA:</b>
• Procura odds superiores a {fair_odds_2h:.2f} no mercado
• Foca em "Over 0.5 Goals 2nd Half" ou similar
• Qualquer odd acima desta tem EV positivo

⏰ {datetime.now().strftime('%H:%M:%S')}

🤖 <i>Santo Graal Bot - Alerta Automático</i>"""
        
        if self.send_telegram_safe(message):
            self.immediate_alerts_sent.add(alert_key)
            return True
        return False
    
    def analyze_fixture(self, fixture, league_name):
        """Analisa uma partida 0-0 e retorna oportunidades de apostas."""
        opportunities = []
        
        probs = self.prob_calculator.calculate_probabilities(
            fixture['teams']['home']['id'],
            fixture['teams']['away']['id'],
            fixture['league']['id']
        )
        
        if not probs:
            return opportunities
        
        # Aplicar multiplicadores
        status = fixture['fixture']['status']['short']
        mult_05, mult_15 = self.get_multipliers(status)
        prob_over_05 = min(probs['over_05'] * mult_05, 99.9)
        prob_over_15 = min(probs['over_15'] * mult_15, 99.9)
        
        # Odds simuladas (margem 5%)
        offered_odds_05 = (100 / prob_over_05) * 0.95
        offered_odds_15 = (100 / prob_over_15) * 0.95
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Over 0.5 (2nd Half)
        ev_05 = self.ev_detector.calculate_ev(prob_over_05, offered_odds_05)
        kelly_05 = self.ev_detector.calculate_kelly(prob_over_05, offered_odds_05)
        
        opportunities.append({
            'fixture': fixture,
            'league_name': league_name,
            'market': 'Over 0.5 Goals (2nd Half)',
            'probability': prob_over_05,
            'fair_odds': 100 / prob_over_05,
            'offered_odds': offered_odds_05,
            'ev': ev_05,
            'kelly': kelly_05,
            'timestamp': timestamp
        })
        
        # Over 1.5 (2nd Half)
        ev_15 = self.ev_detector.calculate_ev(prob_over_15, offered_odds_15)
        kelly_15 = self.ev_detector.calculate_kelly(prob_over_15, offered_odds_15)
        
        opportunities.append({
            'fixture': fixture,
            'league_name': league_name,
            'market': 'Over 1.5 Goals (2nd Half)',
            'probability': prob_over_15,
            'fair_odds': 100 / prob_over_15,
            'offered_odds': offered_odds_15,
            'ev': ev_15,
            'kelly': kelly_15,
            'timestamp': timestamp
        })
        
        return opportunities
    
    def rank_opportunities(self, opportunities):
        """Ranqueia oportunidades por qualidade."""
        min_ev = getattr(config, 'MIN_EV_POSITIVE', 2.0)
        
        for opp in opportunities:
            ev = opp['ev']
            prob = opp['probability']
            offered_odds = opp['offered_odds']
            fair_odds = opp['fair_odds']
            
            if ev >= min_ev and offered_odds > fair_odds:
                bonus = 1000
            elif ev >= 0:
                bonus = 500
            else:
                bonus = 0
            
            opp['rank_score'] = bonus + (ev * 1000) + (prob * 0.1)
        
        ranked = sorted(opportunities, key=lambda x: x['rank_score'], reverse=True)
        for idx, opp in enumerate(ranked, 1):
            opp['rank'] = idx
        return ranked
    
    def format_enhanced_message(self, opportunities):
        """Formata mensagem destacando odds justas."""
        if not opportunities:
            return ""
        
        header = "🏆 <b>SANTO GRAAL - OPORTUNIDADES PREMIUM</b>\n\n"
        
        messages = []
        for i, opp in enumerate(opportunities[:self.best_available_count], 1):
            fixture = opp['fixture']
            status = fixture['fixture']['status']['short']
            
            # Status info
            status_info = {
                'HT': ('⏸️', 'INTERVALO', 'Todo o 2º tempo por jogar'),
                '2H': ('⚽', '2º TEMPO', 'Parte do 2º tempo restante'),
                '1H': ('🕐', '1º TEMPO', 'Ainda no 1º tempo')
            }
            emoji, status_text, time_info = status_info.get(status, ('📊', status, 'Status específico'))
            
            # Destacar odd justa
            is_second_half = "Over 0.5 Goals (2nd Half)" in opp['market']
            if is_second_half:
                fair_odds_highlight = f"🎯 <b>Odd Justa p/ Gol no 2ºT: {opp['fair_odds']:.2f}</b>"
                explanation = "Qualquer odd acima desta tem EV positivo!"
            else:
                fair_odds_highlight = f"📊 Odd Justa: {opp['fair_odds']:.2f}"
                explanation = "Baseado em análise específica"
            
            message = f"""{emoji} <b>#{i} - {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}</b>
🏆 Liga: {opp['league_name']}
📊 Status: {status_text} (0-0) - {time_info}

{fair_odds_highlight}
💡 {explanation}

📈 <b>ANÁLISE DETALHADA:</b>
• Probabilidade: {opp['probability']:.1f}%
• Mercado: {opp['market']}
• <b>EV: {opp['ev']:+.2f}%</b>

💰 <b>RECOMENDAÇÃO:</b>
• Procura odds superiores a {opp['fair_odds']:.2f}
• Odd Simulada: {opp['offered_odds']:.2f}

⏰ {opp['timestamp']}
"""
            messages.append(message)
        
        return header + "\n".join(messages)
    
    def send_telegram_safe(self, message):
        """Envia mensagem com fallback HTML -> texto simples."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # Primeira tentativa: HTML
        payload_html = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload_html, timeout=15)
            response.raise_for_status()
            if response.json().get("ok"):
                return True
            else:
                logger.error(f"❌ Telegram rejeitou (HTML): {response.json()}")
        except Exception as e:
            logger.error(f"❌ Erro envio HTML: {e}")
        
        # Fallback: texto simples
        payload_plain = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload_plain, timeout=15)
            response.raise_for_status()
            return response.json().get("ok", False)
        except Exception as e:
            logger.error(f"❌ Erro envio Plain: {e}")
            return False
    
    def send_telegram_message(self, message):
        """Wrapper de compatibilidade."""
        return self.send_telegram_safe(message)
    
    def test_specific_game(self, home_partial, away_partial):
        """Testa um jogo específico para debug."""
        url = f"{self.base_url}/fixtures"
        headers = {'x-apisports-key': self.api_key}
        params = {'live': 'all', 'timezone': 'UTC'}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])
                
                for fixture in fixtures:
                    home = fixture['teams']['home']['name'].lower()
                    away = fixture['teams']['away']['name'].lower()
                    
                    if (home_partial.lower() in home and away_partial.lower() in away):
                        logger.info(f"🎯 JOGO ENCONTRADO!")
                        logger.info(f"   🏠 Casa: {fixture['teams']['home']['name']}")
                        logger.info(f"   🚗 Fora: {fixture['teams']['away']['name']}")
                        logger.info(f"   📊 Status: {fixture['fixture']['status']['short']}")
                        logger.info(f"   ⚽ Placar: {fixture['goals']['home']}-{fixture['goals']['away']}")
                        logger.info(f"   🏆 Liga: {fixture['league']['name']}")
                        logger.info(f"   🆔 ID: {fixture['fixture']['id']}")
                        
                        would_detect = self.is_game_0x0(fixture)
                        logger.info(f"   🤖 Bot detectaria: {'SIM' if would_detect else 'NÃO'}")
                        return fixture
                
                logger.info(f"❌ Jogo {home_partial} vs {away_partial} não encontrado")
        except Exception as e:
            logger.error(f"❌ Erro no teste: {e}")
        return None
    
    def run(self):
        """Loop principal do bot."""
        logger.info("🚀 Santo Graal Bot iniciando...")
        logger.info(f"🎯 {len(self.leagues)} ligas configuradas")
        
        while True:
            try:
                # Determinar ligas ativas
                active_league_names, check_interval = self.get_active_leagues()
                logger.info(f"🔍 Analisando {len(active_league_names)} ligas ativas...")
                logger.info(f"🏆 Ligas: {', '.join(active_league_names[:5])}{'...' if len(active_league_names) > 5 else ''}")
                
                # Buscar jogos live
                fixtures = self.get_all_live_fixtures_and_filter(active_league_names)
                
                all_opportunities = []
                alerts_sent = 0
                
                for fixture in fixtures:
                    if self.is_game_0x0(fixture):
                        league_name = fixture['league']['name']
                        
                        # Enviar alerta imediato 0-0
                        if self.send_immediate_0x0_alert(fixture, league_name):
                            alerts_sent += 1
                            logger.info(f"🚨 Alerta 0-0 enviado: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                        
                        # Análise para oportunidades
                        opportunities = self.analyze_fixture(fixture, league_name)
                        all_opportunities.extend(opportunities)
                
                if alerts_sent > 0:
                    logger.info(f"📢 {alerts_sent} alertas 0-0 enviados neste ciclo")
                
                # Processar oportunidades
                if all_opportunities:
                    logger.info(f"🎯 {len(all_opportunities)} oportunidades encontradas")
                    
                    # Filtrar por EV mínimo
                    min_ev = getattr(config, 'MIN_EV_POSITIVE', 2.0)
                    quality_opportunities = [opp for opp in all_opportunities if opp['ev'] >= min_ev]
                    
                    if quality_opportunities:
                        ranked = self.rank_opportunities(quality_opportunities)
                        
                        if self.best_available_mode:
                            message = self.format_enhanced_message(ranked)
                            if message and self.send_telegram_message(message):
                                logger.info(f"✅ TOP {min(len(ranked), self.best_available_count)} oportunidades enviadas")
                        else:
                            # Modo individual
                            sent_count = 0
                            for opp in ranked[:self.best_available_count]:
                                msg = self.format_enhanced_message([opp])
                                if self.send_telegram_message(msg):
                                    sent_count += 1
                            logger.info(f"✅ {sent_count} oportunidades individuais enviadas")
                    else:
                        logger.info("📊 Nenhuma oportunidade atende critério de EV mínimo")
                else:
                    if alerts_sent == 0:
                        logger.info("⏳ Nenhum jogo 0-0 encontrado no momento")
                
                # Próximo ciclo
                logger.info(f"⏰ Próxima verificação em {check_interval}s")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("⛔ Bot interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}", exc_info=True)
                time.sleep(60)

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    # Validar configuração
    config.validate_config()
    
    # Iniciar HTTP server
    start_http_server()
    
    # Iniciar bot
    bot = SantoGraalBot()
    bot.run()
