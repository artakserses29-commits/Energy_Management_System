import math
import random
import time


class SimulationReader:
    def __init__(self):
        self.start_time = time.time()
        self._solar_profile = self._generate_solar_profile()

    def _generate_solar_profile(self):
        profile = {}
        for minute in range(1440):
            hour = minute / 60
            if 6 <= hour <= 18:
                angle = (hour - 6) / 12 * math.pi
                base = math.sin(angle) * 800
                noise = random.uniform(-50, 50)
                clouds = random.choice([1.0, 0.8, 0.6, 0.4]) if random.random() < 0.3 else 1.0
                profile[minute] = max(0, (base + noise) * clouds)
            else:
                profile[minute] = 0
        return profile

    def _get_current_minute(self):
        elapsed = time.time() - self.start_time
        return int(elapsed / 2) % 1440

    def read_all(self):
        minute = self._get_current_minute()

        solar_power = self._solar_profile[minute]

        consommation = 50 + random.uniform(-10, 20)

        if solar_power > consommation:
            battery_power = -(solar_power - consommation)
            battery_soc = min(100, 50 + (solar_power - consommation) * 0.01)
        elif solar_power > 0:
            battery_power = consommation - solar_power
            battery_soc = max(0, 50 - (consommation - solar_power) * 0.01)
        else:
            battery_power = consommation
            battery_soc = max(0, 50 - consommation * 0.02 * (minute % 10))

        if minute % 1440 < 60:
            jirama_power = 0
        else:
            jirama_power = 0

        return {
            "solaire": {
                "voltage": 24 + random.uniform(-0.5, 0.5),
                "current": solar_power / 24 if solar_power > 0 else 0,
                "power": round(solar_power, 1),
                "energy": round(solar_power * 0.001, 3),
                "soc": None,
            },
            "batterie": {
                "voltage": 12.5 + (battery_soc - 50) * 0.01 + random.uniform(-0.1, 0.1),
                "current": battery_power / 12.5 if battery_power != 0 else 0,
                "power": round(battery_power, 1),
                "energy": 500,
                "soc": round(battery_soc, 1),
            },
            "jirama": {
                "voltage": 230 if jirama_power > 0 else 0,
                "current": jirama_power / 230 if jirama_power > 0 else 0,
                "power": round(jirama_power, 1),
                "energy": 0,
                "frequency": 50.0 if jirama_power > 0 else 0,
                "power_factor": 1.0 if jirama_power > 0 else 0,
            },
            "groupe": {
                "voltage": 0,
                "current": 0,
                "power": 0,
                "energy": 0,
                "frequency": 0,
                "power_factor": 0,
            },
            "consommation": {
                "voltage": 230,
                "current": consommation / 230,
                "power": round(consommation, 1),
                "energy": round(consommation * 0.001, 3),
                "frequency": 50.0,
                "power_factor": 0.95,
            },
        }

    def close(self):
        pass
