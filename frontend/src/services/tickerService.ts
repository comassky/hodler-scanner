// Ticker analysis endpoints (analysis, chart, fundamentals, news, backtest).
import { enc, getJson, getJsonOrNull, sendJson } from './http'
import type { Analysis, DashboardItem } from '../types/analysis'
import type { ChartData, Fundamentals, News } from '../types/market'
import type { BacktestReport } from '../types/backtest'
import type { LocaleId } from '../types/ui'

function withRefresh(url: string, refresh: boolean): string {
  if (!refresh) return url
  return url + (url.includes('?') ? '&' : '?') + 'refresh=true'
}

export const tickerService = {
  analysis(ticker: string, lang: LocaleId, refresh = false): Promise<Analysis> {
    return getJson<Analysis>(withRefresh(`/ticker/${enc(ticker)}?lang=${lang}`, refresh))
  },

  chart(ticker: string, period: string, refresh = false): Promise<ChartData | null> {
    return getJsonOrNull<ChartData>(withRefresh(`/ticker/${enc(ticker)}/chart?period=${period}`, refresh))
  },

  fundamentals(ticker: string, refresh = false): Promise<Fundamentals | null> {
    return getJsonOrNull<Fundamentals>(withRefresh(`/ticker/${enc(ticker)}/fundamentals`, refresh))
  },

  news(ticker: string, refresh = false): Promise<News | null> {
    return getJsonOrNull<News>(withRefresh(`/ticker/${enc(ticker)}/news`, refresh))
  },

  backtest(ticker: string, refresh = false): Promise<BacktestReport> {
    return getJson<BacktestReport>(withRefresh(`/ticker/${enc(ticker)}/backtest`, refresh))
  },

  /** Batch dashboard snapshot for a set of watchlist tickers. */
  dashboard(tickers: string[], lang: LocaleId): Promise<DashboardItem[]> {
    return sendJson<{ results: DashboardItem[] }>('/tickers', 'POST', { tickers, lang })
      .then(r => r.results)
  },
}
