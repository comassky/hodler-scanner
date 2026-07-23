"""
Hodler Scanner — REST API (FastAPI)
GET /ticker/{ticker_code}  →  full technical analysis as JSON
GET /docs                  →  interactive Swagger UI

This module only wires HTTP routes to the business logic, which lives in
dedicated modules: analysis, charts, fundamentals, news, search, market_data,
cache and serialization.
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

import db
from analysis import analyse_ticker
from backtest import run_backtest
from cache import analysis_cache
from charts import chart_data
from fundamentals import fetch_fundamentals
from market_data import download_batch
from news import fetch_news
from search import search_tickers
from serialization import SafeJSONResponse


def _app_version() -> str:
    """Resolve the app version (single source of truth: frontend/package.json).

    Order: APP_VERSION env → sibling VERSION file (baked in the image) →
    frontend/package.json (local dev) → fallback.
    """
    env = os.getenv("APP_VERSION")
    if env:
        return env
    here = os.path.dirname(__file__)
    try:
        with open(os.path.join(here, "VERSION"), encoding="utf-8") as f:
            if (v := f.read().strip()):
                return v
    except OSError:
        pass
    try:
        with open(os.path.join(here, "..", "frontend", "package.json"), encoding="utf-8") as f:
            return json.load(f).get("version") or "0.0.0-dev"
    except (OSError, ValueError):
        return "0.0.0-dev"


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
    todo = [t for t in tickers if analysis_cache.get(f"{t}:en") is None]
    if not todo:
        return

    # Single grouped network download, then computation capped at 4 threads
    raw = await asyncio.to_thread(download_batch, todo, "500d", False)
    sem = asyncio.Semaphore(4)

    async def _load(ticker: str) -> None:
        async with sem:
            try:
                result = await asyncio.to_thread(analyse_ticker, ticker, "en", raw.get(ticker))
                analysis_cache.set(f"{ticker}:en", result)
            except Exception:
                pass

    await asyncio.gather(*[_load(t) for t in todo])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    asyncio.create_task(_prewarm())
    yield


app = FastAPI(
    title="Hodler Scanner API",
    description="Buy & Hold technical analysis — SMA, RSI, MACD, Bollinger Bands, scoring",
    version=_app_version(),
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:80"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/search", summary="Search tickers by name or symbol", tags=["utils"])
def search(q: str):
    """
    Search Yahoo Finance by company name, ticker symbol or **ISIN**
    (e.g. `Apple`, `MC.PA`, `FR0000121014`). Fuzzy matching tolerates typos.
    """
    return search_tickers(q)


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
        cached = analysis_cache.get(ckey)
        if cached is not None:
            return {**cached, "cached": True}

    try:
        result = await asyncio.to_thread(analyse_ticker, code, lang)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    analysis_cache.set(ckey, result)
    return {**result, "cached": False}


@app.get("/ticker/{ticker_code}/chart", summary="Historical data for charts", tags=["analyse"])
def ticker_chart(ticker_code: str, period: str = "1y", refresh: bool = False):
    """Return price, SMA 200/50, RSI 14 and MACD histogram for the charts."""
    return chart_data(ticker_code, period, refresh)


@app.get("/ticker/{ticker_code}/fundamentals", summary="Fundamental data", tags=["analyse"])
def ticker_fundamentals(ticker_code: str, refresh: bool = False):
    """P/E, market cap, sector, country via yfinance.info."""
    return fetch_fundamentals(ticker_code, refresh)


@app.get("/ticker/{ticker_code}/news", summary="Recent news", tags=["analyse"])
def ticker_news(ticker_code: str, refresh: bool = False):
    """Latest news for the stock via yfinance (Yahoo Finance)."""
    return fetch_news(ticker_code, refresh)


@app.get("/ticker/{ticker_code}/backtest", summary="Light score backtest", tags=["analyse"])
async def ticker_backtest(ticker_code: str, refresh: bool = False):
    """
    Replay the Buy & Hold score over ~5 years of history and report the realized
    forward returns (≈3M / 6M / 12M) grouped by score band — a credibility check
    on the scoring engine.
    """
    try:
        return await asyncio.to_thread(run_backtest, ticker_code, refresh)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cache management ───────────────────────────────────────────────
@app.get("/cache", summary="Cache state", tags=["cache"])
def cache_info():
    """List cached entries with their age and remaining TTL."""
    return analysis_cache.info()


@app.delete("/cache", summary="Clear the entire cache", tags=["cache"])
def cache_clear():
    n = analysis_cache.clear()
    return {"cleared": n}


@app.delete("/cache/{ticker_code}", summary="Invalidate a ticker", tags=["cache"])
def cache_invalidate(ticker_code: str):
    found = analysis_cache.invalidate(ticker_code.upper())
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
            cached = analysis_cache.get(f"{t}:{lang}")
            if cached is not None:
                results_map[t] = {**cached, "cached": True}
                continue
        to_compute.append(t)

    # 2. Single grouped network download for everything else
    if to_compute:
        raw = await asyncio.to_thread(download_batch, to_compute, "500d", body.refresh)
        sem = asyncio.Semaphore(4)  # limit concurrent CPU computation

        async def _work(ticker: str) -> tuple[str, dict]:
            async with sem:
                try:
                    result = await asyncio.to_thread(
                        analyse_ticker, ticker, lang, raw.get(ticker)
                    )
                    analysis_cache.set(f"{ticker}:{lang}", result)
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
