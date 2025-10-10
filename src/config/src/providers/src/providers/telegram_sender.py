import os
import requests

class TelegramError(Exception):
    pass

class TelegramSender:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        if not self.token:
            raise TelegramError("TELEGRAM_TOKEN não configurado")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id, text, disable_preview=True):
        """Envia mensagem para o Telegram"""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": disable_preview,
                "parse_mode": None  # Texto simples para evitar problemas de formatação
            }
            
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            print(f"✅ Mensagem enviada para chat {chat_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
