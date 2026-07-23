from config.settings import (
    BATTERY_SOC_THRESHOLD_LOW,
    BATTERY_SOC_THRESHOLD_HIGH,
    POWER_THRESHOLD_SOLAR_MIN,
    POWER_THRESHOLD_COMPLEMENT,
)


def should_use_battery(solar_power, consommation_power):
    return solar_power < consommation_power


def battery_can_complement(solar_power, consommation_power, battery_soc):
    if battery_soc is None:
        return False
    return battery_soc > BATTERY_SOC_THRESHOLD_LOW


def should_switch_to_jirama(battery_soc):
    if battery_soc is None:
        return True
    return battery_soc < BATTERY_SOC_THRESHOLD_LOW


def should_return_to_solar(battery_soc, solar_power):
    if battery_soc is None:
        return False
    return battery_soc >= BATTERY_SOC_THRESHOLD_HIGH and solar_power > POWER_THRESHOLD_SOLAR_MIN


def should_switch_to_groupe(jirama_power):
    return jirama_power < 1


def should_use_generator(jirama_power, battery_soc):
    return jirama_power < 1 and battery_soc is not None and battery_soc < BATTERY_SOC_THRESHOLD_LOW


def get_solar_state(solar_power):
    if solar_power > POWER_THRESHOLD_SOLAR_MIN:
        return "active"
    return "inactive"


def get_battery_flow(solar_power, consommation_power):
    diff = solar_power - consommation_power
    if diff > POWER_THRESHOLD_COMPLEMENT:
        return "charge", abs(diff)
    elif diff < -POWER_THRESHOLD_COMPLEMENT:
        return "decharge", abs(diff)
    return "idle", 0
