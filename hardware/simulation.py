import math
import random
import time


class SimulationReader:
    def __init__(self):
        self.start_time = time.time()
        self._solar_profile = self._generate_solar_profile()
        self._battery_soc = 70.0
        self._groupe_active = False

    def _generate_solar_profile(self):
        profile = {}
        for minute in range(60):
            hour = minute / 60 * 24
            if 6 <= hour <= 18:
                angle = (hour - 6) / 12 * math.pi
                base = math.sin(angle) * 800
                noise = random.uniform(-50, 50)
                clouds = random.choice([1.0, 0.8, 0.6, 0.4]) if random.random() < 0.3 else 1.0
                profile[minute] = max(0, round((base + noise) * clouds, 1))
            else:
                profile[minute] = 0
        return profile

    def _get_current_minute(self):
        elapsed = time.time() - self.start_time
        return int(elapsed / 2) % 60

    def read_all(self):
        minute = self._get_current_minute()
        solar_power = self._solar_profile[minute]
        consommation = round(50 + random.uniform(-15, 25), 1)

        if solar_power > consommation + 10:
            surplus = solar_power - consommation
            self._battery_soc = min(100, self._battery_soc + surplus * 0.02)
            battery_power = round(-surplus, 1)
        elif solar_power > 0:
            deficit = consommation - solar_power
            if self._battery_soc > 30:
                self._battery_soc = max(0, self._battery_soc - deficit * 0.015)
                battery_power = round(deficit, 1)
            else:
                battery_power = round(-solar_power, 1)
                self._battery_soc = min(100, self._battery_soc + solar_power * 0.01)
        else:
            if self._battery_soc > 30:
                self._battery_soc = max(0, self._battery_soc - consommation * 0.02)
                battery_power = round(consommation, 1)
            else:
                battery_power = 0

        self._battery_soc = round(max(0, min(100, self._battery_soc)), 1)

        if self._battery_soc < 30 and solar_power == 0:
            jirama_power = round(consommation + random.uniform(5, 20), 1)
            self._battery_soc = min(100, self._battery_soc + 0.3)
            battery_power = 0

            if self._battery_soc < 15:
                self._groupe_active = True

            if self._battery_soc > 80:
                jirama_power = 0
                self._groupe_active = False
        else:
            jirama_power = 0

        if self._groupe_active and jirama_power == 0:
            groupe_power = round(consommation + random.uniform(10, 25), 1)
            self._battery_soc = min(100, self._battery_soc + 0.5)
        else:
            groupe_power = 0

        if jirama_power == 0 and groupe_power == 0 and solar_power == 0 and battery_power <= 0:
            battery_power = round(consommation * 0.5, 1)
            self._battery_soc = max(0, self._battery_soc - 0.5)

        return {
            "solaire": {
                "voltage": round(24 + random.uniform(-0.5, 0.5), 1),
                "current": round(solar_power / 24, 3) if solar_power > 0 else 0,
                "power": solar_power,
                "energy": round(solar_power * 0.001, 3),
                "soc": None,
            },
            "batterie": {
                "voltage": round(12.5 + (self._battery_soc - 50) * 0.008 + random.uniform(-0.05, 0.05), 2),
                "current": round(battery_power / 12.5, 3) if abs(battery_power) > 0.1 else 0,
                "power": round(battery_power, 1),
                "energy": round(500 * self._battery_soc / 100, 1),
                "soc": self._battery_soc,
            },
            "jirama": {
                "voltage": round(230 + random.uniform(-2, 2), 1) if jirama_power > 0 else 0,
                "current": round(jirama_power / 230, 3) if jirama_power > 0 else 0,
                "power": jirama_power,
                "energy": round(jirama_power * 0.001, 3),
                "frequency": round(50 + random.uniform(-0.1, 0.1), 1) if jirama_power > 0 else 0,
                "power_factor": round(0.95 + random.uniform(-0.02, 0.02), 2) if jirama_power > 0 else 0,
            },
            "groupe": {
                "voltage": round(230 + random.uniform(-3, 3), 1) if groupe_power > 0 else 0,
                "current": round(groupe_power / 230, 3) if groupe_power > 0 else 0,
                "power": groupe_power,
                "energy": round(groupe_power * 0.001, 3),
                "frequency": round(50 + random.uniform(-0.5, 0.5), 1) if groupe_power > 0 else 0,
                "power_factor": round(0.9 + random.uniform(-0.05, 0.05), 2) if groupe_power > 0 else 0,
            },
            "consommation": {
                "voltage": round(230 + random.uniform(-2, 2), 1),
                "current": round(consommation / 230, 3),
                "power": consommation,
                "energy": round(consommation * 0.001, 3),
                "frequency": round(50 + random.uniform(-0.1, 0.1), 1),
                "power_factor": round(0.95 + random.uniform(-0.02, 0.02), 2),
            },
        }

    def close(self):
        pass
