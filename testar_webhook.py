import requests
import json
import time
from datetime import datetime

# CONFIGURE AQUI COM SEUS VALORES REAIS
WEBHOOK_SECRET = "fb6a5546-8f66-4530-a412-452c1844979d"
BOT_URL = "https://football-alerts-bot-padrao.onrender.com"

def testar_sistema_completo():
    print("🧪 TESTE COMPLETO DO @Jogopadraobot")
    print("=" * 50)
    
    # 1. Verificar se o serviço está online
    print("1️⃣ Verificando serviço...")
    try:
        health_response = requests.get(f"{BOT_URL}/", timeout=15)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Serviço online: {health_data.get('status', 'N/A')}")
            print(f"   Ligas configuradas: {health_data.get('leagues_configured', 'N/A')}")
        else:
            print(f"❌ Serviço offline: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"💥 Erro: {e}")
        return False
    
    # 2. Disparar webhook
    print(f"\n2️⃣ Disparando processamento...")
    try:
        headers = {
            "Authorization": f"Bearer {WEBHOOK_SECRET}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{BOT_URL}/webhook/daily-trigger", 
                               headers=headers, json={}, timeout=30)
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            print(f"✅ Webhook disparado: {data.get('status', 'N/A')}")
            print(f"   Mensagem: {data.get('message', 'N/A')}")
        elif response.status_code == 401:
            print(f"❌ Erro de autenticação: Verifique WEBHOOK_SECRET")
            return False
        elif response.status_code == 403:
            print(f"❌ Token inválido: WEBHOOK_SECRET incorreto")
            return False
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"💥 Erro ao disparar: {e}")
        return False
    
    # 3. Monitorar processamento
    print(f"\n3️⃣ Monitorando processamento...")
    for i in range(6):  # Até 30 segundos
        try:
            time.sleep(5)
            print(f"   ⏳ Aguardando... ({(i+1)*5}s)")
            
            logs_response = requests.get(f"{BOT_URL}/logs?lines=15", timeout=10)
            if logs_response.status_code == 200:
                logs_data = logs_response.json()
                recent_logs = logs_data.get("logs", [])
                
                if recent_logs:
                    print(f"\n📋 LOGS RECENTES:")
                    for log in recent_logs[-8:]:
                        print(f"   {log}")
                    
                    # Verificar se terminou
                    completed = any("Processamento concluído" in log for log in recent_logs[-3:])
                    if completed:
                        print(f"\n✅ Processamento completado!")
                        break
        except Exception as e:
            print(f"   ⚠️ Erro ao monitorar: {e}")
    
    # 4. Status final
    print(f"\n4️⃣ Status final...")
    try:
        status_response = requests.get(f"{BOT_URL}/status", timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            last_exec = status_data.get("system", {}).get("last_execution")
            
            if last_exec:
                print(f"📊 RESULTADO:")
                print(f"   Ligas processadas: {last_exec.get('leagues_processed', 0)}")
                print(f"   Jogos analisados: {last_exec.get('total_games', 0)}")
                print(f"   Alertas enviados: {last_exec.get('total_alerts', 0)}")
                print(f"   Duração: {last_exec.get('duration_seconds', 0):.1f}s")
                
                if last_exec.get('total_alerts', 0) > 0:
                    print(f"\n🎉 SUCESSO! {last_exec['total_alerts']} alertas enviados!")
                    print(f"   Verifique seus canais no Telegram!")
                else:
                    print(f"\n📊 Nenhum alerta enviado hoje.")
                    print(f"   Normal se não há jogos que atendem aos critérios.")
                    
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
    
    return True

if __name__ == "__main__":
    if WEBHOOK_SECRET == "fb6a5546-8f66-4530-a412-452c1844979d":
        print("❌ CONFIGURE O WEBHOOK_SECRET NO SCRIPT!")
        print("   Copie o valor do Render → Environment → WEBHOOK_SECRET")
    else:
        testar_sistema_completo()
