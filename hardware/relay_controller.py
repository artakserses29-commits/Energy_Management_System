from threading import Lock

from config.settings import RELAY_PINS, RELAY_ACTIVE_HIGH

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


class RelayController:
    _instance = None
    _lock = Lock()

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
        self._states = {}
        self._setup()

    def _setup(self):
        if GPIO is None:
            return
        GPIO.setmode(GPIO.BCM)
        for name, pin in RELAY_PINS.items():
            GPIO.setup(pin, GPIO.OUT)
            initial = GPIO.HIGH if RELAY_ACTIVE_HIGH else GPIO.LOW
            GPIO.output(pin, initial)
            self._states[name] = False

    def activate(self, name):
        if name not in RELAY_PINS:
            return False
        with self._lock:
            if GPIO is not None:
                GPIO.output(RELAY_PINS[name], GPIO.HIGH if RELAY_ACTIVE_HIGH else GPIO.LOW)
            self._states[name] = True
        return True

    def deactivate(self, name):
        if name not in RELAY_PINS:
            return False
        with self._lock:
            if GPIO is not None:
                GPIO.output(RELAY_PINS[name], GPIO.LOW if RELAY_ACTIVE_HIGH else GPIO.HIGH)
            self._states[name] = False
        return True

    def is_active(self, name):
        return self._states.get(name, False)

    def activate_only(self, name):
        for source in RELAY_PINS:
            if source == name:
                self.activate(source)
            else:
                self.deactivate(source)

    def get_state(self):
        return {name: self._states.get(name, False) for name in RELAY_PINS}

    def cleanup(self):
        if GPIO is not None:
            GPIO.cleanup()
