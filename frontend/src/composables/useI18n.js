import { computed } from 'vue'
import { useLocalStorage } from '@vueuse/core'

// Available languages — English by default, choice persisted in localStorage.
export const LOCALES = [
  { id: 'en', label: 'EN', name: 'English' },
  { id: 'fr', label: 'FR', name: 'Français' },
]

const _ids = LOCALES.map(l => l.id)
const locale = useLocalStorage('smm_locale', 'en')
if (!_ids.includes(locale.value)) locale.value = 'en'

function setLocale(l) {
  if (_ids.includes(l)) locale.value = l
}

// ── Message catalog ─────────────────────────────────────────────────
const messages = {
  en: {
    header: {
      analysis: 'Analysis', dashboard: 'Dashboard', recent: 'Recent:',
      themeDark: 'Dark', themeGray: 'Gray', themeLight: 'Light',
    },
    search: {
      placeholder: 'Ticker, name or ISIN… (LVMH, Apple, MC.PA, FR0000121014)',
      analyzing: 'Analyzing…', analyze: 'Analyze →', popular: 'Popular:',
      searching: 'Searching…', noResults: 'No matching ticker',
    },
    app: {
      title: 'Technical analysis',
      subtitle: 'SMA · RSI · MACD · Bollinger · Buy & Hold scoring',
      loadingData: 'Downloading Yahoo Finance & computing indicators…',
      loadingHint: 'This can take 5 to 15 seconds',
      error: 'Error',
      follow: '☆ Follow', following: '★ Following',
      refresh: 'Refresh', refreshTitle: 'Reload data without using the cache',
      partialData: 'Partial data', cache: '● Cache', today: 'today',
      inBrief: 'In brief', outOf100: '/ 100',
      signals: 'Signals',
      alertSma200: '⚠ SMA 200 alert', alertW50: '⚠ SMA 50w alert',
      macdCross: '↑ Weekly MACD cross', divergenceRsi: '⤴ RSI divergence',
      dividend: '₀ Div.',
      sessions: 'sessions',
      status: 'Status', explanation: 'Explanation', strategy: 'Strategy',
      targetsStop: 'Targets & Stop', asset: 'Asset', risk: 'Risk',
      indicators: 'Indicators', keyLevels: 'Key levels', analysis: 'Analysis',
      scoreContribution: 'Score contribution', neutralBase: 'Neutral base',
      result: 'result', forces: 'Strengths', watchpoints: 'Watchpoints',
      context: 'Context', noForce: 'No notable strength detected.',
      noRisk: 'No major risk detected.', fundamentals: 'Fundamentals',
      news: 'News',
      footerSource: 'View source on GitHub',
    },
    scoreLabel: { strong: 'STRONG BUY', accumulate: 'ACCUMULATE', watch: 'WATCH', avoid: 'AVOID' },
    sections: {
      overview: 'Overview', charts: 'Charts', indicators: 'Indicators',
      fundamentals: 'Fundamentals', news: 'News', analysis: 'Analysis',
      score: 'Score', forces: 'Strengths & risks', backtest: 'Backtest',
    },
    scoreComp: {
      SMA: 'SMA 200/50w', Tend: 'Trend', '52H': '52W High', '52L': '52W Low',
      Div: 'Dividend', 'RSI-W': 'Weekly RSI', 'RSI-D': 'Daily RSI', Vol: 'Volume',
      'DIV↑': 'RSI Div.', BB: 'Bollinger', 'MACD-W': 'Weekly MACD',
    },
    ind: {
      rsiDaily: 'Daily RSI', rsiWeekly: 'Weekly RSI', bbPct: 'Bollinger %B',
      rvol: 'Relative volume', macdWeekly: 'Weekly MACD (hist.)',
      smaSlope: 'SMA 200 slope (20d)', atr14: 'ATR 14 (volatility)',
      adx14: 'ADX 14 (trend strength)', chop14: 'Choppiness 14',
      oversold: 'oversold', overbought: 'overbought', neutral: 'neutral',
      crossUp: 'Cross ↑',
      sma200d: 'SMA 200 days', sma50w: 'SMA 50 weeks', sma50d: 'SMA 50 days',
      high52: '52-week high', low52: '52-week low',
    },
    regime: {
      label: 'Regime', trend_up: 'Trending', trend_down: 'Trending',
      range: 'Ranging', transition: 'Transition',
    },
    fund: {
      marketCap: 'Market cap', peTtm: 'P/E (ttm)', peForward: 'P/E forward',
      sector: 'Sector', industry: 'Industry', country: 'Country',
      earnings: 'Next earnings',
    },
    charts: {
      title: 'Charts', fibonacci: 'Fibonacci', bollinger: 'Bollinger',
      resetZoom: 'Reset zoom',
      zoomHint: 'Scroll to zoom · drag to select · Shift + drag to pan',
      rsi14: 'RSI 14', macdHist: 'MACD — Histogram', divergences: 'RSI divergences',
      price: 'Price', bbUpper: 'BB upper', bbLower: 'BB lower',
      bullish: 'bullish', bearish: 'bearish', none: 'none detected',
      volume: 'Volume',
      loadError: 'Unable to load the charts',
    },
    dash: {
      title: 'Dashboard', stockWatched: 'stock watched', stocksWatched: 'stocks watched',
      refreshAll: 'Refresh all', updatedAt: 'Updated {t} · auto 5 min',
      add: '+ Add',
      notLoaded: 'Not loaded', load: 'Load →', serverError: 'Server error',
      emptyTitle: 'Your watchlist is empty.',
      emptyHint: 'Add tickers above or click "☆ Follow" during an analysis.',
      remove: 'Remove', alert: '⚠ Alert', cache: 'cache',
      rsiD: 'RSI D', dSma200: '∆ SMA 200', trend: 'Trend',
      sortBy: 'Sort by',
      sort: {
        scoreDesc: 'Score (high → low)',
        scoreAsc: 'Score (low → high)',
        changeDesc: 'Change (high → low)',
        nameAsc: 'Name (A → Z)',
      },
    },
    backtest: {
      title: 'Score backtest',
      subtitle: 'How the opportunity score behaved historically — a transparency check, not a strategy.',
      correlation: 'Correlation',
      baseline: 'Baseline',
      samples: 'Samples',
      period: 'Period',
      score: 'Score',
      price: 'Price',
      sma200: 'SMA 200D',
      avgReturn: 'Avg. return',
      median: 'Median',
      winRate: 'Win rate',
      bandStrong: 'Strong (≥80)',
      bandAccumulate: 'Accumulate (60–79)',
      bandWatch: 'Watch (40–59)',
      bandAvoid: 'Avoid (<40)',
      avgReturnByBand: 'Average {h} forward return by score band (vs buy-anytime baseline)',
      scoreOverTime: 'Historical score vs price',
      decisionLegend: 'Score line color = decision:',
      disclaimer: 'Past performance does not guarantee future results. Forward returns are measured on Friday samples over up to ~10 years of data; longer horizons and small buckets have fewer samples and are statistically noisier.',
      loadError: 'Unable to run the backtest',
    },
    info: {
      backtest: {
        title: 'Score backtest',
        text: 'We replay the exact scoring engine across up to ~10 years of history and measure the realized forward return (3M / 6M / 12M / 3Y / 5Y) after each score, grouped by band.',
        tip: 'If the engine is meaningful, higher score bands should show higher average forward returns than the baseline.',
      },
      btCorrelation: {
        title: 'Correlation (score ↔ return)',
        text: 'Pearson correlation between the score and the realized forward return over the selected horizon, across every sample.',
        formula: 'r = cov(score, return) ÷ (σ_score × σ_return), from −1 to +1',
        levels: [
          { range: '≥ 0.3', label: 'score clearly predictive', tone: 'good' },
          { range: '0.1 – 0.3', label: 'weak but positive link', tone: 'neutral' },
          { range: '≤ 0', label: 'no or inverse relationship', tone: 'bad' },
        ],
        tip: 'Positive = a higher score tended to precede higher returns. It stays a correlation, not a guarantee.',
      },
      btBaseline: {
        title: 'Baseline',
        text: 'Average forward return if you had bought on any sampled date, ignoring the score — the “buy anytime” reference to beat.',
        tip: 'A score band only adds value when its average return sits above this baseline.',
      },
      btSamples: {
        title: 'Samples',
        text: 'Number of historical dates tested — one Friday per week over up to ~10 years. Each sample pairs a score with its measured forward return.',
        tip: 'More samples = more reliable statistics; longer horizons and small bands stay noisy.',
      },
      btPeriod: {
        title: 'Period',
        text: 'Date range covered by the backtest, from the first to the last sampled Friday.',
        tip: 'Bounded by the history available for the stock (up to ~10 years).',
      },
      btBands: {
        title: 'Return by score band',
        text: 'Average forward return grouped by score band (Strong / Accumulate / Watch / Avoid). The dashed line marks the baseline.',
        tip: 'A credible engine shows a descending staircase: higher bands → taller bars.',
      },
      btScoreTime: {
        title: 'Score vs price',
        text: 'The historical score (left axis, 0–100) plotted against the price (right axis) over time.',
        tip: 'Check whether score peaks and troughs lined up with the later price moves.',
      },
      signals: {
        title: 'Signals',
        text: 'Synthetic signals generated by the technical indicators: trend, alerts and timing opportunities on the stock.',
        tip: 'A quick read of the setup before diving into the detailed indicators.',
      },
      indicators: {
        title: 'Technical indicators',
        text: 'A set of indicators covering momentum (RSI, MACD), volatility (Bollinger, ATR) and volume. Each metric lights up a different facet of the stock’s dynamics.',
        tip: 'Hover each metric for its formula and reading thresholds.',
      },
      rsiDaily: {
        title: 'RSI 14 — daily',
        text: 'Strength of the recent move: has the stock risen too fast (expensive) or fallen too much (cheap)?',
        formula: 'RSI = 100 − 100 / (1 + avg gains ÷ avg losses over 14d)',
        levels: [
          { range: '≤ 30', label: 'oversold, rebound possible', tone: 'good' },
          { range: '30–70', label: 'neutral zone', tone: 'neutral' },
          { range: '≥ 70', label: 'overbought, caution', tone: 'bad' },
        ],
        tip: 'On a solid stock, a low RSI = accumulation window.',
      },
      rsiWeekly: {
        title: 'RSI 14 — weekly',
        text: 'Same logic as the daily RSI but on weekly candles: a background view with much less noise.',
        levels: [
          { range: '≤ 45', label: 'deep oversold, potential reversal', tone: 'good' },
          { range: '45–55', label: 'neutral momentum', tone: 'neutral' },
          { range: '≥ 70', label: 'deep overbought', tone: 'bad' },
        ],
        tip: 'More reliable than the daily for a long-term investor.',
      },
      bbPct: {
        title: 'Bollinger %B',
        text: 'Where does the price sit between the statistical floor and ceiling (±2σ bands over 20d)?',
        formula: '%B = (price − lower band) ÷ (upper band − lower band)',
        levels: [
          { range: '< 0.2', label: 'glued to the bottom, rebound likely', tone: 'good' },
          { range: '0.2–0.8', label: 'within the average', tone: 'neutral' },
          { range: '> 0.8', label: 'glued to the top, overheating', tone: 'warn' },
        ],
        tip: 'Below 0 = price out of the lower band, extreme oversold.',
      },
      rvol: {
        title: 'Relative volume (RVOL)',
        text: 'Is today\u2019s move backed by real trading, or is it anecdotal?',
        formula: 'RVOL = today\u2019s volume ÷ 20d average volume',
        levels: [
          { range: '< 0.8×', label: 'calm market, no selling pressure', tone: 'good' },
          { range: '≈ 1×', label: 'normal activity', tone: 'neutral' },
          { range: '≥ 2×', label: 'heavy volume, event, caution', tone: 'warn' },
        ],
        tip: 'A level break on strong volume is far more reliable.',
      },
      macdWeekly: {
        title: 'Weekly MACD — histogram',
        text: 'Is the medium-term momentum accelerating or slowing down? The histogram measures this impulse.',
        formula: 'Hist = MACD − Signal, MACD = EMA 12 − EMA 26 (weekly)',
        levels: [
          { range: 'crosses ↑ 0', label: 'confirmed bullish reversal', tone: 'good' },
          { range: '> 0 ↗', label: 'accelerating momentum', tone: 'good' },
          { range: '< 0', label: 'selling pressure', tone: 'bad' },
        ],
        tip: 'The cross above zero is a strong cyclical buy signal.',
      },
      smaSlope: {
        title: 'SMA 200 slope (over 20d)',
        text: 'Is the long-term average really rising? This is the direction of the underlying trend.',
        formula: '% change of the SMA 200 over the last 20 sessions',
        levels: [
          { range: '> +0.3%', label: 'healthy underlying trend', tone: 'good' },
          { range: '−0.3 to +0.3%', label: 'flat', tone: 'neutral' },
          { range: '< −0.3%', label: 'structural deterioration', tone: 'bad' },
        ],
        tip: 'Ideally positive before investing Buy & Hold.',
      },
      atr14: {
        title: 'ATR 14 — volatility',
        text: 'How much the stock moves on average each day. The % (ATR ÷ price) makes it comparable across stocks.',
        formula: '14d average of the True Range (real range of a session)',
        levels: [
          { range: '< 1.5%', label: 'low volatility, calm candles', tone: 'good' },
          { range: '1.5–3%', label: 'moderate volatility', tone: 'neutral' },
          { range: '> 3%', label: 'high volatility, large swings', tone: 'warn' },
        ],
        tip: 'Suggested stop ≈ price − 1.5 × ATR.',
      },
      adx14: {
        title: 'ADX 14 — trend strength',
        text: 'How strong the current trend is, regardless of its direction (up or down).',
        formula: 'Wilder smoothing of the Directional Index (DX) over 14d',
        levels: [
          { range: '< 20', label: 'no trend, ranging market', tone: 'neutral' },
          { range: '20–25', label: 'trend forming', tone: 'neutral' },
          { range: '> 25', label: 'established trend', tone: 'good' },
        ],
        tip: 'ADX rising above 25 = the trend is gaining traction.',
      },
      chop14: {
        title: 'Choppiness Index 14',
        text: 'Is the market trending cleanly or chopping sideways? Bounded 0–100.',
        formula: '100 × log10(ΣTR ÷ range) ÷ log10(14) over 14d',
        levels: [
          { range: '> 61.8', label: 'consolidation / range', tone: 'neutral' },
          { range: '38.2–61.8', label: 'transition', tone: 'neutral' },
          { range: '< 38.2', label: 'strong directional trend', tone: 'good' },
        ],
        tip: 'High = range (fade the extremes); low = trend (follow it).',
      },
      regime: {
        title: 'Market regime',
        text: 'Is the market trending or going sideways? Combines ADX (trend strength) and the Choppiness Index. Direction (up/down) is given by the adjacent trend badge — this one tells you *how* to read the RSI.',
        levels: [
          { range: 'Trending', label: 'ADX ≥ 25 — follow the move, don\u2019t fade RSI', tone: 'good' },
          { range: 'Ranging', label: 'ADX < 20 or CHOP ≥ 61.8 — play RSI extremes (rebound)', tone: 'neutral' },
          { range: 'Transition', label: 'undecided — wait for confirmation', tone: 'warn' },
        ],
        tip: 'Ranging: RSI oversold = likely rebound. Trending: don\u2019t fade the move.',
      },
      keyLevels: {
        title: 'Key levels',
        text: 'Key price levels used as support/resistance.',
        tip: 'Fibonacci levels (38.2%, 50%, 61.8%) are plotted on the price chart as colored dashed lines.',
      },
      sma200: {
        title: 'SMA 200 days',
        text: 'The long-term reference moving average, the filter used by institutional investors.',
        levels: [
          { range: '−3 to +3%', label: 'confluence zone, key retest', tone: 'good' },
          { range: 'price > SMA', label: 'uptrend preserved', tone: 'good' },
          { range: 'price < SMA', label: 'bearish territory', tone: 'bad' },
        ],
        tip: 'Plotted as an orange dashed line on the chart.',
      },
      sma50w: {
        title: 'SMA 50 weeks',
        text: '≈ 250 sessions, closely followed by fund managers. A return to it after a correction is often a quality Buy & Hold entry.',
        tip: 'Plotted in blue on the chart.',
      },
      high52: {
        title: '52-week high',
        text: 'Peak of the trailing year. The displayed distance measures the current discount from that peak.',
        levels: [
          { range: '≤ −25%', label: 'major correction, strong recovery potential', tone: 'good' },
          { range: '−25 to −8%', label: 'healthy consolidation', tone: 'neutral' },
          { range: '> −8%', label: 'near the highs, limited margin', tone: 'warn' },
        ],
        tip: 'At −5% with solid indicators = potential breakout setup. Serves as the upper anchor for Fibonacci.',
      },
      low52: {
        title: '52-week low',
        text: 'Floor of the trailing year. The distance shows the rebound already achieved from the worst level.',
        levels: [
          { range: '≤ +5%', label: 'capitulation zone, limited residual risk', tone: 'good' },
          { range: '+5 to +15%', label: 'near the yearly floor', tone: 'good' },
          { range: '> +15%', label: 'far from the floor', tone: 'neutral' },
        ],
        tip: 'Near the floor = limited residual risk. Serves as the lower anchor for Fibonacci.',
      },
      sma50: {
        title: 'SMA 50 days',
        text: 'Intermediate moving average, reflects the medium-term trend.',
        levels: [
          { range: '> SMA 200', label: 'Golden Cross, bullish signal', tone: 'good' },
          { range: '< SMA 200', label: 'Death Cross, bearish signal', tone: 'bad' },
        ],
        tip: 'Plotted in blue on the chart.',
      },
      fundamentals: {
        title: 'Fundamentals',
        text: 'Fundamental financial data of the stock, complementing the technical analysis.',
        tip: 'Analyze both together for a complete view before investing.',
      },
      news: {
        title: 'News',
        text: 'Latest news about the stock (source: Yahoo Finance via yfinance).',
        tip: 'For information only: verify the source before any decision.',
      },
      peTtm: {
        title: 'P/E (trailing 12 months)',
        text: 'How many years of current earnings the market accepts to pay for the stock.',
        formula: 'P/E = price ÷ earnings per share (last 12 months)',
        levels: [
          { range: '< 15', label: 'potentially undervalued', tone: 'good' },
          { range: '15–30', label: 'normal valuation', tone: 'neutral' },
          { range: '> 30', label: 'strong growth already priced in', tone: 'warn' },
        ],
      },
      peForward: {
        title: 'Forward P/E',
        text: 'Same ratio but based on estimated earnings for the next 12 months: more forward-looking.',
        levels: [
          { range: 'forward < ttm', label: 'earnings expected to rise', tone: 'good' },
          { range: 'forward > ttm', label: 'earnings expected to fall', tone: 'warn' },
        ],
      },
      earnings: {
        title: 'Next earnings',
        text: 'Publication date of the next quarterly results.',
        tip: 'Volatility is often elevated in the 2 weeks before: adjust position size.',
      },
      analysis: {
        title: 'Analysis',
        text: 'Summary written by the scoring engine: verdict, one-sentence investment thesis, explanation and associated execution strategy.',
        tip: 'Read it together with the score breakdown below.',
      },
      synthese: {
        title: 'Synthesis',
        text: 'Express summary: overall verdict, dominant strength and main identified risk.',
        tip: 'The TL;DR of the analysis, to grasp the thesis at a glance.',
      },
      scoreContribution: {
        title: 'Score breakdown',
        text: 'Each factor adds or removes points from a neutral base of 40/100. The longer the bar, the more the factor weighs.',
        levels: [
          { range: 'Green →', label: 'factor that raises the score', tone: 'good' },
          { range: '← Red', label: 'factor that lowers the score', tone: 'bad' },
        ],
        tip: 'The final score is clamped between 0 and 100.',
      },
      forces: {
        title: 'Strengths',
        text: 'Technical factors that support the stock and raise its score.',
        levels: [
          { range: 'Supports', label: 'price on a key support (SMA 200d/50w)', tone: 'good' },
          { range: 'Oversold', label: 'low RSI, rebound potential', tone: 'good' },
          { range: 'Momentum', label: 'bullish MACD, divergence', tone: 'good' },
          { range: 'Discount', label: 'far below the 52-week high', tone: 'good' },
        ],
        tip: 'The more numerous and heavier the strengths, the higher the score.',
      },
      watchpoints: {
        title: 'Watchpoints',
        text: 'Risk factors that weigh on the score and call for caution.',
        levels: [
          { range: 'Highs', label: 'price near the 52-week high', tone: 'bad' },
          { range: 'Overbought', label: 'stretched RSI, pullback risk', tone: 'bad' },
          { range: 'Trend', label: 'bearish underlying trend', tone: 'bad' },
          { range: 'Volume', label: 'suspicious or event-driven volume', tone: 'warn' },
        ],
        tip: 'A dossier can be strong yet carry watchpoints: weigh both.',
      },
      context: {
        title: 'Context',
        text: 'Neutral observations with no direct impact on the score, provided to complete the picture.',
        tip: 'Useful background, but it does not change the verdict.',
      },
      chartRsi14: {
        title: 'RSI 14',
        text: 'Momentum strength: is the stock oversold (cheap) or overbought (expensive)?',
        levels: [
          { range: '≤ 30', label: 'oversold (green band)', tone: 'good' },
          { range: '30–70', label: 'neutral zone', tone: 'neutral' },
          { range: '≥ 70', label: 'overbought (red band)', tone: 'bad' },
        ],
        tip: 'Price / RSI divergences are detected in the dedicated chart below.',
      },
      chartMacd: {
        title: 'MACD — histogram',
        text: 'Measures the impulse of the trend: is it accelerating or fading?',
        formula: 'Hist = MACD − Signal (exponential moving averages)',
        levels: [
          { range: 'green bars', label: 'bullish momentum', tone: 'good' },
          { range: 'red bars', label: 'bearish momentum', tone: 'bad' },
        ],
        tip: 'A color change signals an imminent MACD / Signal cross.',
      },
      chartDiv: {
        title: 'Price / RSI divergences',
        text: 'Gap between the direction of the price and that of the RSI, often heralding a reversal.',
        levels: [
          { range: '↑ Bullish', label: 'Price makes a new low but RSI rises → rebound likely', tone: 'good' },
          { range: '↓ Bearish', label: 'Price makes a new high but RSI falls → exhaustion', tone: 'bad' },
        ],
        tip: 'Timing signal, to be confirmed by volume and the underlying trend.',
      },
    },
  },
  fr: {
    header: {
      analysis: 'Analyse', dashboard: 'Dashboard', recent: 'Récents :',
      themeDark: 'Noir', themeGray: 'Gris', themeLight: 'Clair',
    },
    search: {
      placeholder: 'Ticker, nom ou ISIN… (LVMH, Apple, MC.PA, FR0000121014)',
      analyzing: 'Analyse…', analyze: 'Analyser →', popular: 'Populaires :',
      searching: 'Recherche…', noResults: 'Aucun ticker correspondant',
    },
    app: {
      title: 'Analyse technique',
      subtitle: 'SMA · RSI · MACD · Bollinger · Scoring Buy & Hold',
      loadingData: 'Téléchargement Yahoo Finance & calcul des indicateurs…',
      loadingHint: 'Cela peut prendre 5 à 15 secondes',
      error: 'Erreur',
      follow: '☆ Suivre', following: '★ Suivi',
      refresh: 'Rafraîchir', refreshTitle: 'Recharger les données sans utiliser le cache',
      partialData: 'Données partielles', cache: '● Cache', today: 'aujourd\u2019hui',
      inBrief: 'En bref', outOf100: '/ 100',
      signals: 'Signaux',
      alertSma200: '⚠ Alerte SMA 200', alertW50: '⚠ Alerte SMA 50w',
      macdCross: '↑ Croisement MACD Hebdo', divergenceRsi: '⤴ Divergence RSI',
      dividend: '₀ Div.',
      sessions: 'séances',
      status: 'Statut', explanation: 'Explication', strategy: 'Stratégie',
      targetsStop: 'Objectifs & Stop', asset: 'Atout', risk: 'Risque',
      indicators: 'Indicateurs', keyLevels: 'Niveaux clés', analysis: 'Analyse',
      scoreContribution: 'Contribution au Score', neutralBase: 'Base neutre',
      result: 'résultat', forces: 'Forces', watchpoints: 'Points de vigilance',
      context: 'Contexte', noForce: 'Aucune force marquante détectée.',
      noRisk: 'Aucun risque majeur détecté.', fundamentals: 'Fondamentaux',
      news: 'Actualités',
      footerSource: 'Voir le code sur GitHub',
    },
    scoreLabel: { strong: 'ACHAT FORT', accumulate: 'ACCUMULATION', watch: 'SURVEILLANCE', avoid: 'À ÉVITER' },
    sections: {
      overview: 'Aperçu', charts: 'Graphiques', indicators: 'Indicateurs',
      fundamentals: 'Fondamentaux', news: 'Actualités', analysis: 'Analyse',
      score: 'Score', forces: 'Forces & risques', backtest: 'Backtest',
    },
    scoreComp: {
      SMA: 'SMA 200/50w', Tend: 'Tendance', '52H': '52W High', '52L': '52W Low',
      Div: 'Dividende', 'RSI-W': 'RSI Hebdo', 'RSI-D': 'RSI Jour', Vol: 'Volume',
      'DIV↑': 'Div. RSI', BB: 'Bollinger', 'MACD-W': 'MACD Hebdo',
    },
    ind: {
      rsiDaily: 'RSI Journalier', rsiWeekly: 'RSI Hebdomadaire', bbPct: 'Bollinger %B',
      rvol: 'Volume relatif', macdWeekly: 'MACD Hebdo (hist.)',
      smaSlope: 'Pente SMA 200 (20j)', atr14: 'ATR 14 (volatilité)',
      adx14: 'ADX 14 (force de tendance)', chop14: 'Choppiness (14)',
      oversold: 'survendu', overbought: 'suracheté', neutral: 'neutre',
      crossUp: 'Cross ↑',
      sma200d: 'SMA 200 jours', sma50w: 'SMA 50 semaines', sma50d: 'SMA 50 jours',
      high52: 'Plus haut 52 sem.', low52: 'Plus bas 52 sem.',
    },
    regime: {
      label: 'Régime', trend_up: 'Tendance', trend_down: 'Tendance',
      range: 'Latéral', transition: 'Transition',
    },
    fund: {
      marketCap: 'Capitalisation', peTtm: 'P/E (ttm)', peForward: 'P/E forward',
      sector: 'Secteur', industry: 'Industrie', country: 'Pays',
      earnings: 'Prochains résultats',
    },
    charts: {
      title: 'Graphiques', fibonacci: 'Fibonacci', bollinger: 'Bollinger',
      resetZoom: 'Reset zoom',
      zoomHint: 'Molette pour zoomer · glisser pour sélectionner · Shift + glisser pour déplacer',
      rsi14: 'RSI 14', macdHist: 'MACD — Histogramme', divergences: 'Divergences RSI',
      price: 'Cours', bbUpper: 'BB sup.', bbLower: 'BB inf.',
      bullish: 'haussière', bearish: 'baissière', none: 'aucune détectée',
      volume: 'Volume',
      loadError: 'Impossible de charger les graphiques',
    },
    dash: {
      title: 'Dashboard', stockWatched: 'valeur surveillée', stocksWatched: 'valeurs surveillées',
      refreshAll: 'Actualiser tout', updatedAt: 'Màj {t} · auto 5 min',
      add: '+ Ajouter',
      notLoaded: 'Non chargé', load: 'Charger →', serverError: 'Erreur serveur',
      emptyTitle: 'Votre watchlist est vide.',
      emptyHint: 'Ajoutez des tickers ci-dessus ou cliquez sur "☆ Suivre" lors d\u2019une analyse.',
      remove: 'Retirer', alert: '⚠ Alerte', cache: 'cache',
      rsiD: 'RSI J', dSma200: '∆ SMA 200', trend: 'Tendance',
      sortBy: 'Trier par',
      sort: {
        scoreDesc: 'Score (élevé → faible)',
        scoreAsc: 'Score (faible → élevé)',
        changeDesc: 'Variation (élevé → faible)',
        nameAsc: 'Nom (A → Z)',
      },
    },
    backtest: {
      title: 'Backtest du score',
      subtitle: 'Comportement historique du score d’opportunité — un contrôle de transparence, pas une stratégie.',
      correlation: 'Corrélation',
      baseline: 'Référence',
      samples: 'Échantillons',
      period: 'Période',
      score: 'Score',
      price: 'Cours',
      sma200: 'SMA 200J',
      avgReturn: 'Rdt. moyen',
      median: 'Médiane',
      winRate: 'Taux de réussite',
      bandStrong: 'Fort (≥80)',
      bandAccumulate: 'Accumuler (60–79)',
      bandWatch: 'Surveiller (40–59)',
      bandAvoid: 'Éviter (<40)',
      avgReturnByBand: 'Rendement moyen à {h} par palier de score (vs référence achat-au-hasard)',
      scoreOverTime: 'Score historique vs cours',
      decisionLegend: 'Couleur de la ligne = décision :',
      disclaimer: 'Les performances passées ne préjugent pas des résultats futurs. Les rendements forward sont mesurés sur des échantillons du vendredi sur jusqu’à ~10 ans ; les horizons longs et les petits paliers ont moins d’échantillons et sont plus bruités.',
      loadError: 'Impossible d’exécuter le backtest',
    },
    info: {
      backtest: {
        title: 'Backtest du score',
        text: 'On rejoue exactement le moteur de scoring sur jusqu’à ~10 ans d’historique et on mesure le rendement forward réalisé (3M / 6M / 12M / 3A / 5A) après chaque score, groupé par palier.',
        tip: 'Si le moteur est pertinent, les paliers de score élevés doivent afficher un rendement forward moyen supérieur à la référence.',
      },
      btCorrelation: {
        title: 'Corrélation (score ↔ rendement)',
        text: 'Corrélation de Pearson entre le score et le rendement forward réalisé sur l’horizon choisi, sur l’ensemble des échantillons.',
        formula: 'r = cov(score, rdt) ÷ (σ_score × σ_rdt), de −1 à +1',
        levels: [
          { range: '≥ 0,3', label: 'score nettement prédictif', tone: 'good' },
          { range: '0,1 – 0,3', label: 'lien faible mais positif', tone: 'neutral' },
          { range: '≤ 0', label: 'lien nul ou inverse', tone: 'bad' },
        ],
        tip: 'Positif = un score élevé a eu tendance à précéder de meilleurs rendements. Cela reste une corrélation, pas une garantie.',
      },
      btBaseline: {
        title: 'Référence',
        text: 'Rendement forward moyen si on avait acheté à n’importe quelle date échantillonnée, sans tenir compte du score — la référence « achat au hasard » à battre.',
        tip: 'Un palier de score n’apporte de la valeur que si son rendement moyen dépasse cette référence.',
      },
      btSamples: {
        title: 'Échantillons',
        text: 'Nombre de dates historiques testées — un vendredi par semaine sur jusqu’à ~10 ans. Chaque échantillon associe un score à son rendement forward mesuré.',
        tip: 'Plus d’échantillons = statistiques plus fiables ; les horizons longs et les petits paliers restent bruités.',
      },
      btPeriod: {
        title: 'Période',
        text: 'Plage de dates couverte par le backtest, du premier au dernier vendredi échantillonné.',
        tip: 'Limitée par l’historique disponible pour le titre (jusqu’à ~10 ans).',
      },
      btBands: {
        title: 'Rendement par palier',
        text: 'Rendement forward moyen groupé par palier de score (Fort / Accumuler / Surveiller / Éviter). La ligne pointillée marque la référence.',
        tip: 'Un moteur crédible dessine un escalier décroissant : palier plus haut → barre plus haute.',
      },
      btScoreTime: {
        title: 'Score vs cours',
        text: 'Le score historique (axe gauche, 0–100) tracé face au cours (axe droit) au fil du temps.',
        tip: 'Vérifie si les sommets et creux du score coïncident avec les mouvements de cours ultérieurs.',
      },
      signals: {
        title: 'Signaux',
        text: 'Signaux synthétiques générés par les indicateurs techniques : tendance, alertes et opportunités de timing sur le titre.',
        tip: 'Une lecture rapide du setup avant de plonger dans le détail des indicateurs.',
      },
      indicators: {
        title: 'Indicateurs techniques',
        text: 'Ensemble d\'indicateurs couvrant le momentum (RSI, MACD), la volatilité (Bollinger, ATR) et le volume. Chaque métrique éclaire une facette différente de la dynamique du titre.',
        tip: 'Survole chaque métrique pour sa formule et ses seuils de lecture.',
      },
      rsiDaily: {
        title: 'RSI 14 — journalier',
        text: 'Force du mouvement récent : le titre est-il monté trop vite (cher) ou trop baissé (bon marché) ?',
        formula: 'RSI = 100 − 100 / (1 + gains moy. ÷ pertes moy. sur 14j)',
        levels: [
          { range: '≤ 30', label: 'survendu, rebond possible', tone: 'good' },
          { range: '30–70', label: 'zone neutre', tone: 'neutral' },
          { range: '≥ 70', label: 'suracheté, prudence', tone: 'bad' },
        ],
        tip: 'Sur un bon dossier, un RSI bas = fenêtre d\u2019accumulation.',
      },
      rsiWeekly: {
        title: 'RSI 14 — hebdomadaire',
        text: 'Même logique que le RSI journalier mais sur bougies hebdo : vision de fond, beaucoup moins de bruit.',
        levels: [
          { range: '≤ 45', label: 'survente de fond, retournement potentiel', tone: 'good' },
          { range: '45–55', label: 'momentum neutre', tone: 'neutral' },
          { range: '≥ 70', label: 'surachat de fond', tone: 'bad' },
        ],
        tip: 'Plus fiable que le journalier pour un investisseur long terme.',
      },
      bbPct: {
        title: 'Bollinger %B',
        text: 'Où se situe le cours entre le plancher et le plafond statistiques (bandes ±2σ sur 20j) ?',
        formula: '%B = (cours − bande basse) ÷ (bande haute − bande basse)',
        levels: [
          { range: '< 0.2', label: 'collé au bas, rebond probable', tone: 'good' },
          { range: '0.2–0.8', label: 'dans la moyenne', tone: 'neutral' },
          { range: '> 0.8', label: 'collé au haut, surchauffe', tone: 'warn' },
        ],
        tip: 'Sous 0 = cours sorti sous la bande basse, survente extrême.',
      },
      rvol: {
        title: 'Volume relatif (RVOL)',
        text: 'Le mouvement du jour est-il soutenu par de vrais échanges, ou anecdotique ?',
        formula: 'RVOL = volume du jour ÷ moyenne du volume sur 20j',
        levels: [
          { range: '< 0.8×', label: 'marché calme, pas de pression vendeuse', tone: 'good' },
          { range: '≈ 1×', label: 'activité normale', tone: 'neutral' },
          { range: '≥ 2×', label: 'gros volumes, évènement, prudence', tone: 'warn' },
        ],
        tip: 'Une cassure de niveau sur fort volume est bien plus fiable.',
      },
      macdWeekly: {
        title: 'MACD hebdo — histogramme',
        text: 'Le momentum moyen terme accélère-t-il ou ralentit-il ? L\u2019histogramme mesure cet élan.',
        formula: 'Hist = MACD − Signal, MACD = EMA 12 − EMA 26 (hebdo)',
        levels: [
          { range: 'croise ↑ 0', label: 'retournement haussier confirmé', tone: 'good' },
          { range: '> 0 ↗', label: 'momentum qui accélère', tone: 'good' },
          { range: '< 0', label: 'pression vendeuse', tone: 'bad' },
        ],
        tip: 'Le croisement au-dessus de zéro est un signal d\u2019achat cyclique fort.',
      },
      smaSlope: {
        title: 'Pente SMA 200 (sur 20j)',
        text: 'La moyenne long terme monte-t-elle vraiment ? C\u2019est la direction de la tendance de fond.',
        formula: 'Variation % de la SMA 200 sur les 20 dernières séances',
        levels: [
          { range: '> +0.3%', label: 'tendance de fond saine', tone: 'good' },
          { range: '−0.3 à +0.3%', label: 'à plat', tone: 'neutral' },
          { range: '< −0.3%', label: 'dégradation structurelle', tone: 'bad' },
        ],
        tip: 'Idéalement positive avant d\u2019investir en Buy & Hold.',
      },
      atr14: {
        title: 'ATR 14 — volatilité',
        text: 'De combien le titre bouge en moyenne chaque jour. Le % (ATR ÷ cours) le rend comparable d\u2019un titre à l\u2019autre.',
        formula: 'Moyenne sur 14j du True Range (amplitude réelle d\u2019une séance)',
        levels: [
          { range: '< 1.5%', label: 'volatilité faible, bougies calmes', tone: 'good' },
          { range: '1.5–3%', label: 'volatilité modérée', tone: 'neutral' },
          { range: '> 3%', label: 'volatilité élevée, fortes amplitudes', tone: 'warn' },
        ],
        tip: 'Stop conseillé ≈ cours − 1.5 × ATR.',
      },
      adx14: {
        title: 'ADX 14 — force de tendance',
        text: 'À quel point la tendance actuelle est forte, indépendamment de sa direction (hausse ou baisse).',
        formula: 'Lissage de Wilder de l\u2019indice directionnel (DX) sur 14j',
        levels: [
          { range: '< 20', label: 'pas de tendance, marché en range', tone: 'neutral' },
          { range: '20–25', label: 'tendance en formation', tone: 'neutral' },
          { range: '> 25', label: 'tendance établie', tone: 'good' },
        ],
        tip: 'ADX qui passe au-dessus de 25 = la tendance prend de la force.',
      },
      chop14: {
        title: 'Choppiness Index 14',
        text: 'Le marché tend-il proprement ou hésite-t-il latéralement ? Borné 0–100.',
        formula: '100 × log10(ΣTR ÷ amplitude) ÷ log10(14) sur 14j',
        levels: [
          { range: '> 61.8', label: 'consolidation / range', tone: 'neutral' },
          { range: '38.2–61.8', label: 'transition', tone: 'neutral' },
          { range: '< 38.2', label: 'tendance directionnelle forte', tone: 'good' },
        ],
        tip: 'Élevé = range (fader les extrêmes) ; bas = tendance (la suivre).',
      },
      regime: {
        title: 'Régime de marché',
        text: 'Le marché est-il en tendance ou latéral ? Combine l\u2019ADX (force de tendance) et le Choppiness Index. La direction (hausse/baisse) est donnée par le badge de tendance voisin — celui-ci indique *comment* lire le RSI.',
        levels: [
          { range: 'Tendance', label: 'ADX ≥ 25 — suivre le mouvement, ne pas fader le RSI', tone: 'good' },
          { range: 'Latéral', label: 'ADX < 20 ou CHOP ≥ 61.8 — jouer les extrêmes RSI (rebond)', tone: 'neutral' },
          { range: 'Transition', label: 'indécis — attendre confirmation', tone: 'warn' },
        ],
        tip: 'Latéral : RSI survendu = rebond probable. Tendance : ne pas fader le mouvement.',
      },
      keyLevels: {
        title: 'Niveaux clés',
        text: 'Niveaux de prix clés utilisés comme support/résistance.',
        tip: 'Les niveaux Fibonacci (38.2%, 50%, 61.8%) sont tracés sur le graphique de prix en pointillés colorés.',
      },
      sma200: {
        title: 'SMA 200 jours',
        text: 'La moyenne mobile de référence du long terme, filtre des investisseurs institutionnels.',
        levels: [
          { range: '−3 à +3%', label: 'zone de confluence, retest clé', tone: 'good' },
          { range: 'cours > SMA', label: 'tendance haussière préservée', tone: 'good' },
          { range: 'cours < SMA', label: 'territoire baissier', tone: 'bad' },
        ],
        tip: 'Tracée en orange pointillé sur le graphique.',
      },
      sma50w: {
        title: 'SMA 50 semaines',
        text: '≈ 250 séances, très suivie par les gérants de fonds. Un retour dessus après correction est souvent un point d\u2019entrée Buy & Hold de qualité.',
        tip: 'Tracée en bleu sur le graphique.',
      },
      high52: {
        title: 'Plus haut 52 semaines',
        text: 'Sommet de l\u2019année glissante. La distance affichée mesure la décote actuelle depuis ce sommet.',
        levels: [
          { range: '≤ −25%', label: 'correction majeure, fort potentiel de reprise', tone: 'good' },
          { range: '−25 à −8%', label: 'consolidation saine', tone: 'neutral' },
          { range: '> −8%', label: 'proche des sommets, marge limitée', tone: 'warn' },
        ],
        tip: 'À −5% avec des indicateurs solides = setup de cassure potentiel. Sert d\u2019ancrage haut au Fibonacci.',
      },
      low52: {
        title: 'Plus bas 52 semaines',
        text: 'Plancher de l\u2019année glissante. La distance montre le rebond déjà réalisé depuis le pire niveau.',
        levels: [
          { range: '≤ +5%', label: 'zone de capitulation, risque résiduel limité', tone: 'good' },
          { range: '+5 à +15%', label: 'proche du plancher annuel', tone: 'good' },
          { range: '> +15%', label: 'loin du plancher', tone: 'neutral' },
        ],
        tip: 'Proche du plancher = risque résiduel limité. Sert d\u2019ancrage bas au Fibonacci.',
      },
      sma50: {
        title: 'SMA 50 jours',
        text: 'Moyenne mobile intermédiaire, reflète la tendance à moyen terme.',
        levels: [
          { range: '> SMA 200', label: 'Golden Cross, signal haussier', tone: 'good' },
          { range: '< SMA 200', label: 'Death Cross, signal baissier', tone: 'bad' },
        ],
        tip: 'Tracée en bleu sur le graphique.',
      },
      fundamentals: {
        title: 'Fondamentaux',
        text: 'Données financières fondamentales du titre, en complément de l’analyse technique.',
        tip: 'À analyser conjointement pour une vision complète avant investissement.',
      },
      news: {
        title: 'Actualités',
        text: 'Dernières actualités du titre (source Yahoo Finance via yfinance).',
        tip: 'À titre informatif : recouper la source avant toute décision.',
      },
      peTtm: {
        title: 'P/E (12 mois écoulés)',
        text: 'Combien d\u2019années de bénéfices actuels le marché accepte de payer pour l\u2019action.',
        formula: 'P/E = cours ÷ bénéfice par action (12 derniers mois)',
        levels: [
          { range: '< 15', label: 'potentiellement sous-évalué', tone: 'good' },
          { range: '15–30', label: 'valorisation normale', tone: 'neutral' },
          { range: '> 30', label: 'forte croissance déjà intégrée', tone: 'warn' },
        ],
      },
      peForward: {
        title: 'P/E forward',
        text: 'Même ratio mais basé sur les bénéfices estimés des 12 prochains mois : plus prospectif.',
        levels: [
          { range: 'forward < ttm', label: 'bénéfices attendus en hausse', tone: 'good' },
          { range: 'forward > ttm', label: 'bénéfices attendus en baisse', tone: 'warn' },
        ],
      },
      earnings: {
        title: 'Prochains résultats',
        text: 'Date de publication des prochains résultats trimestriels.',
        tip: 'Volatilité souvent accrue dans les 2 semaines précédentes : adapter la taille de position.',
      },
      analysis: {
        title: 'Analyse',
        text: 'Synthèse rédigée par le moteur de scoring : verdict, thèse d’investissement en une phrase, explication et stratégie d’exécution.',
        tip: 'À lire avec la décomposition du score ci-dessous.',
      },
      synthese: {
        title: 'Synthèse',
        text: 'Résumé express : verdict global, atout dominant et principal risque identifié.',
        tip: 'Le TL;DR de l’analyse, pour saisir la thèse d’un coup d’œil.',
      },
      scoreContribution: {
        title: 'Décomposition du score',
        text: 'Chaque facteur ajoute ou retire des points à partir d’une base neutre de 40/100. Plus la barre est longue, plus le facteur pèse.',
        levels: [
          { range: 'Vert →', label: 'facteur qui augmente le score', tone: 'good' },
          { range: '← Rouge', label: 'facteur qui diminue le score', tone: 'bad' },
        ],
        tip: 'Le score final est borné entre 0 et 100.',
      },
      forces: {
        title: 'Forces',
        text: 'Facteurs techniques qui soutiennent le titre et augmentent son score.',
        levels: [
          { range: 'Supports', label: 'cours sur un support clé (SMA 200j/50s)', tone: 'good' },
          { range: 'Survente', label: 'RSI bas, potentiel de rebond', tone: 'good' },
          { range: 'Momentum', label: 'MACD haussier, divergence', tone: 'good' },
          { range: 'Décote', label: 'loin sous le sommet 52 semaines', tone: 'good' },
        ],
        tip: 'Plus les forces sont nombreuses et lourdes, plus le score monte.',
      },
      watchpoints: {
        title: 'Points de vigilance',
        text: 'Facteurs de risque qui pèsent sur le score et appellent à la prudence.',
        levels: [
          { range: 'Sommets', label: 'cours proche du plus haut 52 semaines', tone: 'bad' },
          { range: 'Surachat', label: 'RSI étiré, risque de repli', tone: 'bad' },
          { range: 'Tendance', label: 'tendance de fond baissière', tone: 'bad' },
          { range: 'Volume', label: 'volume suspect ou évènementiel', tone: 'warn' },
        ],
        tip: 'Un dossier peut être solide tout en présentant des points de vigilance : peser les deux.',
      },
      context: {
        title: 'Contexte',
        text: 'Observations neutres, sans impact direct sur le score, fournies pour compléter le tableau.',
        tip: 'Informations de fond utiles, mais qui ne changent pas le verdict.',
      },
      chartRsi14: {
        title: 'RSI 14',
        text: 'Force du momentum : le titre est-il survendu (bon marché) ou suracheté (cher) ?',
        levels: [
          { range: '≤ 30', label: 'survendu (bande verte)', tone: 'good' },
          { range: '30–70', label: 'zone neutre', tone: 'neutral' },
          { range: '≥ 70', label: 'suracheté (bande rouge)', tone: 'bad' },
        ],
        tip: 'Les divergences prix / RSI sont détectées dans le graphique dédié plus bas.',
      },
      chartMacd: {
        title: 'MACD — histogramme',
        text: 'Mesure l\u2019élan de la tendance : accélère-t-elle ou s\u2019essouffle-t-elle ?',
        formula: 'Hist = MACD − Signal (moyennes mobiles exponentielles)',
        levels: [
          { range: 'barres vertes', label: 'momentum haussier', tone: 'good' },
          { range: 'barres rouges', label: 'momentum baissier', tone: 'bad' },
        ],
        tip: 'Un changement de couleur annonce un croisement MACD / Signal imminent.',
      },
      chartDiv: {
        title: 'Divergences prix / RSI',
        text: 'Écart entre la direction du prix et celle du RSI, annonçant souvent un retournement.',
        levels: [
          { range: '↑ Haussière', label: 'Prix fait un nouveau plus bas mais le RSI remonte → rebond probable', tone: 'good' },
          { range: '↓ Baissière', label: 'Prix fait un nouveau plus haut mais le RSI baisse → essoufflement', tone: 'bad' },
        ],
        tip: 'Signal de timing, à confirmer par le volume et la tendance de fond.',
      },
    },
  },
}

function _lookup(loc, key) {
  return key.split('.').reduce((o, k) => (o == null ? undefined : o[k]), messages[loc])
}

export function useI18n() {
  function t(key, params) {
    let val = _lookup(locale.value, key)
    if (val === undefined) val = _lookup('en', key)
    if (val === undefined) return key
    if (typeof val === 'string' && params) {
      return val.replace(/\{(\w+)\}/g, (_, k) => (params[k] ?? `{${k}}`))
    }
    return val
  }
  const localeName = computed(() => LOCALES.find(l => l.id === locale.value)?.id ?? 'en')
  return { locale, localeName, setLocale, LOCALES, t }
}
