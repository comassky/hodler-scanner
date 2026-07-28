import { computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'

/**
 * Portfolio data layer: live-valued positions persisted server-side (SQLite).
 * Mutations write to the API and patch the query cache from the response.
 */
const KEY = ['portfolio']

export function usePortfolio() {
  const qc = useQueryClient()

  const { data, isLoading, isFetching, error, refetch, dataUpdatedAt } = useQuery({
    queryKey: KEY,
    refetchInterval: 5 * 60 * 1000,      // refresh valuation every 5 min (foreground)
    refetchIntervalInBackground: false,
    queryFn: async () => {
      const r = await fetch('/portfolio')
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json()
    },
  })

  const positions   = computed(() => data.value?.positions ?? [])
  const totals      = computed(() => data.value?.totals ?? null)
  const loading     = computed(() => isLoading.value)
  const refreshing  = computed(() => isFetching.value)
  const errorMsg    = computed(() => error.value?.message ?? null)
  const lastRefresh = computed(() => (dataUpdatedAt.value ? new Date(dataUpdatedAt.value) : null))

  async function upsert(ticker, quantity, avgCost, note = null) {
    const code = (ticker || '').trim().toUpperCase()
    if (!code) return
    const r = await fetch(`/portfolio/${encodeURIComponent(code)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: Number(quantity), avg_cost: Number(avgCost), note }),
    })
    if (r.ok) qc.setQueryData(KEY, await r.json())
    else refetch()
  }

  async function remove(ticker) {
    const r = await fetch(`/portfolio/${encodeURIComponent(ticker)}`, { method: 'DELETE' })
    if (r.ok) qc.setQueryData(KEY, await r.json())
    else refetch()
  }

  return { positions, totals, loading, refreshing, errorMsg, lastRefresh, refetch, upsert, remove }
}
