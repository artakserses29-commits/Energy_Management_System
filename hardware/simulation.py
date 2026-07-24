import math
import random
import time


class SimulationReader:
    def __init__(self):
        self.start_time = time.time()
        self._battery_soc = 75.0
        self._jirama_on = False
        self._groupe_on = False

    def read_all(self):
        minute = self._get_minute()
        hour = minute / 600 * 24

        solar_power = self._solar_at(hour)
        consommation = round(50 + random.uniform(-10, 20), 1)

        if self._groupe_on:
            groupe_power = round(consommation + random.uniform(5, 20), 1)
            self._battery_soc = min(100, self._battery_soc + 4)
            jirama_power = 0
            battery_power = 0
            if self._battery_soc >= 80:
                self._groupe_on = False
                self._jirama_on = False

        elif self._jirama_on:
            jirama_power = round(consommation + random.uniform(5, 20), 1)
            self._battery_soc = min(100, self._battery_soc + 0.5)
            groupe_power = 0
            battery_power = 0
            if self._battery_soc >= 80:
                self._jirama_on = False

        elif solar_power > consommation + 5:
            surplus = solar_power - consommation
            self._battery_soc = min(100, self._battery_soc + surplus * 0.001)
            battery_power = round(-surplus, 1)
            jirama_power = 0
            groupe_power = 0

        elif solar_power > 0:
            deficit = consommation - solar_power
            self._battery_soc = max(0, self._battery_soc - deficit * 0.002)
            battery_power = round(deficit, 1)
            jirama_power = 0
            groupe_power = 0

        else:
            self._battery_soc = max(0, self._battery_soc - consommation * 0.02)
            battery_power = round(consommation, 1)
            jirama_power = 0
            groupe_power = 0

        self._battery_soc = round(max(0, min(100, self._battery_soc)), 1)

        if self._battery_soc < 30 and solar_power == 0 and not self._jirama_on and not self._groupe_on:
            self._jirama_on = True
        if self._battery_soc < 10 and self._jirama_on and not self._groupe_on:
            self._jirama_on = False
            self._groupe_on = True

        return {
            "solaire": {
                "voltage": round(24 + random.uniform(-0.5, 0.5), 1),
                "current": round(solar_power / 24, 3) if solar_power > 0 else 0,
                "power": round(solar_power, 1),
                "energy": round(solar_power * 0.001, 3),
                "soc": None,
            },
            "batterie": {
                "voltage": round(12 + self._battery_soc * 0.016 + random.uniform(-0.05, 0.05), 2),
                "current": round(abs(battery_power) / 12.5, 3) if abs(battery_power) > 0.5 else 0,
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

    def _get_minute(self):
        return int((time.time() - self.start_time) / 2)

    def _solar_at(self, hour):
        if 6 <= hour <= 18:
            angle = (hour - 6) / 12 * math.pi
            base = math.sin(angle) * 800
            noise = random.uniform(-30, 30)
            cloud_factor = random.choice([0.3, 0.6, 0.8, 1.0])
            return max(0, round((base + noise) * cloud_factor, 1))
        return 0

    def close(self):
        pass
