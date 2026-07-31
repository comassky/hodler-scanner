"""Response schemas for OpenAPI documentation and frontend type generation.

These models mirror the JSON shapes produced by the analysis / backtest / chart /
portfolio modules. They are attached to routes via the ``responses=`` parameter
(documentation only) so the OpenAPI schema — and the generated TypeScript types
in ``frontend/src/types/api.d.ts`` — stay in sync with the API without adding any
runtime validation or response filtering.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ── Shared enums ─────────────────────────────────────────────────────
class MarketRegime(str, Enum):
    trend_up = "trend_up"
    trend_down = "trend_down"
    range = "range"
    transition = "transition"


class BandKey(str, Enum):
    strong = "strong"
    accumulate = "accumulate"
    watch = "watch"
    avoid = "avoid"


class TimingLevel(str, Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"
    unreliable = "unreliable"


# ── Ticker analysis (analysis.py → analyse_ticker) ───────────────────
class AnalysisPrice(BaseModel):
    last: float
    var_jour_pct: float


class AnalysisIndicators(BaseModel):
    sma200: float
    sma50: float
    w50: Optional[float] = None
    sma200_slope_20j_pct: float
    rsi_daily: float
    rsi_weekly: float
    rvol: float
    bb_pct: float
    macd_w_hist: float
    macd_w_hist_prev: float
    macd_w_cross_up: bool
    atr14: float
    atr14_pct: float
    adx14: float
    chop14: float


class AnalysisDistances(BaseModel):
    ecart_sma200_pct: float
    ecart_w50_pct: Optional[float] = None
    dist_52w_high_pct: float
    dist_52w_low_pct: float
    h52w_price: float
    l52w_price: float


class AnalysisFundamentals(BaseModel):
    dividende_annuel: float
    derniere_date_div: str


class AnalysisSignals(BaseModel):
    tendance: str
    regime: MarketRegime
    alerte_sma200: bool
    alerte_w50: bool
    divergence_rsi: bool
    rsi_creux: Optional[tuple[float, float]] = None


class AnalysisSynthese(BaseModel):
    verdict: str
    atout: Optional[str] = None
    risque: Optional[str] = None


class Diagnostic(BaseModel):
    text: str
    impact: float


class AnalysisBlock(BaseModel):
    score: float
    score_details: dict[str, float]
    statut: str
    synthese: AnalysisSynthese
    explication: str
    strategie: str
    objectifs: str
    diagnostics: list[Diagnostic]


class Analysis(BaseModel):
    ticker: str
    name: str
    timestamp: str
    data_partiel: bool
    days_available: int
    price: AnalysisPrice
    indicators: AnalysisIndicators
    distances: AnalysisDistances
    fundamentals: AnalysisFundamentals
    signals: AnalysisSignals
    analysis: AnalysisBlock
    cached: Optional[bool] = None


# ── Charts (charts.py → chart_data) ──────────────────────────────────
class ChartData(BaseModel):
    dates: list[str]
    close: list[Optional[float]]
    sma200: list[Optional[float]]
    sma50: list[Optional[float]]
    rsi: list[Optional[float]]
    macd_hist: list[Optional[float]]
    volume: list[Optional[float]]
    vol_sma20: list[Optional[float]]
    bb_upper: list[Optional[float]]
    bb_lower: list[Optional[float]]


# ── Fundamentals (fundamentals.py → fetch_fundamentals) ──────────────
class Fundamentals(BaseModel):
    pe_trailing: Optional[float] = None
    pe_forward: Optional[float] = None
    market_cap: Optional[float] = None
    sector: str
    industry: str
    country: str
    employees: Optional[int] = None
    earnings_date: Optional[str] = None


# ── News (news.py → fetch_news) ──────────────────────────────────────
class NewsItem(BaseModel):
    title: str
    publisher: Optional[str] = None
    url: str
    published: Optional[str] = None
    thumbnail: Optional[str] = None


class News(BaseModel):
    ticker: str
    count: int
    items: list[NewsItem]


# ── Portfolio (portfolio.py → build_portfolio) ───────────────────────
class Position(BaseModel):
    ticker: str
    name: str
    quantity: float
    avg_cost: float
    price: Optional[float] = None
    cost: float
    value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    weight: Optional[float] = None
    note: Optional[str] = None


class PortfolioTotals(BaseModel):
    cost: float
    value: float
    pnl: float
    pnl_pct: Optional[float] = None
    count: int
    priced: bool


class Portfolio(BaseModel):
    positions: list[Position]
    totals: PortfolioTotals


# ── Search (search.py → search_tickers) ──────────────────────────────
class SearchResult(BaseModel):
    ticker: str
    name: str
    type: str
    exchange: str


# ── Backtest (backtest.py → run_backtest) ────────────────────────────
class BacktestSeriesPoint(BaseModel):
    date: str
    price: float
    score: Optional[float] = None
    sma200: Optional[float] = None


class HorizonStats(BaseModel):
    count: int
    avg_return: Optional[float] = None
    median_return: Optional[float] = None
    win_rate: Optional[float] = None


class ScoreBand(BaseModel):
    key: BandKey
    min: float
    count: int
    avg_return: Optional[float] = None
    median_return: Optional[float] = None
    win_rate: Optional[float] = None
    by_horizon: dict[str, HorizonStats]


class Baseline(BaseModel):
    avg_return: Optional[float] = None
    win_rate: Optional[float] = None
    by_horizon: dict[str, HorizonStats]


class Timing(BaseModel):
    current_score: float
    percentile: float
    band: BandKey
    edge: Optional[float] = None
    engine_edge: Optional[float] = None
    correlation: Optional[float] = None
    horizon: int
    reliable: bool
    level: TimingLevel


class BacktestReport(BaseModel):
    ticker: str
    name: str
    period_start: str
    period_end: str
    samples: int
    horizons_days: list[int]
    primary_horizon: int
    series: list[BacktestSeriesPoint]
    bands: list[ScoreBand]
    baseline: Baseline
    correlation: dict[str, Optional[float]]
    timing: Timing
    cached: bool


# ── Favorites / watchlist (db.py) ────────────────────────────────────
class FavoritesResponse(BaseModel):
    favorites: list[str]
    added: Optional[bool] = None
    removed: Optional[bool] = None
