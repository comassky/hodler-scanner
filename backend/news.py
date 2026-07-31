"""Recent news for a ticker via yfinance (Yahoo Finance)."""
from datetime import datetime

import yfinance as yf
from fastapi import HTTPException

from cache import news_cache


def parse_news_item(it: dict) -> dict:
    """Normalize a yfinance article (handles the old flat format and the new nested one)."""
    c = it.get("content") if isinstance(it, dict) else None
    if isinstance(c, dict):  # recent format (yfinance ≥ 0.2.40)
        url = ((c.get("canonicalUrl") or {}).get("url")
               or (c.get("clickThroughUrl") or {}).get("url"))
        res = (c.get("thumbnail") or {}).get("resolutions") or []
        return {
            "title":     c.get("title"),
            "publisher": (c.get("provider") or {}).get("displayName"),
            "url":       url,
            "published": c.get("pubDate"),
            "thumbnail": res[0].get("url") if res else None,
        }
    # old flat format
    ts, published = it.get("providerPublishTime"), None
    if ts:
        try:
            published = datetime.utcfromtimestamp(int(ts)).isoformat() + "Z"
        except Exception:
            published = None
    res = (it.get("thumbnail") or {}).get("resolutions") or []
    return {
        "title":     it.get("title"),
        "publisher": it.get("publisher"),
        "url":       it.get("link"),
        "published": published,
        "thumbnail": res[0].get("url") if res else None,
    }


def fetch_news(ticker_code: str, refresh: bool = False) -> dict:
    """Latest news for the stock via yfinance (Yahoo Finance)."""
    code = ticker_code.upper()
    cached = news_cache.get(code)
    if cached and not refresh:
        return cached
    try:
        raw = yf.Ticker(code).news or []
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Actualités indisponibles : {e}")

    items = []
    for it in raw:
        try:
            n = parse_news_item(it)
        except Exception:
            continue
        if n.get("title") and n.get("url"):
            items.append(n)

    result = {"ticker": code, "count": len(items), "items": items[:12]}
    news_cache.set(code, result)
    return result
