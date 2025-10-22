"""
Santo Graal Bot EV+ - Sistema de Detecção de Expected Value
Versão com HTTP endpoint para Render Web Service (gratuito)
CORREÇÃO: Telegram MarkdownV2 escape perfeito

Monitora jogos 0-0 no HT e calcula probabilidades/EV para Over 0.5 e Over 1.5 FT
"""

import os
import sys
import time
import requests
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Imports para HTTP endpoint (Render Web Service)
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Imports locais
from config_santo_graal import Config
from probability_calculator_santo_graal import ProbabilityCalculator
from ev_detector_santo_graal import EVDetector

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# HTTP Health Check para Render Web Service
# ============================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler para health check - mantém Render Web Service ativo"""
    
    def do_GET(self):
        """Responde a requisições GET com status do bot"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Santo Graal Bot EV+</title>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif;
                    text-align: center; 
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                }
                .container {
                    background: rgba(255,255,255,0.15);
                    backdrop-filter: blur(10px);
                    padding: 40px;
                    border-radius: 20px;
                    display: inline-block;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                }
                h1 { margin: 0 0 20px 0; font-size: 2.5em; }
                .status { 
                    font-size: 1.2em; 
                    margin: 15px 0;
                    padding: 10px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                }
                .emoji { font-size: 3em; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji">🤖⚽</div>
                <h1>Santo Graal Bot EV+</h1>
                <div class="status">✅ Bot está ONLINE e funcionando!</div>
                <div class="status">🔄 Monitorando jogos 24/7</div>
                <div class="status">📊 Detectando oportunidades EV+</div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Silenciar logs HTTP para não poluir console"""
        pass


def run_health_check_server():
    """Inicia servidor HTTP na porta especificada (10000 no Render)"""
    port = int(os.getenv('PORT', 10000))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🌐 Servidor HTTP iniciado na porta {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor HTTP: {e}")


# ============================================================
# Funções Auxiliares
# ============================================================

def send_telegram_notification(message: str) -> bool:
    """
    Envia notificação via Telegram
    
    Args:
        message: Mensagem a enviar (suporta Markdown)
    
    Returns:
        True se enviado com sucesso, False caso contrário
    """
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            logger.error("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados")
            return False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'MarkdownV2',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"❌ Erro ao enviar Telegram: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exceção ao enviar Telegram: {e}")
        return False


# ============================================================
# Classe Principal do Bot
# ============================================================

