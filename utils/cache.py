import threading
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheItem:
    value: Any
    expire_at: Optional[float]


class TTLCache:
    """Simple in-memory TTL cache for backend services."""

    def __init__(self):
        self._store: dict[str, CacheItem] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None

            if item.expire_at is not None and time.time() > item.expire_at:
                self._store.pop(key, None)
                return None

            return item.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = 60) -> Any:
        expire_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock:
            self._store[key] = CacheItem(value=value, expire_at=expire_at)
        return value

    def get_or_set(self, key: str, factory, ttl_seconds: Optional[int] = 60) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached

        value = factory()
        self.set(key, value, ttl_seconds=ttl_seconds)
        return value


market_data_cache = TTLCache()
