import threading

_lock = threading.Lock()
_mode = "auto"
_manual_source = None


def get_mode():
    with _lock:
        return _mode, _manual_source


def set_mode(mode, manual_source=None):
    global _mode, _manual_source
    with _lock:
        _mode = mode
        _manual_source = manual_source
