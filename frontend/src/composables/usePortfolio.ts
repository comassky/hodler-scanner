import { computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { portfolioService } from '../services/portfolioService'
import type { Portfolio } from '../types/portfolio'

/**
 * Portfolio data layer: live-valued positions persisted server-side (SQLite).
 * Mutations write to the API and patch the query cache from the response.
 */
const KEY = ['portfolio'] as const

export function usePortfolio() {
  const qc = useQueryClient()

  const { data, isLoading, isFetching, error, refetch, dataUpdatedAt } = useQuery<Portfolio>({
    queryKey: KEY,
    refetchInterval: 5 * 60 * 1000,      // refresh valuation every 5 min (foreground)
    refetchIntervalInBackground: false,
    queryFn: portfolioService.get,
  })

  const positions   = computed(() => data.value?.positions ?? [])
  const totals      = computed(() => data.value?.totals ?? null)
  const loading     = computed(() => isLoading.value)
  const refreshing  = computed(() => isFetching.value)
  const errorMsg    = computed(() => error.value?.message ?? null)
  const lastRefresh = computed(() => (dataUpdatedAt.value ? new Date(dataUpdatedAt.value) : null))

  async function upsert(
    ticker: string,
    quantity: number | string,
    avgCost: number | string,
    note: string | null = null,
  ): Promise<void> {
    const code = (ticker || '').trim().toUpperCase()
    if (!code) return
    try {
      const updated = await portfolioService.upsert(code, {
        quantity: Number(quantity),
        avg_cost: Number(avgCost),
        note,
      })
      qc.setQueryData(KEY, updated)
    } catch {
      refetch()
    }
  }

  async function remove(ticker: string): Promise<void> {
    try {
      qc.setQueryData(KEY, await portfolioService.remove(ticker))
    } catch {
      refetch()
    }
  }

  return { positions, totals, loading, refreshing, errorMsg, lastRefresh, refetch, upsert, remove }
}
