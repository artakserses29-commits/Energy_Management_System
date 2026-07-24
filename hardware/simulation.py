import math
import random
import time


class SimulationReader:
    def __init__(self):
        self.start_time = time.time()
        self._battery_soc = 75.0
        self._jirama_available = False
        self._jirama_timer = 0

    def set_battery_soc(self, soc):
        self._battery_soc = max(0, min(100, soc))

    def read_all(self):
        minute = self._get_minute()
        hour = minute / 600 * 24

        solar_power = round(self._solar_at(hour), 1)
        consommation = round(50 + random.uniform(-10, 20), 1)

        self._jirama_timer += 1
        if self._jirama_available and self._jirama_timer > random.randint(30, 60):
            self._jirama_available = False
            self._jirama_timer = 0
        elif not self._jirama_available and self._jirama_timer > random.randint(40, 80):
            self._jirama_available = True
            self._jirama_timer = 0

        if self._jirama_available:
            jirama = {"voltage": 230, "current": 0, "power": 0, "frequency": 50, "power_factor": 0.95}
        else:
            jirama = {"voltage": 0, "current": 0, "power": 0, "frequency": 0, "power_factor": 0}

        return {
            "solaire": {
                "voltage": round(24 + random.uniform(-0.5, 0.5), 1),
                "current": round(solar_power / 24, 3) if solar_power > 0 else 0,
                "power": solar_power,
                "soc": None,
            },
            "batterie": {
                "voltage": round(12 + self._battery_soc * 0.016 + random.uniform(-0.05, 0.05), 2),
                "current": 0,
                "power": 0,
                "soc": self._battery_soc,
            },
            "jirama": jirama,
            "groupe": {"voltage": 0, "current": 0, "power": 0, "frequency": 0, "power_factor": 0},
            "consommation": {
                "voltage": round(230 + random.uniform(-2, 2), 1),
                "current": round(consommation / 230, 3),
                "power": consommation,
                "frequency": round(50 + random.uniform(-0.1, 0.1), 1),
                "power_factor": round(0.95 + random.uniform(-0.02, 0.02), 2),
            },
        }

    def _get_minute(self):
        return int((time.time() - self.start_time) / 2)

    def _solar_at(self, hour):
        if 6 <= hour <= 18:
            angle = (hour - 6) / 12 * math.pi
            base = math.sin(angle) * 800
            noise = random.uniform(-30, 30)
            cloud_factor = random.choice([0.3, 0.6, 0.8, 1.0])
            return max(0, (base + noise) * cloud_factor)
        return 0

    def close(self):
        pass
