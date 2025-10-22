"""
Configurações do Bot Santo Graal com Detecção de Valor EV+
Versão OTIMIZADA com 20 ligas e Smart Mode (consumo inteligente de API)
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
    
    # ===== LIGAS MONITORADAS (20 LIGAS GLOBAIS) =====
    # Top 5 Europeias (Prioridade máxima)
    LEAGUES_PRIORITY_HIGH = [
        39,   # Premier League - Inglaterra
        140,  # La Liga - Espanha
        135,  # Serie A - Itália
        78,   # Bundesliga - Alemanha
        61,   # Ligue 1 - França
    ]
    
    # Europa Adicional (Prioridade média)
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
    
    # Américas e Ásia (Prioridade baixa - horários específicos)
    LEAGUES_PRIORITY_LOW = [
        71,   # Brasileirão Série A - Brasil
        262,  # Liga MX - México
        253,  # MLS - EUA/Canadá
        307,  # Saudi Pro League - Arábia Saudita
        98,   # J1 League - Japão
    ]
    
    # Todas as ligas combinadas
    LEAGUES = LEAGUES_PRIORITY_HIGH + LEAGUES_PRIORITY_MEDIUM + LEAGUES_PRIORITY_LOW
    
    LEAGUE_NAMES = {
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
    SEASON = 2024  # Temporada atual
    
    # ===== OTIMIZAÇÃO DE CONSUMO DE API =====
    # Smart Mode: ajusta ligas monitoradas por horário
    ENABLE_SMART_MODE = True  # ✅ Ativar modo inteligente
    
    @classmethod
    def get_active_leagues(cls):
        """
        Retorna ligas ativas baseado no horário atual (horário do servidor)
        Otimiza consumo de API monitorando ligas relevantes por horário
        
        Horários em UTC (Render usa UTC):
        - 03h-09h UTC = 00h-06h BRT: Ásia + Top Europa
        - 09h-15h UTC = 06h-12h BRT: Europa manhã
        - 15h-21h UTC = 12h-18h BRT: Europa tarde (PICO)
        - 21h-03h UTC = 18h-00h BRT: Europa noite + Américas (PICO MÁXIMO)
        """
        if not cls.ENABLE_SMART_MODE:
            return cls.LEAGUES  # Modo normal: todas as ligas
        
        # Usar UTC (horário do servidor Render)
        hour = datetime.utcnow().hour
        
        # 03h-09h UTC (00h-06h BRT): Ásia + Arábia
        if 3 <= hour < 9:
            return cls.LEAGUES_PRIORITY_HIGH[:2] + [98, 307]  # 2 top europa + Japão + Arábia
        
        # 09h-15h UTC (06h-12h BRT): Europa manhã
        elif 9 <= hour < 15:
            return cls.LEAGUES_PRIORITY_HIGH + cls.LEAGUES_PRIORITY_MEDIUM[:5]  # 10 ligas
        
        # 15h-21h UTC (12h-18h BRT): Europa tarde (PICO)
        elif 15 <= hour < 21:
            return cls.LEAGUES_PRIORITY_HIGH + cls.LEAGUES_PRIORITY_MEDIUM  # 15 ligas
        
        # 21h-03h UTC (18h-00h BRT): Europa noite + Américas (PICO MÁXIMO)
        else:  # 21h-03h
            return cls.LEAGUES  # TODAS as 20 ligas
    
    # ===== CRITÉRIOS DE FILTRAGEM =====
    MAX_DRAW_RATE = 15.0      # Máximo 15% de empates 0x0
    MIN_GAMES_PLAYED = 5      # Mínimo de jogos para análise
    
    # ===== CRITÉRIOS EV+ =====
    MIN_EV_PERCENT = 5.0      # EV mínimo de +5%
    MIN_PROBABILITY_OVER_05 = 70.0  # 70% probabilidade mínima Over 0.5
    MIN_PROBABILITY_OVER_15 = 60.0  # 60% probabilidade mínima Over 1.5
    
    # Odds válidas
    MIN_ODDS_RANGE = 1.10
    MAX_ODDS_RANGE = 3.00
    
    # ===== ANÁLISE NO INTERVALO =====
    ANALYZE_HT_0X0 = True
    HT_MARKETS = ['Over 0.5', 'Over 1.5']
    
    # ===== PESOS PROBABILIDADE =====
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
    
    # ===== MULTIPLICADORES HT 0x0 =====
    HT_0X0_MULTIPLIER_OVER_05 = 1.05
    HT_0X0_MULTIPLIER_OVER_15 = 1.15
    
    # ===== NOTIFICAÇÕES =====
    SEND_START = True
    SEND_HT_0X0 = True
    SEND_EV_OPPORTUNITIES = True
    SEND_EV_NEGATIVE = True
    SEND_SUMMARY = True
    SEND_ERRORS = True
    
    # ===== TIMING (OTIMIZADO PARA API BÁSICA GRATUITA) =====
    MINUTES_BEFORE_MATCH = 30
    CHECK_INTERVAL = 300       # 5 minutos (otimizado para plano gratuito)
    HT_CHECK_INTERVAL = 60
    
    # ===== GESTÃO DE BANCA =====
    KELLY_FRACTION = 0.25
    MAX_STAKE_PERCENT = 5.0
    DEFAULT_BANKROLL = 1000.0
    
    # ===== API SETTINGS =====
    API_RATE_LIMIT = 100
    API_TIMEOUT = 10
    BOOKMAKER_ID = 8
    
    # ===== DATABASE =====
    DB_PATH = 'santo_graal_ev.db'
    
    # ===== LOGGING =====
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls):
        """Valida credenciais"""
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
        """Retorna nome da liga pelo ID"""
        return cls.LEAGUE_NAMES.get(league_id, f"Liga {league_id}")
    
    @classmethod
    def get_current_mode_info(cls):
        """Retorna informações do modo atual"""
        active_leagues = cls.get_active_leagues()
        hour = datetime.utcnow().hour
        
        if 3 <= hour < 9:
            mode = "🌙 Noturno (Ásia/Arábia)"
        elif 9 <= hour < 15:
            mode = "🌅 Manhã (Europa)"
        elif 15 <= hour < 21:
            mode = "☀️ Tarde (Europa PICO)"
        else:
            mode = "🌆 Noite (Global PICO MÁXIMO)"
        
        return {
            'mode': mode,
            'active_leagues': len(active_leagues),
            'total_leagues': len(cls.LEAGUES),
            'leagues': active_leagues
        }
