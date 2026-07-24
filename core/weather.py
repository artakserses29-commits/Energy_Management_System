import json
import math
import urllib.request
from datetime import datetime, timedelta

from config.settings import OWM_API_KEY, OWM_LAT, OWM_LON
from data.database import Database


class WeatherForecast:
    def __init__(self):
        self.db = Database()
        self._cache = {}
        self._simulated = False

    def update_forecast(self):
        if not OWM_API_KEY:
            if not self._simulated:
                self._simulate_forecast()
                self._simulated = True
            return
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/onecall"
                f"?lat={OWM_LAT}&lon={OWM_LON}"
                f"&exclude=current,minutely,hourly,alerts"
                f"&appid={OWM_API_KEY}&units=metric&lang=fr"
            )
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read().decode())
            self._process_forecast(data["daily"])
        except Exception as e:
            print(f"[Weather] Erreur: {e}")

    def _simulate_forecast(self):
        today = datetime.now().date()
        profiles = [
            (10, 8, "Bonne production solaire attendue"),
            (40, 5, "Journee partiellement nuageuse - Surveiller la production"),
            (75, 2, "Journee tres nuageuse - Precharger la batterie et preparer JIRAMA"),
            (20, 7, "Bonne production solaire attendue"),
            (60, 3, "Journee partiellement nuageuse - Surveiller la production"),
        ]
        for i, (clouds, uvi, rec) in enumerate(profiles):
            date = today + timedelta(days=i)
            production = self._estimate_production(clouds, uvi)
            self.db.insert_prevision(
                date_prev=date.isoformat(),
                couverture=clouds,
                irradiance=uvi,
                production_estimee=production,
                recommandation=rec,
            )

    def _process_forecast(self, daily_data):
        for day in daily_data[:5]:
            date = datetime.fromtimestamp(day["dt"]).date()
            clouds = day.get("clouds", 50)
            uvi = day.get("uvi", 0)
            production = self._estimate_production(clouds, uvi)
            recommandation = self._make_recommandation(clouds, production)

            self.db.insert_prevision(
                date_prev=date.isoformat(),
                couverture=clouds,
                irradiance=uvi,
                production_estimee=production,
                recommandation=recommandation,
            )

    def _estimate_production(self, clouds, uvi):
        max_production = 1000
        cloud_factor = max(0, 1 - (clouds / 100) * 0.7)
        uvi_factor = min(1, uvi / 8)
        return round(max_production * cloud_factor * uvi_factor, 1)

    def _make_recommandation(self, clouds, production):
        if clouds > 70 or production < 200:
            return "Journee tres nuageuse - Precharger la batterie et preparer JIRAMA"
        elif clouds > 40 or production < 500:
            return "Journee partiellement nuageuse - Surveiller la production"
        return "Bonne production solaire attendue"

    def check_tomorrow(self):
        previsions = self.db.get_previsions(2)
        if len(previsions) < 2:
            return None
        tomorrow = previsions[1]
        if tomorrow["couverture_nuageuse"] and tomorrow["couverture_nuageuse"] > 60:
            return {
                "alert": True,
                "message": f"Demain nuageux ({tomorrow['couverture_nuageuse']:.0f}%) - "
                           f"Production estimee: {tomorrow['production_estimee']:.0f}W. "
                           f"Prechargez la batterie aujourd'hui",
                "recommandation": tomorrow["recommandation"],
            }
        return {"alert": False, "message": "Demain favorable au solaire"}
