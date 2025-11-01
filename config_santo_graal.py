import os
import sys
from datetime import datetime

# ========================
# CONFIGURAÇÕES BASE
# ========================
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "SUA_CHAVE_API_AQUI")
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "15"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "SEU_TOKEN_TELEGRAM_AQUI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "SEU_CHAT_ID_AQUI")

# ========================
# CONFIGURAÇÕES DO BOT
# ========================
HTTP_PORT = int(os.getenv("PORT", "10000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Multiplicadores para situações 0-0
HALFTIME_0X0_MULTIPLIER_OVER_05 = float(os.getenv("HT_MULT_05", "1.4"))
HALFTIME_0X0_MULTIPLIER_OVER_15 = float(os.getenv("HT_MULT_15", "1.3"))
SECOND_HALF_0X0_MULTIPLIER_OVER_05 = float(os.getenv("2H_MULT_05", "1.2"))
SECOND_HALF_0X0_MULTIPLIER_OVER_15 = float(os.getenv("2H_MULT_15", "1.1"))

# Filtros
MIN_EV_POSITIVE = float(os.getenv("MIN_EV_POSITIVE", "2.0"))
# Kelly Criterion e configurações EV (ADICIONADAS)
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.25"))  # 25% máximo do Kelly
KELLY_MULTIPLIER = float(os.getenv("KELLY_MULTIPLIER", "0.5"))  # Conservador 50%
MIN_KELLY_STAKE = float(os.getenv("MIN_KELLY_STAKE", "10.0"))
MAX_KELLY_STAKE = float(os.getenv("MAX_KELLY_STAKE", "100.0"))
DEFAULT_BANKROLL = float(os.getenv("DEFAULT_BANKROLL", "1000.0"))
GOALS_THRESHOLD = float(os.getenv("GOALS_THRESHOLD", "2.5"))

ENABLE_BEST_AVAILABLE_MODE = True
BEST_AVAILABLE_COUNT = int(os.getenv("BEST_AVAILABLE_COUNT", "2"))

# ========================
# LIGAS MONITORADAS
# ========================
LEAGUES = {
    # Principais Europeias
    'Premier League': 39,
    'La Liga': 140,
    'Serie A': 135,
    'Bundesliga': 78,
    'Ligue 1': 61,
    'Eredivisie': 88,
    'Primeira Liga': 94,
    
    # Segundas Divisões
    'Championship': 40,
    'La Liga 2': 141,
    'Serie B': 136,
    '2. Bundesliga': 79,
    'Ligue 2': 62,
    'Eerste Divisie': 89,
    
    # Outras Ligas Produtivas
    'Eliteserien': 103,
    'Allsvenskan': 113,
    'Superliga': 119,
    'Super Liga': 203,
    'Liga MX': 262,
    'Brasileirão': 71,
    'Argentina Primera': 128,
    'Jupiler Pro League': 144
}

# ========================
# SMART MODE
# ========================
SMART_MODE_CONFIG = {
    'morning': {
        'hours': (6, 15),
        'active_leagues': [
            'Liga MX', 'Brasileirão', 'Argentina Primera',
            'Eliteserien', 'Allsvenskan', 'Superliga'
        ],
        'check_interval': 180
    },
    'afternoon': {
        'hours': (15, 21),
        'active_leagues': [
            'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
            'Championship', 'La Liga 2', 'Serie B', '2. Bundesliga',
            'Eredivisie', 'Primeira Liga', 'Jupiler Pro League',
            'Super Liga'
        ],
        'check_interval': 120
    },
    'night': {
        'hours': (21, 6),
        'active_leagues': [
            'Liga MX', 'Brasileirão', 'Argentina Primera',
            'Premier League', 'Championship'
        ],
        'check_interval': 150
    }
}

# ========================
# VALIDAÇÃO
# ========================
def validate_config():
    """Validação das configurações."""
    issues = []
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "SEU_TOKEN_TELEGRAM_AQUI":
        issues.append("❌ TELEGRAM_BOT_TOKEN não configurado")
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "SEU_CHAT_ID_AQUI":
        issues.append("❌ TELEGRAM_CHAT_ID não configurado")
    
    if not API_FOOTBALL_KEY or API_FOOTBALL_KEY == "SUA_CHAVE_API_AQUI":
        issues.append("❌ API_FOOTBALL_KEY não configurada")
    
    if issues:
        for issue in issues:
            print(issue)
        
        critical = [i for i in issues if "❌" in i]
        if len(critical) >= 3:
            print("🚨 Muitas configurações críticas em falta!")
            sys.exit(1)
    else:
        print("✅ Configurações validadas!")
    
    print(f"🏆 {len(LEAGUES)} ligas configuradas")
    print(f"📊 EV mínimo: {MIN_EV_POSITIVE}%")
