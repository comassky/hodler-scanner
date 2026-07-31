"""Core Buy & Hold technical analysis for a single ticker."""
import re
import threading
import time
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import HTTPException

import db
from i18n import t as _t
from market_data import download_raw, flat_col
from script import (
    calculer_rsi_df,
    detecter_divergence_haussiere,
    generer_analyse_investisseur_lt,
    fetch_single_ticker_info,
)

_ANSI = re.compile(r"\033\[[^m]*m")


def strip_ansi(s: str) -> str:
    """Strip ANSI codes for clean JSON."""
    return _ANSI.sub("", str(s)).strip()


def last(series, default: float = 0.0) -> float:
    """Last non-NaN value of a series (or ``default`` if empty/all-NaN)."""
    s = series.dropna()
    return float(s.iloc[-1]) if not s.empty else default


# ── Memoized names cache (reloaded from SQLite via a TTL) ──────
_names_lock: threading.Lock = threading.Lock()
_names_state: tuple[float, dict] | None = None
_NAMES_TTL = 300.0  # seconds


def get_names_cache() -> dict:
    """Return the names cache, reloaded from SQLite at most every 5 min."""
    global _names_state
    now = time.monotonic()
    with _names_lock:
        if _names_state is None or now - _names_state[0] > _NAMES_TTL:
            _names_state = (now, db.get_names())
        return _names_state[1]


def invalidate_names_cache() -> None:
    """Force a reload of the names cache on next access."""
    global _names_state
    with _names_lock:
        _names_state = None


def analyse_ticker(ticker_code: str, lang: str = "en", data=None) -> dict:
    if data is None:
        data = download_raw(ticker_code, "500d")
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {ticker_code}")

    def _col(key):
        return flat_col(data, key)

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

    # ── ADX 14 (Wilder) — trend *strength* (not direction) ─────────
    _up_move   = high.diff()
    _down_move = -low.diff()
    _plus_dm   = pd.Series(np.where((_up_move > _down_move) & (_up_move > 0), _up_move, 0.0), index=high.index)
    _minus_dm  = pd.Series(np.where((_down_move > _up_move) & (_down_move > 0), _down_move, 0.0), index=low.index)
    _atr_wil   = _tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    _plus_di   = 100 * _plus_dm.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean() / _atr_wil
    _minus_di  = 100 * _minus_dm.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean() / _atr_wil
    _dx        = 100 * (_plus_di - _minus_di).abs() / (_plus_di + _minus_di).replace(0, np.nan)
    adx14_s    = _dx.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    # ── Choppiness Index 14 — range (high) vs trend (low), 0–100 ───
    _atr_sum   = _tr.rolling(14, min_periods=14).sum()
    _hh14      = high.rolling(14, min_periods=14).max()
    _ll14      = low.rolling(14, min_periods=14).min()
    _chop_rng  = (_hh14 - _ll14).replace(0, np.nan)
    chop14_s   = 100 * np.log10(_atr_sum / _chop_rng) / np.log10(14)

    # ── Last values ──────────────────────────────────────────
    sma200_ff   = sma200_s.ffill()
    slope_off   = min(20, len(sma200_ff) - 1)
    sma200_curr = float(sma200_ff.iloc[-1])
    sma200_prev = float(sma200_ff.iloc[-1 - slope_off])
    sma200_slop = (sma200_curr - sma200_prev) / sma200_prev * 100 if sma200_prev else 0.0

    hist_ff    = hist_w_s.ffill()
    hist_curr  = float(hist_ff.iloc[-1])
    hist_prev  = float(hist_ff.iloc[-2]) if len(hist_ff.dropna()) >= 2 else hist_curr

    c_curr    = last(close)
    sma50_v   = last(sma50_s)
    has_w50   = not sma50w_s.dropna().empty
    sma50w_v  = last(sma50w_s, sma200_curr)
    rsi_d     = last(rsi_d_s)
    rsi_w     = last(rsi_w_s)
    h52w_v    = last(h52w_s)
    l52w_v    = last(l52w_s)
    bb_pct_v  = last(bb_pct_s)
    v_curr    = last(volume)
    v_mean    = last(vol20_s)
    rvol      = round(v_curr / v_mean, 2) if v_mean > 0 else 1.0
    var_j     = last(close.pct_change() * 100)
    atr14_v   = last(atr14_s)

    adx14_v    = last(adx14_s)
    chop14_v   = last(chop14_s, 50.0)
    plus_di_v  = last(_plus_di)
    minus_di_v = last(_minus_di)

    # Market regime from ADX (strength) + Choppiness (range vs trend) confluence.
    if adx14_v >= 25 and chop14_v < 61.8:
        regime = "trend_up" if plus_di_v >= minus_di_v else "trend_down"
    elif adx14_v < 20 or chop14_v >= 61.8:
        regime = "range"
    else:
        regime = "transition"

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
    cache = get_names_cache()
    nom   = cache.get(ticker_code)
    if not nom:
        nom = fetch_single_ticker_info(ticker_code)[1]
        db.upsert_name(ticker_code, nom)
        invalidate_names_cache()

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
            "adx14":               round(adx14_v, 1),
            "chop14":              round(chop14_v, 1),
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
            "regime":         regime,
            "alerte_sma200":  bool(-5.0 <= dist_sma200 <= 3.0),
            "alerte_w50":     bool(has_w50 and -5.0 <= dist_w50 <= 3.0),
            "divergence_rsi": div_hauss,
            "rsi_creux":      [round(rsi_c1, 1), round(rsi_c2, 1)] if div_hauss else None,
        },
        "analysis": {
            "score":         score,
            "score_details": sc_det,
            "statut":        strip_ansi(statut_lt),
            "synthese": {
                "verdict": strip_ansi(synthese["verdict"]),
                "atout":   strip_ansi(synthese["atout"])  if synthese["atout"]  else None,
                "risque":  strip_ansi(synthese["risque"]) if synthese["risque"] else None,
            },
            "explication":   strip_ansi(expl),
            "strategie":     strat,
            "objectifs":     strip_ansi(gain_est),
            "diagnostics":   [{"text": strip_ansi(x["text"]), "impact": x["impact"]} for x in diag],
        },
    }
