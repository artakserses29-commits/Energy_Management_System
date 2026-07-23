import struct
import time
from threading import Lock

from config.settings import MODBUS_PORT, MODBUS_BAUDRATE, MODBUS_TIMEOUT, PZEM_DEVICES

try:
    import minimalmodbus
except ImportError:
    minimalmodbus = None


class PZEMReader:
    _instance = None
    _lock = Lock()
    _instruments = {}
    _use_simulation = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sim = None
        self._connect()

    def _connect(self):
        if minimalmodbus is None:
            self._use_simulation = True
            print("[PZEM] minimalmodbus non installé - mode simulation")
            return
        try:
            import serial
            test = serial.Serial(MODBUS_PORT)
            test.close()
        except Exception:
            self._use_simulation = True
            print(f"[PZEM] Port {MODBUS_PORT} indisponible - mode simulation")
            return
        for name, cfg in PZEM_DEVICES.items():
            try:
                instr = minimalmodbus.Instrument(MODBUS_PORT, cfg["address"])
                instr.serial.baudrate = MODBUS_BAUDRATE
                instr.serial.timeout = MODBUS_TIMEOUT
                instr.clear_buffers_before_each_transaction = True
                instr.close_port_after_each_call = False
                self._instruments[name] = (instr, cfg["type"])
            except Exception as e:
                print(f"[PZEM] Erreur connexion {name}: {e}")

    def read_all(self):
        if self._use_simulation:
            if self._sim is None:
                from hardware.simulation import SimulationReader
                self._sim = SimulationReader()
            return self._sim.read_all()
        measurements = {}
        for name, cfg in PZEM_DEVICES.items():
            measurements[name] = self._read_device(name)
        return measurements

    def _read_device(self, name):
        result = {"voltage": 0, "current": 0, "power": 0, "energy": 0, "soc": None}
        if name not in self._instruments:
            return result
        instr, dtype = self._instruments[name]
        try:
            if dtype == "ac":
                data = instr.read_registers(0x0000, 6)
                result["voltage"] = round(data[0] / 10.0, 1)
                result["current"] = round(data[1] / 1000.0, 3)
                result["power"] = round(data[2] / 10.0, 1)
                result["energy"] = data[3]
                result["frequency"] = round(data[4] / 10.0, 1)
                result["power_factor"] = round(data[5] / 100.0, 2)
            else:
                data = instr.read_registers(0x0000, 8)
                result["voltage"] = round(data[0] / 100.0, 2)
                current_raw = (data[1] << 16) | data[2]
                result["current"] = round(current_raw / 1000.0, 3)
                power_raw = (data[3] << 16) | data[4]
                result["power"] = round(power_raw / 10.0, 1)
                energy_raw = (data[5] << 16) | data[6]
                result["energy"] = energy_raw
                result["soc"] = data[7]
        except Exception as e:
            print(f"[PZEM] Erreur lecture {name}: {e}")
        return result

    def close(self):
        for name in list(self._instruments.keys()):
            try:
                instr, _ = self._instruments[name]
                instr.serial.close()
            except Exception:
                pass
        self._instruments.clear()
