<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import { useQuery } from '@tanstack/vue-query'
import AppHeader    from './components/AppHeader.vue'
import TickerSearch from './components/TickerSearch.vue'
import TickerCharts from './components/TickerCharts.vue'
import DashboardView from './components/DashboardView.vue'
import InfoTip       from './components/InfoTip.vue'
import { useWatchlist }  from './composables/useWatchlist.js'
import { useFormatters } from './composables/useFormatters.js'
import { useI18n } from './composables/useI18n.js'

// ── i18n ──────────────────────────────────────────────
const { t, locale } = useI18n()

// ── Navigation ────────────────────────────────────────────────────
const view = ref('analyse')

// ── Watchlist (singleton) ─────────────────────────────────────────
const { watchlist, toggle, has } = useWatchlist()

// ── Formatters ────────────────────────────────────────────────────
const {
  fmt, fmtPct,
  varColor, rsiClass, rsiBarClass, distClass, macdClass,
  scoreCompClass, scoreColorFor, tendanceBadgeClass,
} = useFormatters()

// ── Analysis state ─────────────────────────────────────────────────
const input        = ref('')
const period       = ref('1y')
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

// Map query state onto the names the template already uses.
const result       = computed(() => tickerQuery.data.value ?? null)
const loading      = computed(() => queryEnabled.value && tickerQuery.isLoading.value)
const error        = computed(() => tickerQuery.error.value?.message ?? null)
const chartData    = computed(() => chartQuery.data.value ?? null)
const chartLoading = computed(() => queryEnabled.value && chartQuery.isLoading.value)
const fundamentals = computed(() => fundamentalsQuery.data.value ?? null)
const news         = computed(() => newsQuery.data.value ?? null)

function timeAgo(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return ''
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  const rtf = new Intl.RelativeTimeFormat(locale.value, { numeric: 'auto' })
  if (s < 60) return rtf.format(-s, 'second')
  const m = Math.floor(s / 60); if (m < 60) return rtf.format(-m, 'minute')
  const h = Math.floor(m / 60); if (h < 24) return rtf.format(-h, 'hour')
  const j = Math.floor(h / 24); if (j < 30) return rtf.format(-j, 'day')
  const mo = Math.floor(j / 30); return rtf.format(-mo, 'month')
}

// ── Derived ───────────────────────────────────────────────────────
const d = computed(() => result.value)

const isWatchlisted = computed(() =>
  result.value ? has(result.value.ticker) : false
)

// ── Anchor navigation ─────────────────────────────────────────────
const navSections = computed(() => {
  const s = [
    { id: 'section-apercu',      label: t('sections.overview') },
    { id: 'section-graphiques',  label: t('sections.charts') },
    { id: 'section-indicateurs', label: t('sections.indicators') },
  ]
  if (fundamentals.value) s.push({ id: 'section-fondamentaux', label: t('sections.fundamentals') })
  if (news.value && news.value.items.length) s.push({ id: 'section-actualites', label: t('sections.news') })
  s.push({ id: 'section-analyse', label: t('sections.analysis') })
  if (scoreContribs.value.length) s.push({ id: 'section-score', label: t('sections.score') })
  if (d.value?.analysis?.diagnostics?.length) s.push({ id: 'section-forces', label: t('sections.forces') })
  return s
})

const activeSection = ref('section-apercu')
let _observer = null

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function setupSectionObserver() {
  _observer?.disconnect()
  const els = navSections.value
    .map(s => document.getElementById(s.id))
    .filter(Boolean)
  if (!els.length) return
  _observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter(e => e.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
    if (visible.length) activeSection.value = visible[0].target.id
  }, { rootMargin: '-100px 0px -55% 0px', threshold: 0 })
  els.forEach(el => _observer.observe(el))
}

watch(() => [result.value, fundamentals.value, news.value], () => {
  nextTick(setupSectionObserver)
})

onBeforeUnmount(() => _observer?.disconnect())

const scoreColor = computed(() => {
  const s = d.value?.analysis?.score ?? 0
  if (s >= 80) return { ring: 'ring-1 ring-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10', bar: 'bg-emerald-500', label: t('scoreLabel.strong') }
  if (s >= 60) return { ring: 'ring-1 ring-sky-500',     text: 'text-sky-400',     bg: 'bg-sky-500/10',     bar: 'bg-sky-500',     label: t('scoreLabel.accumulate') }
  if (s >= 40) return { ring: 'ring-1 ring-amber-500',   text: 'text-amber-400',   bg: 'bg-amber-500/10',  bar: 'bg-amber-500',   label: t('scoreLabel.watch') }
  return             { ring: 'ring-1 ring-red-500',      text: 'text-red-400',     bg: 'bg-red-500/10',     bar: 'bg-red-500',     label: t('scoreLabel.avoid') }
})

