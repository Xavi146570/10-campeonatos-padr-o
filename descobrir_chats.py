import requests
import json
from datetime import datetime

# SUBSTITUA pelo seu token completo do @BotFather
BOT_TOKEN = "8215600418:SUA_PARTE_SECRETA_AQUI"

def descobrir_chat_ids():
    """Descobre Chat IDs de canais e grupos onde o bot foi adicionado"""
    try:
        print("🔄 Preparando busca...")
        
        # Limpar webhook que pode bloquear getUpdates
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", timeout=10)
        
        # Buscar atualizações recentes
        print("📥 Buscando Chat IDs...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            updates = response.json()["result"]
            print(f"✅ Encontradas {len(updates)} atualizações\n")
            
            chats_encontrados = {}
            
            for update in updates:
                chat_data = None
                
                # Mensagens normais (grupos/chats privados)
                if "message" in update:
                    chat_data = update["message"]["chat"]
                # Posts de canal
                elif "channel_post" in update:
                    chat_data = update["channel_post"]["chat"]
                
                if chat_data:
                    chat_id = chat_data["id"]
                    nome = chat_data.get("title", chat_data.get("first_name", "Chat Privado"))
                    tipo = chat_data["type"]
                    
                    # Evitar duplicatas
                    if nome not in chats_encontrados:
                        chats_encontrados[nome] = {
                            "id": chat_id,
                            "type": tipo,
                            "name": nome
                        }
            
            # Mostrar resultados organizados
            if chats_encontrados:
                print("🏆 CANAIS/GRUPOS ENCONTRADOS:")
                print("=" * 60)
                
                canais = []
                grupos = []
                privados = []
                
                for nome, info in chats_encontrados.items():
                    if info["type"] == "channel":
                        canais.append(info)
                    elif info["type"] in ["group", "supergroup"]:
                        grupos.append(info)
                    elif info["type"] == "private":
                        privados.append(info)
                
                # Mostrar canais
                if canais:
                    print("📺 CANAIS:")
                    for canal in canais:
                        print(f"   • {canal['name']}: {canal['id']}")
                    print()
                
                # Mostrar grupos
                if grupos:
                    print("👥 GRUPOS:")
                    for grupo in grupos:
                        print(f"   • {grupo['name']}: {grupo['id']}")
                    print()
                
                # Mostrar chats privados
                if privados:
                    print("💬 CHATS PRIVADOS:")
                    for privado in privados:
                        print(f"   • {privado['name']}: {privado['id']}")
                    print()
                
                # Gerar TELEGRAM_CHAT_MAP
                print("📋 TELEGRAM_CHAT_MAP PARA O RENDER:")
                print("=" * 60)
                
                # Mapear automaticamente (você pode ajustar conforme seus canais)
                ligas = ["ENG1", "ESP1", "ITA1", "GER1", "FRA1", "POR1", "BRA1", "ARG1", "BEL1", "TUR1"]
                chat_map = {}
                
                # Usar canais primeiro, depois grupos
                todos_chats = canais + grupos
                
                for i, chat in enumerate(todos_chats):
                    if i < len(ligas):
                        chat_map[ligas[i]] = str(chat["id"])
                
                if chat_map:
                    json_map = json.dumps(chat_map, separators=(',', ':'))
                    print(f"TELEGRAM_CHAT_MAP={json_map}")
                    print()
                    print("⚠️ AJUSTE o mapeamento acima conforme seus canais específicos!")
                    print("   ENG1=Premier League, ESP1=LaLiga, ITA1=Serie A, etc.")
                
                # Chat admin (primeiro chat privado encontrado)
                if privados:
                    print(f"\n👤 ADMIN_TELEGRAM_CHAT_ID={privados[0]['id']}")
                    print("   (Para receber relatórios do sistema)")
                
                return chats_encontrados
            else:
                print("❌ Nenhum chat encontrado!")
                print("\n💡 CERTIFIQUE-SE DE:")
                print("   1. Adicionar @Jogopadraobot aos seus canais/grupos")
                print("   2. Tornar o bot ADMINISTRADOR (obrigatório para canais)")
                print("   3. Ativar permissão 'Post Messages' para o bot")
                print("   4. Enviar pelo menos uma mensagem após adicionar o bot")
                return {}
        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return {}
            
    except Exception as e:
        print(f"💥 Erro: {e}")
        return {}

def testar_envio(chat_id):
    """Testa envio de mensagem para um chat específico"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        message = f"""🧪 TESTE DE CONFIGURAÇÃO

✅ Bot @Jogopadraobot funcionando!
📱 Chat ID: {chat_id}
🕐 Teste: {agora}

Se você recebeu esta mensagem, a configuração está perfeita! 🎉"""

        payload = {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Mensagem de teste enviada com sucesso!")
            return True
        else:
            error_data = response.json()
            error_desc = error_data.get('description', 'Erro desconhecido')
            print(f"❌ Erro {response.status_code}: {error_desc}")
            
            # Diagnósticos específicos
            if "chat not found" in error_desc.lower():
                print("💡 SOLUÇÃO: Verifique se o Chat ID está correto")
            elif "forbidden" in error_desc.lower():
                print("💡 SOLUÇÃO: Torne o bot administrador com permissão 'Post Messages'")
            elif "bot was blocked" in error_desc.lower():
                print("💡 SOLUÇÃO: Desbloqueie o bot no chat privado")
            
            return False
            
    except Exception as e:
        print(f"💥 Erro de conexão: {e}")
        return False

def main():
    print("🤖 DESCOBRIR CHAT IDS - @Jogopadraobot")
    print("=" * 60)
    print("📋 PREPARAÇÃO NECESSÁRIA:")
    print("   1. Crie seus canais de alertas (ex: 'Premier League Alerts')")
    print("   2. Adicione @Jogopadraobot como ADMINISTRADOR de cada canal")
    print("   3. Ative permissão 'Post Messages' para o bot")
    print("   4. Envie uma mensagem teste em cada canal/grupo")
    print("   5. Execute este script")
    print("\n🔍 Iniciando descoberta...\n")
    
    chats = descobrir_chat_ids()
    
    if chats:
        print("\n🧪 TESTE DE ENVIO (Recomendado):")
        print("Digite um Chat ID para enviar mensagem de teste:")
        
        for nome, info in chats.items():
            emoji = "📺" if info["type"] == "channel" else "👥" if info["type"] in ["group", "supergroup"] else "💬"
            print(f"   {emoji} {nome}: {info['id']}")
        
        test_chat = input("\nChat ID para testar (ou Enter para pular): ").strip()
        
        if test_chat:
            if test_chat.lstrip('-').isdigit():
                testar_envio(test_chat)
            else:
                print("❌ Chat ID deve ser um número (ex: -1001234567890)")
    
    print(f"\n🎯 PRÓXIMO PASSO:")
    print(f"   Configure as variáveis no Render e teste o webhook!")

if __name__ == "__main__":
    main()
