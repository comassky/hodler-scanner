"""
Hodler Scanner — REST API (FastAPI)
GET /ticker/{ticker_code}  →  full technical analysis as JSON
GET /docs                  →  interactive Swagger UI
"""
import asyncio
import json
import math
import os
import re
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from script import (
    _get_last,
    calculer_rsi_df,
    detecter_divergence_haussiere,
    generer_analyse_investisseur_lt,
    fetch_single_ticker_info,
)
import db
from i18n import t as _t

_ANSI = re.compile(r"\033\[[^m]*m")


def _strip(s: str) -> str:
    """Strip ANSI codes for clean JSON."""
    return _ANSI.sub("", str(s)).strip()


# ── In-memory TTL cache ───────────────────────────────────────────
class _TTLCache:
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


_cache       = _TTLCache(ttl_seconds=900)   # 15 min — analyses
_chart_cache = _TTLCache(ttl_seconds=3600)  # 1 h   — historical data
_fund_cache  = _TTLCache(ttl_seconds=7200)  # 2 h   — fundamentals
_news_cache  = _TTLCache(ttl_seconds=1800)  # 30 min — news
_raw_cache   = _TTLCache(ttl_seconds=900)   # 15 min — raw OHLCV DataFrames


# ── Memoized names cache (reloaded from SQLite via a TTL) ──────
_names_lock: threading.Lock = threading.Lock()
_names_state: tuple[float, dict] | None = None
_NAMES_TTL = 300.0  # seconds


def _noms_cache() -> dict:
    """Return the names cache, reloaded from SQLite at most every 5 min."""
    global _names_state
    now = time.monotonic()
    with _names_lock:
        if _names_state is None or now - _names_state[0] > _NAMES_TTL:
            _names_state = (now, db.get_names())
        return _names_state[1]


def _invalider_noms_cache() -> None:
    """Force a reload of the names cache on next access."""
    global _names_state
    with _names_lock:
        _names_state = None


# ── Pre-warm at startup ──────────────────────────────────────────
async def _prewarm() -> None:
    """Preload in the background the tickers from TICKERS (env) or the favorites (SQLite)."""
    tickers_env = os.getenv("TICKERS", "")
    if tickers_env:
        tickers = [t.strip().upper() for t in tickers_env.split(",") if t.strip()]
    else:
        tickers = db.get_favorites()

    if not tickers:
        return

    # Only recompute tickers missing from the cache
    todo = [t for t in tickers if _cache.get(f"{t}:en") is None]
    if not todo:
        return

    # Single grouped network download, then computation capped at 4 threads
    raw = await asyncio.to_thread(_download_batch, todo, "500d", False)
    sem = asyncio.Semaphore(4)

    async def _load(ticker: str) -> None:
        async with sem:
            try:
                result = await asyncio.to_thread(_analyse_ticker, ticker, "en", raw.get(ticker))
                _cache.set(f"{ticker}:en", result)
            except Exception:
                pass

    await asyncio.gather(*[_load(t) for t in todo])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    asyncio.create_task(_prewarm())
    yield


