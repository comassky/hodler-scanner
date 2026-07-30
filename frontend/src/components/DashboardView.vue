<script setup>
import { ref, computed } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import DashboardCard from './DashboardCard.vue'
import { useWatchlist } from '../composables/useWatchlist.js'
import { useI18n } from '../composables/useI18n.js'

const emit = defineEmits(['analyse'])

const { watchlist, add, remove } = useWatchlist()
const { t, locale } = useI18n()
const queryClient = useQueryClient()
const wlInput     = ref('')

const SORTS = ['scoreDesc', 'scoreAsc', 'changeDesc', 'nameAsc']
const sortBy = useLocalStorage('smm_dash_sort', 'scoreDesc')

// Batch dashboard data — cached & auto-refreshed every 5 min (foreground only).
// Keyed by locale so a language switch re-fetches the translated analysis text.
// Not keyed by the watchlist: adding a ticker shows a stub until it is loaded,
// matching the original behaviour (explicit "Load" / "Refresh all").
const dashKey = computed(() => ['dashboard', locale.value])
const { data, isLoading, isFetching, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: dashKey,
  enabled: computed(() => watchlist.value.length > 0),
  refetchInterval: 5 * 60 * 1000,
  refetchIntervalInBackground: false,
  queryFn: async () => {
    const res = await fetch('/tickers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers: watchlist.value, lang: locale.value }),
    })
    if (!res.ok) throw new Error(t('dash.serverError'))
    return (await res.json()).results
  },
})

const dashData    = computed(() => data.value ?? [])
const dashLoading = computed(() => isLoading.value)   // skeleton on first load only
const refreshing  = computed(() => isFetching.value)  // button feedback on any fetch
const dashError   = computed(() => error.value?.message ?? null)
const lastRefresh = computed(() => (dataUpdatedAt.value ? new Date(dataUpdatedAt.value) : null))

// Sorted cards: by default descending score; errors always at the end
const sortedData = computed(() => {
  const score = d => d?.analysis?.score ?? -Infinity
  const change = d => d?.price?.var_jour_pct ?? -Infinity
  return [...dashData.value].sort((a, b) => {
    if (a.error !== b.error) return a.error ? 1 : -1
    if (a.error && b.error) return a.ticker.localeCompare(b.ticker)
    switch (sortBy.value) {
      case 'scoreAsc':   return score(a) - score(b)
      case 'changeDesc': return change(b) - change(a)
      case 'nameAsc':    return (a.name || a.ticker).localeCompare(b.name || b.ticker)
      default:           return score(b) - score(a)
    }
  })
})

const loadedTickers   = computed(() => new Set(dashData.value.map(d => d.ticker)))
const unloadedTickers = computed(() => watchlist.value.filter(t => !loadedTickers.value.has(t)))

function loadDashboard() { refetch() }

function removeCard(ticker) {
  remove(ticker)
  // Drop the card from the cache without a full refetch.
  queryClient.setQueryData(dashKey.value, old => (old ?? []).filter(r => r.ticker !== ticker))
}

function addWlInput() {
  const code = wlInput.value.trim().toUpperCase()
  if (!code || watchlist.value.includes(code)) { wlInput.value = ''; return }
  add(code)
  wlInput.value = ''
}

// Expose reload for parent (header button etc.)
defineExpose({ reload: loadDashboard })
</script>

<template>
  <div class="px-4 md:px-6 xl:px-8 py-8 pb-20">

    <!-- Header row -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-xl font-bold tracking-tight">{{ t('dash.title') }}</h1>
        <p class="text-zinc-500 text-sm">
          {{ watchlist.length }} {{ watchlist.length > 1 ? t('dash.stocksWatched') : t('dash.stockWatched') }}
        </p>
      </div>
      <div class="flex flex-col items-end gap-1.5 self-start sm:self-auto">
        <div class="flex items-center gap-2">
          <label class="relative">
            <select v-model="sortBy"
              class="appearance-none bg-zinc-800 hover:bg-zinc-700 text-zinc-300 pl-3 pr-8 py-2 rounded-xl text-sm transition-colors cursor-pointer focus:outline-none focus:border-indigo-500/50 border border-transparent"
              :title="t('dash.sortBy')">
              <option v-for="s in SORTS" :key="s" :value="s">{{ t('dash.sort.' + s) }}</option>
            </select>
            <svg class="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
            </svg>
          </label>
          <button @click="loadDashboard()" :disabled="refreshing"
            class="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-300 px-4 py-2 rounded-xl text-sm transition-colors">
            <svg class="w-4 h-4" :class="refreshing ? 'animate-spin' : ''"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            {{ t('dash.refreshAll') }}
          </button>
        </div>
        <p v-if="lastRefresh" class="text-xs text-zinc-600">
          {{ t('dash.updatedAt', { t: lastRefresh.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' }) }) }}
        </p>
      </div>
    </div>

    <!-- Add ticker -->
    <div class="flex gap-2 mb-6 max-w-sm">
      <input v-model="wlInput" @keyup.enter="addWlInput()"
        :placeholder="t('dash.addPlaceholder')"
        class="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2.5 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50 text-sm font-mono transition-colors" />
      <button @click="addWlInput()"
        class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-4 py-2.5 rounded-xl text-sm transition-colors whitespace-nowrap">
        {{ t('dash.add') }}
      </button>
    </div>

    <!-- Error -->
    <div v-if="dashError"
      class="text-red-400 text-sm mb-4 bg-red-500/8 border border-red-500/20 rounded-xl px-4 py-3">
      {{ dashError }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="dashLoading"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
      <div v-for="t in watchlist" :key="t"
        class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 h-52 animate-pulse">
        <div class="h-4 bg-zinc-800 rounded w-16 mb-2"></div>
        <div class="h-3 bg-zinc-800 rounded w-32 mb-4"></div>
        <div class="h-8 bg-zinc-800 rounded w-24 mb-4"></div>
        <div class="space-y-2">
          <div class="h-3 bg-zinc-800 rounded w-full"></div>
          <div class="h-3 bg-zinc-800 rounded w-3/4"></div>
          <div class="h-3 bg-zinc-800 rounded w-4/5"></div>
        </div>
      </div>
    </div>

    <!-- Cards grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">

      <DashboardCard
        v-for="item in sortedData" :key="item.ticker"
        :item="item"
        @analyse="$emit('analyse', $event)"
        @remove="removeCard" />

      <!-- Unloaded stubs -->
      <div v-for="ticker in unloadedTickers" :key="'stub-' + ticker"
        class="bg-zinc-900 border border-zinc-800 border-dashed rounded-2xl p-4 flex flex-col items-center justify-center gap-2 h-52 text-center">
        <p class="font-mono font-bold text-zinc-400 text-sm">{{ ticker }}</p>
        <p class="text-xs text-zinc-600">{{ t('dash.notLoaded') }}</p>
        <button @click="loadDashboard()" class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors mt-1">
          {{ t('dash.load') }}
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!watchlist.length" class="text-center py-24">
      <p class="text-zinc-500 text-sm">{{ t('dash.emptyTitle') }}</p>
      <p class="text-zinc-600 text-xs mt-2">{{ t('dash.emptyHint') }}</p>
    </div>
  </div>
</template>