class SantoGraalBot:
    """Bot principal que monitora jogos e detecta oportunidades EV+"""
    
    def __init__(self):
        """Inicializa o bot"""
        self.api_key = os.getenv('API_FOOTBALL_KEY')
        
        if not self.api_key:
            raise ValueError("❌ API_FOOTBALL_KEY não encontrada no .env")
        
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': self.api_key
        }
        
        self.probability_calculator = ProbabilityCalculator()
        self.ev_detector = EVDetector()
        
        # Cache para evitar notificações duplicadas
        self.notified_fixtures = set()
        
        logger.info("Santo Graal Bot EV+ inicializado")
    
    def get_upcoming_fixtures(self, hours_ahead: int = 24) -> List[Dict]:
        """
        Busca jogos próximos nas ligas configuradas
        
        Args:
            hours_ahead: Quantas horas à frente buscar
        
        Returns:
            Lista de fixtures
        """
        fixtures = []
        
        now = datetime.now(timezone.utc)
        date_from = now.strftime('%Y-%m-%d')
        date_to = (now + timedelta(hours=hours_ahead)).strftime('%Y-%m-%d')
        
        for league_id in Config.LEAGUES:
            try:
                url = f"{self.base_url}/fixtures"
                params = {
                    'league': league_id,
                    'season': Config.SEASON,
                    'from': date_from,
                    'to': date_to
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('response'):
                        fixtures.extend(data['response'])
                else:
                    logger.warning(f"⚠️ Erro ao buscar fixtures da liga {league_id}: {response.status_code}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Exceção ao buscar fixtures da liga {league_id}: {e}")
        
        return fixtures
    
    def get_live_fixtures(self) -> List[Dict]:
        """
        Busca jogos ao vivo nas ligas configuradas
        
        Returns:
            Lista de fixtures ao vivo
        """
        fixtures = []
        
        for league_id in Config.get_active_leagues():
            try:
                url = f"{self.base_url}/fixtures"
                params = {
                    'league': league_id,
                    'live': 'all'
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('response'):
                        fixtures.extend(data['response'])
                else:
                    logger.warning(f"⚠️ Erro ao buscar live fixtures da liga {league_id}: {response.status_code}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Exceção ao buscar live fixtures da liga {league_id}: {e}")
        
        return fixtures
    
    def get_fixture_statistics(self, fixture_id: int) -> Optional[Dict]:
        """
        Busca estatísticas de um jogo específico
        
        Args:
            fixture_id: ID do jogo
        
        Returns:
            Dicionário com estatísticas ou None
        """
        try:
            url = f"{self.base_url}/fixtures/statistics"
            params = {'fixture': fixture_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return data['response']
            else:
                logger.warning(f"⚠️ Erro ao buscar estatísticas do jogo {fixture_id}: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ Exceção ao buscar estatísticas do jogo {fixture_id}: {e}")
        
        return None
    
    def get_team_statistics(self, team_id: int, league_id: int) -> Optional[Dict]:
        """
        Busca estatísticas de um time na temporada
        
        Args:
            team_id: ID do time
            league_id: ID da liga
        
        Returns:
            Dicionário com estatísticas ou None
        """
        try:
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': team_id,
                'league': league_id,
                'season': Config.SEASON
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return data['response']
            else:
                logger.warning(f"⚠️ Erro ao buscar estatísticas do time {team_id}: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ Exceção ao buscar estatísticas do time {team_id}: {e}")
        
        return None
    
    def get_h2h(self, team1_id: int, team2_id: int, last_n: int = 10) -> List[Dict]:
        """
        Busca histórico de confrontos diretos
        
        Args:
            team1_id: ID do primeiro time
            team2_id: ID do segundo time
            last_n: Número de jogos a buscar
        
        Returns:
            Lista de confrontos
        """
        try:
            url = f"{self.base_url}/fixtures/headtohead"
            params = {
                'h2h': f"{team1_id}-{team2_id}",
                'last': last_n
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return data['response']
            else:
                logger.warning(f"⚠️ Erro ao buscar H2H {team1_id}-{team2_id}: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ Exceção ao buscar H2H {team1_id}-{team2_id}: {e}")
        
        return []
    
    def get_odds(self, fixture_id: int) -> Optional[Dict]:
        """
        Busca odds de um jogo específico
        
        Args:
            fixture_id: ID do jogo
        
        Returns:
            Dicionário com odds ou None
        """
        try:
            url = f"{self.base_url}/odds"
            params = {
                'fixture': fixture_id,
                'bookmaker': Config.BOOKMAKER_ID
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return data['response'][0] if data['response'] else None
            else:
                logger.warning(f"⚠️ Erro ao buscar odds do jogo {fixture_id}: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ Exceção ao buscar odds do jogo {fixture_id}: {e}")
        
        return None
    
    def extract_over_odds(self, odds_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """
        Extrai odds de Over 0.5 e Over 1.5 dos dados da API
        
        Args:
            odds_data: Dados de odds da API
        
        Returns:
            Tuple (over_05_odds, over_15_odds)
        """
        over_05 = None
        over_15 = None
        
        if not odds_data or 'bookmakers' not in odds_data:
            return over_05, over_15
        
        try:
            bookmakers = odds_data['bookmakers']
            
            for bookmaker in bookmakers:
                if 'bets' not in bookmaker:
                    continue
                
                for bet in bookmaker['bets']:
                    if bet['name'] == 'Goals Over/Under':
                        for value in bet['values']:
                            if value['value'] == 'Over 0.5':
                                over_05 = float(value['odd'])
                            elif value['value'] == 'Over 1.5':
                                over_15 = float(value['odd'])
        
        except Exception as e:
            logger.error(f"❌ Erro ao extrair odds: {e}")
        
        return over_05, over_15
    
    def check_0x0_draw_rate(self, team1_stats: Dict, team2_stats: Dict) -> bool:
        """
        Verifica se ambos os times têm taxa de empate 0-0 <= 15%
        
        Args:
            team1_stats: Estatísticas do time 1
            team2_stats: Estatísticas do time 2
        
        Returns:
            True se ambos atendem o critério
        """
        try:
            # Time 1
            fixtures1 = team1_stats.get('fixtures', {})
            draws1 = fixtures1.get('draws', {}).get('total', 0)
            total1 = fixtures1.get('played', {}).get('total', 0)
            
            if total1 == 0:
                return False
            
            draw_rate1 = (draws1 / total1) * 100
            
            # Time 2
            fixtures2 = team2_stats.get('fixtures', {})
            draws2 = fixtures2.get('draws', {}).get('total', 0)
            total2 = fixtures2.get('played', {}).get('total', 0)
            
            if total2 == 0:
                return False
            
            draw_rate2 = (draws2 / total2) * 100
            
            logger.info(f"📊 Taxa empate 0-0: Time1={draw_rate1:.1f}%, Time2={draw_rate2:.1f}%")
            
            return draw_rate1 <= Config.MAX_DRAW_RATE and draw_rate2 <= Config.MAX_DRAW_RATE
        
        except Exception as e:
            logger.error(f"❌ Erro ao verificar taxa de empate: {e}")
            return False
    
    def is_halftime_0x0(self, fixture: Dict) -> bool:
        """
        Verifica se o jogo está 0-0 no intervalo
        
        Args:
            fixture: Dados do jogo
        
        Returns:
            True se está 0-0 no HT
        """
        try:
            status = fixture.get('fixture', {}).get('status', {})
            short_status = status.get('short', '')
            
            # Verificar se está no intervalo
            if short_status != 'HT':
                return False
            
            # Verificar placar
            score = fixture.get('score', {})
            halftime = score.get('halftime', {})
            home = halftime.get('home')
            away = halftime.get('away')
            
            return home == 0 and away == 0
        
        except Exception as e:
            logger.error(f"❌ Erro ao verificar HT 0-0: {e}")
            return False
    
    def process_fixture(self, fixture: Dict):
        """
        Processa um jogo e detecta oportunidades EV+
        
        Args:
            fixture: Dados do jogo
        """
        try:
            fixture_id = fixture['fixture']['id']
            
            # Evitar processar múltiplas vezes
            if fixture_id in self.notified_fixtures:
                return
            
            home_team = fixture['teams']['home']
            away_team = fixture['teams']['away']
            league = fixture['league']
            
            logger.info(f"🔍 Processando: {home_team['name']} vs {away_team['name']}")
            
            # Buscar estatísticas dos times
            home_stats = self.get_team_statistics(home_team['id'], league['id'])
            away_stats = self.get_team_statistics(away_team['id'], league['id'])
            
            if not home_stats or not away_stats:
                logger.warning("⚠️ Não foi possível obter estatísticas dos times")
                return
            
            # Verificar taxa de empate 0-0
            if not self.check_0x0_draw_rate(home_stats, away_stats):
                logger.info("❌ Times não atendem critério de taxa de empate 0-0")
                return
            
            # Buscar H2H
            h2h_matches = self.get_h2h(home_team['id'], away_team['id'])
            
            # Calcular probabilidades
            match_data = {
                'home_stats': home_stats,
                'away_stats': away_stats,
                'h2h': h2h_matches,
                'is_ht_0x0': True  # Sabemos que está 0-0 no HT
            }
            
            prob_over_05, prob_over_15 = self.probability_calculator.calculate_probabilities(match_data)
            
            logger.info(f"📊 Probabilidades: Over 0.5 = {prob_over_05:.1f}%, Over 1.5 = {prob_over_15:.1f}%")
            
            # Buscar odds
            odds_data = self.get_odds(fixture_id)
            
            if not odds_data:
                logger.warning("⚠️ Não foi possível obter odds")
                return
            
            over_05_odds, over_15_odds = self.extract_over_odds(odds_data)
            
            if not over_05_odds or not over_15_odds:
                logger.warning("⚠️ Odds Over 0.5/1.5 não disponíveis")
                return
            
            logger.info(f"💰 Odds: Over 0.5 = {over_05_odds}, Over 1.5 = {over_15_odds}")
            
            # Detectar EV+
            opportunities = self.ev_detector.detect_ev_opportunities(
                prob_over_05=prob_over_05,
                prob_over_15=prob_over_15,
                over_05_odds=over_05_odds,
                over_15_odds=over_15_odds
            )
            
            # Processar oportunidades EV+
            for opp in opportunities:
                if opp['is_ev_positive']:
                    message = self.ev_detector.format_ev_message(
                        fixture=fixture,
                        opportunity=opp
                    )
                    
                    if send_telegram_notification(message):
                        logger.info("✅ Notificação EV+ enviada!")
                        self.notified_fixtures.add(fixture_id)
                    else:
                        logger.error("❌ Falha ao enviar notificação EV+")
                
                # Enviar notificação EV- se configurado
                elif Config.SEND_EV_NEGATIVE:
                    message = self.ev_detector.format_ev_negative_message(
                        fixture=fixture,
                        opportunity=opp
                    )
                    
                    send_telegram_notification(message)
                    logger.info("📚 Notificação EV- (educativa) enviada")
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar fixture: {e}")
    
    def run(self):
        """Executa o loop principal do bot"""
        logger.info("🚀 Santo Graal Bot EV+ iniciado!")
        
        while True:
            try:
                # Verificar jogos próximos (próximas 24h)
                logger.info("⏰ Verificando jogos nas próximas 24h...")
                upcoming = self.get_upcoming_fixtures(hours_ahead=24)
                logger.info(f"Encontrados {len(upcoming)} jogos próximos")
                
                # Verificar jogos ao vivo 0-0 no HT
                logger.info("🔴 Verificando jogos ao vivo...")
                live = self.get_live_fixtures()
                
                # Filtrar apenas jogos 0-0 no HT
                ht_0x0_fixtures = [f for f in live if self.is_halftime_0x0(f)]
                
                logger.info(f"Encontrados {len(ht_0x0_fixtures)} jogos ao vivo 0-0")
                
                # Processar jogos 0-0 no HT
                for fixture in ht_0x0_fixtures:
                    self.process_fixture(fixture)
                    time.sleep(1)  # Rate limiting
                
                # Aguardar antes do próximo ciclo
                logger.info(f"💤 Aguardando {Config.CHECK_INTERVAL} segundos até próxima verificação...")
                time.sleep(Config.CHECK_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("⚠️ Bot interrompido pelo usuário")
                break
            
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                time.sleep(60)  # Aguardar 1 minuto em caso de erro


# ============================================================
# Função Principal
# ============================================================

def main():
    """Função principal"""
    
    # Iniciar servidor HTTP em thread separada (para Render Web Service)
    health_thread = Thread(target=run_health_check_server, daemon=True)
    health_thread.start()
    logger.info(f"✅ Health check endpoint ativo na porta {os.getenv('PORT', 10000)}")
    
    bot = SantoGraalBot()
    
    try:
        # Enviar mensagem de inicialização
        # CORREÇÃO: Escape MarkdownV2 perfeito - SEM pontos decimais
        startup_message = (
            "🤖 *Santo Graal Bot EV\\+ Iniciado\\!*\n\n"
            f"📊 *Ligas monitoradas:* {len(Config.LEAGUES)}\n"
            f"⚡ *EV mínimo:* \\+{int(Config.MIN_EV_PERCENT)}%\n"
            f"💰 *Stake máximo:* {int(Config.MAX_STAKE_PERCENT)}% da banca\n"
            f"🎯 *Kelly Criterion:* {int(Config.KELLY_FRACTION * 100)}% conservador\n\n"
            "✅ Sistema pronto\\! Monitorando jogos 24/7"
        )
        send_telegram_notification(startup_message)
    except Exception as e:
        logger.error(f"❌ Erro ao enviar Telegram: {e}")
    
    # Iniciar bot
    bot.run()


if __name__ == "__main__":
    main()