function fmtMarketCap(v) {
  if (v == null) return '—'
  if (v >= 1e12) return (v / 1e12).toFixed(2) + ' T'
  if (v >= 1e9)  return (v / 1e9).toFixed(2)  + ' Md'
  if (v >= 1e6)  return (v / 1e6).toFixed(2)  + ' M'
  return v.toLocaleString()
}

// Score contributions, sorted by descending impact (for the signed bars)
const scoreContribs = computed(() => {
  const sd = d.value?.analysis?.score_details
  if (!sd) return []
  return Object.entries(sd)
    .map(([key, val]) => ({ key, val, label: t(`scoreComp.${key}`) }))
    .sort((a, b) => b.val - a.val)
})
const scoreContribMax = computed(() =>
  Math.max(1, ...scoreContribs.value.map(c => Math.abs(c.val)))
)

// Diagnostics split into Strengths / Watch-outs / Context by their impact
const forces     = computed(() => (d.value?.analysis?.diagnostics ?? []).filter(x => x.impact > 0))
const vigilances = computed(() => (d.value?.analysis?.diagnostics ?? []).filter(x => x.impact < 0))
const neutres    = computed(() => (d.value?.analysis?.diagnostics ?? []).filter(x => x.impact === 0))

// ── Search ──────────────────────────────────────────────
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
      ])
    } finally {
      forceReload.value = false
    }
  }
}

// ── Dashboard → Analysis ──────────────────────────────────────────────
function goToAnalyse(ticker) {
  view.value = 'analyse'
  nextTick(() => search(ticker))
}
</script>

