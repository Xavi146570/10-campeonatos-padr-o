"""
Configurações do Bot Santo Graal com Detecção de Valor EV+
Versão aprimorada com cálculo de Expected Value para Over 0.5 e Over 1.5
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===== API CREDENTIALS =====
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ===== LIGAS MONITORADAS (Santo Graal Original) =====
LEAGUES = {
    39: 'Premier League',      # Inglaterra
    140: 'La Liga',            # Espanha
    135: 'Serie A',            # Itália
    78: 'Bundesliga',          # Alemanha
    61: 'Ligue 1',             # França
}

# ===== CRITÉRIOS DE FILTRAGEM (Santo Graal Original) =====
# Times com baixa taxa de empate 0x0
MAX_DRAW_0X0_RATE = 0.15  # Máximo 15% de empates 0x0
MIN_GAMES_PLAYED = 5      # Mínimo de jogos para análise

# ===== CRITÉRIOS OVER 0.5 (Santo Graal Original) =====
MIN_ODDS_OVER_0_5 = 1.15  # Odds mínimas para Over 0.5

# ===== CRITÉRIOS EV+ (NOVA FUNCIONALIDADE) =====
# Expected Value positivo para detecção de oportunidades
MIN_EV_PERCENTAGE = 5.0   # EV mínimo de +5% para considerar oportunidade
MIN_PROBABILITY_OVER_0_5 = 0.70  # 70% probabilidade mínima Over 0.5
MIN_PROBABILITY_OVER_1_5 = 0.60  # 60% probabilidade mínima Over 1.5

# Odds válidas para análise
MIN_ODDS_RANGE = 1.10
MAX_ODDS_RANGE = 3.00

# ===== CONFIGURAÇÕES DE ANÁLISE NO INTERVALO =====
# Quando detectar HT 0-0, calcular EV+ para:
ANALYZE_HT_0_0 = True
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
HT_0_0_MULTIPLIERS = {
    'over_0_5': 1.05,  # Ligeiro aumento (times precisam reagir)
    'over_1_5': 1.15,  # Aumento maior (2º tempo mais aberto)
}

# ===== CONFIGURAÇÕES DE NOTIFICAÇÃO =====
NOTIFICATION_SETTINGS = {
    'send_start': True,        # Notificar início de análise
    'send_ht_0_0': True,       # Notificar quando detectar HT 0-0
    'send_ev_opportunities': True,  # Notificar oportunidades EV+
    'send_ev_negative': True,  # ✅ NOVO: Notificar também quando EV- (educativo)
    'send_summary': True,      # Enviar resumo diário
    'send_errors': True,       # Notificar erros críticos
}

# ===== TIMING =====
MINUTES_BEFORE_MATCH = 30  # Monitorar jogos 30 min antes
CHECK_INTERVAL = 300       # Verificar a cada 5 minutos (300 seg)
HT_CHECK_INTERVAL = 120    # Verificar HT a cada 2 minutos

# ===== GESTÃO DE BANCA (Kelly Criterion) =====
KELLY_FRACTION = 0.25      # Usar 25% do Kelly completo (gestão conservadora)
MAX_STAKE_PERCENTAGE = 5.0  # Máximo 5% da banca por aposta

# ===== API SETTINGS =====
API_RATE_LIMIT = 100       # Limite diário de requests (ajustar conforme plano)
API_TIMEOUT = 10           # Timeout de 10 segundos

# ===== DATABASE =====
DB_PATH = 'santo_graal_ev.db'

# ===== LOGGING =====
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
