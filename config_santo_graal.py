"""
Configurações do Bot Santo Graal com Detecção de Valor EV+
Versão CORRIGIDA com UEFA Champions League + 23 ligas totais
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Classe de configuração centralizada do Santo Graal Bot EV+"""
    
    # ===== API CREDENTIALS =====
    API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # ===== COMPETIÇÕES INTERNACIONAIS (PRIORIDADE MÁXIMA!) =====
    LEAGUES_INTERNATIONAL = [
        2,    # UEFA Champions League ⚽ ESSENCIAL!
        3,    # UEFA Europa League
        848,  # UEFA Conference League
        13,   # Copa Libertadores (América do Sul)
    ]
    
    # ===== LIGAS NACIONAIS - TOP 5 EUROPA =====
    LEAGUES_PRIORITY_HIGH = [
        39,   # Premier League - Inglaterra
        140,  # La Liga - Espanha
        135,  # Serie A - Itália
        78,   # Bundesliga - Alemanha
        61,   # Ligue 1 - França
    ]
    
    # ===== EUROPA ADICIONAL =====
    LEAGUES_PRIORITY_MEDIUM = [
        88,   # Eredivisie - Holanda
        40,   # Championship - Inglaterra 2ª divisão
        94,   # Primeira Liga - Portugal
        144,  # Jupiler Pro League - Bélgica
        203,  # Super Lig - Turquia
        179,  # Scottish Premiership - Escócia
        218,  # Austrian Bundesliga - Áustria
        207,  # Swiss Super League - Suíça
        235,  # Russian Premier League - Rússia
        197,  # Greek Super League - Grécia
    ]
    
    # ===== AMÉRICAS E ÁSIA =====
    LEAGUES_PRIORITY_LOW = [
        71,   # Brasileirão Série A - Brasil
        262,  # Liga MX - México
        253,  # MLS - EUA/Canadá
        307,  # Saudi Pro League - Arábia Saudita
        98,   # J1 League - Japão
    ]
    
    # ===== TODAS AS LIGAS COMBINADAS (24 TOTAL) =====
    LEAGUES = (
        LEAGUES_INTERNATIONAL +  # 4 competições internacionais
        LEAGUES_PRIORITY_HIGH +  # 5 ligas top
        LEAGUES_PRIORITY_MEDIUM + # 10 ligas europa
        LEAGUES_PRIORITY_LOW     # 5 américas/ásia
    )
    
    LEAGUE_NAMES = {
        # Competições Internacionais
        2: 'UEFA Champions League ⚽🏆',
        3: 'UEFA Europa League 🏆',
        848: 'UEFA Conference League 🏆',
        13: 'Copa Libertadores 🏆',
        
        # Top 5 Europa
        39: 'Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        140: 'La Liga 🇪🇸',
        135: 'Serie A 🇮🇹',
        78: 'Bundesliga 🇩🇪',
        61: 'Ligue 1 🇫🇷',
        
        # Europa Adicional
        88: 'Eredivisie 🇳🇱',
        40: 'Championship 🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        94: 'Primeira Liga 🇵🇹',
        144: 'Jupiler Pro League 🇧🇪',
        203: 'Super Lig 🇹🇷',
        179: 'Scottish Premiership 🏴󠁧󠁢󠁳󠁣󠁴󠁿',
        218: 'Austrian Bundesliga 🇦🇹',
        207: 'Swiss Super League 🇨🇭',
        235: 'Russian Premier League 🇷🇺',
        197: 'Greek Super League 🇬🇷',
        
        # Américas
        71: 'Brasileirão Série A 🇧🇷',
        262: 'Liga MX 🇲🇽',
        253: 'MLS 🇺🇸',
        
        # Ásia/Outros
        307: 'Saudi Pro League 🇸🇦',
        98: 'J1 League 🇯🇵',
    }
    
    # ===== TEMPORADA =====
    SEASON = 2024
    
    # ===== SMART MODE =====
    ENABLE_SMART_MODE = True
    
    @classmethod
    def get_active_leagues(cls):
        """
        Retorna ligas ativas por horário UTC
        COMPETIÇÕES INTERNACIONAIS SEMPRE ATIVAS! (Champions, Europa League, etc.)
        """
        if not cls.ENABLE_SMART_MODE:
            return cls.LEAGUES
        
        hour = datetime.utcnow().hour
        
        # SEMPRE incluir competições internacionais (Champions League, etc.)
        base_leagues = cls.LEAGUES_INTERNATIONAL.copy()
        
        # 03h-09h UTC: Ásia + Top 2 Europa
        if 3 <= hour < 9:
            return base_leagues + cls.LEAGUES_PRIORITY_HIGH[:2] + [98, 307]
        
        # 09h-15h UTC: Europa manhã
        elif 9 <= hour < 15:
            return base_leagues + cls.LEAGUES_PRIORITY_HIGH + cls.LEAGUES_PRIORITY_MEDIUM[:5]
        
        # 15h-21h UTC: Europa tarde (PICO)
        elif 15 <= hour < 21:
            return base_leagues + cls.LEAGUES_PRIORITY_HIGH + cls.LEAGUES_PRIORITY_MEDIUM
        
        # 21h-03h UTC: Global (PICO MÁXIMO)
        else:
            return cls.LEAGUES  # TODAS as ligas
    
    # ===== OUTROS PARAMETROS =====
    MAX_DRAW_RATE = 15.0
    MIN_GAMES_PLAYED = 5
    MIN_EV_PERCENT = 5.0
    MIN_PROBABILITY_OVER_05 = 70.0
    MIN_PROBABILITY_OVER_15 = 60.0
    MIN_ODDS_RANGE = 1.10
    MAX_ODDS_RANGE = 3.00
    ANALYZE_HT_0X0 = True
    HT_MARKETS = ['Over 0.5', 'Over 1.5']
    
    PROBABILITY_WEIGHTS = {
        'poisson': 0.25,
        'historical_rate': 0.15,
        'recent_trend': 0.10,
        'h2h': 0.12,
        'offensive_strength': 0.10,
        'offensive_trend': 0.08,
        'season_phase': 0.08,
        'motivation': 0.07,
        'match_importance': 0.05,
    }
    
    HT_0X0_MULTIPLIER_OVER_05 = 1.05
    HT_0X0_MULTIPLIER_OVER_15 = 1.15
    
    SEND_START = True
    SEND_HT_0X0 = True
    SEND_EV_OPPORTUNITIES = True
    SEND_EV_NEGATIVE = True
    SEND_SUMMARY = True
    SEND_ERRORS = True
    
    MINUTES_BEFORE_MATCH = 30
    CHECK_INTERVAL = 300  # 5 minutos
    HT_CHECK_INTERVAL = 60
    
    KELLY_FRACTION = 0.25
    MAX_STAKE_PERCENT = 5.0
    DEFAULT_BANKROLL = 1000.0
    
    API_RATE_LIMIT = 100
    API_TIMEOUT = 10
    BOOKMAKER_ID = 8
    DB_PATH = 'santo_graal_ev.db'
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls):
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
        return cls.LEAGUE_NAMES.get(league_id, f"Liga {league_id}")
    
    @classmethod
    def get_current_mode_info(cls):
        active_leagues = cls.get_active_leagues()
        hour = datetime.utcnow().hour
        
        if 3 <= hour < 9:
            mode = "🌙 Noturno Ásia"
        elif 9 <= hour < 15:
            mode = "🌅 Manhã Europa"
        elif 15 <= hour < 21:
            mode = "☀️ Tarde Europa PICO"
        else:
            mode = "🌆 Noite Global PICO"
        
        return {
            'mode': mode,
            'active_leagues': len(active_leagues),
            'total_leagues': len(cls.LEAGUES),
            'leagues': active_leagues
        }
