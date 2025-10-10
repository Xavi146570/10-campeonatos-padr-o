import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from config.leagues import get_league_config, get_chat_id_for_league
from providers.api_football import ApiFootballClient
from providers.telegram_sender import TelegramSender
from engine.analyzer import MatchAnalyzer
from engine.formatter import MessageFormatter

def main():
    """Função principal otimizada para conta paga"""
    league_code = os.getenv("LEAGUE_CODE")
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    
    if not league_code:
        print("❌ LEAGUE_CODE não definido")
        return
    
    league_config = get_league_config(league_code)
    if not league_config:
        print(f"❌ Configuração não encontrada para {league_code}")
        return
    
    chat_id = get_chat_id_for_league(league_code)
    if not chat_id:
        print(f"❌ TELEGRAM_CHAT_ID não configurado")
        return
    
    print(f"🚀 Bot PREMIUM iniciado - {league_config['name']}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🧪 Modo: {'DRY RUN' if dry_run else 'PRODUÇÃO'}")
    
    try:
        # Inicializar componentes
        api = ApiFootballClient()
        telegram = TelegramSender()
        analyzer = MatchAnalyzer(league_config)
        formatter = MessageFormatter()
        
        # Buscar jogos de hoje
        fixtures = api.get_fixtures_today(
            league_config["api_id"], 
            league_config["timezone"]
        )
        
        if not fixtures:
            print("ℹ️ Nenhum jogo encontrado para hoje")
            print_execution_summary(api, 0, 0)
            return
        
        # Coletar IDs únicos de times
        team_ids = []
        for fixture in fixtures:
            team_ids.extend([
                fixture["teams"]["home"]["id"],
                fixture["teams"]["away"]["id"]
            ])
        
        print(f"🔍 Processando {len(fixtures)} jogos com {len(set(team_ids))} times únicos")
        
        # Buscar stats em lote (otimizado)
        team_stats = api.get_teams_stats_batch(list(set(team_ids)))
        
        # Processar cada jogo
        messages_sent = 0
        games_analyzed = 0
        
        for fixture in fixtures:
            try:
                home_id = fixture["teams"]["home"]["id"]
                away_id = fixture["teams"]["away"]["id"]
                home_name = fixture["teams"]["home"]["name"]
                away_name = fixture["teams"]["away"]["name"]
                
                games_analyzed += 1
                
                # Stats dos times (já em cache/lote)
                home_stats = team_stats.get(home_id, (None, 0))
                away_stats = team_stats.get(away_id, (None, 0))
                
                if analyzer.meets_highlight_criteria(home_stats, away_stats):
                    print(f"✅ DESTAQUE: {home_name} vs {away_name}")
                    
                    match_data = analyzer.prepare_match_data(fixture, home_stats, away_stats)
                    message = formatter.format_highlight_message(match_data)
                    
                    if dry_run:
                        print("🧪 DRY RUN - Mensagem formatada:")
                        print("-" * 60)
                        print(message)
                        print("-" * 60)
                    else:
                        if telegram.send_message(chat_id, message):
                            messages_sent += 1
                            print(f"📨 Mensagem enviada para {league_config['name']}")
                else:
                    home_avg = home_stats[0] or 0
                    away_avg = away_stats[0] or 0
                    min_req = league_config['criteria']['min_team_avg_goals']
                    print(f"⏭️ {home_name} vs {away_name} - H:{home_avg:.2f} A:{away_avg:.2f} (min:{min_req:.2f})")
                    
            except Exception as e:
                print(f"❌ Erro ao processar {home_name} vs {away_name}: {e}")
                continue
        
        # Relatório final
        print_execution_summary(api, games_analyzed, messages_sent)
        
        # Alerta se consumo alto
        if api.request_count > (api.max_requests_per_run * 0.8):
            print("⚠️ ALERTA: Consumo alto de API detectado!")
        
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        sys.exit(1)

def print_execution_summary(api, games_analyzed, messages_sent):
    """Imprime resumo detalhado da execução"""
    stats = api.get_execution_stats()
    
    print(f"\n📊 RELATÓRIO DE EXECUÇÃO:")
    print(f"   🎯 Jogos analisados: {games_analyzed}")
    print(f"   📨 Alertas enviados: {messages_sent}")
    print(f"   🌐 Requests utilizados: {stats['requests_used']}/{stats['max_allowed']}")
    print(f"   📦 Entradas em cache: {stats['cache_entries']}")
    print(f"   ⚡ Eficiência: {stats['efficiency']} de quota poupada")
    print(f"   ✅ Execução concluída com sucesso!")

if __name__ == "__main__":
    main()
Agendamento Escalonado Otimizado
render.yaml (Horários Inteligentes)
Copyservices: []

cronJobs:
  # BLOCO EUROPEU MATINAL (07:00-08:45 UTC)
  - name: football-alerts-eng1
    runtime: python
    schedule: "0 7 * * *"    # 07:00 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: ENG1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-esp1
    runtime: python
    schedule: "15 7 * * *"   # 07:15 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: ESP1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-ita1
    runtime: python
    schedule: "30 7 * * *"   # 07:30 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: ITA1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-ger1
    runtime: python
    schedule: "45 7 * * *"   # 07:45 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: GER1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-fra1
    runtime: python
    schedule: "0 8 * * *"    # 08:00 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: FRA1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-por1
    runtime: python
    schedule: "15 8 * * *"   # 08:15 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: POR1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-bel1
    runtime: python
    schedule: "30 8 * * *"   # 08:30 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: BEL1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-tur1
    runtime: python
    schedule: "45 8 * * *"   # 08:45 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: TUR1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  # BLOCO AMERICANO (11:00-11:15 UTC) - Evita conflito com pico europeu
  - name: football-alerts-bra1
    runtime: python
    schedule: "0 11 * * *"   # 11:00 UTC (08:00 Brasília)
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: BRA1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false

  - name: football-alerts-arg1
    runtime: python
    schedule: "15 11 * * *"  # 11:15 UTC
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/main.py"
    envVars:
      - key: LEAGUE_CODE
        value: ARG1
      - key: MAX_API_REQUESTS
        value: "20"
      - key: API_REQUEST_DELAY
        value: "0.8"
      - key: TELEGRAM_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
      - key: API_FOOTBALL_KEY
        sync: false