<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100">

    <AppHeader
      v-model:view="view"
      :watchlist-count="watchlist.length"
      :history="history"
      @search="search"
    />

    <!-- ═════ ANALYSIS ═══════════════════════════════════════════ -->
    <main v-if="view === 'analyse'" class="px-4 md:px-6 xl:px-8 py-8 pb-20">

      <!-- Search bar -->
      <div class="mb-6">
        <h1 class="text-xl font-bold tracking-tight mb-0.5">{{ t('app.title') }}</h1>
        <p class="text-zinc-500 text-sm mb-5">{{ t('app.subtitle') }}</p>
        <TickerSearch
          v-model="input"
          :loading="loading"
          :has-result="!!result"
          @search="search"
        />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center py-24 gap-4">
        <div class="w-10 h-10 rounded-full border-2 border-zinc-800 border-t-indigo-500 animate-spin"></div>
        <p class="text-zinc-500 text-sm">{{ t('app.loadingData') }}</p>
        <p class="text-zinc-600 text-xs">{{ t('app.loadingHint') }}</p>
      </div>

      <!-- Error -->
      <div v-else-if="error"
        class="flex items-start gap-3 bg-red-500/8 border border-red-500/25 rounded-xl px-4 py-4 text-red-400">
        <svg class="w-5 h-5 mt-0.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
        </svg>
        <div>
          <p class="font-medium text-sm">{{ t('app.error') }}</p>
          <p class="text-red-400/70 text-xs mt-0.5">{{ error }}</p>
        </div>
      </div>

      <!-- ── Result ───────────────────────────────────────────── -->
      <div v-else-if="d" class="space-y-3">

        <!-- Pinned anchor menu -->
        <nav class="sticky top-14 z-30 -mx-4 md:-mx-6 xl:-mx-8 px-4 md:px-6 xl:px-8 py-2 bg-zinc-950/85 backdrop-blur-md border-b border-zinc-800/60">
          <div class="flex gap-1 overflow-x-auto">
            <button v-for="s in navSections" :key="s.id" @click="scrollToSection(s.id)"
              :class="['px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors',
                activeSection === s.id
                  ? 'bg-indigo-500/15 text-indigo-300'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60']">
              {{ s.label }}
            </button>
          </div>
        </nav>

        <!-- 1. Header card — full width -->
        <div id="section-apercu" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div class="min-w-0 lg:max-w-md">
              <div class="flex flex-wrap items-center gap-2 mb-1">
                <span class="text-2xl font-bold tracking-tight font-mono">{{ d.ticker }}</span>
                <button @click="toggle(d.ticker)"
                  :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all border',
                    isWatchlisted
                      ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-400 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400'
                      : 'border-zinc-700 text-zinc-500 hover:border-indigo-500/40 hover:text-indigo-400']">
                  {{ isWatchlisted ? t('app.following') : t('app.follow') }}
                </button>
                <button @click="search(d.ticker, true)" :disabled="loading"
                  :title="t('app.refreshTitle')"
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border border-zinc-700 text-zinc-500 hover:border-indigo-500/40 hover:text-indigo-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                  <svg :class="['w-3 h-3', loading && 'animate-spin']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                  </svg>
                  {{ t('app.refresh') }}
                </button>
                <span v-if="d.data_partiel"
                  class="text-xs bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30 px-2 py-0.5 rounded-full">
                  {{ t('app.partialData') }}
                </span>
                <span v-if="d.cached"
                  class="text-xs bg-zinc-800 text-zinc-500 px-2 py-0.5 rounded-full">{{ t('app.cache') }}</span>
              </div>
              <p class="text-zinc-400 text-sm truncate mb-4">{{ d.name }}</p>
              <div class="flex items-baseline gap-3 flex-wrap">
                <span class="text-4xl font-bold tracking-tight font-mono">{{ fmt(d.price.last) }}</span>
                <span :class="['text-xl font-semibold font-mono', varColor(d.price.var_jour_pct)]">
                  {{ d.price.var_jour_pct >= 0 ? '+' : '' }}{{ fmt(d.price.var_jour_pct, 2) }}%
                </span>
                <span class="text-sm text-zinc-500">{{ t('app.today') }}</span>
              </div>
            </div>

            <!-- Quick summary (fills the space, actionable recap) -->
            <div v-if="d.analysis.synthese"
              class="hidden lg:block flex-1 self-center min-w-0 max-w-md border-l border-zinc-800 pl-6">
              <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-1.5">{{ t('app.inBrief') }}</p>
              <p :class="['text-sm font-semibold mb-2', scoreColor.text]">{{ d.analysis.synthese.verdict }}</p>
              <div class="space-y-1">
                <div v-if="d.analysis.synthese.atout" class="flex items-baseline gap-2 text-xs">
                  <span class="text-emerald-400 shrink-0">▲</span>
                  <span class="text-zinc-300 truncate">{{ d.analysis.synthese.atout }}</span>
                </div>
                <div v-if="d.analysis.synthese.risque" class="flex items-baseline gap-2 text-xs">
                  <span class="text-amber-400 shrink-0">▼</span>
                  <span class="text-zinc-300 truncate">{{ d.analysis.synthese.risque }}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2.5 shrink-0">
              <!-- Score ring -->
              <div :class="['flex flex-col items-center justify-center px-5 py-4 rounded-2xl', scoreColor.ring, scoreColor.bg]">
                <span :class="['text-4xl font-bold tabular-nums font-mono', scoreColor.text]">{{ d.analysis.score }}</span>
                <span class="text-zinc-500 text-xs mt-1">{{ t('app.outOf100') }}</span>
                <span :class="['text-xs font-semibold mt-2 tracking-wide', scoreColor.text]">{{ scoreColor.label }}</span>
                <div class="relative w-20 h-1 bg-zinc-800 rounded-full mt-3">
                  <div :class="['h-full rounded-full transition-all duration-700', scoreColor.bar]"
                       :style="{ width: d.analysis.score + '%' }"></div>
                  <div class="absolute top-0 h-full w-px bg-zinc-950/70" style="left:40%"></div>
                  <div class="absolute top-0 h-full w-px bg-zinc-950/70" style="left:60%"></div>
                  <div class="absolute top-0 h-full w-px bg-zinc-950/70" style="left:80%"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Signals -->
          <div class="mt-5 pt-4 border-t border-zinc-800">
            <div class="flex flex-wrap items-center gap-2">
              <span class="flex items-center text-[10px] uppercase tracking-wider text-zinc-500 mr-1">{{ t('app.signals') }}<InfoTip v-bind="t('info.signals')" /></span>
              <span :class="['inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium', tendanceBadgeClass(d.signals.tendance)]">
                {{ d.signals.tendance }}
              </span>
              <span v-if="d.signals.alerte_sma200"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/25">
                {{ t('app.alertSma200') }}
              </span>
              <span v-if="d.signals.alerte_w50"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/25">
                {{ t('app.alertW50') }}
              </span>
              <span v-if="d.indicators.macd_w_cross_up"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/25">
                {{ t('app.macdCross') }}
              </span>
              <span v-if="d.signals.divergence_rsi"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/25">
                {{ t('app.divergenceRsi') }}
                <span v-if="d.signals.rsi_creux" class="opacity-70 text-xs font-mono">
                  {{ fmt(d.signals.rsi_creux[0], 1) }} → {{ fmt(d.signals.rsi_creux[1], 1) }}
                </span>
              </span>
              <span v-if="d.fundamentals.dividende_annuel > 0"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-zinc-800 text-zinc-300 ring-1 ring-zinc-700/50">
                {{ t('app.dividend') }}
                <span class="font-semibold font-mono">{{ fmt(d.fundamentals.dividende_annuel) }}</span>
                <span class="text-zinc-500 text-xs">{{ d.fundamentals.derniere_date_div }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 2. Two-column: Charts (left) + Sidebar (right) -->
        <div id="section-graphiques" class="scroll-mt-28 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-3">

          <!-- Charts -->
          <TickerCharts v-model:period="period" :data="chartData" :loading="chartLoading" />

          <!-- Right sidebar -->
          <div class="space-y-3">

            <!-- Indicators -->
            <div id="section-indicateurs" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
              <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.indicators') }}<InfoTip v-bind="t('info.indicators')" /></h2>
              <div class="space-y-4">
                <!-- RSI Daily -->
                <div>
                  <div class="flex justify-between items-center mb-1.5">
                    <span class="flex items-center text-xs text-zinc-400">{{ t('ind.rsiDaily') }}<InfoTip v-bind="t('info.rsiDaily')" /></span>
                    <span :class="['text-sm font-semibold font-mono', rsiClass(d.indicators.rsi_daily)]">
                      {{ fmt(d.indicators.rsi_daily, 1) }}
                      <span class="text-xs opacity-60">
                        {{ d.indicators.rsi_daily <= 35 ? t('ind.oversold') : d.indicators.rsi_daily >= 70 ? t('ind.overbought') : t('ind.neutral') }}
                      </span>
                    </span>
                  </div>
                  <div class="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div class="absolute inset-y-0 left-0 bg-emerald-500/15 rounded-l-full" style="width:35%"></div>
                    <div class="absolute inset-y-0 right-0 bg-red-500/15 rounded-r-full" style="width:30%"></div>
                    <div :class="['absolute top-0 h-full w-1 rounded-full -translate-x-1/2', rsiBarClass(d.indicators.rsi_daily)]"
                         :style="{ left: Math.min(100, d.indicators.rsi_daily) + '%' }"></div>
                  </div>
                </div>
                <!-- RSI Weekly -->
                <div>
                  <div class="flex justify-between items-center mb-1.5">
                    <span class="flex items-center text-xs text-zinc-400">{{ t('ind.rsiWeekly') }}<InfoTip v-bind="t('info.rsiWeekly')" /></span>
                    <span :class="['text-sm font-semibold font-mono', rsiClass(d.indicators.rsi_weekly)]">{{ fmt(d.indicators.rsi_weekly, 1) }}</span>
                  </div>
                  <div class="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div class="absolute inset-y-0 left-0 bg-emerald-500/15 rounded-l-full" style="width:35%"></div>
                    <div class="absolute inset-y-0 right-0 bg-red-500/15 rounded-r-full" style="width:30%"></div>
                    <div :class="['absolute top-0 h-full w-1 rounded-full -translate-x-1/2', rsiBarClass(d.indicators.rsi_weekly)]"
                         :style="{ left: Math.min(100, d.indicators.rsi_weekly) + '%' }"></div>
                  </div>
                </div>
                <!-- BB %B -->
                <div>
                  <div class="flex justify-between items-center mb-1.5">
                    <span class="flex items-center text-xs text-zinc-400">{{ t('ind.bbPct') }}<InfoTip v-bind="t('info.bbPct')" /></span>
                    <span :class="['text-sm font-semibold font-mono', d.indicators.bb_pct < 0.2 ? 'text-emerald-400' : d.indicators.bb_pct > 0.8 ? 'text-amber-400' : 'text-zinc-300']">
                      {{ fmt(d.indicators.bb_pct, 3) }}
                    </span>
                  </div>
                  <div class="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div class="absolute inset-y-0 left-0 bg-emerald-500/15 rounded-l-full" style="width:20%"></div>
                    <div class="absolute inset-y-0 right-0 bg-amber-500/15 rounded-r-full" style="width:20%"></div>
                    <div class="absolute top-0 h-full w-1 bg-zinc-400 rounded-full -translate-x-1/2"
                         :style="{ left: Math.max(0, Math.min(100, d.indicators.bb_pct * 100)) + '%' }"></div>
                  </div>
                  <div class="flex justify-between text-zinc-700 text-xs mt-1 font-mono">
                    <span>0</span><span>0.5</span><span>1</span>
                  </div>
                </div>
                <!-- RVOL -->
                <div class="flex justify-between items-center">
                  <span class="flex items-center text-xs text-zinc-400">{{ t('ind.rvol') }}<InfoTip v-bind="t('info.rvol')" /></span>
                  <span :class="['text-sm font-semibold font-mono', d.indicators.rvol >= 2 ? 'text-amber-400' : d.indicators.rvol < 0.8 ? 'text-emerald-400' : 'text-zinc-300']">
                    {{ fmt(d.indicators.rvol, 2) }}×
                  </span>
                </div>
                <!-- MACD -->
                <div class="flex justify-between items-center">
                  <span class="flex items-center text-xs text-zinc-400">{{ t('ind.macdWeekly') }}<InfoTip v-bind="t('info.macdWeekly')" /></span>
                  <div class="flex items-center gap-2">
                    <span v-if="d.indicators.macd_w_cross_up"
                      class="text-xs bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded">{{ t('ind.crossUp') }}</span>
                    <span :class="['text-sm font-semibold font-mono', macdClass(d.indicators.macd_w_hist)]">
                      {{ d.indicators.macd_w_hist >= 0 ? '+' : '' }}{{ fmt(d.indicators.macd_w_hist, 4) }}
                    </span>
                  </div>
                </div>
                <!-- SMA slope -->
                <div class="flex justify-between items-center">
                  <span class="flex items-center text-xs text-zinc-400">{{ t('ind.smaSlope') }}<InfoTip v-bind="t('info.smaSlope')" /></span>
                  <span :class="['text-sm font-semibold font-mono', d.indicators.sma200_slope_20j_pct > 0.3 ? 'text-emerald-400' : d.indicators.sma200_slope_20j_pct < -0.3 ? 'text-red-400' : 'text-zinc-400']">
                    {{ d.indicators.sma200_slope_20j_pct >= 0 ? '+' : '' }}{{ fmt(d.indicators.sma200_slope_20j_pct, 2) }}%
                  </span>
                </div>
                <!-- ATR 14 -->
                <div v-if="d.indicators.atr14 != null" class="flex justify-between items-center border-t border-zinc-800/40 pt-2 mt-1">
                  <span class="flex items-center text-xs text-zinc-400">{{ t('ind.atr14') }}<InfoTip v-bind="t('info.atr14')" /></span>
                  <div class="flex items-center gap-1.5">
                    <span class="text-sm font-semibold font-mono text-zinc-300">{{ fmt(d.indicators.atr14) }}</span>
                    <span class="text-xs text-zinc-600">({{ fmt(d.indicators.atr14_pct, 1) }}%)</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Key levels -->
            <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
              <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.keyLevels') }}<InfoTip v-bind="t('info.keyLevels')" /></h2>
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <div>
                    <p class="flex items-center text-xs text-zinc-400">{{ t('ind.sma200d') }}<InfoTip v-bind="t('info.sma200')" /></p>
                    <p class="text-sm font-semibold text-zinc-200 font-mono">{{ fmt(d.indicators.sma200) }}</p>
                  </div>
                  <span :class="['text-sm font-semibold tabular-nums font-mono', distClass(d.distances.ecart_sma200_pct)]">
                    {{ fmtPct(d.distances.ecart_sma200_pct) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <div>
                    <p class="flex items-center text-xs text-zinc-400">{{ t('ind.sma50w') }}<InfoTip v-bind="t('info.sma50w')" /></p>
                    <p class="text-sm font-semibold text-zinc-200 font-mono">
                      {{ d.indicators.w50 !== null ? fmt(d.indicators.w50) : '—' }}
                    </p>
                  </div>
                  <span :class="['text-sm font-semibold tabular-nums font-mono', d.distances.ecart_w50_pct !== null ? distClass(d.distances.ecart_w50_pct) : 'text-zinc-500']">
                    {{ d.distances.ecart_w50_pct !== null ? fmtPct(d.distances.ecart_w50_pct) : '—' }}
                  </span>
                </div>
                <div class="border-t border-zinc-800 pt-3 flex justify-between items-center">
                  <div>
                    <p class="flex items-center text-xs text-zinc-400">{{ t('ind.high52') }}<InfoTip v-bind="t('info.high52')" /></p>
                    <p class="text-sm font-semibold text-zinc-200 font-mono">{{ fmt(d.distances.h52w_price) }}</p>
                  </div>
                  <span class="text-sm font-semibold tabular-nums text-red-400 font-mono">
                    {{ fmtPct(d.distances.dist_52w_high_pct) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <div>
                    <p class="flex items-center text-xs text-zinc-400">{{ t('ind.low52') }}<InfoTip v-bind="t('info.low52')" /></p>
                    <p class="text-sm font-semibold text-zinc-200 font-mono">{{ fmt(d.distances.l52w_price) }}</p>
                  </div>
                  <span class="text-sm font-semibold tabular-nums text-emerald-400 font-mono">
                    +{{ fmt(d.distances.dist_52w_low_pct, 1) }}%
                  </span>
                </div>
                <div class="border-t border-zinc-800 pt-3 flex justify-between items-center">
                  <span class="flex items-center text-xs text-zinc-400">{{ t('ind.sma50d') }}<InfoTip v-bind="t('info.sma50')" /></span>
                  <span class="text-sm font-semibold text-zinc-300 font-mono">{{ fmt(d.indicators.sma50) }}</span>
                </div>
              </div>
            </div>
          </div>
          <!-- /sidebar -->
        </div>
        <!-- /2-col -->

        <!-- Fundamentals (async) -->
        <div v-if="fundamentals" id="section-fondamentaux" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
          <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.fundamentals') }}<InfoTip v-bind="t('info.fundamentals')" /></h2>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-7 gap-3">
            <div v-if="fundamentals.market_cap">
              <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.marketCap') }}</p>
              <p class="text-sm font-semibold font-mono text-zinc-100">{{ fmtMarketCap(fundamentals.market_cap) }}</p>
            </div>
            <div v-if="fundamentals.pe_trailing != null">
              <p class="flex items-center text-xs text-zinc-500 mb-0.5">{{ t('fund.peTtm') }}<InfoTip v-bind="t('info.peTtm')" /></p>
              <p class="text-sm font-semibold font-mono text-zinc-100">{{ fmt(fundamentals.pe_trailing, 1) }}×</p>
            </div>
            <div v-if="fundamentals.pe_forward != null">
              <p class="flex items-center text-xs text-zinc-500 mb-0.5">{{ t('fund.peForward') }}<InfoTip v-bind="t('info.peForward')" /></p>
              <p class="text-sm font-semibold font-mono text-zinc-100">{{ fmt(fundamentals.pe_forward, 1) }}×</p>
            </div>
            <div v-if="fundamentals.sector">
              <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.sector') }}</p>
              <p class="text-sm text-zinc-200 truncate">{{ fundamentals.sector }}</p>
            </div>
            <div v-if="fundamentals.industry">
              <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.industry') }}</p>
              <p class="text-sm text-zinc-300 truncate">{{ fundamentals.industry }}</p>
            </div>
            <div v-if="fundamentals.country">
              <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.country') }}</p>
              <p class="text-sm text-zinc-200">{{ fundamentals.country }}</p>
            </div>
            <div v-if="fundamentals.earnings_date">
              <p class="flex items-center text-xs text-zinc-500 mb-0.5">{{ t('fund.earnings') }}<InfoTip v-bind="t('info.earnings')" /></p>
              <p class="text-sm font-semibold text-indigo-400">{{ fundamentals.earnings_date }}</p>
            </div>
          </div>
        </div>

        <!-- News -->
        <div v-if="news && news.items.length" id="section-actualites" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
          <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.news') }}<InfoTip v-bind="t('info.news')" /></h2>
          <ul class="space-y-1">
            <li v-for="(n, i) in news.items" :key="i">
              <a :href="n.url" target="_blank" rel="noopener noreferrer"
                 class="group flex gap-3 items-start hover:bg-zinc-800/40 rounded-lg -mx-2 px-2 py-2 transition-colors">
                <img v-if="n.thumbnail" :src="n.thumbnail" alt=""
                     class="w-14 h-14 rounded-lg object-cover shrink-0 bg-zinc-800" loading="lazy" />
                <div class="min-w-0 flex-1">
                  <p class="text-sm text-zinc-200 group-hover:text-white leading-snug line-clamp-2">{{ n.title }}</p>
                  <p class="text-xs text-zinc-500 mt-1">
                    <span v-if="n.publisher" class="text-zinc-400">{{ n.publisher }}</span>
                    <span v-if="n.publisher && timeAgo(n.published)"> · </span>
                    <span>{{ timeAgo(n.published) }}</span>
                  </p>
                </div>
                <svg class="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 shrink-0 mt-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17L17 7M17 7H8M17 7v9" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </a>
            </li>
          </ul>
        </div>

        <!-- 3. Analysis text — full width -->
        <div id="section-analyse" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
          <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.analysis') }}<InfoTip v-bind="t('info.analysis')" /></h2>
          <div v-if="d.analysis.synthese"
            :class="['rounded-xl p-4 mb-5 ring-1', scoreColor.bg, scoreColor.ring]">
            <div class="flex items-center gap-2 mb-3">
              <span :class="['w-1.5 h-1.5 rounded-full shrink-0', scoreColor.bar]"></span>
              <p :class="['text-sm font-bold tracking-wide', scoreColor.text]">{{ d.analysis.synthese.verdict }}</p>
              <InfoTip v-bind="t('info.synthese')" />
            </div>
            <div class="space-y-1.5 pl-3.5">
              <div v-if="d.analysis.synthese.atout" class="flex items-baseline gap-2.5 text-sm">
                <span class="text-emerald-400 text-xs shrink-0">▲</span>
                <span class="text-zinc-500 shrink-0 w-14">{{ t('app.asset') }}</span>
                <span class="text-zinc-200">{{ d.analysis.synthese.atout }}</span>
              </div>
              <div v-if="d.analysis.synthese.risque" class="flex items-baseline gap-2.5 text-sm">
                <span class="text-amber-400 text-xs shrink-0">▼</span>
                <span class="text-zinc-500 shrink-0 w-14">{{ t('app.risk') }}</span>
                <span class="text-zinc-200">{{ d.analysis.synthese.risque }}</span>
              </div>
            </div>
          </div>
          <div class="space-y-5">
            <div class="flex items-start gap-3">
              <div :class="['w-1.5 h-1.5 mt-2 rounded-full shrink-0', scoreColor.bar]"></div>
              <div>
                <p class="text-xs text-zinc-500 mb-1">{{ t('app.status') }}</p>
                <p class="text-zinc-100 font-semibold">{{ d.analysis.statut }}</p>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <div class="w-1.5 h-1.5 mt-2 rounded-full shrink-0 bg-zinc-600"></div>
              <div>
                <p class="text-xs text-zinc-500 mb-1">{{ t('app.explanation') }}</p>
                <p class="text-zinc-300 text-sm leading-relaxed">{{ d.analysis.explication }}</p>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <div class="w-1.5 h-1.5 mt-2 rounded-full shrink-0 bg-indigo-500"></div>
              <div>
                <p class="text-xs text-zinc-500 mb-1">{{ t('app.strategy') }}</p>
                <p class="text-zinc-300 text-sm leading-relaxed">{{ d.analysis.strategie }}</p>
              </div>
            </div>
            <div class="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800/50">
              <p class="text-xs text-zinc-500 mb-2">{{ t('app.targetsStop') }}</p>
              <p class="text-zinc-300 text-sm leading-relaxed whitespace-pre-line font-mono">{{ d.analysis.objectifs }}</p>
            </div>
          </div>
        </div>

        <!-- 4. Score breakdown — signed contribution bars -->
        <div v-if="scoreContribs.length" id="section-score"
          class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
          <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-1">{{ t('app.scoreContribution') }}<InfoTip v-bind="t('info.scoreContribution')" /></h2>
          <p class="text-xs text-zinc-600 mb-4">{{ t('app.neutralBase') }} <span class="font-mono text-zinc-500">40</span> · {{ t('app.result') }} <span :class="['font-mono font-semibold', scoreColor.text]">{{ d.analysis.score }}/100</span></p>
          <div class="space-y-1.5">
            <div v-for="c in scoreContribs" :key="c.key" class="flex items-center gap-2">
              <span class="w-20 shrink-0 text-xs text-zinc-400 text-right truncate">{{ c.label }}</span>
              <div class="relative flex-1 h-5">
                <div class="absolute inset-y-0 left-1/2 w-px bg-zinc-700/70"></div>
                <div v-if="c.val > 0" class="absolute inset-y-1 left-1/2 rounded-r bg-emerald-500/70"
                     :style="{ width: (c.val / scoreContribMax * 50) + '%' }"></div>
                <div v-else-if="c.val < 0" class="absolute inset-y-1 rounded-l bg-red-500/70"
                     :style="{ right: '50%', width: (Math.abs(c.val) / scoreContribMax * 50) + '%' }"></div>
                <div v-else class="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center">
                  <span class="w-1 h-1 rounded-full bg-zinc-600"></span>
                </div>
              </div>
              <span :class="['w-9 shrink-0 text-xs font-mono font-semibold text-right', scoreCompClass(c.val)]">
                {{ c.val > 0 ? '+' : '' }}{{ c.val }}
              </span>
            </div>
          </div>
        </div>

        <!-- 5. Strengths vs Watch-outs -->
        <div v-if="d.analysis.diagnostics?.length" id="section-forces"
          class="scroll-mt-28 grid grid-cols-1 md:grid-cols-2 gap-3">
          <!-- Strengths -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <h2 class="flex items-center text-xs font-semibold text-emerald-400/90 uppercase tracking-widest mb-4">
              {{ t('app.forces') }}
              <span class="ml-2 bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded text-xs">{{ forces.length }}</span>
              <InfoTip v-bind="t('info.forces')" />
            </h2>
            <ul v-if="forces.length" class="space-y-3">
              <li v-for="(diag, i) in forces" :key="i" class="flex gap-2.5 text-sm text-zinc-300 leading-relaxed">
                <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 bg-emerald-500"></span>
                <span class="flex-1">{{ diag.text }}</span>
                <span class="text-emerald-400 font-mono text-xs font-semibold shrink-0">+{{ diag.impact }}</span>
              </li>
            </ul>
            <p v-else class="text-sm text-zinc-600">{{ t('app.noForce') }}</p>
          </div>
          <!-- Watch-outs -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <h2 class="flex items-center text-xs font-semibold text-amber-400/90 uppercase tracking-widest mb-4">
              {{ t('app.watchpoints') }}
              <span class="ml-2 bg-amber-500/15 text-amber-400 px-1.5 py-0.5 rounded text-xs">{{ vigilances.length }}</span>
              <InfoTip v-bind="t('info.watchpoints')" />
            </h2>
            <ul v-if="vigilances.length" class="space-y-3">
              <li v-for="(diag, i) in vigilances" :key="i" class="flex gap-2.5 text-sm text-zinc-300 leading-relaxed">
                <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 bg-red-500"></span>
                <span class="flex-1">{{ diag.text }}</span>
                <span class="text-red-400 font-mono text-xs font-semibold shrink-0">{{ diag.impact }}</span>
              </li>
            </ul>
            <p v-else class="text-sm text-zinc-600">{{ t('app.noRisk') }}</p>
          </div>
          <!-- Neutral context -->
          <div v-if="neutres.length" class="md:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">{{ t('app.context') }}<InfoTip v-bind="t('info.context')" /></h2>
            <ul class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
              <li v-for="(diag, i) in neutres" :key="i" class="flex gap-2.5 text-sm text-zinc-400 leading-relaxed">
                <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 bg-zinc-600"></span>
                <span>{{ diag.text }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Footer meta -->
        <div class="flex justify-between items-center text-xs text-zinc-700 px-1 pt-1">
          <span>{{ d.days_available }} {{ t('app.sessions') }}</span>
          <span>{{ new Date(d.timestamp).toLocaleString(locale, { dateStyle: 'short', timeStyle: 'short' }) }}</span>
        </div>
      </div>
      <!-- /result -->
    </main>

    <!-- ═════ DASHBOARD ═══════════════════════════════════════════ -->
    <DashboardView
      v-else-if="view === 'watchlist'"
      @analyse="goToAnalyse"
    />

  </div>
</template>
