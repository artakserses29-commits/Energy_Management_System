import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# --- Modbus PZEM ---
MODBUS_PORT = os.getenv("MODBUS_PORT", "/dev/ttyUSB0")
MODBUS_BAUDRATE = 9600
MODBUS_TIMEOUT = 1

PZEM_DEVICES = {
    "solaire": {"address": 1, "type": "dc"},
    "batterie": {"address": 2, "type": "dc"},
    "jirama": {"address": 3, "type": "ac"},
    "groupe": {"address": 4, "type": "ac"},
    "consommation": {"address": 5, "type": "ac"},
}

# --- GPIO Relais ---
RELAY_PINS = {
    "solaire": 17,
    "batterie": 18,
    "jirama": 22,
    "groupe": 23,
}
RELAY_ACTIVE_HIGH = True

# --- Seuils batterie ---
BATTERY_SOC_THRESHOLD_LOW = 30
BATTERY_SOC_THRESHOLD_HIGH = 80
BATTERY_VOLTAGE_FULL = 13.8
BATTERY_VOLTAGE_EMPTY = 10.5

# --- Seuils commutation ---
POWER_THRESHOLD_SOLAR_MIN = 10
POWER_THRESHOLD_COMPLEMENT = 10

# --- Base de données ---
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "energy.db"))
DB_PURGE_DAYS = 30

# --- Web ---
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = False

# --- OpenWeatherMap ---
OWM_API_KEY = os.getenv("OWM_API_KEY", "")
OWM_LAT = os.getenv("OWM_LAT", "-18.8792")
OWM_LON = os.getenv("OWM_LON", "47.5079")
OWM_FORECAST_INTERVAL_HOURS = 6

# --- Notifications ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")

# --- Mesure ---
MEASURE_INTERVAL_SECONDS = 2
