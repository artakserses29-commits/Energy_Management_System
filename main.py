import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import MEASURE_INTERVAL_SECONDS, OWM_FORECAST_INTERVAL_HOURS, FLASK_HOST, FLASK_PORT
from core.energy_manager import EnergyManager
from core.weather import WeatherForecast
from data.database import Database
from hardware.pzem_reader import PZEMReader
from webserver import run_server

shutdown = threading.Event()
scheduler = BackgroundScheduler()


def measurement_loop():
    try:
        pzem = PZEMReader()
        db = Database()
        manager = EnergyManager()
    except Exception as e:
        print(f"[Mesure] Erreur init: {e}")
        return

    while not shutdown.is_set():
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
            print(f"[Mesure] Erreur: {e}")

        shutdown.wait(MEASURE_INTERVAL_SECONDS)


def weather_loop():
    weather = WeatherForecast()
    while not shutdown.is_set():
        try:
            weather.update_forecast()
            alert = weather.check_tomorrow()
            if alert and alert.get("alert"):
                Database().insert_evenement("meteo", alert["message"], "warning")
        except Exception as e:
            print(f"[Meteo] Erreur: {e}")
        shutdown.wait(OWM_FORECAST_INTERVAL_HOURS * 3600)


def main():
    print("Demarrage du systeme de gestion d'energie...")

    db = Database()
    db._init_db()

    scheduler.add_job(db.purge_old_data, "interval", hours=24, id="purge", replace_existing=True)
    scheduler.start()

    t1 = threading.Thread(target=measurement_loop, daemon=True)
    t2 = threading.Thread(target=weather_loop, daemon=True)
    t1.start()
    t2.start()
    print("Threads mesure et meteo demarres.")

    try:
        run_server(host="127.0.0.1", port=FLASK_PORT)
    finally:
        shutdown.set()
        print("Arret en cours...")
        scheduler.shutdown(wait=False)
        print("Systeme arrete.")


if __name__ == "__main__":
    main()
