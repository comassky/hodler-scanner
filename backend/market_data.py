"""OHLCV data download with a raw-DataFrame cache (single or batched calls)."""
import pandas as pd
import yfinance as yf

from cache import raw_cache


def flat_col(data, key):
    """Return column ``key`` as a flat Series (handles yfinance's MultiIndex frames)."""
    c = data[key]
    return c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c


def download_raw(ticker_code: str, period: str = "500d", refresh: bool = False):
    """Download (or fetch from the raw cache) an OHLCV DataFrame."""
    key = f"{ticker_code}:{period}"
    if not refresh:
        cached = raw_cache.get(key)
        if cached is not None:
            return cached
    data = yf.download(
        ticker_code, period=period, interval="1d",
        progress=False, auto_adjust=False, actions=True,
    )
    if data is not None and not data.empty:
        raw_cache.set(key, data)
    return data


def download_batch(tickers: list[str], period: str = "500d", refresh: bool = False) -> dict:
    """
    Download several tickers in a single network call (instead of N).

    Returns ``{ticker: DataFrame}``. Tickers already in the raw cache are not
    re-downloaded; those that fail return an empty DataFrame.
    """
    out: dict = {}
    missing: list[str] = []
    for t in tickers:
        if not refresh:
            cached = raw_cache.get(f"{t}:{period}")
            if cached is not None:
                out[t] = cached
                continue
        missing.append(t)

    if not missing:
        return out

    if len(missing) == 1:
        try:
            frames = {missing[0]: download_raw(missing[0], period, refresh=True)}
        except Exception:
            frames = {missing[0]: pd.DataFrame()}
    else:
        try:
            data = yf.download(
                missing, period=period, interval="1d",
                progress=False, auto_adjust=False, actions=True,
                group_by="ticker", threads=True,
            )
        except Exception:
            data = None
        frames = {}
        for t in missing:
            try:
                frames[t] = data[t] if data is not None else pd.DataFrame()
            except (KeyError, TypeError):
                frames[t] = pd.DataFrame()

    for t, df in frames.items():
        if df is not None and not df.empty:
            raw_cache.set(f"{t}:{period}", df)
        out[t] = df
    return out
