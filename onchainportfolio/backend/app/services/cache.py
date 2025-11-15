import time
from typing import Any, Tuple

class TTLCache:
    def __init__(self):
        self._data: dict[str, Tuple[float, Any]] = {}

    def get(self, key: str):
        now = time.time()
        hit = self._data.get(key)
        if not hit:
            return None
        exp, val = hit
        if now > exp:
            self._data.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: int):
        self._data[key] = (time.time() + ttl_seconds, value)

cache = TTLCache()
