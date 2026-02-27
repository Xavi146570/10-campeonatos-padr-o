"""
Santo Graal Bot - Modo Best Available (SEM REPETIÇÕES)
Bot com cache para evitar notificar os mesmos jogos múltiplas vezes
"""

import requests
import time
from datetime import datetime, timedelta
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
# HTTP SERVER (RENDER/RAILWAY)
# ========================
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler para health check."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Santo Graal Bot is running!')
    
    def log_message(self, format, *args):
        pass

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
    """Bot principal com Modo Best Available e cache anti-repetição."""
    
    def __init__(self):
        self.api_key = config.API_FOOTBALL_KEY
        self.telegram_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = config.API_FOOTBALL_BASE_URL
        
        self.prob_calculator = ProbabilityCalculator()
        self.ev_detector = EVDetector()
        
        self.leagues = config.LEAGUES
        self.smart_mode_config = config.SMART_MODE_CONFIG
        
        self.best_available_mode = config.ENABLE_BEST_AVAILABLE_MODE
        self.best_available_count = config.BEST_AVAILABLE_COUNT
        
        # ========================================
        # CACHE: Jogos já notificados
        # ========================================
        self.notified_fixtures = {}  # {fixture_id: timestamp_notificacao}
        self.cache_duration = 3600  # 1 hora (em segundos)
        
        logger.info("✅ Santo Graal Bot inicializado")
        logger.info(f"🎯 Modo Best Available: {'ATIVO' if self.best_available_mode else 'DESATIVADO'}")
        logger.info(f"📊 TOP {self.best_available_count} jogos por ciclo")
        logger.info(f"🗄️ Cache anti-repetição: {self.cache_duration}s ({self.cache_duration//60} minutos)")
    
    def _clean_cache(self):
        """Remove jogos notificados há mais de 1 hora do cache."""
        now = datetime.now()
        expired_fixtures = [
            fixture_id for fixture_id, notified_at in self.notified_fixtures.items()
            if (now - notified_at).total_seconds() > self.cache_duration
        ]
        
        for fixture_id in expired_fixtures:
            del self.notified_fixtures[fixture_id]
        
        if expired_fixtures:
            logger.info(f"🧹 Limpou {len(expired_fixtures)} jogos do cache")
    
    def _is_already_notified(self, fixture_id):
        """Verifica se um jogo já foi notificado recentemente."""
        if fixture_id in self.notified_fixtures:
            notified_at = self.notified_fixtures[fixture_id]
            elapsed = (datetime.now() - notified_at).total_seconds()
            logger.info(f"⏭️ Jogo {fixture_id} já notificado há {elapsed:.0f}s (ignorando)")
            return True
        return False
    
    def _mark_as_notified(self, fixture_id):
        """Marca um jogo como já notificado."""
        self.notified_fixtures[fixture_id] = datetime.now()
        logger.info(f"✅ Jogo {fixture_id} marcado como notificado")
    
    def get_active_leagues(self):
        """Retorna ligas ativas baseado no Smart Mode (horário UTC)."""
        current_hour = datetime.utcnow().hour
        
        for period, config_data in self.smart_mode_config.items():
            start_hour, end_hour = config_data['hours']
            
            if start_hour > end_hour:
                if current_hour >= start_hour or current_hour < end_hour:
                    logger.info(f"⏰ Smart Mode: {period} ({start_hour}h-{end_hour}h UTC)")
                    return config_data['active_leagues'], config_data['check_interval']
            else:
                if start_hour <= current_hour < end_hour:
                    logger.info(f"⏰ Smart Mode: {period} ({start_hour}h-{end_hour}h UTC)")
                    return config_data['active_leagues'], config_data['check_interval']
        
        logger.warning("⚠️ Smart Mode fallback")
        return list(self.leagues.keys())[:10], 180
    
    def is_game_0x0(self, fixture):
        """Verifica se o jogo está 0-0 em qualquer momento válido (HT, 1H, 2H)."""
        status = fixture['fixture']['status']['short']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        
        valid_statuses = ['HT', '1H', '2H']
        
        if status in valid_statuses and home_score == 0 and away_score == 0:
            logger.info(f"✅ 0-0 detectado ({status}): {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            return True
        
        return False
    
    def get_live_fixtures(self, league_id):
        """Busca partidas ao vivo de uma liga específica."""
        url = f"{self.base_url}/fixtures"
        headers = {'x-apisports-key': self.api_key}
        params = {
            'league': league_id,
            'live': 'all'
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
        """Retorna multiplicadores baseados no status do jogo."""
        if status == 'HT':
            return (config.HALFTIME_0X0_MULTIPLIER_OVER_05, config.HALFTIME_0X0_MULTIPLIER_OVER_15)
        elif status == '2H':
            return (config.SECOND_HALF_0X0_MULTIPLIER_OVER_05, config.SECOND_HALF_0X0_MULTIPLIER_OVER_15)
        else:
            return (config.HALFTIME_0X0_MULTIPLIER_OVER_05, config.HALFTIME_0X0_MULTIPLIER_OVER_15)
    
    def analyze_fixture(self, fixture, league_name):
        """Analisa uma partida 0-0 e retorna oportunidades de apostas."""
        opportunities = []
        
        probs = self.prob_calculator.calculate_probabilities(
            fixture['teams']['home']['id'],
            fixture['teams']['away']['id'],
            fixture['league']['id']
        )
        
        if not probs:
            logger.warning(f"⚠️ Não conseguiu calcular probabilidades para {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            return opportunities
        
        status = fixture['fixture']['status']['short']
        mult_05, mult_15 = self.get_multipliers(status)
        
        prob_over_05 = min(probs['over_05'] * mult_05, 100.0)
        prob_over_15 = min(probs['over_15'] * mult_15, 100.0)
        
        offered_odds_05 = (100 / prob_over_05) * 0.95
        offered_odds_15 = (100 / prob_over_15) * 0.95
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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
        """Ranqueia oportunidades por qualidade."""
        for opp in opportunities:
            ev = opp['ev']
            prob = opp['probability']
            offered_odds = opp['offered_odds']
            fair_odds = 100 / prob
            
            if ev >= config.MIN_EV_POSITIVE and offered_odds > fair_odds:
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
    
    def send_telegram_message(self, message):
        """Envia mensagem para o Telegram."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("✅ Mensagem enviada com sucesso para Telegram")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar mensagem Telegram: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False
    
    def run(self):
        """Loop principal do bot."""
        logger.info("🚀 Santo Graal Bot iniciando...")
        logger.info(f"🎯 {len(self.leagues)} ligas configuradas")
        
        while True:
            try:
                # Limpar cache de jogos antigos
                self._clean_cache()
                
                active_league_names, check_interval = self.get_active_leagues()
                active_league_ids = [self.leagues[name] for name in active_league_names if name in self.leagues]
                
                logger.info(f"🔴 Verificando jogos ao vivo em {len(active_league_ids)} ligas...")
                
                all_opportunities = []
                
                for league_name in active_league_names:
                    if league_name not in self.leagues:
                        continue
                    
                    league_id = self.leagues[league_name]
                    fixtures = self.get_live_fixtures(league_id)
                    
                    for fixture in fixtures:
                        if self.is_game_0x0(fixture):
                            fixture_id = fixture['fixture']['id']
                            
                            # ========================================
                            # VERIFICAR SE JÁ FOI NOTIFICADO
                            # ========================================
                            if self._is_already_notified(fixture_id):
                                continue  # Pular este jogo
                            
                            opportunities = self.analyze_fixture(fixture, league_name)
                            all_opportunities.extend(opportunities)
                
                if all_opportunities:
                    logger.info(f"🎯 {len(all_opportunities)} oportunidades encontradas")
                    
                    ranked_opportunities = self.rank_opportunities(all_opportunities)
                    
                    if self.best_available_mode:
                        message = self.ev_detector.format_best_available_message(ranked_opportunities)
                        if message:
                            self.send_telegram_message(message)
                            logger.info(f"✅ TOP {self.best_available_count} oportunidades enviadas")
                            
                            # ========================================
                            # MARCAR JOGOS COMO NOTIFICADOS
                            # ========================================
                            for opp in ranked_opportunities[:self.best_available_count]:
                                fixture_id = opp['fixture']['fixture']['id']
                                self._mark_as_notified(fixture_id)
                    else:
                        for opp in ranked_opportunities:
                            if opp['ev'] >= config.MIN_EV_POSITIVE:
                                message = self.ev_detector.format_ev_message(
                                    opp['fixture'], opp['league_name'], opp['market'],
                                    opp['probability'], opp['offered_odds'],
                                    opp['ev'], opp['kelly'], opp['timestamp']
                                )
                                self.send_telegram_message(message)
                                
                                # Marcar como notificado
                                fixture_id = opp['fixture']['fixture']['id']
                                self._mark_as_notified(fixture_id)
                else:
                    logger.info("⏳ Nenhum jogo 0-0 encontrado no momento")
                
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
    config.validate_config()
    start_http_server()
    bot = SantoGraalBot()
    bot.run()
