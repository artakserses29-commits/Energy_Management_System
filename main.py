import signal
import sys
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import MEASURE_INTERVAL_SECONDS, OWM_FORECAST_INTERVAL_HOURS, FLASK_HOST, FLASK_PORT
from core.energy_manager import EnergyManager
from core.weather import WeatherForecast
from data.database import Database
from hardware.pzem_reader import PZEMReader
from hardware.relay_controller import RelayController
from web.app import create_app

scheduler = BackgroundScheduler()
running = True


def signal_handler(sig, frame):
    global running
    running = False
    print("\nArrêt du système...")


def measurement_loop():
    pzem = PZEMReader()
    relay = RelayController()
    db = Database()
    manager = EnergyManager()

    while running:
        try:
            mesures = pzem.read_all()
            manager.evaluate(mesures)
            status = manager.get_status()

            for source, data in mesures.items():
                db.insert_mesure(
                    source=source,
                    voltage=data.get("voltage", 0),
                    current=data.get("current", 0),
                    power=data.get("power", 0),
                    energy=data.get("energy", 0),
                    soc=data.get("soc"),
                    frequency=data.get("frequency"),
                    power_factor=data.get("power_factor"),
                )

            db.insert_etat(
                source_active=status["current_state"],
                batterie_soc=mesures.get("batterie", {}).get("soc"),
                solaire_power=mesures.get("solaire", {}).get("power", 0),
                batterie_power=mesures.get("batterie", {}).get("power", 0),
                jirama_power=mesures.get("jirama", {}).get("power", 0),
                conso_power=mesures.get("consommation", {}).get("power", 0),
                mode=status["mode"],
            )

        except Exception as e:
            print(f"[Main] Erreur boucle mesure: {e}")

        time.sleep(MEASURE_INTERVAL_SECONDS)


def weather_loop():
    weather = WeatherForecast()
    while running:
        try:
            weather.update_forecast()
            alert = weather.check_tomorrow()
            if alert and alert.get("alert"):
                db = Database()
                db.insert_evenement("meteo", alert["message"], "warning")
        except Exception as e:
            print(f"[Main] Erreur météo: {e}")

        for _ in range(OWM_FORECAST_INTERVAL_HOURS * 3600 // 10):
            if not running:
                break
            time.sleep(10)


def cleanup():
    print("Nettoyage des ressources...")
    pzem = PZEMReader()
    relay = RelayController()
    pzem.close()
    relay.cleanup()
    db = Database()
    db.close()
    scheduler.shutdown(wait=False)
    print("Système arrêté.")


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Démarrage du système de gestion d'énergie...")

    db = Database()
    db._init_db()

    scheduler.add_job(
        db.purge_old_data,
        "interval",
        hours=24,
        id="purge",
        replace_existing=True,
    )
    scheduler.start()

    measure_thread = threading.Thread(target=measurement_loop, daemon=True)
    measure_thread.start()

    weather_thread = threading.Thread(target=weather_loop, daemon=True)
    weather_thread.start()

    print(f"Serveur web démarré sur http://{FLASK_HOST}:{FLASK_PORT}")
    app = create_app()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

    cleanup()


if __name__ == "__main__":
    main()
