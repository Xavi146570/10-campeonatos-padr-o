import os
import json
import time
import threading
from datetime import datetime

from .config.leagues import LEAGUE_CONFIGS
from .providers.api_football import ApiFootballClient
from .providers.telegram_sender import TelegramSender
from .engine.analyzer import MatchAnalyzer
from .engine.formatter import MessageFormatter

class FootballProcessor:
    def __init__(self):
        self.is_running = False
        self.last_execution = None
        self.execution_history = []
        self.logs = []
        self.lock = threading.Lock()

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with self.lock:
            self.logs.append(log_entry)
            if len(self.logs) > 200:
                self.logs = self.logs[-200:]

    def is_processing(self):
        return self.is_running

    def get_recent_logs(self, lines=50):
        with self.lock:
            return self.logs[-lines:] if lines <= len(self.logs) else self.logs

    def get_execution_history(self):
        return self.execution_history[-10:]

    def process_all_leagues(self, dry_run=None):
        if self.is_running:
            self.log("⚠️ Processamento já em andamento")
            return
        
        self.is_running = True
        start_time = datetime.now()
        
        try:
            effective_dry_run = dry_run if dry_run is not None else os.getenv("GLOBAL_DRY_RUN", "false").lower() == "true"
            
            self.log(f"🚀 Iniciando processamento - {'DRY RUN' if effective_dry_run else 'PRODUÇÃO'}")
            self.log(f"🏆 Processando {len(LEAGUE_CONFIGS)} ligas")
            
            # Inicializar clientes
            api = ApiFootballClient()
            telegram = TelegramSender()
            
            # Estatísticas globais
            total_games = 0
            total_alerts = 0
            leagues_processed = 0
            
            # Processar cada liga
            for league_code, league_config in LEAGUE_CONFIGS.items():
                try:
                    self.log(f"🔍 Processando {league_config['name']}...")
                    
                    result = self._process_single_league_internal(
                        league_code, league_config, api, telegram, effective_dry_run
                    )
                    
                    leagues_processed += 1
                    total_games += result.get("games_analyzed", 0)
                    total_alerts += result.get("alerts_sent", 0)
                    
                    self.log(f"✅ {league_config['name']}: {result.get('alerts_sent', 0)} alertas")
                    
                    # Pausa entre ligas
                    time.sleep(2)
                    
                except Exception as e:
                    self.log(f"❌ Erro em {league_config.get('name', league_code)}: {e}")
                    continue
            
            # Relatório final
            duration = datetime.now() - start_time
            execution_summary = {
                "timestamp": start_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "leagues_processed": leagues_processed,
                "total_games": total_games,
                "total_alerts": total_alerts,
                "api_requests": api.request_count,
                "dry_run": effective_dry_run
            }
            
            self.execution_history.append(execution_summary)
            self.last_execution = execution_summary
            
            self.log(f"🎉 Processamento concluído!")
            self.log(f"📊 Resumo: {leagues_processed} ligas, {total_games} jogos, {total_alerts} alertas")
            self.log(f"⏱️ Duração: {duration.total_seconds():.1f}s")
            
            # Enviar resumo para admin
            self._send_admin_summary(execution_summary, telegram, effective_dry_run)
            
        except Exception as e:
            self.log(f"💥 Erro crítico: {e}")
        finally:
            self.is_running = False

    def _process_single_league_internal(self, league_code, league_config, api, telegram, dry_run):
        analyzer = MatchAnalyzer(league_config)
        formatter = MessageFormatter()
        
        # Buscar jogos
        fixtures = api.get_fixtures_today(
            league_config["api_id"],
            league_config["timezone"]
        )
        
        if not fixtures:
            return {"games_analyzed": 0, "alerts_sent": 0}
        
        # Coletar IDs únicos
        team_ids = []
        for fixture in fixtures:
            team_ids.extend([
                fixture["teams"]["home"]["id"],
                fixture["teams"]["away"]["id"]
            ])
        
        # Buscar stats em lote
        team_stats = api.get_teams_stats_batch(list(set(team_ids)))
        
        # Processar jogos
        alerts_sent = 0
        games_analyzed = len(fixtures)
        
        # Obter chat ID específico da liga
        chat_id = self._get_chat_id_for_league(league_code)
        
        for fixture in fixtures:
            try:
                home_id = fixture["teams"]["home"]["id"]
                away_id = fixture["teams"]["away"]["id"]
                
                home_stats = team_stats.get(home_id, (None, 0))
                away_stats = team_stats.get(away_id, (None, 0))
                
                if analyzer.meets_highlight_criteria(home_stats, away_stats):
                    match_data = analyzer.prepare_match_data(fixture, home_stats, away_stats)
                    message = formatter.format_highlight_message(match_data)
                    
                    if dry_run:
                        self.log(f"🧪 DRY RUN - {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                    else:
                        if chat_id and telegram.send_message(chat_id, message):
                            alerts_sent += 1
                            
            except Exception as e:
                self.log(f"❌ Erro ao processar jogo: {e}")
                continue
        
        return {"games_analyzed": games_analyzed, "alerts_sent": alerts_sent}

    def _get_chat_id_for_league(self, league_code):
        # Tentar chat específico por liga
        chat_map_json = os.getenv("TELEGRAM_CHAT_MAP")
        if chat_map_json:
            try:
                chat_map = json.loads(chat_map_json)
                return chat_map.get(league_code)
            except:
                pass
        
        # Fallback para chat geral
        return os.getenv("TELEGRAM_CHAT_ID")

    def _send_admin_summary(self, summary, telegram, dry_run):
        admin_chat = os.getenv("ADMIN_TELEGRAM_CHAT_ID")
        if not admin_chat or dry_run:
            return
        
        try:
            message = f"""📊 RELATÓRIO DIÁRIO - Football Alerts

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}
🏆 Ligas: {summary['leagues_processed']}
⚽ Jogos: {summary['total_games']}
🚨 Alertas: {summary['total_alerts']}
🌐 API Requests: {summary['api_requests']}
⏱️ Duração: {summary['duration_seconds']:.1f}s

✅ Sistema funcionando normalmente"""

            telegram.send_message(admin_chat, message)
            
        except Exception as e:
            self.log(f"⚠️ Erro ao enviar resumo: {e}")
