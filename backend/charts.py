"""Historical series prepared for the frontend charts."""
import pandas as pd
from fastapi import HTTPException

from cache import chart_cache
from market_data import download_raw, flat_col
from script import calculer_rsi_df

_VALID_PERIODS = {"3mo", "6mo", "1y", "2y", "max"}


def chart_data(ticker_code: str, period: str = "1y", refresh: bool = False) -> dict:
    """Return price, SMA 200/50, RSI 14, MACD histogram, volume and Bollinger bands."""
    if period not in _VALID_PERIODS:
        period = "1y"
    code = ticker_code.upper()
    cache_key = f"{code}:{period}"
    cached = chart_cache.get(cache_key)
    if cached and not refresh:
        return cached

    data = download_raw(code, period, refresh=refresh)
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {ticker_code}")

    close     = flat_col(data, "Close")
    volume    = flat_col(data, "Volume")
    vol_sma20 = volume.rolling(20, min_periods=1).mean()
    sma200    = close.rolling(200, min_periods=1).mean()
    sma50     = close.rolling(50,  min_periods=1).mean()
    rsi       = calculer_rsi_df(close.to_frame()).iloc[:, 0]

    ema12  = close.ewm(span=12, adjust=False).mean()
    ema26  = close.ewm(span=26, adjust=False).mean()
    macd   = ema12 - ema26
    hist   = macd - macd.ewm(span=9, adjust=False).mean()

    bb_mid   = close.rolling(20, min_periods=10).mean()
    bb_std   = close.rolling(20, min_periods=10).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    def _s(series):
        return [round(float(v), 4) if pd.notna(v) else None for v in series]
    def _sv(series):
        return [int(v) if pd.notna(v) and v > 0 else None for v in series]

    result = {
        "dates":     [str(ts.date()) for ts in close.index],
        "close":     _s(close),
        "sma200":    _s(sma200),
        "sma50":     _s(sma50),
        "rsi":       _s(rsi),
        "macd_hist": _s(hist),
        "volume":    _sv(volume),
        "vol_sma20": _sv(vol_sma20),
        "bb_upper":  _s(bb_upper),
        "bb_lower":  _s(bb_lower),
    }
    chart_cache.set(cache_key, result)
    return result
