GUIA_RAPIDO.md
Descrição: Guia rápido para começar em 5 minutos
Localização: Pasta raiz do projeto

Copy# ⚡ Santo Graal EV+ - Guia Rápido

## 🚀 Começar em 5 Minutos

### 1️⃣ Instalar Dependências
```bash
pip install -r requirements.txt
2️⃣ Configurar Credenciais
Copy# Copiar template
cp .env.example .env

# Editar com suas credenciais
nano .env
Preencher:

API_FOOTBALL_KEY=sua_chave_api_football
TELEGRAM_BOT_TOKEN=seu_token_bot
TELEGRAM_CHAT_ID=seu_chat_id
3️⃣ Testar Sistema
Copypython test_santo_graal_ev.py
Resultado esperado:

✅ Calculador de Probabilidades: PASSOU
✅ Detector de EV: PASSOU
✅ Kelly Criterion: PASSOU
✅ Casos Extremos: PASSOU

🎉 TODOS OS TESTES PASSARAM COM SUCESSO!
4️⃣ Executar Bot
Copypython santo_graal_bot_ev.py
📱 Obter Credenciais
API-Football
Acessar: https://www.api-football.com/
Criar conta gratuita ou paga
Copiar chave da API
Importante: Plano com odds ao vivo recomendado
Telegram Bot
Abrir Telegram e buscar @BotFather
Enviar /newbot
Seguir instruções
Copiar token fornecido
Telegram Chat ID
Buscar @userinfobot no Telegram
Enviar /start
Copiar ID fornecido
🎯 Como Funciona
Fluxo Automático
08:00 → Bot inicia análise diária

↓

Busca jogos próximos (30 min antes)
• Verifica times com baixa taxa 0x0
• Notifica jogos identificados

↓

Monitora jogos ao vivo 0-0
• Verifica placar a cada 2 minutos
• Detecta quando chega ao HT 0-0

↓

ANÁLISE NO HT 0-0:
1. Calcula probabilidades Over 0.5 e Over 1.5
2. Busca odds disponíveis
3. Calcula Expected Value (EV)
4. Se EV ≥ +5%, NOTIFICA!

↓

Notificação Telegram com:
• Probabilidades calculadas
• EV%
• Stake recomendado (Kelly)
• Melhor mercado (Over 0.5 ou 1.5)
📊 Interpretar Notificações
Exemplo de Notificação EV+
🔥 OPORTUNIDADE EV+ DETECTADA NO HT 0-0!

Jogo: Liverpool vs Manchester City
Liga: Premier League
Placar HT: 0-0

📊 ANÁLISE Over 1.5
• Odd: 1.50
• Probabilidade: 72.3%
• EV: +8.45%          ← VALOR ESPERADO POSITIVO
• Confiança: 78%

💰 GESTÃO DE BANCA
• Kelly Completo: 18.6%
• Kelly Conservador: 4.7%
• Stake Recomendado: 3.7%  ← APOSTAR 3.7% DA BANCA

Alternativa - Over 0.5:
Odd 1.20 | EV +3.2% | Stake 2.1%
Decisão
✅ Apostar? Sim, EV de +8.45% indica lucro esperado
💰 Quanto? 3.7% da banca total
🎯 Onde? Over 1.5 (melhor que Over 0.5)

⚙️ Configurações Principais
config_santo_graal.py
Copy# Ajustar conforme sua estratégia:

MIN_EV_PERCENTAGE = 5.0        # Mínimo EV para notificar
MIN_PROBABILITY_OVER_0_5 = 0.70  # 70% prob mínima
MIN_PROBABILITY_OVER_1_5 = 0.60  # 60% prob mínima

KELLY_FRACTION = 0.25          # 25% Kelly (conservador)
MAX_STAKE_PERCENTAGE = 5.0     # Máx 5% por aposta

MAX_DRAW_0X0_RATE = 0.15       # Times com ≤15% empates 0x0

# 🆕 Notificações EV-
'send_ev_negative': True       # Ativar (educativo)
# 'send_ev_negative': False    # Desativar (apenas EV+)
Personalizar Ligas
CopyLEAGUES = {
    39: 'Premier League',
    140: 'La Liga',
    135: 'Serie A',
    78: 'Bundesliga',
    61: 'Ligue 1',
    # Adicionar mais:
    # 94: 'Primeira Liga (Portugal)',
    # 88: 'Eredivisie (Holanda)',
}
🔧 Solução de Problemas
Erro: "API-Football quota exceeded"
Causa: Limite diário atingido
Solução: Aguardar reset ou upgrade de plano

Erro: "Telegram bot unauthorized"
Causa: Token incorreto
Solução: Verificar token no .env

Não recebe notificações
Causa: Chat ID incorreto
Solução: Usar @userinfobot para obter ID correto

Odds não disponíveis
Causa: Plano API não inclui odds ao vivo
Solução: Bot usa odds estimadas (funciona, mas menos preciso)

📈 Melhores Práticas
1. Gestão de Banca
✅ Fazer:

Respeitar stake recomendado
Nunca exceder 5% por aposta
Manter registro de resultados
❌ Evitar:

Aumentar stake após perdas
Apostar mais que recomendado
Ignorar gestão Kelly
2. Seleção de Apostas
✅ Fazer:

Apostar apenas EV ≥ +5%
Preferir alta confiança (>70%)
Seguir recomendação de mercado
❌ Evitar:

Apostar por "sentimento"
Ignorar análise matemática
Apostar em todas notificações
3. Expectativas Realistas
✅ Entender:

ROI esperado: +5% a +10%
Variância é normal
Mínimo 100 apostas para avaliar
Lucro vem no longo prazo
❌ Não esperar:

100% de acerto
Lucro em toda aposta
Resultados imediatos
📊 Monitorar Performance
Registrar Apostas
Criar planilha com:

Data/hora
Jogo
Mercado (Over 0.5 ou 1.5)
Odd
EV%
Stake recomendado
Stake usado
Resultado
Lucro/prejuízo
Calcular ROI
ROI = (Lucro Total / Investimento Total) × 100

Exemplo:
100 apostas × 3% stake = 300 unidades investidas
Lucro líquido = +22 unidades

ROI = (22 / 300) × 100 = +7.3% ✅
Meta de Performance
Bom: ROI ≥ +5%
Excelente: ROI ≥ +8%
Excepcional: ROI ≥ +10%
❓ FAQ Rápido
Q: Quantas notificações por dia?
A: Varia, 2-5 oportunidades EV+ típicas (10+ se send_ev_negative: True)

Q: Preciso ficar online?
A: Não, bot roda continuamente

Q: Funciona em mobile?
A: Sim, via servidor (Render/VPS)

Q: Posso usar em múltiplas ligas?
A: Sim, editar LEAGUES em config

Q: E se perder várias apostas seguidas?
A: Normal (variância). Avaliar após 100+ apostas

Q: Posso aumentar EV mínimo?
A: Sim, editar MIN_EV_PERCENTAGE (mais rigoroso = menos notificações)

🎯 Checklist de Sucesso
Antes de começar, confirmar:

 Dependências instaladas
 Credenciais configuradas no .env
 Testes passaram (todos ✅)
 Entende conceito de EV
 Entende gestão Kelly
 Tem banca dedicada
 Planilha de controle pronta
Se todos ✅ → PRONTO PARA USAR! 🚀

Boa sorte e apostas responsáveis! 🍀

"Matemática não garante vitória em cada aposta, mas garante lucro no longo prazo."
