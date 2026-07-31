import { ref, computed } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import { useQuery } from '@tanstack/vue-query'
import { useI18n } from './useI18n'
import { tickerService } from '../services/tickerService'
import type { Analysis, ScoreDetails } from '../types/analysis'
import type { ChartData, Fundamentals, News } from '../types/market'
import type { BacktestReport } from '../types/backtest'

export interface ScoreContribution {
  key: string
  val: number
  label: string
}

/**
 * Ticker analysis data layer: owns the active ticker, the TanStack queries
 * (analysis, chart, fundamentals, news, backtest) and the search action.
 * Kept out of App.vue to keep the root component focused on layout.
 */
export function useTickerAnalysis() {
  const { t, locale } = useI18n()

  const input        = ref('')
  const period       = ref('6mo')
  const activeTicker = ref('')      // currently analyzed ticker — drives the queries
  const forceReload  = ref(false)   // one-shot cache-bypass flag for a forced refresh
  const history      = useLocalStorage<string[]>('smm_history', [])

  const queryEnabled = computed(() => !!activeTicker.value)

  // Main analysis (localized) — re-fetched automatically on ticker/locale change.
  const tickerQuery = useQuery<Analysis>({
    queryKey: ['ticker', activeTicker, locale],
    enabled: queryEnabled,
    queryFn: () => tickerService.analysis(activeTicker.value, locale.value, forceReload.value),
  })
  // Chart — re-fetched automatically on ticker/period change (no page spinner).
  const chartQuery = useQuery<ChartData | null>({
    queryKey: ['chart', activeTicker, period],
    enabled: queryEnabled,
    queryFn: () => tickerService.chart(activeTicker.value, period.value, forceReload.value),
  })
  const fundamentalsQuery = useQuery<Fundamentals | null>({
    queryKey: ['fundamentals', activeTicker],
    enabled: queryEnabled,
    queryFn: () => tickerService.fundamentals(activeTicker.value, forceReload.value),
  })
  const newsQuery = useQuery<News | null>({
    queryKey: ['news', activeTicker],
    enabled: queryEnabled,
    queryFn: () => tickerService.news(activeTicker.value, forceReload.value),
  })
  const backtestQuery = useQuery<BacktestReport>({
    queryKey: ['backtest', activeTicker],
    enabled: queryEnabled,
    retry: false,
    queryFn: () => tickerService.backtest(activeTicker.value, forceReload.value),
  })

  // Map query state onto friendly names.
  const result       = computed(() => tickerQuery.data.value ?? null)
  const loading      = computed(() => queryEnabled.value && tickerQuery.isLoading.value)
  const error        = computed(() => tickerQuery.error.value?.message ?? null)
  const chartData    = computed(() => chartQuery.data.value ?? null)
  const chartLoading = computed(() => queryEnabled.value && chartQuery.isLoading.value)
  const fundamentals        = computed(() => fundamentalsQuery.data.value ?? null)
  const fundamentalsLoading = computed(() => queryEnabled.value && fundamentalsQuery.isLoading.value)
  const fundamentalsReady   = computed(() => queryEnabled.value && fundamentalsQuery.isFetched.value)
  const news         = computed(() => newsQuery.data.value ?? null)
  const newsLoading  = computed(() => queryEnabled.value && newsQuery.isLoading.value)
  const newsReady    = computed(() => queryEnabled.value && newsQuery.isFetched.value)
  const backtest        = computed(() => backtestQuery.data.value ?? null)
  const backtestLoading = computed(() => queryEnabled.value && backtestQuery.isLoading.value)
  const backtestError   = computed(() => backtestQuery.error.value?.message ?? null)

  // Score contributions, sorted by descending impact (for the signed bars).
  const scoreContribs = computed<ScoreContribution[]>(() => {
    const sd: ScoreDetails | undefined = result.value?.analysis?.score_details
    if (!sd) return []
    return Object.entries(sd)
      .map(([key, val]) => ({ key, val, label: t(`scoreComp.${key}`) as string }))
      .sort((a, b) => b.val - a.val)
  })
  const scoreContribMax = computed(() =>
    Math.max(1, ...scoreContribs.value.map(c => Math.abs(c.val)))
  )

  async function search(ticker: string | null = null, force = false): Promise<void> {
    const code = (ticker || input.value).trim().toUpperCase()
    if (!code) return
    input.value = code
    history.value = [code, ...history.value.filter(x => x !== code)].slice(0, 8)

    const sameTicker = activeTicker.value === code
    activeTicker.value = code
    // A new ticker changes the query keys → queries refetch on their own.
    // For the same ticker (re-run / forced refresh) we trigger explicitly.
    if (force || sameTicker) {
      forceReload.value = force
      try {
        await Promise.allSettled([
          tickerQuery.refetch(),
          chartQuery.refetch(),
          fundamentalsQuery.refetch(),
          newsQuery.refetch(),
          backtestQuery.refetch(),
        ])
      } finally {
        forceReload.value = false
      }
    }
  }

  return {
    input, period, activeTicker, history,
    result, loading, error,
    chartData, chartLoading,
    fundamentals, fundamentalsLoading, fundamentalsReady,
    news, newsLoading, newsReady,
    backtest, backtestLoading, backtestError,
    scoreContribs, scoreContribMax,
    search,
  }
}
