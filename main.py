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

    soc = None
    while not shutdown.is_set():
        try:
            mesures = pzem.read_all()
            solar_power = mesures["solaire"]["power"]
            conso = mesures["consommation"]["power"]
            if soc is None:
                soc = mesures["batterie"]["soc"]
            mesures["batterie"]["soc"] = soc

            manager.evaluate(mesures)
            status = manager.get_status()
            state = status["current_state"]

            deficit = conso - solar_power

            if deficit <= 0:
                battery_power = -deficit
                if soc >= 100:
                    battery_power = 0
                mesures["jirama"]["power"] = 0
                mesures["groupe"]["power"] = 0
            else:
                if state in ("solaire", "batterie"):
                    battery_power = -deficit
                    mesures["jirama"]["power"] = 0
                    mesures["groupe"]["power"] = 0
                elif state == "jirama":
                    if soc >= 100:
                        battery_power = 0
                        mesures["jirama"]["power"] = round(deficit)
                    else:
                        recharge = round(deficit * 0.3)
                        battery_power = recharge
                        mesures["jirama"]["power"] = round(deficit + recharge)
                    mesures["groupe"]["power"] = 0
                elif state == "groupe":
                    if soc >= 100:
                        battery_power = 0
                        mesures["groupe"]["power"] = round(deficit)
                    else:
                        recharge = round(deficit * 0.3)
                        battery_power = recharge
                        mesures["groupe"]["power"] = round(deficit + recharge)
                    mesures["jirama"]["power"] = 0

            mesures["batterie"]["power"] = battery_power

            if battery_power > 0:
                soc = min(100, soc + battery_power * 0.015)
            elif battery_power < 0:
                soc = max(0, soc + battery_power * 0.02)
            soc = round(soc, 1)
            mesures["batterie"]["soc"] = soc
            pzem.set_battery_soc(soc)

            for src in ("jirama", "groupe"):
                if src != state:
                    mesures[src]["voltage"] = 0
                    mesures[src]["current"] = 0
                    mesures[src]["power"] = 0
                    if "frequency" in mesures[src]:
                        mesures[src]["frequency"] = 0
                    if "power_factor" in mesures[src]:
                        mesures[src]["power_factor"] = 0

            p = abs(battery_power)
            mesures["batterie"]["voltage"] = round(12 + soc * 0.016, 2)
            mesures["batterie"]["current"] = round(p / 12.5, 3) if p > 5 else 0

            if state == "jirama" or state == "groupe":
                pj = mesures[state]["power"]
                mesures[state]["voltage"] = 230
                mesures[state]["current"] = round(pj / 230, 3) if pj > 0 else 0
                mesures[state]["frequency"] = 50
                mesures[state]["power_factor"] = 0.95

            db.insert_snapshot(mesures, {
                "source_active": state,
                "batterie_soc": soc,
                "solaire_power": solar_power,
                "batterie_power": battery_power,
                "jirama_power": mesures["jirama"]["power"],
                "conso_power": conso,
                "mode": status["mode"],
            })

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
    db.clear_all()

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
