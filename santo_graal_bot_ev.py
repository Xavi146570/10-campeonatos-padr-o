"""
Santo Graal Bot com Detecção de Expected Value (EV+)
Versão aprimorada: mantém funcionalidade original + adiciona análise EV no HT 0-0
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import config_santo_graal as config
from probability_calculator_santo_graal import ProbabilityCalculatorSantoGraal
from ev_detector_santo_graal import EVDetectorSantoGraal


# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class SantoGraalBotEV:
    """
    Bot Santo Graal com detecção de Expected Value.
    
    Funcionalidades:
    1. Monitora times com baixa taxa de empate 0x0 (funcionalidade original)
    2. Verifica jogos 30 min antes do início
    3. Acompanha jogos ao vivo que estão 0-0
    4. Quando detecta HT 0-0, calcula EV+ para Over 0.5 e Over 1.5
    5. Envia notificação Telegram se odds são EV+
    """
    
    def __init__(self):
        self.api_key = config.API_FOOTBALL_KEY
        self.telegram_token = config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = "https://v3.football.api-sports.io"
        
        # Inicializar componentes de análise EV
        self.prob_calculator = ProbabilityCalculatorSantoGraal()
        self.ev_detector = EVDetectorSantoGraal()
        
        # Cache para evitar notificações duplicadas
        self.notified_matches = set()
        
        # Validar credenciais
        if not self.api_key or not self.telegram_token or not self.telegram_chat_id:
            raise ValueError("Credenciais API não configuradas! Verifique .env")
        
        logger.info("Santo Graal Bot EV+ inicializado")
    
    def run(self):
        """Loop principal do bot"""
        logger.info("🚀 Santo Graal Bot EV+ iniciado!")
        self.send_telegram_message("🤖 Santo Graal Bot EV+ ATIVO\n\nMonitorando jogos com baixa taxa 0x0...")
        
        while True:
            try:
                # 1. VERIFICAR JOGOS PRÓXIMOS (30 min antes)
                upcoming_matches = self.get_upcoming_matches()
                logger.info(f"Encontrados {len(upcoming_matches)} jogos próximos")
                
                for match in upcoming_matches:
                    self.analyze_upcoming_match(match)
                
                # 2. VERIFICAR JOGOS AO VIVO (0-0)
                live_matches = self.get_live_matches_0_0()
                logger.info(f"Encontrados {len(live_matches)} jogos ao vivo 0-0")
                
                for match in live_matches:
                    # Verificar se está no intervalo
                    if self.is_halftime(match):
                        self.analyze_ht_0_0(match)
                
                # Aguardar antes da próxima verificação
                time.sleep(config.HT_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}", exc_info=True)
                time.sleep(60)  # Aguardar 1 min em caso de erro
    
    def get_upcoming_matches(self) -> List[Dict]:
        """
        Busca jogos que começam nos próximos 30 minutos
        (Funcionalidade original do Santo Graal)
        """
        try:
            now = datetime.utcnow()
            start_time = now + timedelta(minutes=25)
            end_time = now + timedelta(minutes=35)
            
            matches = []
            
            for league_id in config.LEAGUES.keys():
                url = f"{self.base_url}/fixtures"
                params = {
                    'league': league_id,
                    'season': self._get_current_season(),
                    'from': start_time.strftime('%Y-%m-%d'),
                    'to': end_time.strftime('%Y-%m-%d')
                }
                
                response = self._make_api_request(url, params)
                
                if response and response.get('results', 0) > 0:
                    fixtures = response.get('response', [])
                    matches.extend(fixtures)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar jogos próximos: {e}")
            return []
    
    def get_live_matches_0_0(self) -> List[Dict]:
        """
        Busca jogos ao vivo com placar 0-0
        """
        try:
            matches = []
            
            for league_id in config.LEAGUES.keys():
                url = f"{self.base_url}/fixtures"
                params = {
                    'league': league_id,
                    'season': self._get_current_season(),
                    'live': 'all'
                }
                
                response = self._make_api_request(url, params)
                
                if response and response.get('results', 0) > 0:
                    fixtures = response.get('response', [])
                    
                    # Filtrar apenas 0-0
                    for fixture in fixtures:
                        score = fixture.get('goals', {})
                        if score.get('home') == 0 and score.get('away') == 0:
                            matches.append(fixture)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar jogos ao vivo: {e}")
            return []
    
    def is_halftime(self, match: Dict) -> bool:
        """Verifica se jogo está no intervalo (HT)"""
        status = match.get('fixture', {}).get('status', {}).get('short', '')
        return status == 'HT'
    
    def analyze_upcoming_match(self, match: Dict):
        """
        Analisa jogo próximo verificando taxa de empate 0x0 dos times
        (Funcionalidade original do Santo Graal)
        """
        try:
            fixture = match.get('fixture', {})
            teams = match.get('teams', {})
            
            home_team = teams.get('home', {}).get('name', 'N/A')
            away_team = teams.get('away', {}).get('name', 'N/A')
            match_id = fixture.get('id')
            
            # Verificar se já analisamos este jogo
            if match_id in self.notified_matches:
                return
            
            # Buscar estatísticas dos times
            home_stats = self.get_team_stats(teams.get('home', {}).get('id'))
            away_stats = self.get_team_stats(teams.get('away', {}).get('id'))
            
            if not home_stats or not away_stats:
                return
            
            # Verificar taxa de empate 0x0
            home_draw_rate = home_stats.get('draw_0x0_rate', 1.0)
            away_draw_rate = away_stats.get('draw_0x0_rate', 1.0)
            
            # Se ambos times têm BAIXA taxa de 0x0, é candidato para Santo Graal
            if (home_draw_rate <= config.MAX_DRAW_0X0_RATE and 
                away_draw_rate <= config.MAX_DRAW_0X0_RATE):
                
                logger.info(f"✅ Candidato Santo Graal: {home_team} vs {away_team}")
                logger.info(f"   Taxa 0x0: Casa {home_draw_rate:.1%} | Fora {away_draw_rate:.1%}")
                
                # Marcar como notificado
                self.notified_matches.add(match_id)
                
                # Enviar notificação
                msg = f"⚽ **SANTO GRAAL - Jogo Identificado**\n\n"
                msg += f"**{home_team} vs {away_team}**\n"
                msg += f"Liga: {config.LEAGUES.get(match.get('league', {}).get('id'), 'N/A')}\n"
                msg += f"Início: {fixture.get('date', 'N/A')}\n\n"
                msg += f"📊 **Taxa Empate 0x0:**\n"
                msg += f"• {home_team}: {home_draw_rate:.1%}\n"
                msg += f"• {away_team}: {away_draw_rate:.1%}\n\n"
                msg += f"🔍 Bot acompanhará ao vivo para análise EV+ no HT 0-0"
                
                self.send_telegram_message(msg)
                
        except Exception as e:
            logger.error(f"Erro ao analisar jogo próximo: {e}")
    
    def analyze_ht_0_0(self, match: Dict):
        """
        ANÁLISE PRINCIPAL NO HT 0-0 COM DETECÇÃO DE EV+
        
        Quando jogo chega ao intervalo 0-0:
        1. Calcula probabilidades Over 0.5 e Over 1.5 para o 2º tempo
        2. Busca odds disponíveis
        3. Calcula Expected Value (EV)
        4. Se EV+, envia notificação com recomendação
        """
        try:
            fixture = match.get('fixture', {})
            teams = match.get('teams', {})
            league = match.get('league', {})
            
            match_id = fixture.get('id')
            home_team = teams.get('home', {}).get('name', 'N/A')
            away_team = teams.get('away', {}).get('name', 'N/A')
            
            # Verificar se já notificamos este HT 0-0
            ht_key = f"HT_{match_id}"
            if ht_key in self.notified_matches:
                return
            
            logger.info(f"🔍 Analisando HT 0-0: {home_team} vs {away_team}")
            
            # 1. COLETAR ESTATÍSTICAS
            home_stats = self.get_team_stats(teams.get('home', {}).get('id'))
            away_stats = self.get_team_stats(teams.get('away', {}).get('id'))
            h2h_stats = self.get_h2h_stats(
                teams.get('home', {}).get('id'),
                teams.get('away', {}).get('id')
            )
            
            if not home_stats or not away_stats:
                logger.warning("Estatísticas incompletas, pulando análise")
                return
            
            # 2. COLETAR INFORMAÇÕES CONTEXTUAIS
            match_info = {
                'home_team': home_team,
                'away_team': away_team,
                'league': config.LEAGUES.get(league.get('id'), 'N/A'),
                'games_played': home_stats.get('games_played', 15),
                'home_position': home_stats.get('position', 10),
                'away_position': away_stats.get('position', 10),
                'is_derby': False  # Poderia implementar detecção de derbys
            }
            
            # 3. CALCULAR PROBABILIDADES
            probabilities = self.prob_calculator.calculate_probabilities_at_ht(
                home_stats,
                away_stats,
                h2h_stats,
                match_info
            )
            
            logger.info(f"Probabilidades calculadas:")
            logger.info(f"  Over 0.5: {probabilities['over_0_5']:.1%}")
            logger.info(f"  Over 1.5: {probabilities['over_1_5']:.1%}")
            logger.info(f"  Confiança: {probabilities['confidence']:.1%}")
            
            # 4. BUSCAR ODDS
            odds_data = self.get_live_odds(match_id)
            
            if not odds_data:
                logger.warning("Odds não disponíveis")
                return
            
            odds_over_0_5 = odds_data.get('over_0_5', 0)
            odds_over_1_5 = odds_data.get('over_1_5', 0)
            
            if not odds_over_0_5 and not odds_over_1_5:
                logger.warning("Nenhuma odd disponível para análise")
                return
            
            # 5. ANALISAR EV+ PARA OVER 0.5
            ev_analysis_0_5 = None
            if odds_over_0_5 > 0:
                ev_analysis_0_5 = self.ev_detector.analyze_opportunity(
                    market='Over 0.5',
                    probability=probabilities['over_0_5'],
                    odds=odds_over_0_5,
                    confidence=probabilities['confidence']
                )
            
            # 6. ANALISAR EV+ PARA OVER 1.5
            ev_analysis_1_5 = None
            if odds_over_1_5 > 0:
                ev_analysis_1_5 = self.ev_detector.analyze_opportunity(
                    market='Over 1.5',
                    probability=probabilities['over_1_5'],
                    odds=odds_over_1_5,
                    confidence=probabilities['confidence']
                )
            
            # 7. COMPARAR E DECIDIR MELHOR OPORTUNIDADE
            comparison = self.ev_detector.compare_markets(
                ev_analysis_0_5, 
                ev_analysis_1_5,
                over_0_5_prob=probabilities['over_0_5'],
                over_1_5_prob=probabilities['over_1_5'],
                over_0_5_odds=odds_over_0_5 or 0,
                over_1_5_odds=odds_over_1_5 or 0
            )
            
            # 8. ENVIAR NOTIFICAÇÃO
            if comparison.get('has_opportunity'):
                # 🔥 EV+ DETECTADO - APOSTAR!
                message = self.ev_detector.format_opportunity_message(comparison, match_info)
                self.send_telegram_message(message)
                
                logger.info(f"✅ EV+ DETECTADO: {home_team} vs {away_team}")
                logger.info(f"   Mercado: {comparison['best_market']}")
                logger.info(f"   EV: +{comparison['analysis']['ev_percentage']:.2f}%")
            else:
                # ⛔ EV- DETECTADO - NÃO APOSTAR (mas notificar para educação)
                logger.info(f"❌ Sem EV+: {home_team} vs {away_team}")
                
                # Verificar se deve notificar EV negativo
                if config.NOTIFICATION_SETTINGS.get('send_ev_negative', False):
                    message = self.ev_detector.format_ev_negative_message(comparison, match_info)
                    self.send_telegram_message(message)
                    logger.info(f"📚 Notificação educativa EV- enviada")
            
            # Marcar como notificado
            self.notified_matches.add(ht_key)
            
        except Exception as e:
            logger.error(f"Erro ao analisar HT 0-0: {e}", exc_info=True)
    
    def get_team_stats(self, team_id: int) -> Optional[Dict]:
        """
        Busca estatísticas do time na temporada atual.
        Retorna dados necessários para cálculo de probabilidades.
        """
        try:
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': team_id,
                'season': self._get_current_season(),
                'league': list(config.LEAGUES.keys())[0]  # Usar primeira liga como referência
            }
            
            response = self._make_api_request(url, params)
            
            if not response or response.get('results', 0) == 0:
                return None
            
            data = response.get('response', {})
            fixtures = data.get('fixtures', {})
            goals = data.get('goals', {})
            
            # Calcular estatísticas necessárias
            total_games = fixtures.get('played', {}).get('total', 0)
            
            if total_games < config.MIN_GAMES_PLAYED:
                return None
            
            # Taxa de Over 0.5 e Over 1.5 (aproximação baseada em gols)
            total_goals = goals.get('for', {}).get('total', {}).get('total', 0)
            avg_goals = total_goals / total_games if total_games > 0 else 1.5
            
            # Estimativa Over 0.5: ~85% dos jogos têm pelo menos 1 gol
            over_0_5_rate = 0.85
            
            # Estimativa Over 1.5 baseada em média de gols
            if avg_goals >= 2.5:
                over_1_5_rate = 0.75
            elif avg_goals >= 2.0:
                over_1_5_rate = 0.65
            else:
                over_1_5_rate = 0.55
            
            # Taxa de empate 0x0
            draws = fixtures.get('draws', {}).get('total', 0)
            # Estimar que ~40% dos empates são 0x0
            draw_0x0_rate = (draws * 0.4) / total_games if total_games > 0 else 0.15
            
            return {
                'team_id': team_id,
                'games_played': total_games,
                'goals_per_game': avg_goals,
                'over_0_5_rate': over_0_5_rate,
                'over_1_5_rate': over_1_5_rate,
                'recent_over_0_5_rate': 0.80,  # Valor padrão
                'recent_over_1_5_rate': 0.65,
                'draw_0x0_rate': draw_0x0_rate,
                'offensive_rating': 60,  # Valor padrão
                'goals_last_5': int(avg_goals * 5),
                'position': 10  # Valor padrão
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar stats do time {team_id}: {e}")
            return None
    
    def get_h2h_stats(self, home_id: int, away_id: int) -> Dict:
        """Busca estatísticas de confrontos diretos (H2H)"""
        try:
            url = f"{self.base_url}/fixtures/headtohead"
            params = {
                'h2h': f"{home_id}-{away_id}",
                'last': 5
            }
            
            response = self._make_api_request(url, params)
            
            if not response or response.get('results', 0) == 0:
                return {'total_games': 0, 'over_0_5_rate': 0.75, 'over_1_5_rate': 0.60}
            
            fixtures = response.get('response', [])
            total_games = len(fixtures)
            
            # Calcular taxa Over 0.5 e Over 1.5 nos H2H
            over_0_5_count = 0
            over_1_5_count = 0
            
            for fixture in fixtures:
                goals = fixture.get('goals', {})
                total = (goals.get('home', 0) + goals.get('away', 0))
                
                if total >= 1:
                    over_0_5_count += 1
                if total >= 2:
                    over_1_5_count += 1
            
            over_0_5_rate = over_0_5_count / total_games if total_games > 0 else 0.75
            over_1_5_rate = over_1_5_count / total_games if total_games > 0 else 0.60
            
            return {
                'total_games': total_games,
                'over_0_5_rate': over_0_5_rate,
                'over_1_5_rate': over_1_5_rate
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar H2H: {e}")
            return {'total_games': 0, 'over_0_5_rate': 0.75, 'over_1_5_rate': 0.60}
    
    def get_live_odds(self, fixture_id: int) -> Optional[Dict]:
        """
        Busca odds ao vivo para Over 0.5 e Over 1.5
        
        NOTA: API-Football requer plano específico para odds ao vivo.
        Esta função é um placeholder - adaptar conforme disponibilidade da API.
        """
        try:
            url = f"{self.base_url}/odds/live"
            params = {
                'fixture': fixture_id,
                'bet': 5  # Goals Over/Under
            }
            
            response = self._make_api_request(url, params)
            
            if not response or response.get('results', 0) == 0:
                # Se odds ao vivo não disponíveis, retornar odds estimadas
                logger.warning("Odds ao vivo não disponíveis, usando estimativas")
                return {
                    'over_0_5': 1.20,  # Odd típica Over 0.5
                    'over_1_5': 1.50   # Odd típica Over 1.5
                }
            
            # Processar odds da API
            # NOTA: Formato exato depende da resposta da API
            # Este é um exemplo genérico
            
            return {
                'over_0_5': 1.20,
                'over_1_5': 1.50
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar odds: {e}")
            return None
    
    def send_telegram_message(self, message: str):
        """Envia mensagem para Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Mensagem Telegram enviada")
            else:
                logger.error(f"❌ Erro ao enviar Telegram: {response.text}")
                
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
    
    def _make_api_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Faz requisição para API-Football"""
        try:
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na requisição API: {e}")
            return None
    
    def _get_current_season(self) -> int:
        """Retorna temporada atual baseada no mês"""
        now = datetime.utcnow()
        
        # Se jan-jun: temporada = ano anterior
        # Se jul-dez: temporada = ano atual
        if now.month <= 6:
            return now.year - 1
        else:
            return now.year


def main():
    """Função principal"""
    try:
        bot = SantoGraalBotEV()
        bot.run()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)


if __name__ == "__main__":
    main()
