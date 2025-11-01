"""
Configuração do Santo Graal Bot - Modo Best Available
Sistema detecta jogos 0-0 (HT/1H/2H) e notifica TOP 2 melhores oportunidades
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ========================
# TOKENS E CREDENCIAIS
# ========================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')

# ========================
# CONFIGURAÇÃO DE LIGAS - SMART MODE
# ========================
# 24 ligas totais com horários de pico otimizados

LEAGUES = {
    # TIER 1 - TOP EUROPEU (Always Active)
    'Premier League': 39,
    'La Liga': 140,
    'Champions League': 2,  # UEFA Champions League
    
    # TIER 2 - EUROPA PRINCIPAL (15h-03h UTC)
    'Bundesliga': 78,
    'Serie A': 135,
    'Ligue 1': 61,
    'Eredivisie': 88,
    'Liga Portugal': 94,
    'Championship': 40,
    
    # TIER 3 - EUROPA SECUNDÁRIA (15h-03h UTC)
    'Serie B': 136,
    'La Liga 2': 141,
    'Bundesliga 2': 79,
    'Ligue 2': 62,
    'Scottish Premiership': 179,
    
    # TIER 4 - GLOBAL (21h-03h UTC - Pico Global)
    'MLS': 253,
    'Liga MX': 262,
    'Brasileirão': 71,
    'Argentino': 128,
    
    # TIER 5 - ÁSIA/OCEANIA (03h-09h UTC - Madrugada Europa)
    'J-League': 98,
    'K-League': 292,
    'A-League': 188,
    'Chinese Super League': 169,
    'Saudi Pro League': 307,
    'Indian Super League': 323
}

# ========================
# SMART MODE - OTIMIZAÇÃO POR HORÁRIO
# ========================
SMART_MODE_CONFIG = {
    'night': {  # 03h-09h UTC (Madrugada Europa)
        'hours': (3, 9),
        'active_leagues': [
            'J-League', 'K-League', 'A-League', 'Chinese Super League',
            'Premier League', 'La Liga'  # Top 2 Europa sempre
        ],
        'check_interval': 180  # 3 minutos
    },
    'morning': {  # 09h-15h UTC (Manhã Europa)
        'hours': (9, 15),
        'active_leagues': [
            'Premier League', 'La Liga', 'Bundesliga', 'Serie A',
            'Ligue 1', 'Eredivisie', 'Liga Portugal', 'Championship',
            'Scottish Premiership', 'Champions League'
        ],
        'check_interval': 180
    },
    'afternoon': {  # 15h-21h UTC (Tarde Europa - PICO)
        'hours': (15, 21),
        'active_leagues': [
            'Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1',
            'Eredivisie', 'Liga Portugal', 'Championship', 'Serie B', 'La Liga 2',
            'Bundesliga 2', 'Ligue 2', 'Scottish Premiership', 'Champions League',
            'MLS'
        ],
        'check_interval': 120  # 2 minutos - mais frequente no pico
    },
    'evening': {  # 21h-03h UTC (Noite Europa + Américas - PICO GLOBAL)
        'hours': (21, 24),  # 21h-00h
        'active_leagues': list(LEAGUES.keys()),  # TODAS as 24 ligas
        'check_interval': 120
    },
    'late_night': {  # 00h-03h UTC (continuação do pico)
        'hours': (0, 3),
        'active_leagues': list(LEAGUES.keys()),
        'check_interval': 120
    }
}

# ========================
# MODO BEST AVAILABLE
# ========================
ENABLE_BEST_AVAILABLE_MODE = True  # ✅ Sempre notificar TOP jogos disponíveis
BEST_AVAILABLE_COUNT = 2  # TOP 2 jogos (mesmo se EV negativo)
MIN_EV_THRESHOLD = 0.05  # 5% - usado apenas para destacar EV+ reais

# ========================
# EXPECTED VALUE (EV)
# ========================
MIN_EV_POSITIVE = 0.05  # +5% mínimo para EV+ perfeito
SHOW_EV_NEGATIVE = True  # Mostrar também EV- (educativo)

# ========================
# MULTIPLICADORES POR STATUS
# ========================
# Intervalo (HT) - Ambas equipes descansadas, 45 min restantes
HALFTIME_0X0_MULTIPLIER_OVER_05 = 1.05  # +5% probabilidade Over 0.5
HALFTIME_0X0_MULTIPLIER_OVER_15 = 1.15  # +15% probabilidade Over 1.5

# 2º Tempo (2H) - Tempo correndo, mais conservador
SECOND_HALF_0X0_MULTIPLIER_OVER_05 = 1.10  # +10% Over 0.5 (urgência)
SECOND_HALF_0X0_MULTIPLIER_OVER_15 = 1.20  # +20% Over 1.5 (desespero)

# ========================
# KELLY CRITERION
# ========================
KELLY_FRACTION = 0.25  # 25% conservador (1/4 Kelly)

# ========================
# TELEGRAM
# ========================
TELEGRAM_PARSE_MODE = 'MarkdownV2'

# ========================
# API FOOTBALL
# ========================
API_FOOTBALL_BASE_URL = 'https://v3.football.api-sports.io'
API_REQUEST_TIMEOUT = 10  # segundos

# ========================
# BOT TIMING
# ========================
CHECK_INTERVAL = 180  # 3 minutos (padrão - Smart Mode ajusta)
SEASON = 2024

# ========================
# LOGGING
# ========================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ========================
# HTTP SERVER (RENDER)
# ========================
HTTP_PORT = 10000  # Porta para manter web service ativo no Render

# ========================
# VALIDAÇÃO
# ========================
def validate_config():
    """Valida se todas as variáveis de ambiente necessárias estão configuradas."""
    missing = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing.append('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_CHAT_ID:
        missing.append('TELEGRAM_CHAT_ID')
    if not API_FOOTBALL_KEY:
        missing.append('API_FOOTBALL_KEY')
    
    if missing:
        raise ValueError(f"❌ Variáveis de ambiente faltando: {', '.join(missing)}")
    
    print("✅ Configuração validada com sucesso!")
    print(f"🎯 Modo Best Available: {'ATIVO' if ENABLE_BEST_AVAILABLE_MODE else 'DESATIVADO'}")
    print(f"📊 Notificando TOP {BEST_AVAILABLE_COUNT} jogos por ciclo")
    print(f"🏆 {len(LEAGUES)} ligas configuradas (Smart Mode)")
    print(f"⏱️ Check interval base: {CHECK_INTERVAL}s (ajustado por horário)")

if __name__ == "__main__":
    validate_config()

# Configurações adicionais para versão super poderosa

# Odds API (The Odds API recomendado)
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "YOUR_ODDS_API_KEY")

# Risk Management
INITIAL_BANKROLL = float(os.getenv("INITIAL_BANKROLL", "1000.0"))
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "60.0"))

# Margem simulada quando sem odds reais
BOOKMAKER_MARGIN_SIMULATED = float(os.getenv("BOOKMAKER_MARGIN", "0.05"))  # 5%

# Performance
MIN_EV_POSITIVE = float(os.getenv("MIN_EV_POSITIVE", "2.0"))  # 2% mínimo

def validate_config():
    """Validação melhorada das configurações."""
    issues = []
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "SEU_TOKEN_TELEGRAM_AQUI":
        issues.append("⚠️ TELEGRAM_BOT_TOKEN não configurado")
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "SEU_CHAT_ID_AQUI":
        issues.append("⚠️ TELEGRAM_CHAT_ID não configurado")
    
    if not API_FOOTBALL_KEY or API_FOOTBALL_KEY == "SUA_CHAVE_API_AQUI":
        issues.append("⚠️ API_FOOTBALL_KEY não configurada")
    
    if not ODDS_API_KEY or ODDS_API_KEY == "YOUR_ODDS_API_KEY":
        issues.append("⚠️ ODDS_API_KEY não configurada (usará odds simuladas)")
    
    if issues:
        for issue in issues:
            print(issue)
        
        if len(issues) >= 3:  # Muitos problemas críticos
            print("❌ Muitas configurações em falta. Bot pode não funcionar corretamente.")
    else:
        print("✅ Todas as configurações validadas com sucesso!")
