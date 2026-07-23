import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.energy_manager import EnergyManager, SourceState
from core.rules import (
    should_use_battery,
    battery_can_complement,
    should_switch_to_jirama,
    should_return_to_solar,
    should_switch_to_groupe,
    get_battery_flow,
)


def test_solar_surplus_charges_battery():
    flow, power = get_battery_flow(70, 50)
    assert flow == "charge"
    assert power == 20


def test_solar_deficit_battery_complements():
    flow, power = get_battery_flow(40, 50)
    assert flow == "decharge"
    assert power == 10


def test_solar_zero_battery_full():
    flow, power = get_battery_flow(0, 50)
    assert flow == "decharge"
    assert power == 50


def test_should_use_battery():
    assert should_use_battery(40, 50) is True
    assert should_use_battery(70, 50) is False


def test_battery_can_complement():
    assert battery_can_complement(40, 50, 50) is True
    assert battery_can_complement(40, 50, 20) is False


def test_should_switch_to_jirama():
    assert should_switch_to_jirama(25) is True
    assert should_switch_to_jirama(50) is False


def test_should_return_to_solar():
    assert should_return_to_solar(85, 50) is True
    assert should_return_to_solar(70, 50) is False
    assert should_return_to_solar(85, 5) is False


def test_should_switch_to_groupe():
    assert should_switch_to_groupe(0) is True
    assert should_switch_to_groupe(100) is False


def test_battery_flow_idle():
    flow, power = get_battery_flow(55, 50)
    assert flow == "idle" or power < 10


if __name__ == "__main__":
    test_solar_surplus_charges_battery()
    test_solar_deficit_battery_complements()
    test_solar_zero_battery_full()
    test_should_use_battery()
    test_battery_can_complement()
    test_should_switch_to_jirama()
    test_should_return_to_solar()
    test_should_switch_to_groupe()
    test_battery_flow_idle()
    print("Tous les tests passés.")
