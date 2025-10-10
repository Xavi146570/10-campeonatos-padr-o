import os
import sys
from datetime import datetime

# Adicionar src ao path para imports
sys.path.insert(0, os.path.dirname(__file__))

from config.leagues import get_league_config, get_chat_id_for_league
from providers.api_football import ApiFootballClient
from providers.telegram_sender import TelegramSender
from engine.analyzer import MatchAnalyzer
from engine.formatter import MessageFormatter

def main():
    """Função principal executada por cada Cron Job"""
    # Obter configurações via variáveis de ambiente
    league_code = os.getenv("LEAGUE_CODE")
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    
    if not league_code:
        print("❌ LEAGUE_CODE não definido")
        return
        
    # Carregar configuração da liga
    league_config = get_league_config(league_code)
    if not league_config:
        print(f"❌ Configuração não encontrada para {league_code}")
        return
        
    chat_id = get_chat_id_for_league(league_code)
    if not chat_id:
        print(f"❌ TELEGRAM_CHAT_ID não configurado para {league_code}")
        return
        
    print(f"🚀 Iniciando bot para {league_config['name']}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Inicializar componentes
        api_client = ApiFootballClient()
        telegram = TelegramSender()
        analyzer = MatchAnalyzer(league_config)
        formatter = MessageFormatter()
        
        # Buscar jogos de hoje
        fixtures = api_client.get_fixtures_today(
            league_config["api_id"], 
            league_config["timezone"]
        )
        
        print(f"📊 Encontrados {len(fixtures)} jogos para hoje")
        
        if not fixtures:
            print("ℹ️ Nenhum jogo encontrado")
            return
            
        # Analisar cada jogo
        messages_sent = 0
        
        for fixture in fixtures:
            try:
                home_id = fixture["teams"]["home"]["id"]
                away_id = fixture["teams"]["away"]["id"]
                
                print(f"🔍 Analisando: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                
                # Buscar estatísticas recentes
                home_stats = api_client.get_team_recent_avg_goals(home_id)
                away_stats = api_client.get_team_recent_avg_goals(away_id)
                
                # Verificar critérios
                if analyzer.meets_highlight_criteria(home_stats, away_stats):
                    print("✅ Jogo atende aos critérios!")
                    
                    # Preparar e formatar mensagem
                    match_data = analyzer.prepare_match_data(fixture, home_stats, away_stats)
                    message = formatter.format_highlight_message(match_data)
                    
                    if dry_run:
                        print("🧪 DRY RUN - Mensagem:")
                        print("-" * 50)
                        print(message)
                        print("-" * 50)
                    else:
                        # Enviar mensagem
                        if telegram.send_message(chat_id, message):
                            messages_sent += 1
                else:
                    print("⏭️ Jogo não atende aos critérios")
                    print(f"   Home: {home_stats[0]:.2f} | Away: {away_stats[0]:.2f} | Min: {league_config['criteria']['min_team_avg_goals']:.2f}")
                    
            except Exception as e:
                print(f"❌ Erro ao processar jogo: {e}")
                continue
                
        print(f"✅ Processamento concluído! Mensagens enviadas: {messages_sent}")
        
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
