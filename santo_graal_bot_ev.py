"""
Santo Graal Bot - Super Powered Edition
Bot profissional de value betting com odds reais, gestão de risco e tracking completo
"""

import requests
import time
import sqlite3
import json
import hashlib
import asyncio
import aiohttp
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import config_santo_graal as config
from probability_calculator_santo_graal import ProbabilityCalculator
from ev_detector_santo_graal import EVDetector

# ========================
# ESTRUTURAS DE DADOS
# ========================
@dataclass
class Opportunity:
    """Estrutura para oportunidades de apostas."""
    fixture_id: int
    home_team: str
    away_team: str
    league_name: str
    status: str
    market: str
    probability: float
    fair_odds: float
    best_odds: float
    best_bookmaker: str
    ev: float
    kelly_stake: float
    confidence: float
    timestamp: datetime
    opportunity_hash: str

# ========================
# CONFIGURAÇÃO DE LOGGING
# ========================
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# ========================
# GERENCIADOR DE BASE DE DADOS
# ========================
class DatabaseManager:
    """Gerenciador da base de dados SQLite para tracking."""
    
    def __init__(self, db_path: str = "santo_graal.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa tabelas necessárias."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de oportunidades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER NOT NULL,
                opportunity_hash TEXT UNIQUE NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                league_name TEXT NOT NULL,
                status TEXT NOT NULL,
                market TEXT NOT NULL,
                probability REAL NOT NULL,
                fair_odds REAL NOT NULL,
                best_odds REAL NOT NULL,
                best_bookmaker TEXT NOT NULL,
                ev REAL NOT NULL,
                kelly_stake REAL NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabela de performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_opportunities INTEGER DEFAULT 0,
                avg_ev REAL DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                best_ev REAL DEFAULT 0,
                notifications_sent INTEGER DEFAULT 0
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_opportunities_fixture_id ON opportunities(fixture_id)')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de dados inicializada")
    
    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """Salva oportunidade evitando duplicados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO opportunities 
                (fixture_id, opportunity_hash, home_team, away_team, league_name, status, 
                 market, probability, fair_odds, best_odds, best_bookmaker, ev, kelly_stake, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opportunity.fixture_id, opportunity.opportunity_hash, opportunity.home_team,
                opportunity.away_team, opportunity.league_name, opportunity.status,
                opportunity.market, opportunity.probability, opportunity.fair_odds,
                opportunity.best_odds, opportunity.best_bookmaker, opportunity.ev,
                opportunity.kelly_stake, opportunity.confidence
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar oportunidade: {e}")
            return False
    
    def mark_as_notified(self, opportunity_hash: str):
        """Marca oportunidade como notificada."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE opportunities SET notified_at = CURRENT_TIMESTAMP WHERE opportunity_hash = ?',
                (opportunity_hash,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Erro ao marcar como notificada: {e}")
    
    def get_performance_stats(self, days: int = 7) -> Dict:
        """Retorna estatísticas dos últimos N dias."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_opportunities,
                    COUNT(CASE WHEN notified_at IS NOT NULL THEN 1 END) as notified,
                    AVG(ev) as avg_ev,
                    MAX(ev) as best_ev,
                    AVG(confidence) as avg_confidence
                FROM opportunities 
                WHERE created_at >= date('now', '-{} days')
            '''.format(days))
            
            stats = cursor.fetchone()
            conn.close()
            
            return {
                'total_opportunities': stats[0] or 0,
                'notified_opportunities': stats[1] or 0,
                'avg_ev': round(stats[2] or 0, 2),
                'best_ev': round(stats[3] or 0, 2),
                'avg_confidence': round(stats[4] or 0, 2)
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}

# ========================
# PROVEDOR DE ODDS REAIS
# ========================
class OddsProvider:
    """Integração com APIs de odds reais."""
    
    def __init__(self):
        self.odds_api_key = config.ODDS_API_KEY
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache = {}  # Cache de odds com TTL
        self.cache_ttl = 300  # 5 minutos
        
        self.active = bool(self.odds_api_key and self.odds_api_key != "YOUR_ODDS_API_KEY")
        logger.info(f"🎰 Odds Provider: {'ATIVO' if self.active else 'DESATIVADO (usando simulação)'}")
    
    async def get_best_odds_async(self, fixture_id: int, market: str) -> Optional[Dict]:
        """Busca melhores odds para um mercado específico."""
        if not self.active:
            return None
        
        cache_key = f"{fixture_id}_{market}"
        
        # Verificar cache
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cached_data['data']
        
        try:
            # Mapear mercado para formato da API
            api_market = self._map_market_to_api(market)
            if not api_market:
                return None
            
            url = f"{self.base_url}/sports/soccer/odds"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'eu',
                'markets': api_market,
                'oddsFormat': 'decimal',
                'bookmakers': 'bet365,pinnacle,betfair_ex_eu,unibet'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        best_odds_data = self._extract_best_odds(data, fixture_id, market)
                        
                        if best_odds_data:
                            # Salvar no cache
                            self.cache[cache_key] = {
                                'data': best_odds_data,
                                'timestamp': datetime.now()
                            }
                            return best_odds_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds para fixture {fixture_id}: {e}")
        
        return None
    
    def _map_market_to_api(self, market: str) -> Optional[str]:
        """Mapeia mercados internos para formato da API."""
        mapping = {
            'Over 0.5 Goals (2nd Half)': 'totals',
            'Over 1.5 Goals (2nd Half)': 'totals'
        }
        return mapping.get(market)
    
    def _extract_best_odds(self, api_data: List, fixture_id: int, market: str) -> Optional[Dict]:
        """Extrai melhores odds dos dados da API."""
        best_odds = 0.0
        best_bookmaker = ""
        
        target_point = 0.5 if "0.5" in market else 1.5
        
        for event in api_data:
            if str(event.get('id')) == str(fixture_id):
                for bookmaker in event.get('bookmakers', []):
                    for market_data in bookmaker.get('markets', []):
                        if market_data['key'] == 'totals':
                            for outcome in market_data['outcomes']:
                                if (outcome.get('name') == 'Over' and 
                                    outcome.get('point') == target_point):
                                    odds = outcome.get('price', 0)
                                    if odds > best_odds:
                                        best_odds = odds
                                        best_bookmaker = bookmaker['title']
        
        if best_odds > 1.0:
            return {
                'odds': best_odds,
                'bookmaker': best_bookmaker,
                'is_real': True
            }
        
        return None

# ========================
# RISK MANAGER
# ========================
class RiskManager:
    """Gestão de risco com Kelly Criterion."""
    
    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.max_kelly_fraction = 0.25  # Máximo 25%
        self.min_stake = 10.0
        self.max_stake = 100.0
        
        logger.info(f"💰 Risk Manager: Bankroll €{bankroll}")
    
    def calculate_optimal_stake(self, probability: float, odds: float, confidence: float) -> Dict:
        """Calcula stake ótimo usando Kelly modificado."""
        # Kelly Criterion: f = (bp - q) / b
        b = odds - 1
        p = probability / 100
        q = 1 - p
        
        if b <= 0 or p <= 0:
            return {'recommended_stake': 0, 'kelly_fraction': 0}
        
        # Kelly fractionário
        kelly_fraction = (b * p - q) / b
        
        # Ajustar por confiança
        adjusted_kelly = kelly_fraction * (confidence / 100)
        
        # Aplicar limites
        capped_kelly = min(max(adjusted_kelly, 0), self.max_kelly_fraction)
        
        # Calcular stake
        theoretical_stake = self.bankroll * capped_kelly
        final_stake = max(min(theoretical_stake, self.max_stake), 
                         self.min_stake if capped_kelly > 0 else 0)
        
        return {
            'recommended_stake': round(final_stake, 2),
            'kelly_fraction': round(capped_kelly, 4),
            'bankroll_percentage': round((final_stake / self.bankroll) * 100, 2)
        }

# ========================
# BOT PRINCIPAL SUPER PODEROSO
# ========================
class SuperSantoGraalBot:
    """Versão super poderosa do Santo Graal Bot."""
    
    def __init__(self):
        # Componentes principais
        self.db = DatabaseManager()
        self.odds_provider = OddsProvider()
        self.risk_manager = RiskManager(config.INITIAL_BANKROLL)
        
        # Configurações base
        self.api_key = (config.API_FOOTBALL_KEY or "").strip()
        self.telegram_token = (config.TELEGRAM_BOT_TOKEN or "").strip()
        self.chat_id = (config.TELEGRAM_CHAT_ID or "").strip()
        self.base_url = config.API_FOOTBALL_BASE_URL
        
        # Calculadoras existentes
        self.prob_calculator = ProbabilityCalculator()
        self.ev_detector = EVDetector()
        
        # Configurações
        self.leagues = config.LEAGUES
        self.smart_mode_config = config.SMART_MODE_CONFIG
        self.best_available_count = config.BEST_AVAILABLE_COUNT
        
        # Cache para duplicados
        self.notified_hashes = set()
        
        logger.info("🚀 Super Santo Graal Bot inicializado")
        logger.info(f"💾 Base de dados: Ativa")
        logger.info(f"🎰 Odds reais: {'ATIVO' if self.odds_provider.active else 'SIMULADO'}")
        logger.info(f"💰 Bankroll: €{config.INITIAL_BANKROLL}")
    
    def generate_opportunity_hash(self, fixture_id: int, market: str, status: str, odds: float) -> str:
        """Gera hash único para evitar duplicados."""
        unique_string = f"{fixture_id}_{market}_{status}_{odds:.2f}_{datetime.now().strftime('%Y%m%d%H')}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def calculate_confidence(self, fixture_data: Dict, odds_data: Optional[Dict]) -> float:
        """Calcula nível de confiança da oportunidade."""
        base_confidence = 70.0
        
        # Ajustes baseados no status
        status = fixture_data.get('fixture', {}).get('status', {}).get('short', '')
        if status == 'HT':
            base_confidence += 15  # Intervalo é momento ideal
        elif status == '2H':
            base_confidence += 10  # Segundo tempo
        
        # Ajuste baseado em odds reais vs simuladas
        if odds_data and odds_data.get('is_real'):
            base_confidence += 10
        else:
            base_confidence -= 15  # Penalizar odds simuladas
        
        return min(max(base_confidence, 0), 100)
    
    async def analyze_fixture_advanced(self, fixture: Dict, league_name: str) -> List[Opportunity]:
        """Análise avançada com odds reais."""
        opportunities = []
        
        try:
            # Calcular probabilidades base
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
            
            prob_over_05 = min(probs['over_05'] * mult_05, 100.0)
            prob_over_15 = min(probs['over_15'] * mult_15, 100.0)
            
            # Analisar mercados
            markets = [
                ('Over 0.5 Goals (2nd Half)', prob_over_05),
                ('Over 1.5 Goals (2nd Half)', prob_over_15)
            ]
            
            for market, probability in markets:
                # Buscar odds reais
                odds_data = await self.odds_provider.get_best_odds_async(fixture['fixture']['id'], market)
                
                # Fallback para odds simuladas se necessário
                if not odds_data:
                    fair_odds = 100 / probability
                    simulated_odds = fair_odds * (1 - config.BOOKMAKER_MARGIN_SIMULATED)
                    odds_data = {
                        'odds': simulated_odds,
                        'bookmaker': 'Simulado',
                        'is_real': False
                    }
                
                # Calcular métricas
                fair_odds = 100 / probability
                ev = ((odds_data['odds'] * probability / 100) - 1) * 100
                
                # Filtrar apenas EV positivo
                if ev < config.MIN_EV_POSITIVE:
                    continue
                
                # Calcular confiança
                confidence = self.calculate_confidence(fixture, odds_data)
                
                # Calcular stake Kelly
                risk_analysis = self.risk_manager.calculate_optimal_stake(
                    probability, odds_data['odds'], confidence
                )
                
                # Gerar hash único
                opportunity_hash = self.generate_opportunity_hash(
                    fixture['fixture']['id'], market, status, odds_data['odds']
                )
                
                # Verificar duplicados
                if opportunity_hash in self.notified_hashes:
                    continue
                
                # Criar oportunidade
                opportunity = Opportunity(
                    fixture_id=fixture['fixture']['id'],
                    home_team=fixture['teams']['home']['name'],
                    away_team=fixture['teams']['away']['name'],
                    league_name=league_name,
                    status=status,
                    market=market,
                    probability=probability,
                    fair_odds=fair_odds,
                    best_odds=odds_data['odds'],
                    best_bookmaker=odds_data['bookmaker'],
                    ev=ev,
                    kelly_stake=risk_analysis['recommended_stake'],
                    confidence=confidence,
                    timestamp=datetime.now(),
                    opportunity_hash=opportunity_hash
                )
                
                opportunities.append(opportunity)
                
        except Exception as e:
            logger.error(f"❌ Erro na análise avançada: {e}")
        
        return opportunities
    
    def get_multipliers(self, status: str) -> Tuple[float, float]:
        """Retorna multiplicadores baseados no status."""
        if status == 'HT':
            return (config.HALFTIME_0X0_MULTIPLIER_OVER_05, config.HALFTIME_0X0_MULTIPLIER_OVER_15)
        elif status == '2H':
            return (config.SECOND_HALF_0X0_MULTIPLIER_OVER_05, config.SECOND_HALF_0X0_MULTIPLIER_OVER_15)
        else:
            return (config.HALFTIME_0X0_MULTIPLIER_OVER_05, config.HALFTIME_0X0_MULTIPLIER_OVER_15)
    
    def format_super_message(self, opportunities: List[Opportunity]) -> str:
        """Formata mensagem super completa."""
        if not opportunities:
            return ""
        
        header = "🏆 <b>SANTO GRAAL - OPORTUNIDADES PREMIUM</b>\n\n"
        
        messages = []
        for i, opp in enumerate(opportunities[:self.best_available_count], 1):
            odds_type = "✅ Real" if opp.best_bookmaker != "Simulado" else "🟡 Simulada"
            
            message = f"""🎯 <b>#{i} - {opp.home_team} vs {opp.away_team}</b>
🏆 Liga: {opp.league_name}
📊 Status: {opp.status} (0-0)
💰 Mercado: {opp.market}

📈 <b>ANÁLISE:</b>
• Probabilidade: {opp.probability:.1f}%
• Odd Justa: {opp.fair_odds:.2f}
• <b>Melhor Odd: {opp.best_odds:.2f}</b> ({odds_type})
• <b>EV: {opp.ev:+.2f}%</b>
• Confiança: {opp.confidence:.0f}%

💡 <b>RECOMENDAÇÃO KELLY:</b>
• Stake Sugerido: €{opp.kelly_stake:.2f}
• Bookmaker: {opp.best_bookmaker}

⏰ {opp.timestamp.strftime('%H:%M:%S')}
"""
            messages.append(message)
        
        # Estatísticas
        stats = self.db.get_performance_stats(7)
        if stats:
            footer = f"""
📊 <b>PERFORMANCE (7 dias):</b>
• Oportunidades: {stats['total_opportunities']}
• Notificadas: {stats['notified_opportunities']}
• EV Médio: {stats['avg_ev']:+.1f}%
• Melhor EV: {stats['best_ev']:+.1f}%
"""
        else:
            footer = ""
        
        return header + "\n".join(messages) + footer
    
    def send_telegram_safe(self, message: str) -> bool:
        """Envio seguro com fallback HTML -> texto."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # HTML primeiro
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
        except Exception as e:
            logger.error(f"❌ Erro HTML: {e}")
        
        # Fallback texto simples
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
            logger.error(f"❌ Erro Plain: {e}")
            return False
    
    async def run_super_cycle(self):
        """Ciclo super avançado do bot."""
        try:
            # Determinar ligas ativas
            active_league_names, check_interval = self.get_active_leagues()
            logger.info(f"🔍 Analisando {len(active_league_names)} ligas ativas...")
            
            all_opportunities = []
            
            # Buscar jogos 0-0
            for league_name in active_league_names:
                if league_name not in self.leagues:
                    continue
                
                league_id = self.leagues[league_name]
                fixtures = await self.get_live_fixtures_async(league_id)
                
                for fixture in fixtures:
                    if self.is_game_0x0(fixture):
                        opportunities = await self.analyze_fixture_advanced(fixture, league_name)
                        all_opportunities.extend(opportunities)
            
            # Processar oportunidades
            if all_opportunities:
                logger.info(f"🎯 {len(all_opportunities)} oportunidades encontradas")
                
                # Salvar na base de dados
                for opp in all_opportunities:
                    self.db.save_opportunity(opp)
                
                # Filtrar por qualidade
                quality_opportunities = [
                    opp for opp in all_opportunities 
                    if opp.ev >= config.MIN_EV_POSITIVE and opp.confidence >= config.MIN_CONFIDENCE_THRESHOLD
                ]
                
                if quality_opportunities:
                    # Ranquear por EV ponderado por confiança
                    ranked = sorted(quality_opportunities, 
                                  key=lambda x: (x.ev * 0.7 + x.confidence * 0.3), 
                                  reverse=True)
                    
                    # Enviar TOP N
                    message = self.format_super_message(ranked)
                    if message and self.send_telegram_safe(message):
                        # Marcar como notificadas
                        for opp in ranked[:self.best_available_count]:
                            self.notified_hashes.add(opp.opportunity_hash)
                            self.db.mark_as_notified(opp.opportunity_hash)
                        
                        logger.info(f"✅ {min(len(ranked), self.best_available_count)} oportunidades premium enviadas")
                    else:
                        logger.error("❌ Falha ao enviar notificação")
                else:
                    logger.info("📊 Oportunidades não atendem critérios de qualidade")
            else:
                logger.info("⏳ Nenhum jogo 0-0 encontrado")
            
            return check_interval
            
        except Exception as e:
            logger.error(f"❌ Erro no ciclo super: {e}", exc_info=True)
            return 120
    
    def get_active_leagues(self):
        """Determina ligas ativas baseado no Smart Mode."""
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
        
        return list(self.leagues.keys())[:10], 180
    
    async def get_live_fixtures_async(self, league_id: int) -> List[Dict]:
        """Busca fixtures de forma assíncrona."""
        url = f"{self.base_url}/fixtures"
        headers = {'x-apisports-key': self.api_key}
        params = {'league': league_id, 'live': 'all'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', [])
        except Exception as e:
            logger.error(f"❌ Erro ao buscar fixtures async: {e}")
        
        return []
    
    def is_game_0x0(self, fixture: Dict) -> bool:
        """Verifica se jogo está 0-0."""
        status = fixture['fixture']['status']['short']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        
        valid_statuses = ['HT', '1H', '2H']
        
        if status in valid_statuses and home_score == 0 and away_score == 0:
            logger.info(f"✅ 0-0 detectado ({status}): {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            return True
        
        return False
    
    async def run_forever(self):
        """Loop principal assíncrono."""
        logger.info("🚀 Super Santo Graal Bot iniciando...")
        
        while True:
            try:
                check_interval = await self.run_super_cycle()
                logger.info(f"⏰ Próxima verificação em {check_interval}s")
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("⛔ Bot interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}", exc_info=True)
                await asyncio.sleep(60)

# ========================
# HTTP SERVER
# ========================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'version': 'Super Powered Edition'
        }
        
        self.wfile.write(json.dumps(status).encode())
    
    def log_message(self, format, *args):
        pass

def start_http_server():
    server = HTTPServer(('0.0.0.0', config.HTTP_PORT), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"🌐 HTTP server started on port {config.HTTP_PORT}")

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    # Validar configuração
    config.validate_config()
    
    # Iniciar HTTP server
    start_http_server()
    
    # Iniciar bot super poderoso
    bot = SuperSantoGraalBot()
    
    # Executar de forma assíncrona
    try:
        asyncio.run(bot.run_forever())
    except KeyboardInterrupt:
        logger.info("👋 Super Santo Graal Bot finalizado")
