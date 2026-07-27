import { ref, computed } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import { useQuery } from '@tanstack/vue-query'
import { useI18n } from './useI18n.js'

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
  const history      = useLocalStorage('smm_history', [])

  const enc = s => encodeURIComponent(s)
  function withRefresh(url) {
    if (!forceReload.value) return url
    return url + (url.includes('?') ? '&' : '?') + 'refresh=true'
  }
  const queryEnabled = computed(() => !!activeTicker.value)

  // Main analysis (localized) — re-fetched automatically on ticker/locale change.
  const tickerQuery = useQuery({
    queryKey: ['ticker', activeTicker, locale],
    enabled: queryEnabled,
    queryFn: async () => {
      const r = await fetch(withRefresh(`/ticker/${enc(activeTicker.value)}?lang=${locale.value}`))
      if (!r.ok) throw new Error(((await r.json().catch(() => ({}))).detail) ?? `HTTP ${r.status}`)
      return r.json()
    },
  })
  // Chart — re-fetched automatically on ticker/period change (no page spinner).
  const chartQuery = useQuery({
    queryKey: ['chart', activeTicker, period],
    enabled: queryEnabled,
    queryFn: async () => {
      const r = await fetch(withRefresh(`/ticker/${enc(activeTicker.value)}/chart?period=${period.value}`))
      return r.ok ? r.json() : null
    },
  })
  const fundamentalsQuery = useQuery({
    queryKey: ['fundamentals', activeTicker],
    enabled: queryEnabled,
    queryFn: async () => {
      const r = await fetch(withRefresh(`/ticker/${enc(activeTicker.value)}/fundamentals`))
      return r.ok ? r.json() : null
    },
  })
  const newsQuery = useQuery({
    queryKey: ['news', activeTicker],
    enabled: queryEnabled,
    queryFn: async () => {
      const r = await fetch(withRefresh(`/ticker/${enc(activeTicker.value)}/news`))
      return r.ok ? r.json() : null
    },
  })
  const backtestQuery = useQuery({
    queryKey: ['backtest', activeTicker],
    enabled: queryEnabled,
    retry: false,
    queryFn: async () => {
      const r = await fetch(withRefresh(`/ticker/${enc(activeTicker.value)}/backtest`))
      if (!r.ok) throw new Error(((await r.json().catch(() => ({}))).detail) ?? `HTTP ${r.status}`)
      return r.json()
    },
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
  const scoreContribs = computed(() => {
    const sd = result.value?.analysis?.score_details
    if (!sd) return []
    return Object.entries(sd)
      .map(([key, val]) => ({ key, val, label: t(`scoreComp.${key}`) }))
      .sort((a, b) => b.val - a.val)
  })
  const scoreContribMax = computed(() =>
    Math.max(1, ...scoreContribs.value.map(c => Math.abs(c.val)))
  )

  async function search(ticker, force = false) {
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
