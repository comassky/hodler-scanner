import { ref, watch } from 'vue'

const LS_KEY = 'smm_watchlist'

// Singleton — shared across all components that call useWatchlist()
// Initialized from the localStorage cache for immediate display, then
// synced with the backend (source of truth: SQLite).
const watchlist = ref(
  JSON.parse(localStorage.getItem(LS_KEY) || '[]')
)

// Local mirror (offline cache / instant display on next load)
watch(watchlist, v => localStorage.setItem(LS_KEY, JSON.stringify(v)), { deep: true })

async function _json(url, options) {
  const res = await fetch(url, options)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Initial load from the server (+ localStorage migration if empty server-side)
const ready = (async () => {
  try {
    let { favorites } = await _json('/favorites')
    if (!favorites.length && watchlist.value.length) {
      // No server data but a local list exists: migrate it.
      favorites = (await _json('/favorites', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers: watchlist.value }),
      })).favorites
    }
    watchlist.value = favorites
  } catch {
    // Backend unavailable: keep the localStorage cache.
  }
})()

export function useWatchlist() {
  async function add(code) {
    if (!code) return
    code = code.toUpperCase()
    if (watchlist.value.includes(code)) return
    watchlist.value = [...watchlist.value, code] // optimistic
    try {
      const { favorites } = await _json(`/favorites/${encodeURIComponent(code)}`, { method: 'POST' })
      watchlist.value = favorites
    } catch { /* keep the optimistic state */ }
  }

  async function remove(ticker) {
    watchlist.value = watchlist.value.filter(t => t !== ticker) // optimistic
    try {
      const { favorites } = await _json(`/favorites/${encodeURIComponent(ticker)}`, { method: 'DELETE' })
      watchlist.value = favorites
    } catch { /* keep the optimistic state */ }
  }

  function toggle(ticker) {
    watchlist.value.includes(ticker) ? remove(ticker) : add(ticker)
  }

  function has(ticker) {
    return watchlist.value.includes(ticker)
  }

  return { watchlist, add, remove, toggle, has, ready }
}
