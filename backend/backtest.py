"""
Light historical backtest of the Buy & Hold opportunity score.

Goal: measure whether a **high score in the past** was actually followed by
**higher forward returns** — a transparency/credibility check on the scoring
engine, not a trading system.

Method
------
Every technical indicator used by the engine (SMA, Wilder RSI, Bollinger,
weekly MACD, rolling 52w high/low, RVOL…) is **causal**: its value at bar ``i``
depends only on bars ``≤ i``. So the full indicator series can be computed once,
then the *exact same* scoring function (``generer_analyse_investisseur_lt``) is
replayed at many historical dates. For each sampled date we look at the realized
forward return over several horizons (≈3M / 6M / 12M) and aggregate the results
by score band.

Sampling is done on **Fridays only** so that the weekly-resampled indicators
(``resample('W-FRI')``) never peek into the future of the current week.

The indicator formulas below mirror those in ``analysis.analyse_ticker`` — keep
them in sync if the engine changes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import HTTPException

import db
from cache import backtest_cache
from market_data import download_raw, flat_col
from script import (
    calculer_rsi_df,
    detecter_divergence_haussiere,
    fetch_single_ticker_info,
    generer_analyse_investisseur_lt,
)

# Forward-return horizons in trading days (≈ 3M, 6M, 12M, 3Y and 5Y).
HORIZONS = (63, 126, 252, 756, 1260)
PRIMARY_HORIZON = 126
_WARMUP = 252            # sessions of history required before the first sample
_HISTORY_PERIOD = "10y"  # downloaded window (long enough for multi-year horizons)

# Score bands (aligned with the status thresholds of the analysis engine).
_BANDS = (
    ("strong", 80, 101),
    ("accumulate", 60, 80),
    ("watch", 40, 60),
    ("avoid", 0, 40),
)


def _last_valid(series: pd.Series, default: float = 0.0) -> float:
    s = series.dropna()
    return float(s.iloc[-1]) if not s.empty else default


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _build_item(
    i: int,
    date: pd.Timestamp,
    name: str,
    close: pd.Series,
    volume: pd.Series,
    divs: pd.Series,
    series: dict,
) -> dict:
    """Reconstruct the scoring ``item`` dict as it would have looked at bar ``i``."""
    c = float(close.iloc[i])

    sma200_ff = series["sma200"].ffill()
    sma200_v = float(sma200_ff.iloc[i])
    off = min(20, i)
    sma200_prev = float(sma200_ff.iloc[i - off])
    slope = (sma200_v - sma200_prev) / sma200_prev * 100 if sma200_prev else 0.0

    sma50_v = _last_valid(series["sma50"].iloc[: i + 1], sma200_v)
    h52w_v = _last_valid(series["h52w"].iloc[: i + 1], c)
    l52w_v = _last_valid(series["l52w"].iloc[: i + 1], c)
    bb_pct_v = _last_valid(series["bb_pct"].iloc[: i + 1], 0.5)
    v_curr = float(volume.iloc[i]) if not pd.isna(volume.iloc[i]) else 0.0
    v_mean = _last_valid(series["vol20"].iloc[: i + 1], 0.0)
    rvol = round(v_curr / v_mean, 2) if v_mean > 0 else 1.0
    rsi_d = _last_valid(series["rsi_d"].iloc[: i + 1], 50.0)

    # ── Weekly indicators (sliced up to the sample date → no look-ahead) ──
    w50_hist = series["sma50w"].loc[:date]
    has_w50 = not w50_hist.dropna().empty
    sma50w_v = _last_valid(w50_hist, sma200_v)
    rsi_w = _last_valid(series["rsi_w"].loc[:date], 50.0)

    hist_ff = series["macd_w_hist"].loc[:date].ffill()
    hist_curr = float(hist_ff.iloc[-1]) if not hist_ff.empty else 0.0
    hist_prev = float(hist_ff.iloc[-2]) if len(hist_ff.dropna()) >= 2 else hist_curr

    # ── Distances ────────────────────────────────────────────────────
    dist_sma200 = (c - sma200_v) / sma200_v * 100 if sma200_v else 0.0
    dist_w50 = (c - sma50w_v) / sma50w_v * 100 if sma50w_v else 0.0
    dist_52h = (c - h52w_v) / h52w_v * 100 if h52w_v else 0.0
    dist_52l = (c - l52w_v) / l52w_v * 100 if l52w_v else 0.0

    # ── Trailing 12-month dividend as of the sample date ──────────────
    annual_div = 0.0
    if not divs.empty:
        cutoff = date - pd.DateOffset(years=1)
        window = divs[(divs.index >= cutoff) & (divs.index <= date) & (divs > 0)]
        annual_div = float(window.sum())

    # ── Bullish RSI divergence over the window ending at the sample ───
    div_hauss, rsi_c1, rsi_c2 = detecter_divergence_haussiere(
        close.iloc[: i + 1], series["rsi_d"].iloc[: i + 1]
    )

    return {
        "Code": name, "Nom": name, "Cours": round(c, 2),
        "RSI_val": rsi_d, "RSI_W_val": rsi_w, "RVOL_val": rvol,
        "52w_val": dist_52h, "Ecart_sma200_val": dist_sma200,
        "Ecart_w50_val": dist_w50, "H52W_price": h52w_v,
        "SMA200_val": sma200_v, "Div_Montant": annual_div,
        "Div_Date": "N/A", "W50_valide": has_w50,
        "SMA50_val": sma50_v, "SMA200_slope": slope,
        "L52W_price": l52w_v, "Dist_52wLow_val": dist_52l,
        "Divergence_RSI": div_hauss,
        "Div_RSI_creux1": rsi_c1,
        "Div_RSI_creux2": rsi_c2,
        "BB_pct_val": bb_pct_v,
        "MACD_W_hist": hist_curr,
        "MACD_W_hist_prev": hist_prev,
    }


def _compute_series(close, volume) -> dict:
    """Compute every indicator series once, over the full history (mirror of analysis.py)."""
    close_w = close.resample("W-FRI").last()
    bb_mid = close.rolling(20, min_periods=10).mean()
    bb_std = close.rolling(20, min_periods=10).std()
    ema12w = close_w.ewm(span=12, min_periods=1, adjust=False).mean()
    ema26w = close_w.ewm(span=26, min_periods=1, adjust=False).mean()
    macd_w = ema12w - ema26w
    return {
        "sma200": close.rolling(200, min_periods=1).mean(),
        "sma50": close.rolling(50, min_periods=1).mean(),
        "sma50w": close_w.rolling(50, min_periods=5).mean(),
        "h52w": close.rolling(252, min_periods=1).max(),
        "l52w": close.rolling(252, min_periods=1).min(),
        "rsi_d": calculer_rsi_df(close.to_frame()).iloc[:, 0],
        "rsi_w": calculer_rsi_df(close_w.to_frame()).iloc[:, 0],
        "bb_pct": (close - (bb_mid - 2 * bb_std)) / (4 * bb_std),
        "vol20": volume.rolling(20).mean(),
        "macd_w_hist": macd_w - macd_w.ewm(span=9, min_periods=1, adjust=False).mean(),
    }


def _aggregate(rows: list[dict]) -> dict:
    """Bucket the sampled points by score band and compute return statistics."""
    def _stats(subset: list[dict], horizon: int) -> dict:
        vals = [r["returns"][horizon] for r in subset if horizon in r["returns"]]
        if not vals:
            return {"count": 0, "avg_return": None, "median_return": None, "win_rate": None}
        arr = np.asarray(vals, dtype=float)
        return {
            "count": len(vals),
            "avg_return": round(float(arr.mean()) * 100, 2),
            "median_return": round(float(np.median(arr)) * 100, 2),
            "win_rate": round(float((arr > 0).mean()) * 100, 1),
        }

    bands = []
    for key, lo, hi in _BANDS:
        subset = [r for r in rows if lo <= r["score"] < hi]
        primary = _stats(subset, PRIMARY_HORIZON)
        bands.append({
            "key": key, "min": lo,
            "count": len(subset),
            "avg_return": primary["avg_return"],
            "median_return": primary["median_return"],
            "win_rate": primary["win_rate"],
            "by_horizon": {str(h): _stats(subset, h) for h in HORIZONS},
        })

    baseline = {
        "avg_return": _stats(rows, PRIMARY_HORIZON)["avg_return"],
        "win_rate": _stats(rows, PRIMARY_HORIZON)["win_rate"],
        "by_horizon": {str(h): _stats(rows, h) for h in HORIZONS},
    }

    corr = {}
    for h in HORIZONS:
        pts = [(r["score"], r["returns"][h]) for r in rows if h in r["returns"]]
        corr[str(h)] = (
            round(c, 3) if (c := _pearson([p[0] for p in pts], [p[1] for p in pts])) is not None
            else None
        )
    return {"bands": bands, "baseline": baseline, "correlation": corr}


def run_backtest(ticker_code: str, refresh: bool = False) -> dict:
    """Run the light backtest for a ticker and return a JSON-serializable report."""
    code = ticker_code.upper()
    ckey = f"{code}:bt"
    if not refresh:
        cached = backtest_cache.get(ckey)
        if cached is not None:
            return {**cached, "cached": True}

    data = download_raw(code, _HISTORY_PERIOD, refresh=refresh)
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {code}")

    close = flat_col(data, "Close")
    volume = flat_col(data, "Volume")
    divs = flat_col(data, "Dividends").fillna(0.0) if "Dividends" in data else pd.Series(dtype=float)
    n = int(close.count())
    min_h = min(HORIZONS)
    if n < _WARMUP + min_h + 20:
        raise HTTPException(
            status_code=422,
            detail=f"Historique insuffisant pour un backtest ({n} sessions)",
        )

    series = _compute_series(close, volume)
    idx = close.index

    name = db.get_names().get(code) or fetch_single_ticker_info(code)[1]

    # Per-date scores are causal (depend only on data ≤ that date) → deterministic
    # and safe to persist. Reuse stored scores and only replay the new dates.
    stored = {} if refresh else db.get_backtest_scores(code)
    fresh_rows: list[tuple] = []

    rows: list[dict] = []
    price_arr = close.to_numpy(dtype=float)
    sma200_arr = series["sma200"].ffill().to_numpy(dtype=float)
    last_scorable = len(idx) - 1
    for i in range(_WARMUP, len(idx)):
        date = idx[i]
        if date.weekday() != 4:            # Fridays only → clean weekly buckets
            continue
        if pd.isna(price_arr[i]):
            continue

        returns = {}
        for h in HORIZONS:
            j = i + h
            if j <= last_scorable and not pd.isna(price_arr[j]) and price_arr[i] > 0:
                returns[h] = price_arr[j] / price_arr[i] - 1.0
        if not returns:
            continue

        date_str = date.strftime("%Y-%m-%d")
        price = round(float(price_arr[i]), 2)
        sma200 = round(float(sma200_arr[i]), 2) if not pd.isna(sma200_arr[i]) else None
        hit = stored.get(date_str)
        if hit is not None:
            score = hit[1]
            if hit[2] is None:             # backfill sma200 on legacy rows
                fresh_rows.append((date_str, price, score, sma200))
        else:
            item = _build_item(i, date, name, close, volume, divs, series)
            _, _, score, *_ = generer_analyse_investisseur_lt(item, "en")
            score = int(score)
            fresh_rows.append((date_str, price, score, sma200))

        rows.append({
            "date": date_str,
            "price": price,
            "score": score,
            "sma200": sma200,
            "returns": returns,
        })

    if len(rows) < 12:
        raise HTTPException(status_code=422, detail="Trop peu de points pour un backtest fiable")

    if fresh_rows:
        db.save_backtest_scores(code, fresh_rows)

    # Keep only horizons with enough realized samples (long horizons need more history).
    avail = [h for h in HORIZONS if sum(1 for r in rows if h in r["returns"]) >= 12]
    if not avail:
        avail = [min(HORIZONS)]
    primary = PRIMARY_HORIZON if PRIMARY_HORIZON in avail else avail[-1]

    agg = _aggregate(rows)
    report = {
        "ticker": code,
        "name": name,
        "period_start": rows[0]["date"],
        "period_end": rows[-1]["date"],
        "samples": len(rows),
        "horizons_days": avail,
        "primary_horizon": primary,
        "series": [{"date": r["date"], "price": r["price"], "score": r["score"], "sma200": r["sma200"]} for r in rows],
        "bands": agg["bands"],
        "baseline": agg["baseline"],
        "correlation": agg["correlation"],
        "cached": False,
    }
    backtest_cache.set(ckey, report)
    return report
