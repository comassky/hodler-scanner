"""Fundamental data (P/E, market cap, sector…) via yfinance."""
import yfinance as yf
from fastapi import HTTPException

from cache import fund_cache


def fetch_fundamentals(ticker_code: str, refresh: bool = False) -> dict:
    """P/E, market cap, sector, country and next earnings date via yfinance.info."""
    code = ticker_code.upper()
    cached = fund_cache.get(code)
    if cached and not refresh:
        return cached
    try:
        tk   = yf.Ticker(code)
        info = tk.info
        result = {
            "pe_trailing":   info.get("trailingPE"),
            "pe_forward":    info.get("forwardPE"),
            "market_cap":    info.get("marketCap"),
            "sector":        info.get("sector", ""),
            "industry":      info.get("industry", ""),
            "country":       info.get("country", ""),
            "employees":     info.get("fullTimeEmployees"),
            "earnings_date": None,
        }
        try:
            cal = tk.calendar
            if isinstance(cal, dict) and "Earnings Date" in cal:
                ed = cal["Earnings Date"]
                dates = [d for d in (ed if hasattr(ed, "__iter__") and not isinstance(ed, str) else [ed]) if d is not None]
                if dates:
                    result["earnings_date"] = str(dates[0])[:10]
        except Exception:
            pass
        fund_cache.set(code, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
