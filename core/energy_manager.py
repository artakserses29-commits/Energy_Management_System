from enum import Enum

from config.settings import (
    BATTERY_SOC_THRESHOLD_LOW,
    BATTERY_SOC_THRESHOLD_HIGH,
    POWER_THRESHOLD_SOLAR_MIN,
    POWER_THRESHOLD_COMPLEMENT,
)
from core.shared_state import get_mode, set_mode
from data.database import Database
from hardware.relay_controller import RelayController
from notifications.telegram_notifier import TelegramNotifier
from notifications.whatsapp_notifier import WhatsAppNotifier


class SourceState(Enum):
    SOLAIRE = "solaire"
    BATTERIE = "batterie"
    JIRAMA = "jirama"
    GROUPE = "groupe"

SOC_CRITICAL = 5


class EnergyManager:
    def __init__(self):
        self.db = Database()
        self.relay = RelayController()
        self.telegram = TelegramNotifier()
        self.whatsapp = WhatsAppNotifier()
        self.current_state = SourceState.SOLAIRE
        self.last_state = None
        self.mode = "auto"
        self.manual_source = None
        self._last_change_time = 0

    def evaluate(self, mesures):
        mode, manual_source = get_mode()
        self.mode = mode
        self.manual_source = manual_source
        if mode == "manuel" and manual_source:
            self._apply_source(manual_source)
            return

        import time
        now = time.time()

        solar_power = mesures.get("solaire", {}).get("power", 0)
        battery_soc = mesures.get("batterie", {}).get("soc", None)
        battery_power = mesures.get("batterie", {}).get("power", 0)
        consommation = mesures.get("consommation", {}).get("power", 0)
        jirama_voltage = mesures.get("jirama", {}).get("voltage", 0)

        new_state = self._decide(solar_power, battery_soc, battery_power,
                                 consommation, jirama_voltage)

        JIRAMA_OK = jirama_voltage > 10

        if new_state != self.current_state:
            emergency = (new_state == SourceState.GROUPE or
                         battery_soc is not None and battery_soc <= SOC_CRITICAL or
                         self.current_state in (SourceState.JIRAMA, SourceState.GROUPE)
                         and not JIRAMA_OK)
            debounce = 5 if emergency else 30
            if now - self._last_change_time >= debounce:
                self.last_state = self.current_state
                self.current_state = new_state
                self._last_change_time = now
                self._on_state_change()

        self._apply_source(self.current_state.value)

    def _decide(self, solar_power, battery_soc, battery_power,
                consommation, jirama_voltage):
        JIRAMA_OK = jirama_voltage > 10

        if self.current_state == SourceState.JIRAMA:
            if not JIRAMA_OK:
                if battery_soc is not None and battery_soc > SOC_CRITICAL:
                    return SourceState.BATTERIE
                return SourceState.GROUPE
            if battery_soc is not None and battery_soc >= BATTERY_SOC_THRESHOLD_HIGH:
                if solar_power > POWER_THRESHOLD_SOLAR_MIN:
                    return SourceState.SOLAIRE
                return SourceState.BATTERIE
            return SourceState.JIRAMA

        if self.current_state == SourceState.GROUPE:
            if battery_soc is not None and battery_soc >= BATTERY_SOC_THRESHOLD_HIGH:
                if solar_power > POWER_THRESHOLD_SOLAR_MIN:
                    return SourceState.SOLAIRE
                if JIRAMA_OK:
                    return SourceState.JIRAMA
                return SourceState.BATTERIE
            return SourceState.GROUPE

        if solar_power > POWER_THRESHOLD_SOLAR_MIN:
            if battery_soc is not None and battery_soc >= 100 and consommation <= solar_power:
                return SourceState.SOLAIRE
            if battery_soc is None or battery_soc > BATTERY_SOC_THRESHOLD_LOW:
                return SourceState.SOLAIRE
            if battery_soc is not None and battery_soc > SOC_CRITICAL:
                return SourceState.BATTERIE
            if JIRAMA_OK:
                return SourceState.JIRAMA
            return SourceState.GROUPE

        if battery_soc is not None and battery_soc > BATTERY_SOC_THRESHOLD_LOW:
            return SourceState.BATTERIE

        if battery_soc is not None and battery_soc > SOC_CRITICAL:
            if JIRAMA_OK:
                return SourceState.JIRAMA
            return SourceState.GROUPE

        return SourceState.GROUPE

    def _on_state_change(self):
        event_type = f"commutation_{self.current_state.value}"
        levels = {
            SourceState.SOLAIRE: "success",
            SourceState.BATTERIE: "info",
            SourceState.JIRAMA: "warning",
            SourceState.GROUPE: "critical",
        }
        msg = f"Commutation vers {self.current_state.value.upper()}"
        self.db.insert_evenement(event_type, msg, levels.get(self.current_state, "info"))

        if self.current_state == SourceState.GROUPE:
            self.telegram.send_message(f"⚠️ {msg} - Démarrage manuel du groupe nécessaire")
            self.whatsapp.send_message(f"⚠️ {msg} - Démarrage manuel du groupe nécessaire")
        elif self.current_state == SourceState.JIRAMA and self.last_state == SourceState.SOLAIRE:
            self.telegram.send_message(f"⚡ {msg} (batterie faible)")

    def _apply_source(self, source_name):
        if source_name == "solaire":
            self.relay.activate_only("solaire")
        elif source_name == "batterie":
            self.relay.activate_only("batterie")
        elif source_name == "jirama":
            self.relay.activate_only("jirama")
        elif source_name == "groupe":
            self.relay.activate_only("groupe")

    def set_mode(self, mode, source=None):
        set_mode(mode, source)
        if mode == "auto":
            self.db.insert_evenement("mode", "Passage en mode automatique", "info")
        else:
            self.db.insert_evenement("mode", f"Passage en mode manuel ({source})", "warning")

    def get_status(self):
        return {
            "current_state": self.current_state.value,
            "mode": self.mode,
            "manual_source": self.manual_source,
            "relay_states": self.relay.get_state(),
        }
