import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

import db
from i18n import t as _translate

# --- ANSI COLORS (CONSOLE DISPLAY) ---
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_RED = "\033[91m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_CYAN = "\033[96m"
CLR_MAGENTA = "\033[95m"
CLR_ALERT = "\033[1;33;41m"

# --- LIST OF GIANTS, ETFs & FLAGSHIP STOCKS (TICKERS) ---
TICKERS_DEFAUT = (
    "WPEA.PA,ESE.PA,CW8.PA,PAEEM.PA,ETZ.PA,"
    "MC.PA,OR.PA,AIR.PA,TTE.PA,SAN.PA,SU.PA,BN.PA,EL.PA,CS.PA,GLE.PA,ACA.PA,ML.PA,DG.PA,VIE.PA,RI.PA,EN.PA,SGO.PA,KER.PA,STLAP.PA,"
    "ASML.AS,SAP.DE,SIE.DE,ALV.DE,DTE.DE,MBG.DE,BMW.DE,VOW3.DE,"
    "AZN.L,SHEL.L,HSBA.L,BP.L,ULVR.L,"
    "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,NFLX,WDC,MU,INTC,AMD,QCOM,AVGO,TSM,ORCL,CRM,ADBE,"
    "JPM,V,MA,BAC,WFC,GS,MS,C,AXP,BRK-B,"
    "DIS,NKE,PEP,KO,JNJ,PG,WMT,HD,COST,MCD,SBUX,"
    "UNH,LLY,ABBV,MRK,AMGN,"
    "RTX,HON,CAT,BA,GE,LMT,"
    "T,VZ,"
    "XOM,CVX,COP,"
    "PYPL,UBER,SHOP"
)


# ==============================================================================
# 1. CACHING & MULTI-THREADED I/O
# ==============================================================================
def charger_cache_noms():
    """Load the ticker names cache from SQLite."""
    db.init_db()
    return db.get_names()


def sauvegarder_cache_noms(cache):
    """Persist the ticker names cache to SQLite."""
    db.init_db()
    db.save_names(cache)


def fetch_single_ticker_info(ticker_code, cached_name=None):
    """Fetch only the name (dividends via batch download)."""
    if cached_name:
        return ticker_code, cached_name  # no network call
    try:
        info = yf.Ticker(ticker_code).info
        nom  = info.get("longName") or info.get("shortName") or ticker_code
        return ticker_code, nom
    except Exception:
        return ticker_code, ticker_code


def obtenir_infos_entreprises_parallele(tickers):
    noms_cache    = charger_cache_noms()
    a_recuperer   = [t for t in tickers if t not in noms_cache]
    nb_cached     = len(tickers) - len(a_recuperer)

    if a_recuperer:
        print(f"🌐 Noms : {len(a_recuperer)} à récupérer ({nb_cached} en cache)...")
        with ThreadPoolExecutor(max_workers=min(32, len(a_recuperer))) as executor:
            futures = [executor.submit(fetch_single_ticker_info, t) for t in a_recuperer]
            for future in as_completed(futures):
                ticker_code, nom = future.result()
                noms_cache[ticker_code] = nom
        sauvegarder_cache_noms(noms_cache)
    else:
        print(f"✅ Noms : {nb_cached} tickers en cache")

    return noms_cache


# ==============================================================================
# 2. SAFETY FUNCTIONS AND VECTORIZED INDICATORS (HARDENED)
# ==============================================================================
def _get_last(val_or_series, default=0.0):
    """Extract the last valid value from a series/scalar with NaN handling."""
    try:
        if isinstance(val_or_series, np.ndarray):
            valid = val_or_series[np.isfinite(val_or_series)]
            return float(valid[-1]) if len(valid) > 0 else default
        if isinstance(val_or_series, pd.Series):
            clean = val_or_series.dropna()
            return float(clean.iloc[-1]) if not clean.empty else default
        if pd.isna(val_or_series):
            return default
        return float(val_or_series)
    except (IndexError, KeyError, ValueError, TypeError):
        return default


def calculer_rsi_df(df, period=14):
    """RSI (Wilder smoothing) for all columns of a DataFrame — TradingView-compliant."""
    delta     = df.diff()
    gain      = delta.clip(lower=0)
    loss      = (-delta).clip(lower=0)
    avg_gain  = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss  = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    rs   = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi  = 100.0 - (100.0 / (1.0 + rs))
    rsi  = rsi.where(avg_loss  != 0, other=100.0)
    rsi  = rsi.where(avg_gain  != 0, other=0.0)
    rsi  = rsi.where(~both_zero,     other=50.0)
    return rsi.fillna(50.0)


def detecter_divergence_haussiere(prix_series, rsi_series, lookback=80, min_separation=10, rsi_delta=5.0):
    """
    Classic bullish divergence over the last `lookback` sessions:
    Price at a lower low + RSI at a higher low → potential reversal signal.
    Returns (detected: bool, rsi_low1: float, rsi_low2: float).
    """
    try:
        # Align both series on the common index
        common_idx = prix_series.dropna().index.intersection(rsi_series.dropna().index)
        if len(common_idx) < lookback:
            return False, None, None
        px  = prix_series[common_idx].iloc[-lookback:].values
        rsi = rsi_series[common_idx].iloc[-lookback:].values
        n, half = len(px), 5
        # Local minima: px[i] is the minimum of its ±3-bar window
        lows = []
        for i in range(half, n - half):
            if px[i] == min(px[i - half: i + half + 1]):
                if not lows or (i - lows[-1][0]) >= min_separation:
                    lows.append((i, float(px[i]), float(rsi[i])))
        if len(lows) < 2:
            return False, None, None
        _, p1_px, p1_rsi = lows[-2]
        _, p2_px, p2_rsi = lows[-1]
        # Condition: price lower low (>0.1% gap) + RSI higher low (>rsi_delta points)
        if p2_px < p1_px * 0.999 and p2_rsi > p1_rsi + rsi_delta:
            return True, round(p1_rsi, 1), round(p2_rsi, 1)
        return False, None, None
    except Exception:
        return False, None, None


# ==============================================================================
# 3. EXPORT AND COLORING
# ==============================================================================
_ANSI_RE = re.compile(r'\033\[[^m]*m')

def _vlen(s):
    """Visual length without ANSI codes."""
    return len(_ANSI_RE.sub('', str(s)))

def _pad(s, w, align='l'):
    """Correct padding regardless of ANSI codes."""
    s = str(s); p = max(0, w - _vlen(s))
    return (' ' * p + s) if align == 'r' else (s + ' ' * p)

def _c_pct(v):
    s = str(v)
    if s.startswith('+') and s != '+0.00%': return f"{CLR_GREEN}{s}{CLR_RESET}"
    if s.startswith('-'):                   return f"{CLR_RED}{s}{CLR_RESET}"
    return s

def _c_rsi(v):
    try:
        f = float(v); s = f"{f:.1f}"
        if f <= 35:  return f"{CLR_RED}{CLR_BOLD}{s}{CLR_RESET}"
        if f <= 45:  return f"{CLR_RED}{s}{CLR_RESET}"
        if f >= 70:  return f"{CLR_YELLOW}{CLR_BOLD}{s}{CLR_RESET}"
        if f >= 60:  return f"{CLR_YELLOW}{s}{CLR_RESET}"
        return s
    except Exception: return str(v)

_TEND_LABEL = {
    "↑ Haussier": "Haussier", "↑ Neutre": "Ntr Bull",
    "↓ Neutre":   "Ntr Bear",  "↓ Baissier": "Baissier",
}

def _c_tend(v):
    label = _TEND_LABEL.get(str(v), str(v))
    if 'Haussier' in label or 'Bull' in label: return f"{CLR_GREEN}{label}{CLR_RESET}"
    if 'Baissier' in label or 'Bear' in label: return f"{CLR_RED}{label}{CLR_RESET}"
    return label

def _c_bb(v):
    try:
        f = float(v); s = f"{f:.2f}"
        if f < 0.0:  return f"{CLR_RED}{CLR_BOLD}{s}{CLR_RESET}"
        if f < 0.2:  return f"{CLR_RED}{s}{CLR_RESET}"
        if f > 1.0:  return f"{CLR_YELLOW}{CLR_BOLD}{s}{CLR_RESET}"
        if f > 0.8:  return f"{CLR_YELLOW}{s}{CLR_RESET}"
        return s
    except Exception: return str(v)

def _c_signal(v):
    s = (str(v).replace("🚨 ", "")
                .replace(" 📐DIV↑", "+DIV").replace("📐DIV↑", "DIV")
                .replace(" MACD↑", "+MACD"))
    if 'ALERTE' in s: return f"{CLR_ALERT}{s}{CLR_RESET}"
    if 'DIV' in s or 'MACD' in s: return f"{CLR_CYAN}{s}{CLR_RESET}"
    return s

def _print_legende():
    """Compact legend of the table colors."""
    _B  = CLR_BOLD;  _D = "\033[2m";  _X = CLR_RESET
    G   = f"{CLR_GREEN}■{_X}";  GB = f"{CLR_GREEN}{_B}■{_X}"
    R   = f"{CLR_RED}■{_X}";    RB = f"{CLR_RED}{_B}■{_X}"
    Y   = f"{CLR_YELLOW}■{_X}"; YB = f"{CLR_YELLOW}{_B}■{_X}"
    C   = f"{CLR_CYAN}■{_X}";   AL = f"{CLR_ALERT} ALERTE {_X}"

    print(f"\n  {_D}{'─'*82}{_X}")
    print(f"  {_B}LÉGENDE{_X}")
    print(f"  {_D}Pct / SMA / 52w{_X}   {G} positif   {R} négatif")
    print(f"  {_D}RSI            {_X}   {RB} ≤35 {_D}survente extrême{_X}   {R} 36‑45   {Y} 60‑69   {YB} ≥70 {_D}surachat extrême{_X}")
    print(f"  {_D}BB%            {_X}   {RB} <0  {_D}hors bande basse{_X}   {R} 0‑0.2   {Y} 0.8‑1   {YB} >1  {_D}hors bande haute{_X}")
    print(f"  {_D}Tendance       {_X}   {GB} Haussier   {R} Baissier")
    print(f"  {_D}Signal         {_X}   {AL}  cours en zone support ±5%  {_X}   {C} DIV↑ {_D}divergence RSI haussière (creux prix↓ / RSI↑){_X}   {C} MACD↑ {_D}croisement haussier MACD hebdo{_X}")
    print(f"  {_D}{'─'*82}{_X}")


# Table columns: (row_key, header, width, align, color_fn)
_TABLE_COLS = [
    ("Code",             "TICKER",  9,  'l', None),
    ("Nom",              "NOM",     18, 'l', None),
    ("Cours",            "COURS",   9,  'r', None),
    ("Var. Jour",        "VAR.J",   7,  'r', _c_pct),
    ("Ecart_sma200_val", "SMA200%", 8,  'r', lambda v: _c_pct(f"{float(v):+.2f}%")),
    ("RSI_val",          "RSI",     5,  'r', _c_rsi),
    ("BB_pct_val",       "BB%",     6,  'r', _c_bb),
    ("52w_val",          "52wH%",   7,  'r', lambda v: _c_pct(f"{float(v):+.1f}%")),
    ("Div_Montant",      "DIV/AN",  8,  'r', lambda v: f"{float(v):.2f}" if float(v) > 0 else "—"),
    ("Tendance",         "TEND.",   9,  'l', _c_tend),
    ("Statut",           "SIGNAL",  14, 'l', _c_signal),
]

def afficher_tableau(resultats_rows):
    """Main table with per-cell coloring."""
    _print_legende()
    SEP   = "  "
    total = sum(c[2] for c in _TABLE_COLS) + len(SEP) * (len(_TABLE_COLS) - 1)
    bar   = "─" * total
    print(f"\n{CLR_BOLD}" + SEP.join(_pad(c[1], c[2], c[3]) for c in _TABLE_COLS) + CLR_RESET)
    print(bar)
    for row in resultats_rows:
        parts = []
        for key, _, w, align, cfn in _TABLE_COLS:
            raw = row.get(key, "")
            try:    cell = cfn(raw) if cfn is not None else str(raw)
            except: cell = str(raw)
            parts.append(_pad(cell, w, align))
        print(SEP.join(parts))
    print(bar)
    nb_alt = sum(1 for r in resultats_rows if "ALERTE" in str(r.get("Statut", "")))
    nb_div = sum(1 for r in resultats_rows if r.get("Divergence_RSI", False))
    print(f"  {CLR_BOLD}{nb_alt}{CLR_RESET} alerte(s)  ·  "
          f"{CLR_CYAN}{nb_div}{CLR_RESET} divergence(s) RSI  ·  "
          f"{len(resultats_rows)} tickers analysés")


def afficher_fiche(item, diag_list, statut_lt, score, explication, strat, gain_est, score_details=None):
    """Structured analysis sheet per signal."""
    W   = 82
    SEP = "─" * W
    _DIM = "\033[2m"
    code, nom, cours = item['Code'], item['Nom'], item['Cours']
    sma  = item.get('SMA200_val', 0)
    sc   = CLR_GREEN if score >= 80 else (CLR_CYAN if score >= 60 else CLR_YELLOW)
    print(f"\n{SEP}")
    print(f"  {CLR_BOLD}{code}{CLR_RESET}  {nom}"
          f"  ·  {sc}[{score}/100]{CLR_RESET}"
          f"  ·  cours {cours}  sma200 {sma:.2f}")
    if score_details:
        def _fmtd(v):
            if v > 0: return f"{CLR_GREEN}+{v}{CLR_RESET}"
            if v < 0: return f"{CLR_RED}{v}{CLR_RESET}"
            return ""
        parts = [f"{_DIM}{k}{CLR_RESET}{_fmtd(v)}" for k, v in score_details.items() if v != 0]
        print(f"  {_DIM}score  base+40  " + "  ".join(parts) + f"  = {score}/100{CLR_RESET}")
    print(f"  {statut_lt}")
    print(f"  {explication}")
    print(f"\n  {CLR_BOLD}Analyse{CLR_RESET}")
    for i, d in enumerate(diag_list):
        _txt = d["text"] if isinstance(d, dict) else d
        conn = "  └─" if i == len(diag_list) - 1 else "  ├─"
        print(f"{conn} {_txt}")
    print(f"\n  {CLR_BOLD}Objectifs{CLR_RESET}")
    for g in gain_est.split("\n"):
        print(f"  {g.strip()}")
    print(f"\n  {CLR_MAGENTA}Action : {strat}{CLR_RESET}")


# ==============================================================================
# 4. SCORING ENGINE AND AUDITED FINANCIAL CALCULATIONS
# ==============================================================================
def generer_analyse_investisseur_lt(item, lang="en"):
    def _t(key, **params):
        return _translate(lang, key, **params)

    c_curr = item["Cours"]
    rsi_daily = item["RSI_val"]
    rsi_weekly = item["RSI_W_val"]
    rvol = item["RVOL_val"]
    dist_52w = item["52w_val"]
    ecart_sma200 = item["Ecart_sma200_val"]
    ecart_w50 = item["Ecart_w50_val"]
    h52w_price = item["H52W_price"]
    sma200_price = item["SMA200_val"]
    div_montant = item["Div_Montant"]
    div_date = item["Div_Date"]

    has_w50      = item.get("W50_valide", True)
    sma50_price  = item.get("SMA50_val",      sma200_price)
    sma200_slope = item.get("SMA200_slope",    0.0)
    l52w_price   = item.get("L52W_price",      c_curr)
    dist_52w_low = item.get("Dist_52wLow_val", 0.0)
    div_haussiere = item.get("Divergence_RSI",  False)
    rsi_creux1    = item.get("Div_RSI_creux1")
    rsi_creux2    = item.get("Div_RSI_creux2")
    bb_pct_val    = item.get("BB_pct_val",       0.5)
    macd_w_hist   = item.get("MACD_W_hist",      0.0)
    macd_w_prev   = item.get("MACD_W_hist_prev", 0.0)

    diagnostics = []          # structured list: {text, impact}
    _sc = {"SMA": 0, "Tend": 0, "52H": 0, "52L": 0, "Div": 0,
           "RSI-W": 0, "RSI-D": 0, "Vol": 0, "DIV\u2191": 0, "BB": 0, "MACD-W": 0}
    score_opportunite = 40

    def _add(cat, text, delta=0):
        """Add a diagnostic (with its signed impact) and update the score."""
        nonlocal score_opportunite
        if text:
            diagnostics.append({"text": text, "impact": delta})
        _sc[cat] += delta
        score_opportunite += delta

    confluence_sma200 = -3.0 <= ecart_sma200 <= 3.0
    confluence_w50 = has_w50 and (-3.5 <= ecart_w50 <= 3.5)

    # 1. Support analysis (distinction above / below)
    if confluence_sma200 and confluence_w50:
        if ecart_sma200 <= 0 and ecart_w50 <= 0:
            _add("SMA", _t("sma.confluence_major_below", ecart_sma200=ecart_sma200, ecart_w50=ecart_w50), 35)
        else:
            _add("SMA", _t("sma.confluence_major_touch", ecart_sma200=ecart_sma200, ecart_w50=ecart_w50), 22)
    elif confluence_sma200:
        if ecart_sma200 <= 0:
            _add("SMA", _t("sma.support_mt_below", ecart_sma200=ecart_sma200), 20)
        else:
            _add("SMA", _t("sma.sma200_above", ecart_sma200=ecart_sma200), 10)
    elif confluence_w50:
        if ecart_w50 <= 0:
            _add("SMA", _t("sma.support_lt_below", ecart_w50=ecart_w50), 20)
        else:
            _add("SMA", _t("sma.sma50w_above", ecart_w50=ecart_w50), 10)
    else:
        _add("SMA", _t("sma.deep_discount", ecart_sma200=ecart_sma200, ecart_w50=ecart_w50), 10)

    # 1b. Trend structure (SMA50d vs SMA200d + SMA200 slope over 20 sessions)
    if sma50_price > sma200_price:
        if sma200_slope > 0.5:
            _add("Tend", _t("trend.bullish_confirmed", sma50_price=sma50_price, sma200_slope=sma200_slope), 15)
        else:
            _add("Tend", _t("trend.favorable"), 8)
    else:
        if sma200_slope < -0.5:
            _add("Tend", _t("trend.bearish", sma50_price=sma50_price, sma200_slope=sma200_slope), -15)
        else:
            _add("Tend", _t("trend.neutral_bearish"), -8)

    # 2. Correction relative to the highs
    if dist_52w <= -25.0:
        _add("52H", _t("high52.major_correction", dist_52w=dist_52w), 25)
    elif -25.0 < dist_52w <= -15.0:
        _add("52H", _t("high52.significant_consolidation", dist_52w=dist_52w), 15)
    elif -15.0 < dist_52w <= -8.0:
        _add("52H", _t("high52.moderate_consolidation", dist_52w=dist_52w), 5)
    else:
        _add("52H", _t("high52.near_highs", dist_52w=dist_52w), -15)

    # 2b. Proximity to the annual floor (capitulation zone)
    if dist_52w_low <= 5.0:
        _add("52L", _t("low52.capitulation_zone", dist_52w_low=dist_52w_low, l52w_price=l52w_price), 12)
    elif dist_52w_low <= 15.0:
        _add("52L", _t("low52.near_floor", dist_52w_low=dist_52w_low, l52w_price=l52w_price), 6)

    # 3. Annual dividend (12-month sum)
    rendement_div_pct = 0.0
    if div_montant > 0 and c_curr > 0:
        rendement_div_pct = round((div_montant / c_curr) * 100.0, 2)
        _add("Div", _t("div.annual", div_montant=div_montant, div_date=div_date, rendement_div_pct=rendement_div_pct), 10)

    # 4. Weekly RSI
    if rsi_weekly <= 35:
        _add("RSI-W", _t("rsiw.deep_oversold", rsi_weekly=rsi_weekly), 20)
    elif rsi_weekly <= 45:
        _add("RSI-W", _t("rsiw.oversold", rsi_weekly=rsi_weekly), 12)
    elif rsi_weekly <= 55:
        _add("RSI-W", _t("rsiw.neutral", rsi_weekly=rsi_weekly), 4)

    # 5. Daily RSI
    if rsi_daily <= 30:
        _add("RSI-D", _t("rsid.extreme_oversold", rsi_daily=rsi_daily), 15)
    elif rsi_daily <= 40:
        _add("RSI-D", _t("rsid.oversold", rsi_daily=rsi_daily), 10)
    elif rsi_daily <= 50:
        _add("RSI-D", _t("rsid.neutral_low", rsi_daily=rsi_daily), 5)
    elif rsi_daily >= 70:
        _add("RSI-D", _t("rsid.overbought", rsi_daily=rsi_daily), -10)

    # 6. Relative volumes
    if rvol >= 2.0:
        _add("Vol", _t("vol.very_high", rvol=rvol), -10)
    elif rvol >= 1.3:
        _add("Vol", _t("vol.above_avg", rvol=rvol), 0)
    elif rvol < 0.8:
        _add("Vol", _t("vol.low", rvol=rvol), 10)

    # 7. Bullish RSI divergence
    if div_haussiere and rsi_creux1 is not None and rsi_creux2 is not None:
        _add("DIV\u2191", _t("divrsi.bullish", rsi_creux1=rsi_creux1, rsi_creux2=rsi_creux2), 18)

    # 8. Bollinger Bands (20d, ±2σ)
    if bb_pct_val < 0.0:
        _add("BB", _t("bb.below_lower", bb_pct_val=bb_pct_val), 10)
    elif bb_pct_val < 0.2:
        _add("BB", _t("bb.near_lower", bb_pct_val=bb_pct_val), 6)
    elif bb_pct_val > 1.0:
        _add("BB", _t("bb.above_upper", bb_pct_val=bb_pct_val), -6)
    elif bb_pct_val > 0.8:
        _add("BB", _t("bb.near_upper", bb_pct_val=bb_pct_val), -3)

    # 9. Weekly MACD (12, 26, 9)
    if macd_w_hist > 0 and macd_w_prev <= 0:
        _add("MACD-W", _t("macdw.bullish_cross"), 15)
    elif macd_w_hist > 0 and macd_w_hist > macd_w_prev:
        _add("MACD-W", _t("macdw.positive_expanding", macd_w_hist=macd_w_hist), 8)
    elif macd_w_hist < 0 and macd_w_hist > macd_w_prev:
        _add("MACD-W", _t("macdw.negative_narrowing", macd_w_hist=macd_w_hist), 4)
    elif macd_w_hist < 0 and macd_w_hist < macd_w_prev:
        _add("MACD-W", _t("macdw.negative_expanding", macd_w_hist=macd_w_hist), -8)


    score_opportunite = max(0, min(100, score_opportunite))

    # --- FINANCIAL CALCULATIONS (1 YEAR) ---
    pot_sma200_pct = ((sma200_price - c_curr) / c_curr) * 100.0 if c_curr > 0 else 0.0
    pot_52w_pct    = ((h52w_price  - c_curr) / c_curr) * 100.0 if c_curr > 0 else 0.0

    # 65% of the recovery to the 52w high = conservative 1-year target
    gain_capital_pct   = max(0.0, pot_52w_pct * 0.65)
    gain_total_est_pct = round(gain_capital_pct + rendement_div_pct, 2)
    gain_1000e         = round(1000.0 * (gain_total_est_pct / 100.0), 2)

    stop_pct = ((l52w_price - c_curr) / c_curr) * 100.0 if c_curr > 0 else 0.0
    estimation_gain_str = _t(
        "estimation.gain",
        sma200_price=sma200_price, pot_sma200_pct=pot_sma200_pct,
        h52w_price=h52w_price, pot_52w_pct=pot_52w_pct,
        l52w_price=l52w_price, stop_pct=stop_pct,
        c_green=CLR_GREEN, c_bold=CLR_BOLD, c_reset=CLR_RESET,
        rendement_div_pct=rendement_div_pct,
        gain_total_est_pct=gain_total_est_pct, gain_1000e=gain_1000e)

    # --- CONTEXTUAL RECOMMENDATIONS ---
    div_mention   = _t("misc.div_mention", rendement_div_pct=rendement_div_pct) if rendement_div_pct > 0 else ""
    below_support = ecart_sma200 <= 0

    if score_opportunite >= 80:
        statut_lt = f"{CLR_GREEN}{_t('status.strong', score=score_opportunite)}{CLR_RESET}"
        _ctx = _t("ctx.support_retest_below") if below_support else _t("ctx.touching_ma")
        explication = _t("expl.strong", ctx=_ctx, dist_52w_abs=abs(dist_52w), div_mention=div_mention)
        strategie_dca = _t("strat.strong")
    elif 60 <= score_opportunite < 80:
        statut_lt = f"{CLR_CYAN}{_t('status.attractive', score=score_opportunite)}{CLR_RESET}"
        explication = _t("expl.attractive", div_mention=div_mention)
        strategie_dca = _t("strat.attractive")
    elif 40 <= score_opportunite < 60:
        statut_lt = f"{CLR_YELLOW}{_t('status.watch', score=score_opportunite)}{CLR_RESET}"
        explication = _t("expl.watch")
        strategie_dca = _t("strat.watch")
    else:
        statut_lt = f"{CLR_RED}{_t('status.avoid', score=score_opportunite)}{CLR_RESET}"
        explication = _t("expl.avoid")
        strategie_dca = _t("strat.avoid")

    # --- SUMMARY: investment thesis in one sentence ---
    def _court(txt):
        base = txt.split(" : ")[0].split(" — ")[0].strip()
        while base and not base[0].isalnum():   # strip the leading emoji
            base = base[1:].lstrip()
        return base

    _forces  = sorted((d for d in diagnostics if d["impact"] > 0), key=lambda x: x["impact"], reverse=True)
    _risques = sorted((d for d in diagnostics if d["impact"] < 0), key=lambda x: x["impact"])
    _action = (
        _t("verdict.strong")  if score_opportunite >= 80 else
        _t("verdict.gradual") if score_opportunite >= 60 else
        _t("verdict.watch")   if score_opportunite >= 40 else
        _t("verdict.avoid")
    )
    synthese = {
        "verdict": _action,
        "atout":   _court(_forces[0]["text"])  if _forces  else None,
        "risque":  _court(_risques[0]["text"]) if _risques else None,
    }

    return diagnostics, statut_lt, score_opportunite, explication, strategie_dca, estimation_gain_str, _sc, synthese


# ==============================================================================
# 5. MAIN SCANNER ENGINE
# ==============================================================================
def analyser_actions_pro(tickers, seuil_hauteur_pct=3.0, seuil_marge_basse_pct=-5.0):
    _BAR  = "━" * 82
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n{_BAR}")
    print(f"  {CLR_BOLD}SCANNER BUY & HOLD  ·  STRATÉGIE INVESTISSEUR L.T.{CLR_RESET}"
          f"  {CLR_CYAN}{now_str}{CLR_RESET}")
    print(f"  {len(tickers)} tickers  ·  zone alerte SMA : {seuil_marge_basse_pct:+.1f}% à +{seuil_hauteur_pct:.1f}%")
    print(_BAR)

    noms_map = obtenir_infos_entreprises_parallele(tickers)

    try:
        _BATCH = 25
        close_parts, volume_parts, div_parts = [], [], []
        for _i in range(0, len(tickers), _BATCH):
            _batch = tickers[_i:_i + _BATCH]
            try:
                _data = yf.download(_batch, period="500d", interval="1d", progress=False,
                                    auto_adjust=False, actions=True)
                if _data.empty:
                    continue
                if len(_batch) == 1:
                    close_parts.append(_data[["Close"]].rename(columns={"Close": _batch[0]}))
                    volume_parts.append(_data[["Volume"]].rename(columns={"Volume": _batch[0]}))
                    if "Dividends" in _data:
                        div_parts.append(_data[["Dividends"]].rename(columns={"Dividends": _batch[0]}))
                else:
                    close_parts.append(_data["Close"])
                    volume_parts.append(_data["Volume"])
                    if "Dividends" in _data:
                        div_parts.append(_data["Dividends"])
            except Exception as _e:
                print(f"⚠️  Erreur batch {_batch}: {_e}")

        if not close_parts:
            print("❌ Aucune donnée récupérée.")
            return

        close_prices = pd.concat(close_parts, axis=1, sort=False)
        volume_data  = pd.concat(volume_parts, axis=1, sort=False)

        # Dividends extracted from the batch download (no separate HTTP calls)
        div_data = pd.concat(div_parts, axis=1, sort=False) if div_parts else pd.DataFrame()
        _cutoff  = pd.Timestamp.now() - pd.DateOffset(years=1)
        dividendes_map = {}
        for _t in close_prices.columns:
            if not div_data.empty and _t in div_data.columns:
                _col    = div_data[_t].fillna(0.0)
                _recent = _col[_col.index >= _cutoff]
                _annual = float(_recent[_recent > 0].sum())
                _last_d = _col[_col > 0]
                dividendes_map[_t] = {
                    "montant": _annual,
                    "date":    _last_d.index[-1].strftime("%Y-%m-%d") if not _last_d.empty else "N/A",
                }
            else:
                dividendes_map[_t] = {"montant": 0.0, "date": "N/A"}

        if close_prices.empty:
            print("❌ Erreur : Impossible d'extraire les prix de clôture.")
            return

        # ── VECTORIZED CALCULATIONS (BEFORE THE LOOP) ────────────────────────
        # min_periods=1: partial calculations for newly listed tickers
        sma_200_daily = close_prices.rolling(window=200, min_periods=1).mean()
        vol_20j_mean  = volume_data.rolling(window=20).mean() if not volume_data.empty else pd.DataFrame()

        close_weekly  = close_prices.resample("W-FRI").last()
        sma_50_weekly = close_weekly.rolling(window=50, min_periods=5).mean()

        rsi_daily_df  = calculer_rsi_df(close_prices)
        rsi_weekly_df = calculer_rsi_df(close_weekly)
        h52w_df       = close_prices.rolling(window=252, min_periods=1).max()
        l52w_df       = close_prices.rolling(window=252, min_periods=1).min()
        sma_50_daily  = close_prices.rolling(window=50, min_periods=1).mean()

        # Bollinger Bands (20d, ±2σ)
        _bb_mid   = close_prices.rolling(window=20, min_periods=10).mean()
        _bb_std   = close_prices.rolling(window=20, min_periods=10).std()
        _bb_upper = _bb_mid + 2 * _bb_std
        _bb_lower = _bb_mid - 2 * _bb_std
        bb_pct_df = (close_prices - _bb_lower) / (_bb_upper - _bb_lower)  # 0=low, 1=high

        # Weekly MACD (12, 26, 9 — EWM)
        _ema12_w    = close_weekly.ewm(span=12, min_periods=1, adjust=False).mean()
        _ema26_w    = close_weekly.ewm(span=26, min_periods=1, adjust=False).mean()
        _macd_w     = _ema12_w - _ema26_w
        _signal_w   = _macd_w.ewm(span=9, min_periods=1, adjust=False).mean()
        macd_hist_w = _macd_w - _signal_w

        # Last valid values — ffill does a single pass per DataFrame
        cp_ff        = close_prices.ffill()
        _sma200_ff   = sma_200_daily.ffill()
        last_close   = cp_ff.iloc[-1]
        last_var     = (close_prices.pct_change() * 100.0).ffill().iloc[-1]
        last_sma200  = _sma200_ff.iloc[-1]
        last_w50     = sma_50_weekly.ffill().iloc[-1]
        last_rsi_d   = rsi_daily_df.ffill().iloc[-1]
        last_rsi_w   = rsi_weekly_df.ffill().iloc[-1]
        last_vol     = volume_data.ffill().iloc[-1]  if not volume_data.empty  else pd.Series(dtype=float)
        last_vol20   = vol_20j_mean.ffill().iloc[-1] if not vol_20j_mean.empty else pd.Series(dtype=float)
        last_h52w        = h52w_df.ffill().iloc[-1]
        last_l52w        = l52w_df.ffill().iloc[-1]
        last_sma50       = sma_50_daily.ffill().iloc[-1]
        _slope_offset    = min(20, len(sma_200_daily) - 1)
        last_sma200_prev = _sma200_ff.iloc[-1 - _slope_offset]

        _bb_ff            = bb_pct_df.ffill()
        _macd_w_ff        = macd_hist_w.ffill()
        last_bb_pct       = _bb_ff.iloc[-1]
        last_macd_w_hist  = _macd_w_ff.iloc[-1]
        last_macd_w_prev  = _macd_w_ff.iloc[-2] if len(_macd_w_ff) >= 2 else _macd_w_ff.iloc[-1]

        # Filter: tickers with at least 20 days (viable RSI)
        valid_counts  = close_prices.count()
        valid_tickers = [t for t in tickers if t in close_prices.columns and valid_counts[t] >= 20]

        resultats          = []
        alertes_detaillees = []

        for ticker_code in valid_tickers:
            days_avail  = int(valid_counts.get(ticker_code, 0))
            data_partiel = days_avail < 200  # SMA200 based on fewer than 200d
            c_curr = _get_last(last_close[ticker_code])
            if c_curr == 0.0:
                continue

            sma200_curr = _get_last(last_sma200[ticker_code])
            if sma200_curr == 0.0:
                continue

            w50_raw  = last_w50.get(ticker_code, np.nan)
            has_w50  = not pd.isna(w50_raw)
            w50_curr = float(w50_raw) if has_w50 else sma200_curr

            rsi_daily  = _get_last(last_rsi_d[ticker_code],            default=50.0)
            rsi_weekly = _get_last(last_rsi_w.get(ticker_code, np.nan), default=50.0)

            v_curr = _get_last(last_vol.get(ticker_code,   np.nan), default=0.0)
            v_mean = _get_last(last_vol20.get(ticker_code, np.nan), default=0.0)
            rvol   = round(v_curr / v_mean, 1) if v_mean > 0 else 1.0

            h52w = _get_last(last_h52w[ticker_code], default=c_curr)
            l52w_price       = _get_last(last_l52w[ticker_code],        default=c_curr)
            sma50_curr       = _get_last(last_sma50[ticker_code],       default=sma200_curr)
            sma200_prev_val  = _get_last(last_sma200_prev[ticker_code], default=sma200_curr)
            sma200_slope     = ((sma200_curr - sma200_prev_val) / sma200_prev_val) * 100.0 if sma200_prev_val > 0 else 0.0
            dist_52w_low_pct = ((c_curr - l52w_price) / l52w_price) * 100.0 if l52w_price > 0 else 0.0

            bb_pct_curr      = _get_last(last_bb_pct.get(ticker_code,      np.nan), default=0.5)
            macd_hist_curr   = _get_last(last_macd_w_hist.get(ticker_code, np.nan), default=0.0)
            macd_hist_prev_v = _get_last(last_macd_w_prev.get(ticker_code, np.nan), default=0.0)
            macd_cross_up    = bool(macd_hist_curr > 0 and macd_hist_prev_v <= 0)

            if sma50_curr > sma200_curr:
                if sma200_slope > 0.3:
                    tendance_str = "↑ Haussier"
                else:
                    tendance_str = "↑ Neutre"  # bullish cross, flat SMA200
            else:
                if sma200_slope < -0.3:
                    tendance_str = "↓ Baissier"
                else:
                    tendance_str = "↓ Neutre"  # bearish cross, flat SMA200

            # Bullish RSI divergence (over the last 80 sessions)
            div_haussiere, rsi_creux1, rsi_creux2 = detecter_divergence_haussiere(
                close_prices[ticker_code], rsi_daily_df[ticker_code]
            )

            var_jour_pct = _get_last(last_var.get(ticker_code, np.nan), default=0.0)
            dist_sma200_pct = ((c_curr - sma200_curr) / sma200_curr) * 100.0
            dist_w50_pct    = ((c_curr - w50_curr)    / w50_curr)    * 100.0 if w50_curr  > 0 else 0.0
            dist_52w_pct    = ((c_curr - h52w)         / h52w)        * 100.0 if h52w      > 0 else 0.0

            div_info      = dividendes_map.get(ticker_code, {"montant": 0.0, "date": "N/A"})
            div_str       = f"{div_info['montant']:.2f}/an ({div_info['date']})" if div_info["montant"] > 0 else "—"
            alerte_sma200 = seuil_marge_basse_pct <= dist_sma200_pct <= seuil_hauteur_pct
            alerte_w50    = seuil_marge_basse_pct <= dist_w50_pct    <= seuil_hauteur_pct
            est_alerte    = alerte_sma200 or alerte_w50

            row = {
                "Code":             ticker_code + ("~" if data_partiel else ""),
                "Nom":              noms_map.get(ticker_code, ticker_code)[:18],
                "Cours":            round(c_curr, 2),
                "Var. Jour":        f"{var_jour_pct:+.2f}%",
                "Écart SMA200":     f"{dist_sma200_pct:+.2f}%",
                "Écart W50":        f"{dist_w50_pct:+.2f}%" if has_w50 else "N/D",
                "RSI Daily":        round(rsi_daily, 1),
                "RVOL":             f"{rvol}x",
                "52w High":         f"{dist_52w_pct:+.1f}%",
                "Dividende":        div_str,
                "Tendance":         tendance_str,
                "Statut":           ("🚨 ALERTE" if est_alerte else "OK") + (" 📐DIV↑" if div_haussiere else "") + (" MACD↑" if macd_cross_up else ""),
                "SMA200_val":       sma200_curr,
                "W50_val":          w50_curr,
                "W50_valide":       has_w50,
                "RSI_val":          rsi_daily,
                "RSI_W_val":        rsi_weekly,
                "RVOL_val":         rvol,
                "52w_val":          dist_52w_pct,
                "Ecart_sma200_val": dist_sma200_pct,
                "Ecart_w50_val":    dist_w50_pct,
                "H52W_price":       h52w,
                "Div_Montant":      div_info["montant"],
                "Div_Date":         div_info["date"],
                "SMA50_val":        sma50_curr,
                "SMA200_slope":     sma200_slope,
                "L52W_price":       l52w_price,
                "Dist_52wLow_val":  dist_52w_low_pct,
                "Divergence_RSI":   div_haussiere,
                "Div_RSI_creux1":   rsi_creux1,
                "Div_RSI_creux2":   rsi_creux2,
                "BB_pct_val":       bb_pct_curr,
                "MACD_W_hist":      macd_hist_curr,
                "MACD_W_hist_prev": macd_hist_prev_v,
            }

            resultats.append(row)
            if est_alerte:
                alertes_detaillees.append(row)

        if resultats:
            df_res  = pd.DataFrame(resultats)
            df_disp = df_res.drop(columns=[
                "SMA200_val", "W50_val", "W50_valide", "RSI_val", "RSI_W_val", "RVOL_val",
                "52w_val", "Ecart_sma200_val", "Ecart_w50_val", "H52W_price",
                "Div_Montant", "Div_Date",
                "SMA50_val", "SMA200_slope", "L52W_price", "Dist_52wLow_val",
                "Divergence_RSI", "Div_RSI_creux1", "Div_RSI_creux2",
                "BB_pct_val", "MACD_W_hist", "MACD_W_hist_prev",
            ])

            afficher_tableau(resultats)

            _BAR = "━" * 82
            print(f"\n{_BAR}")
            print(f"  {CLR_BOLD}SYNTHÈSE D'INVESTISSEMENT{CLR_RESET}  ·  {len(alertes_detaillees)} signal(s)")
            print(_BAR)

            if alertes_detaillees:
                alertes_etudiees = sorted(
                    [(item, *generer_analyse_investisseur_lt(item)) for item in alertes_detaillees],
                    key=lambda x: x[3], reverse=True,
                )
                for item, diag_list, statut_lt, score, explication, strat, gain_est, sc_det, synthese in alertes_etudiees:
                    afficher_fiche(item, diag_list, statut_lt, score, explication, strat, gain_est, sc_det)
                print("\u2500" * 82)
            else:
                print(f"  ✅ Aucune action dans la zone cible ({seuil_marge_basse_pct:+.1f}% à +{seuil_hauteur_pct:.1f}%).")

    except Exception as e:
        print(f"❌ Erreur générale : {e}")


if __name__ == "__main__":
    tickers_env = os.getenv("TICKERS", TICKERS_DEFAUT)
    liste_actions = [t.strip().upper() for t in tickers_env.split(",") if t.strip()]

    seuil_env = float(os.getenv("SEUIL_PCT", "3.0"))
    marge_basse = float(os.getenv("MARGE_SOUS_SUPPORT_PCT", "-5.0"))
    if marge_basse > 0:
        marge_basse = -marge_basse

    if liste_actions:
        analyser_actions_pro(
            liste_actions,
            seuil_hauteur_pct=seuil_env,
            seuil_marge_basse_pct=marge_basse,
        )
