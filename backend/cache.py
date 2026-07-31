"""In-memory TTL caches shared across the API layer."""
import threading
import time

from cachetools import TTLCache as _TTLCache


class TTLCache:
    """Thread-safe, size-bounded cache with automatic expiration (wraps cachetools)."""

    def __init__(self, ttl_seconds: int = 900, maxsize: int = 2048):
        self._ttl = ttl_seconds
        self._store = _TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._added: dict[str, float] = {}   # key -> insertion time, for info()
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            self._store[key] = value
            self._added[key] = time.monotonic()

    def invalidate(self, key: str) -> bool:
        with self._lock:
            self._added.pop(key, None)
            return self._store.pop(key, None) is not None

    def clear(self) -> int:
        with self._lock:
            n = len(self._store)
            self._store.clear()
            self._added.clear()
            return n

    def info(self) -> dict:
        now = time.monotonic()
        with self._lock:
            self._store.expire()                       # drop expired entries
            self._added = {k: t for k, t in self._added.items() if k in self._store}
            entries = [
                {
                    "ticker": k,
                    "age_s": int(now - t),
                    "expires_in_s": max(0, int(self._ttl - (now - t))),
                }
                for k, t in self._added.items()
            ]
        return {
            "ttl_seconds": self._ttl,
            "count": len(entries),
            "entries": entries,
        }


# Shared cache instances (import these, do not create your own).
analysis_cache = TTLCache(ttl_seconds=900)    # 15 min — analyses
chart_cache    = TTLCache(ttl_seconds=3600)   # 1 h   — historical data
fund_cache     = TTLCache(ttl_seconds=7200)   # 2 h   — fundamentals
news_cache     = TTLCache(ttl_seconds=1800)   # 30 min — news
raw_cache      = TTLCache(ttl_seconds=900)    # 15 min — raw OHLCV DataFrames
backtest_cache = TTLCache(ttl_seconds=21600)  # 6 h   — historical backtests

_ALL_CACHES = (
    analysis_cache, chart_cache, fund_cache, news_cache, raw_cache, backtest_cache,
)


def clear_all_caches() -> int:
    """Clear every shared in-memory cache. Return the total entries removed."""
    return sum(c.clear() for c in _ALL_CACHES)
