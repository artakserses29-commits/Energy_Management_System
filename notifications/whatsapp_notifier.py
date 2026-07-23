import json
import urllib.request

from config.settings import WHATSAPP_API_URL, WHATSAPP_API_KEY


class WhatsAppNotifier:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def send_message(self, text):
        if not WHATSAPP_API_URL or not WHATSAPP_API_KEY:
            return False
        try:
            payload = json.dumps({
                "api_key": WHATSAPP_API_KEY,
                "message": text[:4096],
            }).encode()
            req = urllib.request.Request(WHATSAPP_API_URL, data=payload,
                                         headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.status == 200
        except Exception as e:
            print(f"[WhatsApp] Erreur: {e}")
            return False
