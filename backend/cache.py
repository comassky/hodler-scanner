"""In-memory TTL caches shared across the API layer."""
import threading
import time


class TTLCache:
    """Thread-safe cache with automatic expiration."""

    def __init__(self, ttl_seconds: int = 900):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, dict]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry and (time.monotonic() - entry[0]) < self._ttl:
                return entry[1]
            return None

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            self._store[key] = (time.monotonic(), value)

    def invalidate(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> int:
        with self._lock:
            n = len(self._store)
            self._store.clear()
            return n

    def info(self) -> dict:
        now = time.monotonic()
        with self._lock:
            valid = [(k, v) for k, v in self._store.items() if (now - v[0]) < self._ttl]
        return {
            "ttl_seconds": self._ttl,
            "count": len(valid),
            "entries": [
                {
                    "ticker": k,
                    "age_s": int(now - v[0]),
                    "expires_in_s": max(0, int(self._ttl - (now - v[0]))),
                }
                for k, v in valid
            ],
        }


# Shared cache instances (import these, do not create your own).
analysis_cache = TTLCache(ttl_seconds=900)    # 15 min — analyses
chart_cache    = TTLCache(ttl_seconds=3600)   # 1 h   — historical data
fund_cache     = TTLCache(ttl_seconds=7200)   # 2 h   — fundamentals
news_cache     = TTLCache(ttl_seconds=1800)   # 30 min — news
raw_cache      = TTLCache(ttl_seconds=900)    # 15 min — raw OHLCV DataFrames
backtest_cache = TTLCache(ttl_seconds=21600)  # 6 h   — historical backtests
