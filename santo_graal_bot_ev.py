"""
Santo Graal Bot - Modo Best Available
Bot completo que detecta jogos 0-0 (HT/1H/2H), ranqueia por EV e notifica TOP 2
"""

import requests
import time
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
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Santo Graal Bot is running!')
    
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
    """Bot principal com Modo Best Available."""
    
    def __init__(self):
        # .strip() previne problemas com quebras de linha (%0A)
        self.api_key = (config.API_FOOTBALL_KEY or "").strip()
        self.telegram_token = (config.TELEGRAM_BOT_TOKEN or "").strip()
        self.chat_id = (config.TELEGRAM_CHAT_ID or "").strip()
        self.base_url = config.API_FOOTBALL_BASE_URL
        
        self.prob_calculator = ProbabilityCalculator()
        self.ev_detector = EVDetector()
        
        self.leagues = config.LEAGUES
        self.smart_mode_config = config.SMART_MODE_CONFIG
        
        self.best_available_mode = config.ENABLE_BEST_AVAILABLE_MODE
        self.best_available_count = config.BEST_AVAILABLE_COUNT
        
        logger.info("✅ Santo Graal Bot inicializado")
        logger.info(f"🎯 Modo Best Available: {'ATIVO' if self.best_available_mode else 'DESATIVADO'}")
        logger.info(f"📊 TOP {self.best_available_count} jogos por ciclo")
    
    def get_active_leagues(self):
        """Retorna ligas ativas baseado no Smart Mode (horário UTC)."""
        current_hour = datetime.utcnow().hour
        
        for period, config_data in self.smart_mode_config.items():
            start_hour, end_hour = config_data['hours']
            
            # Tratamento especial para período que cruza meia-noite
            if start_hour > end_hour:  # Ex: 21h-03h
                if current_hour >= start_hour or current_hour < end_hour:
                    logger.info(f"⏰ Smart Mode: {period} ({start_hour}h-{end_hour}h UTC)")
                    return config_data['active_leagues'], config_data['check_interval']
            else:
                if start_hour <= current_hour < end_hour:
                    logger.info(f"⏰ Smart Mode: {period} ({start_hour}h-{end_hour}h UTC)")
                    return config_data['active_leagues'], config_data['check_interval']
        
        # Fallback (não deveria acontecer)
        logger.warning("⚠️ Smart Mode fallback - usando configuração padrão")
        return list(self.leagues.keys())[:10], 180
    
    def is_game_0x0(self, fixture):
        """
        Verifica se o jogo está 0-0 em qualquer momento válido (HT, 1H, 2H).
        """
        status = fixture['fixture']['status']['short']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        
        # Status válidos: HT (Intervalo), 1H (1º Tempo), 2H (2º Tempo)
        valid_statuses = ['HT', '1H', '2H']
        
        if status in valid_statuses and home_score == 0 and away_score == 0:
            logger.info(f"✅ 0-0 detectado ({status}): {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            return True
        
        return False
    
    def get_live_fixtures(self, league_id):
        """
        Busca partidas ao vivo de uma liga específica.
        """
        url = f"{self.base_url}/fixtures"
        headers = {
            'x-apisports-key': self.api_key
        }
        params = {
            'league': league_id,
            'live': 'all'  # IMPORTANTE: Não incluir 'season' ao buscar jogos ao vivo
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=config.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get('results', 0) > 0:
                return data['response']
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar fixtures da liga {league_id}: {e}")
            return []
    
    def get_multipliers(self, status):
        """
        Retorna multiplicadores baseados no status do jogo.
        """
        if status == 'HT':
            return (config.HALFTIME_0X0_MULTIPLIER_OVER_05, config.HALFTIME_0X0_MULTIPLIER_OVER_15)
        elif status == '2H':
            return (config.SECOND_HALF_0X0_MULTIPLIER_OVER_05, config.SECOND_HALF_0X0_MULTIPLIER_OVER_15)
        else:  # 1H ou outros
            return (config.HALFTIME_0X0_MULTIPLIER_OVER_05, config.HALFTIME_0X0_MULTIPLIER_OVER_15)
    
    def analyze_fixture(self, fixture, league_name):
        """
        Analisa uma partida 0-0 e retorna oportunidades de apostas.
        """
        opportunities = []
        
        # Calcular probabilidades base
        probs = self.prob_calculator.calculate_probabilities(
            fixture['teams']['home']['id'],
            fixture['teams']['away']['id'],
            fixture['league']['id']
        )
        
        if not probs:
            logger.warning(f"⚠️ Não foi possível calcular probabilidades para {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            return opportunities
        
        # Aplicar multiplicadores baseado no status
        status = fixture['fixture']['status']['short']
        mult_05, mult_15 = self.get_multipliers(status)
        
        prob_over_05 = min(probs['over_05'] * mult_05, 100.0)
        prob_over_15 = min(probs['over_15'] * mult_15, 100.0)
        
        # Mock de odds (em produção, usar API de odds real)
        offered_odds_05 = (100 / prob_over_05) * 0.95  # 5% margem da casa
        offered_odds_15 = (100 / prob_over_15) * 0.95
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Analisar Over 0.5
        ev_05 = self.ev_detector.calculate_ev(prob_over_05, offered_odds_05)
        kelly_05 = self.ev_detector.calculate_kelly(prob_over_05, offered_odds_05)
        
        opportunities.append({
            'fixture': fixture,
            'league_name': league_name,
            'market': 'Over 0.5 Goals (2nd Half)',
            'probability': prob_over_05,
            'offered_odds': offered_odds_05,
            'ev': ev_05,
            'kelly': kelly_05,
            'timestamp': timestamp
        })
        
        # Analisar Over 1.5
        ev_15 = self.ev_detector.calculate_ev(prob_over_15, offered_odds_15)
        kelly_15 = self.ev_detector.calculate_kelly(prob_over_15, offered_odds_15)
        
        opportunities.append({
            'fixture': fixture,
            'league_name': league_name,
            'market': 'Over 1.5 Goals (2nd Half)',
            'probability': prob_over_15,
            'offered_odds': offered_odds_15,
            'ev': ev_15,
            'kelly': kelly_15,
            'timestamp': timestamp
        })
        
        return opportunities
    
    def rank_opportunities(self, opportunities):
        """
        Ranqueia oportunidades por qualidade (EV+ e odds > fair primeiro, depois maior EV).
        """
        for opp in opportunities:
            ev = opp['ev']
            prob = opp['probability']
            offered_odds = opp['offered_odds']
            fair_odds = 100 / prob
            
            if ev >= config.MIN_EV_POSITIVE and offered_odds > fair_odds:
                bonus = 1000  # Grande bônus
            elif ev >= 0:
                bonus = 500
            else:
                bonus = 0
            
            opp['rank_score'] = bonus + (ev * 1000) + (prob * 0.1)
        
        ranked = sorted(opportunities, key=lambda x: x['rank_score'], reverse=True)
        for idx, opp in enumerate(ranked, 1):
            opp['rank'] = idx
        return ranked
    
    def send_telegram_safe(self, message):
        """Envia mensagem com fallback automático (HTML -> texto simples)."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # Primeira tentativa: HTML (resolve problemas com pontos em odds)
        payload_html = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload_html, timeout=config.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                return True
            else:
                logger.error(f"❌ Telegram rejeitou (HTML): {data}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Erro HTTP Telegram (HTML): {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar (HTML): {e}")
        
        # Fallback: Texto simples (sem formatação)
        payload_plain = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload_plain, timeout=config.API_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                return True
            else:
                logger.error(f"❌ Telegram rejeitou (Plain): {data}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar (Plain): {e}")
        
        return False
    
    def send_telegram_message(self, message):
        """Wrapper para compatibilidade com código existente."""
        return self.send_telegram_safe(message)
    
    def run(self):
        """Loop principal do bot."""
        logger.info("🚀 Santo Graal Bot iniciando...")
        logger.info(f"🎯 {len(self.leagues)} ligas configuradas")
        
        while True:
            try:
                # Determinar ligas ativas e intervalo baseado no Smart Mode
                active_league_names, check_interval = self.get_active_leagues()
                active_league_ids = [self.leagues[name] for name in active_league_names if name in self.leagues]
                
                logger.info(f"🔴 Verificando jogos ao vivo em {len(active_league_ids)} ligas...")
                
                all_opportunities = []
                
                # Buscar jogos 0-0 em todas as ligas ativas
                for league_name in active_league_names:
                    if league_name not in self.leagues:
                        continue
                    
                    league_id = self.leagues[league_name]
                    fixtures = self.get_live_fixtures(league_id)
                    
                    for fixture in fixtures:
                        if self.is_game_0x0(fixture):
                            opportunities = self.analyze_fixture(fixture, league_name)
                            all_opportunities.extend(opportunities)
                
                # Se houver oportunidades, ranquear e notificar TOP N
                if all_opportunities:
                    logger.info(f"🎯 {len(all_opportunities)} oportunidades encontradas")
                    
                    ranked_opportunities = self.rank_opportunities(all_opportunities)
                    
                    # Enviar TOP N (Best Available)
                    sent_count = 0
                    if self.best_available_mode:
                        message = self.ev_detector.format_best_available_message(
                            ranked_opportunities[:self.best_available_count]
                        )
                        if message and self.send_telegram_message(message):
                            sent_count = min(len(ranked_opportunities), self.best_available_count)
                            logger.info(f"✅ TOP {self.best_available_count} oportunidades enviadas")
                        else:
                            logger.error("❌ Falha ao enviar mensagem do Telegram")
                    else:
                        # Modo legado: enviar apenas EV+
                        for opp in ranked_opportunities:
                            if opp['ev'] >= config.MIN_EV_POSITIVE:
                                message = self.ev_detector.format_ev_message(
                                    opp['fixture'], opp['league_name'], opp['market'],
                                    opp['probability'], opp['offered_odds'],
                                    opp['ev'], opp['kelly'], opp['timestamp']
                                )
                                if self.send_telegram_message(message):
                                    sent_count += 1
                        
                        if sent_count > 0:
                            logger.info(f"✅ {sent_count} oportunidades EV+ enviadas")
                else:
                    logger.info("⏳ Nenhum jogo 0-0 encontrado no momento")
                
                # Aguardar próximo ciclo
                logger.info(f"⏰ Próxima verificação em {check_interval}s")
                time.sleep(check_interval)
            
            except KeyboardInterrupt:
                logger.info("⛔ Bot interrompido pelo usuário")
                break
            
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}", exc_info=True)
                time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente

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