def _json_safe(obj):
    """Recursively replace NaN/Inf floats with None so the payload is valid JSON."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


class SafeJSONResponse(JSONResponse):
    """JSONResponse that renders NaN/Inf as null instead of raising."""

    def render(self, content) -> bytes:
        return json.dumps(
            _json_safe(content),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")


app = FastAPI(
    title="Hodler Scanner API",
    description="Buy & Hold technical analysis — SMA, RSI, MACD, Bollinger Bands, scoring",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:80"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────
def _download_raw(ticker_code: str, period: str = "500d", refresh: bool = False):
    """Download (or fetch from the raw cache) an OHLCV DataFrame."""
    key = f"{ticker_code}:{period}"
    if not refresh:
        cached = _raw_cache.get(key)
        if cached is not None:
            return cached
    data = yf.download(
        ticker_code, period=period, interval="1d",
        progress=False, auto_adjust=False, actions=True,
    )
    if data is not None and not data.empty:
        _raw_cache.set(key, data)
    return data


def _download_batch(tickers: list[str], period: str = "500d", refresh: bool = False) -> dict:
    """
    Download several tickers in a single network call (instead of N).

    Returns ``{ticker: DataFrame}``. Tickers already in the raw cache are not
    re-downloaded; those that fail return an empty DataFrame.
    """
    out: dict = {}
    missing: list[str] = []
    for t in tickers:
        if not refresh:
            cached = _raw_cache.get(f"{t}:{period}")
            if cached is not None:
                out[t] = cached
                continue
        missing.append(t)

    if not missing:
        return out

    if len(missing) == 1:
        try:
            frames = {missing[0]: _download_raw(missing[0], period, refresh=True)}
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
            _raw_cache.set(f"{t}:{period}", df)
        out[t] = df
    return out


def _analyse_ticker(ticker_code: str, lang: str = "en", data=None) -> dict:
    if data is None:
        data = _download_raw(ticker_code, "500d")
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {ticker_code}")

    # Flat columns for a single ticker
    def _col(key):
        c = data[key]
        return c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c

    close  = _col("Close")
    high   = _col("High")
    low    = _col("Low")
    volume = _col("Volume")
    divs   = _col("Dividends") if "Dividends" in data else pd.Series(dtype=float)

    days_avail   = int(close.count())
    if days_avail == 0:
        # Delisted / unknown symbol: yfinance returns an all-NaN frame.
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {ticker_code}")
    data_partiel = days_avail < 200

    # ── Vectorized indicators ─────────────────────────────────────
    close_w  = close.resample("W-FRI").last()
    sma200_s = close.rolling(200, min_periods=1).mean()
    sma50_s  = close.rolling(50,  min_periods=1).mean()
    sma50w_s = close_w.rolling(50, min_periods=5).mean()
    h52w_s   = close.rolling(252, min_periods=1).max()
    l52w_s   = close.rolling(252, min_periods=1).min()

    rsi_d_s  = calculer_rsi_df(close.to_frame()).iloc[:, 0]
    rsi_w_s  = calculer_rsi_df(close_w.to_frame()).iloc[:, 0]

    bb_mid   = close.rolling(20, min_periods=10).mean()
    bb_std   = close.rolling(20, min_periods=10).std()
    # %B = (price - lower_band) / (upper_band - lower_band)
    bb_pct_s = (close - (bb_mid - 2 * bb_std)) / (4 * bb_std)

    ema12w   = close_w.ewm(span=12, min_periods=1, adjust=False).mean()
    ema26w   = close_w.ewm(span=26, min_periods=1, adjust=False).mean()
    macd_w   = ema12w - ema26w
    hist_w_s = macd_w - macd_w.ewm(span=9, min_periods=1, adjust=False).mean()
    vol20_s  = volume.rolling(20).mean()
    # ── ATR 14 ─────────────────────────────────────────────────────
    _tr     = pd.concat([(high - low).abs(), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr14_s = _tr.rolling(14, min_periods=1).mean()

    # ── Last values ──────────────────────────────────────────
    sma200_ff   = sma200_s.ffill()
    slope_off   = min(20, len(sma200_ff) - 1)
    sma200_curr = float(sma200_ff.iloc[-1])
    sma200_prev = float(sma200_ff.iloc[-1 - slope_off])
    sma200_slop = (sma200_curr - sma200_prev) / sma200_prev * 100 if sma200_prev else 0.0

    hist_ff    = hist_w_s.ffill()
    hist_curr  = float(hist_ff.iloc[-1])
    hist_prev  = float(hist_ff.iloc[-2]) if len(hist_ff.dropna()) >= 2 else hist_curr

    c_curr    = float(close.ffill().iloc[-1])
    sma50_v   = float(sma50_s.ffill().iloc[-1])
    w50_ff    = sma50w_s.ffill()
    has_w50   = not w50_ff.dropna().empty
    sma50w_v  = float(w50_ff.iloc[-1]) if has_w50 else sma200_curr
    rsi_d     = float(rsi_d_s.ffill().iloc[-1])
    rsi_w     = float(rsi_w_s.ffill().iloc[-1])
    h52w_v    = float(h52w_s.ffill().iloc[-1])
    l52w_v    = float(l52w_s.ffill().iloc[-1])
    bb_pct_v  = float(bb_pct_s.ffill().iloc[-1])
    v_curr    = float(volume.ffill().iloc[-1])
    v_mean    = float(vol20_s.ffill().iloc[-1]) if not vol20_s.dropna().empty else 0.0
    rvol      = round(v_curr / v_mean, 2) if v_mean > 0 else 1.0
    var_j     = float((close.pct_change() * 100).ffill().iloc[-1])
    atr14_v   = float(atr14_s.ffill().iloc[-1])

    # ── Dividends ─────────────────────────────────────────────────
    annual_div, last_div_date = 0.0, "N/A"
    if not divs.empty:
        divs   = divs.fillna(0.0)
        cutoff = pd.Timestamp.now() - pd.DateOffset(years=1)
        annual_div = float(divs[(divs.index >= cutoff) & (divs > 0)].sum())
        ld = divs[divs > 0]
        last_div_date = ld.index[-1].strftime("%Y-%m-%d") if not ld.empty else "N/A"

    # ── RSI divergence ─────────────────────────────────────────────
    div_hauss, rsi_c1, rsi_c2 = detecter_divergence_haussiere(close, rsi_d_s)

    # ── Trend ───────────────────────────────────────────────────
    if sma50_v > sma200_curr:
        tendance = _t(lang, "trend.up_bullish") if sma200_slop > 0.3 else _t(lang, "trend.up_neutral")
    else:
        tendance = _t(lang, "trend.down_bearish") if sma200_slop < -0.3 else _t(lang, "trend.down_neutral")

    # ── Distances ──────────────────────────────────────────────────
    dist_sma200 = (c_curr - sma200_curr) / sma200_curr * 100 if sma200_curr else 0.0
    dist_w50    = (c_curr - sma50w_v)    / sma50w_v    * 100 if sma50w_v    else 0.0
    dist_52h    = (c_curr - h52w_v)      / h52w_v      * 100 if h52w_v      else 0.0
    dist_52l    = (c_curr - l52w_v)      / l52w_v      * 100 if l52w_v      else 0.0

    # ── Name (local cache first) ──────────────────────────────────
    cache = _noms_cache()
    nom   = cache.get(ticker_code)
    if not nom:
        nom = fetch_single_ticker_info(ticker_code)[1]
        db.upsert_name(ticker_code, nom)
        _invalider_noms_cache()

    # ── Scoring ────────────────────────────────────────────────────
    item = {
        "Code": ticker_code, "Nom": nom, "Cours": round(c_curr, 2),
        "RSI_val": rsi_d,    "RSI_W_val": rsi_w,    "RVOL_val": rvol,
        "52w_val": dist_52h, "Ecart_sma200_val": dist_sma200,
        "Ecart_w50_val": dist_w50,  "H52W_price":  h52w_v,
        "SMA200_val": sma200_curr,  "Div_Montant": annual_div,
        "Div_Date":   last_div_date,"W50_valide":  has_w50,
        "SMA50_val":  sma50_v,      "SMA200_slope": sma200_slop,
        "L52W_price": l52w_v,       "Dist_52wLow_val": dist_52l,
        "Divergence_RSI":   div_hauss,
        "Div_RSI_creux1":   rsi_c1,
        "Div_RSI_creux2":   rsi_c2,
        "BB_pct_val":       bb_pct_v,
        "MACD_W_hist":      hist_curr,
        "MACD_W_hist_prev": hist_prev,
    }
    diag, statut_lt, score, expl, strat, gain_est, sc_det, synthese = generer_analyse_investisseur_lt(item, lang)

    return {
        "ticker":        ticker_code,
        "name":          nom,
        "timestamp":     datetime.now().isoformat(),
        "data_partiel":  data_partiel,
        "days_available": days_avail,
        "price": {
            "last":        round(c_curr, 2),
            "var_jour_pct": round(var_j, 2),
        },
        "indicators": {
            "sma200":              round(sma200_curr, 2),
            "sma50":               round(sma50_v, 2),
            "w50":                 round(sma50w_v, 2) if has_w50 else None,
            "sma200_slope_20j_pct": round(sma200_slop, 2),
            "rsi_daily":           round(rsi_d, 1),
            "rsi_weekly":          round(rsi_w, 1),
            "rvol":                rvol,
            "bb_pct":              round(bb_pct_v, 3),
            "macd_w_hist":         round(hist_curr, 4),
            "macd_w_hist_prev":    round(hist_prev, 4),
            "macd_w_cross_up":     bool(hist_curr > 0 and hist_prev <= 0),
            "atr14":               round(atr14_v, 2),
            "atr14_pct":           round(atr14_v / c_curr * 100, 2) if c_curr else 0.0,
        },
        "distances": {
            "ecart_sma200_pct":  round(dist_sma200, 2),
            "ecart_w50_pct":     round(dist_w50,    2) if has_w50 else None,
            "dist_52w_high_pct": round(dist_52h, 1),
            "dist_52w_low_pct":  round(dist_52l, 1),
            "h52w_price":        round(h52w_v, 2),
            "l52w_price":        round(l52w_v, 2),
        },
        "fundamentals": {
            "dividende_annuel":  round(annual_div, 2),
            "derniere_date_div": last_div_date,
        },
        "signals": {
            "tendance":       tendance,
            "alerte_sma200":  bool(-5.0 <= dist_sma200 <= 3.0),
            "alerte_w50":     bool(has_w50 and -5.0 <= dist_w50 <= 3.0),
            "divergence_rsi": div_hauss,
            "rsi_creux":      [round(rsi_c1, 1), round(rsi_c2, 1)] if div_hauss else None,
        },
        "analysis": {
            "score":         score,
            "score_details": sc_det,
            "statut":        _strip(statut_lt),
            "synthese": {
                "verdict": _strip(synthese["verdict"]),
                "atout":   _strip(synthese["atout"])  if synthese["atout"]  else None,
                "risque":  _strip(synthese["risque"]) if synthese["risque"] else None,
            },
            "explication":   _strip(expl),
            "strategie":     strat,
            "objectifs":     _strip(gain_est),
            "diagnostics":   [{"text": _strip(x["text"]), "impact": x["impact"]} for x in diag],
        },
    }



@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/search", summary="Search tickers by name or symbol", tags=["utils"])
def search_tickers(q: str):
    """Search via Yahoo Finance Search (min. 2 characters)."""
    if len(q.strip()) < 2:
        return []
    try:
        quotes = yf.Search(q, max_results=8).quotes
        return [
            {
                "ticker":   r.get("symbol", ""),
                "name":     r.get("longname") or r.get("shortname", ""),
                "type":     r.get("typeDisp", ""),
                "exchange": r.get("exchDisp", ""),
            }
            for r in quotes
            if r.get("symbol")
        ]
    except Exception:
        return []


@app.get("/ticker/{ticker_code}", summary="Full technical analysis of a ticker")
async def get_ticker(ticker_code: str, refresh: bool = False, lang: str = "en"):
    """
    Return all technical indicators + B&H score for a ticker.

    **Examples**: `MC.PA`, `AAPL`, `ASML.AS`, `BTC-USD`

    - `refresh=true`: force recomputation even if the cache is valid
    - `lang`: language of the analysis text (`en` by default, `fr`)
    """
    code = ticker_code.upper()
    lang = "fr" if lang == "fr" else "en"
    ckey = f"{code}:{lang}"

    if not refresh:
        cached = _cache.get(ckey)
        if cached is not None:
            return {**cached, "cached": True}

    try:
        result = await asyncio.to_thread(_analyse_ticker, code, lang)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    _cache.set(ckey, result)
    return {**result, "cached": False}


@app.get("/ticker/{ticker_code}/chart", summary="Historical data for charts", tags=["analyse"])
def ticker_chart(ticker_code: str, period: str = "1y", refresh: bool = False):
    """Return price, SMA 200/50, RSI 14 and MACD histogram for the charts."""
    if period not in {"3mo", "6mo", "1y", "2y", "max"}:
        period = "1y"
    cache_key = f"{ticker_code.upper()}:{period}"
    cached = _chart_cache.get(cache_key)
    if cached and not refresh:
        return cached

    data = _download_raw(ticker_code.upper(), period, refresh=refresh)
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {ticker_code}")

    def _col(key):
        c = data[key]
        return c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c

    close     = _col("Close")
    volume    = _col("Volume")
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
    _chart_cache.set(cache_key, result)
    return result


@app.get("/ticker/{ticker_code}/fundamentals", summary="Fundamental data", tags=["analyse"])
def ticker_fundamentals(ticker_code: str, refresh: bool = False):
    """P/E, market cap, sector, country via yfinance.info."""
    code = ticker_code.upper()
    cached = _fund_cache.get(code)
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
        _fund_cache.set(code, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _parse_news_item(it: dict) -> dict:
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


@app.get("/ticker/{ticker_code}/news", summary="Recent news", tags=["analyse"])
def ticker_news(ticker_code: str, refresh: bool = False):
    """Latest news for the stock via yfinance (Yahoo Finance)."""
    code = ticker_code.upper()
    cached = _news_cache.get(code)
    if cached and not refresh:
        return cached
    try:
        raw = yf.Ticker(code).news or []
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Actualités indisponibles : {e}")

    items = []
    for it in raw:
        try:
            n = _parse_news_item(it)
        except Exception:
            continue
        if n.get("title") and n.get("url"):
            items.append(n)

    result = {"ticker": code, "count": len(items), "items": items[:12]}
    _news_cache.set(code, result)
    return result


# ── Cache management ───────────────────────────────────────────────
@app.get("/cache", summary="Cache state", tags=["cache"])
def cache_info():
    """List cached entries with their age and remaining TTL."""
    return _cache.info()


@app.delete("/cache", summary="Clear the entire cache", tags=["cache"])
def cache_clear():
    n = _cache.clear()
    return {"cleared": n}


@app.delete("/cache/{ticker_code}", summary="Invalidate a ticker", tags=["cache"])
def cache_invalidate(ticker_code: str):
    found = _cache.invalidate(ticker_code.upper())
    if not found:
        raise HTTPException(status_code=404, detail=f"{ticker_code.upper()} not in cache")
    return {"invalidated": ticker_code.upper()}


# ── Favorites (watchlist persisted in SQLite) ────────────────────────
class FavoritesImport(BaseModel):
    tickers: list[str]

    @field_validator("tickers")
    @classmethod
    def _clean(cls, v):
        return [t.strip().upper() for t in v if t and t.strip()]


@app.get("/favorites", summary="List favorites", tags=["favorites"])
def favorites_list():
    """Return the watchlist persisted server-side."""
    return {"favorites": db.get_favorites()}


@app.put("/favorites", summary="Replace the entire favorites list", tags=["favorites"])
def favorites_set(body: FavoritesImport):
    """Fully replace the watchlist (used for import/migration)."""
    return {"favorites": db.set_favorites(body.tickers)}


@app.post("/favorites/{ticker_code}", summary="Add a favorite", tags=["favorites"])
def favorites_add(ticker_code: str):
    added = db.add_favorite(ticker_code)
    return {"favorites": db.get_favorites(), "added": added}


@app.delete("/favorites/{ticker_code}", summary="Remove a favorite", tags=["favorites"])
def favorites_remove(ticker_code: str):
    removed = db.remove_favorite(ticker_code)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{ticker_code.upper()} n'est pas un favori")
    return {"favorites": db.get_favorites(), "removed": True}


# ── Batch analysis ────────────────────────────────────────────────────────────
class TickerListRequest(BaseModel):
    tickers: list[str]
    refresh: bool = False
    lang: str = "en"

    @field_validator("tickers")
    @classmethod
    def _check(cls, v):
        if not v:
            raise ValueError("La liste de tickers est vide")
        if len(v) > 50:
            raise ValueError("Maximum 50 tickers par requête")
        return [t.strip().upper() for t in v]


@app.post("/tickers", summary="Analyze a list of tickers")
async def post_tickers(body: TickerListRequest):
    """
    Analyze several tickers in parallel.

    ```json
    { "tickers": ["MC.PA", "ASML.AS", "AIR.PA"], "refresh": false, "lang": "en" }
    ```

    Each entry in the result contains either the data or an `error` field.
    """
    lang = "fr" if body.lang == "fr" else "en"

    results_map: dict = {}
    to_compute: list[str] = []

    # 1. Serve already-cached analyses first
    for t in body.tickers:
        if not body.refresh:
            cached = _cache.get(f"{t}:{lang}")
            if cached is not None:
                results_map[t] = {**cached, "cached": True}
                continue
        to_compute.append(t)

    # 2. Single grouped network download for everything else
    if to_compute:
        raw = await asyncio.to_thread(_download_batch, to_compute, "500d", body.refresh)
        sem = asyncio.Semaphore(4)  # limit concurrent CPU computation

        async def _work(ticker: str) -> tuple[str, dict]:
            async with sem:
                try:
                    result = await asyncio.to_thread(
                        _analyse_ticker, ticker, lang, raw.get(ticker)
                    )
                    _cache.set(f"{ticker}:{lang}", result)
                    return ticker, {**result, "cached": False}
                except HTTPException as e:
                    return ticker, {"ticker": ticker, "error": e.detail}
                except Exception as e:
                    return ticker, {"ticker": ticker, "error": str(e)}

        for ticker, res in await asyncio.gather(*[_work(t) for t in to_compute]):
            results_map[ticker] = res

    results = [results_map[t] for t in body.tickers]
    return {"count": len(results), "results": results}


# ── Static frontend (SPA) ────────────────────────────────────────
# Mounted last so that API routes keep priority.
_STATIC = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC):
    app.mount("/", StaticFiles(directory=_STATIC, html=True), name="spa")
