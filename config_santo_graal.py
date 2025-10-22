"""
Configurações do Bot Santo Graal com Detecção de Valor EV+
Versão aprimorada com cálculo de Expected Value para Over 0.5 e Over 1.5
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Classe de configuração centralizada do Santo Graal Bot EV+"""
    
    # ===== API CREDENTIALS =====
    API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # ===== LIGAS MONITORADAS (Santo Graal Original) =====
    LEAGUES = [
        39,   # Premier League - Inglaterra
        140,  # La Liga - Espanha
        135,  # Serie A - Itália
        78,   # Bundesliga - Alemanha
        61,   # Ligue 1 - França
    ]
    
    LEAGUE_NAMES = {
        39: 'Premier League',
        140: 'La Liga',
        135: 'Serie A',
        78: 'Bundesliga',
        61: 'Ligue 1',
    }
    
    # ===== TEMPORADA =====
    SEASON = 2024  # Temporada atual
    
    # ===== CRITÉRIOS DE FILTRAGEM (Santo Graal Original) =====
    # Times com baixa taxa de empate 0x0
    MAX_DRAW_RATE = 15.0      # Máximo 15% de empates 0x0
    MIN_GAMES_PLAYED = 5      # Mínimo de jogos para análise
    
    # ===== CRITÉRIOS EV+ (NOVA FUNCIONALIDADE) =====
    # Expected Value positivo para detecção de oportunidades
    MIN_EV_PERCENT = 5.0      # EV mínimo de +5% para considerar oportunidade
    MIN_PROBABILITY_OVER_05 = 70.0  # 70% probabilidade mínima Over 0.5
    MIN_PROBABILITY_OVER_15 = 60.0  # 60% probabilidade mínima Over 1.5
    
    # Odds válidas para análise
    MIN_ODDS_RANGE = 1.10
    MAX_ODDS_RANGE = 3.00
    
    # ===== CONFIGURAÇÕES DE ANÁLISE NO INTERVALO =====
    # Quando detectar HT 0-0, calcular EV+ para:
    ANALYZE_HT_0X0 = True
    HT_MARKETS = ['Over 0.5', 'Over 1.5']  # Mercados a analisar no HT
    
    # ===== PESOS PARA CÁLCULO DE PROBABILIDADE =====
    # Sistema de 9 indicadores adaptado para detecção no intervalo
    PROBABILITY_WEIGHTS = {
        # Indicadores Primários (50%)
        'poisson': 0.25,           # Distribuição de Poisson
        'historical_rate': 0.15,   # Taxa histórica Over
        'recent_trend': 0.10,      # Tendência últimos 5 jogos
        
        # Indicadores Secundários (30%)
        'h2h': 0.12,              # Head-to-Head
        'offensive_strength': 0.10, # Força ofensiva
        'offensive_trend': 0.08,   # Tendência ofensiva
        
        # Indicadores Contextuais (20%)
        'season_phase': 0.08,      # Fase da temporada
        'motivation': 0.07,        # Motivação dos times
        'match_importance': 0.05,  # Importância do jogo
    }
    
    # ===== AJUSTES PARA ANÁLISE NO INTERVALO =====
    # Multiplicadores de probabilidade quando jogo está 0-0 no HT
    HT_0X0_MULTIPLIER_OVER_05 = 1.05  # Ligeiro aumento (times precisam reagir)
    HT_0X0_MULTIPLIER_OVER_15 = 1.15  # Aumento maior (2º tempo mais aberto)
    
    # ===== CONFIGURAÇÕES DE NOTIFICAÇÃO =====
    SEND_START = True              # Notificar início de análise
    SEND_HT_0X0 = True             # Notificar quando detectar HT 0-0
    SEND_EV_OPPORTUNITIES = True   # Notificar oportunidades EV+
    SEND_EV_NEGATIVE = True        # ✅ NOVO: Notificar também quando EV- (educativo)
    SEND_SUMMARY = True            # Enviar resumo diário
    SEND_ERRORS = True             # Notificar erros críticos
    
    # ===== TIMING =====
    MINUTES_BEFORE_MATCH = 30  # Monitorar jogos 30 min antes
    CHECK_INTERVAL = 120       # Verificar a cada 2 minutos (120 seg)
    HT_CHECK_INTERVAL = 60     # Verificar HT a cada 1 minuto
    
    # ===== GESTÃO DE BANCA (Kelly Criterion) =====
    KELLY_FRACTION = 0.25          # Usar 25% do Kelly completo (gestão conservadora)
    MAX_STAKE_PERCENT = 5.0        # Máximo 5% da banca por aposta
    DEFAULT_BANKROLL = 1000.0      # Banca padrão para cálculos (ajustar conforme necessário)
    
    # ===== API SETTINGS =====
    API_RATE_LIMIT = 100       # Limite diário de requests (ajustar conforme plano)
    API_TIMEOUT = 10           # Timeout de 10 segundos
    BOOKMAKER_ID = 8           # Bet365 (padrão para odds)
    
    # ===== DATABASE =====
    DB_PATH = 'santo_graal_ev.db'
    
    # ===== LOGGING =====
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls):
        """Valida se todas as credenciais necessárias estão configuradas"""
        errors = []
        
        if not cls.API_FOOTBALL_KEY:
            errors.append("API_FOOTBALL_KEY não configurada")
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN não configurado")
        
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID não configurado")
        
        if errors:
            raise ValueError(f"Configurações inválidas: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_league_name(cls, league_id: int) -> str:
        """Retorna o nome da liga pelo ID"""
        return cls.LEAGUE_NAMES.get(league_id, f"Liga {league_id}")


# Validar configurações ao importar (opcional - comentar se quiser validar manualmente)
# Config.validate()
