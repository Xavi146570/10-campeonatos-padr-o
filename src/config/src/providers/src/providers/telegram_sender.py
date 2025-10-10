import os
import requests

class TelegramSender:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        if not self.token:
            raise Exception("TELEGRAM_TOKEN não configurado")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id, text, disable_preview=True):
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": disable_preview
            }
            
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro Telegram: {e}")
            return False
