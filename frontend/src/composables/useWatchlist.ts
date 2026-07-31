import { useLocalStorage } from '@vueuse/core'
import type { Ref } from 'vue'
import { watchlistService } from '../services/watchlistService'

const LS_KEY = 'smm_watchlist'

// Singleton — shared across all components that call useWatchlist().
// Initialized from the localStorage cache for immediate display, then synced
// with the backend (source of truth: SQLite). useLocalStorage keeps the ref
// and localStorage mirror in sync automatically.
const watchlist = useLocalStorage<string[]>(LS_KEY, [])

// Initial load from the server (+ localStorage migration if empty server-side).
const ready: Promise<void> = (async () => {
  try {
    let favorites = await watchlistService.list()
    if (!favorites.length && watchlist.value.length) {
      favorites = await watchlistService.replace(watchlist.value)
    }
    watchlist.value = favorites
  } catch {
    // Backend unavailable: keep the localStorage cache.
  }
})()

export interface UseWatchlist {
  watchlist: Ref<string[]>
  add: (code: string) => Promise<void>
  remove: (ticker: string) => Promise<void>
  toggle: (ticker: string) => void
  has: (ticker: string) => boolean
  reset: () => void
  ready: Promise<void>
}

export function useWatchlist(): UseWatchlist {
  async function add(code: string): Promise<void> {
    if (!code) return
    code = code.toUpperCase()
    if (watchlist.value.includes(code)) return
    watchlist.value = [...watchlist.value, code] // optimistic
    try {
      watchlist.value = await watchlistService.add(code)
    } catch { /* keep the optimistic state */ }
  }

  async function remove(ticker: string): Promise<void> {
    watchlist.value = watchlist.value.filter(t => t !== ticker) // optimistic
    try {
      watchlist.value = await watchlistService.remove(ticker)
    } catch { /* keep the optimistic state */ }
  }

  function toggle(ticker: string): void {
    if (watchlist.value.includes(ticker)) remove(ticker)
    else add(ticker)
  }

  function has(ticker: string): boolean {
    return watchlist.value.includes(ticker)
  }

  // Clear the local watchlist mirror (used after a server-side data reset).
  function reset(): void {
    watchlist.value = []
  }

  return { watchlist, add, remove, toggle, has, reset, ready }
}
