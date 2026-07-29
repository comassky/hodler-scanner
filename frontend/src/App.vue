<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount, onMounted } from 'vue'
import AppHeader      from './components/AppHeader.vue'
import TickerSearch   from './components/TickerSearch.vue'
import SearchModal    from './components/SearchModal.vue'
import TickerCharts   from './components/TickerCharts.vue'
import DashboardView  from './components/DashboardView.vue'
import PortfolioView  from './components/PortfolioView.vue'
import ResetModal     from './components/ResetModal.vue'
import NewsList       from './components/NewsList.vue'
import BacktestPanel  from './components/BacktestPanel.vue'
import AnalysisOverview  from './components/analysis/AnalysisOverview.vue'
import EntryTiming       from './components/analysis/EntryTiming.vue'
import ScoreHistory      from './components/analysis/ScoreHistory.vue'
import StrategyBacktest  from './components/analysis/StrategyBacktest.vue'
import IndicatorsCard    from './components/analysis/IndicatorsCard.vue'
import KeyLevelsCard     from './components/analysis/KeyLevelsCard.vue'
import FundamentalsCard  from './components/analysis/FundamentalsCard.vue'
import AnalysisNarrative from './components/analysis/AnalysisNarrative.vue'
import ScoreBreakdown    from './components/analysis/ScoreBreakdown.vue'
import DiagnosticsCards  from './components/analysis/DiagnosticsCards.vue'
import { useWatchlist }      from './composables/useWatchlist.js'
import { useI18n }           from './composables/useI18n.js'
import { useTickerAnalysis } from './composables/useTickerAnalysis.js'
import { useQueryClient }    from '@tanstack/vue-query'

// ── i18n ──────────────────────────────────────────────
const { t, locale } = useI18n()

// App version — injected at build time by Vite (see vite.config.js).
/* global __APP_VERSION__ */
const appVersion = __APP_VERSION__

// ── Navigation ────────────────────────────────────────────────────
const view = ref('watchlist')

// ── Watchlist (singleton) ─────────────────────────────────────────
const { watchlist, toggle, has, reset: resetWatchlist } = useWatchlist()

const queryClient = useQueryClient()

// ── Analysis data layer ───────────────────────────────────────────
const {
  input, period, history,
  result: d, loading, error,
  chartData, chartLoading,
  fundamentals, fundamentalsLoading, fundamentalsReady,
  news, newsLoading, newsReady,
  backtest, backtestLoading, backtestError,
  scoreContribs, scoreContribMax,
  search,
} = useTickerAnalysis()

const isWatchlisted = computed(() => (d.value ? has(d.value.ticker) : false))

// ── Anchor navigation ─────────────────────────────────────────────
const navSections = computed(() => {
  const s = [
    { id: 'section-apercu',      label: t('sections.overview') },
    { id: 'section-timing',      label: t('sections.timing') },
  ]
  if (backtest.value?.timing) s.push({ id: 'section-scorehist', label: t('sections.scoreHist') })
  s.push({ id: 'section-graphiques',  label: t('sections.charts') })
  s.push({ id: 'section-indicateurs', label: t('sections.indicators') })
  if (fundamentals.value) s.push({ id: 'section-fondamentaux', label: t('sections.fundamentals') })
  s.push({ id: 'section-analyse', label: t('sections.analysis') })
  if (scoreContribs.value.length) s.push({ id: 'section-score', label: t('sections.score') })
  if (d.value?.analysis?.diagnostics?.length) s.push({ id: 'section-forces', label: t('sections.forces') })
  s.push({ id: 'section-backtest', label: t('sections.backtest') })
  if (backtest.value) s.push({ id: 'section-strategy', label: t('sections.strategy') })
  if (news.value && news.value.items.length) s.push({ id: 'section-actualites', label: t('sections.news') })
  return s
})

const activeSection = ref('section-apercu')
let _observer = null

function scrollToSection(id) {
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  document.getElementById(id)?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
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

watch(() => [d.value, fundamentals.value, news.value, backtest.value], () => {
  nextTick(setupSectionObserver)
})

onBeforeUnmount(() => _observer?.disconnect())

// ── Dashboard → Analysis ──────────────────────────────────────────
function goToAnalyse(ticker) {
  view.value = 'analyse'
  nextTick(() => search(ticker))
}

// ── Reset (selective clear of caches + DB rows) ─────────────────
const resetModalOpen = ref(false)
async function onResetConfirm(options, done) {
  try {
    const res = await fetch('/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    if (options.watchlist) resetWatchlist()
    await queryClient.invalidateQueries()
    if (options.portfolio && view.value === 'portfolio') view.value = 'watchlist'
  } catch (e) {
    window.alert(t('reset.error'))
  } finally {
    done?.()
  }
}

// ── Global quick-search modal (Ctrl/Cmd + F) ──────────────────────
const searchModalOpen = ref(false)

function isTypingTarget(el) {
  if (!el) return false
  const tag = el.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable
}

function onGlobalKeydown(e) {
  // Open our ticker/ISIN quick-search with Cmd/Ctrl+K (the industry-standard
  // command-palette shortcut), or "/" when the user isn't already typing in a
  // field. The browser's native Cmd/Ctrl+F ("find in page") is left untouched.
  const openByCmdK = (e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')
  const openBySlash = e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey && !isTypingTarget(e.target)
  if (openByCmdK || openBySlash) {
    e.preventDefault()
    searchModalOpen.value = true
  }
}

function onModalSearch(ticker) {
  view.value = 'analyse'
  nextTick(() => search(ticker))
}

onMounted(() => window.addEventListener('keydown', onGlobalKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onGlobalKeydown))
</script>

<template>
  <div class="min-h-screen flex flex-col bg-zinc-950 text-zinc-100">

    <AppHeader
      v-model:view="view"
      :watchlist-count="watchlist.length"
      :history="history"
      @search="search"
      @open-search="searchModalOpen = true"
      @reset="resetModalOpen = true"
    />
    <!-- ═════ ANALYSIS ═══════════════════════════════════════════ -->
    <main v-if="view === 'analyse'" class="flex-1 px-4 md:px-6 xl:px-8 py-8 pb-20">

      <!-- Search bar -->
      <div class="mb-6">
        <h1 class="text-xl font-bold tracking-tight mb-0.5">{{ t('app.title') }}</h1>
        <p class="text-zinc-500 text-sm mb-5">{{ t('app.subtitle') }}</p>
        <TickerSearch
          v-model="input"
          :loading="loading"
          :has-result="!!d"
          @search="search"
        />
      </div>

      <!-- Loading — skeleton mirroring the result layout (perceived speed, no CLS) -->
      <div v-if="loading" class="space-y-3" aria-busy="true" aria-live="polite">
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
          <div class="flex items-center gap-4">
            <div class="h-10 w-44 rounded-lg bg-zinc-800/60 animate-pulse"></div>
            <div class="h-10 w-24 rounded-lg bg-zinc-800/60 animate-pulse ml-auto"></div>
          </div>
          <div class="h-24 rounded-xl bg-zinc-800/40 animate-pulse"></div>
        </div>
        <div class="h-28 rounded-2xl bg-zinc-900 border border-zinc-800 animate-pulse"></div>
        <div class="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-3">
          <div class="h-80 rounded-2xl bg-zinc-900 border border-zinc-800 animate-pulse"></div>
          <div class="space-y-3">
            <div class="h-36 rounded-2xl bg-zinc-900 border border-zinc-800 animate-pulse"></div>
            <div class="h-36 rounded-2xl bg-zinc-900 border border-zinc-800 animate-pulse"></div>
          </div>
        </div>
        <p class="text-center text-zinc-600 text-xs pt-2">{{ t('app.loadingData') }}</p>
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
          <div class="flex gap-1 overflow-x-auto scroll-fade-x">
            <button v-for="s in navSections" :key="s.id" @click="scrollToSection(s.id)"
              :class="['px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors',
                activeSection === s.id
                  ? 'bg-indigo-500/15 text-indigo-300'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60']">
              {{ s.label }}
            </button>
          </div>
        </nav>

        <!-- 1. Overview header + signals -->
        <AnalysisOverview
          :data="d"
          :is-watchlisted="isWatchlisted"
          :loading="loading"
          @toggle="toggle"
          @refresh="search($event, true)"
        />

        <!-- 1b. Entry timing — is now a good moment to buy & hold? -->
        <EntryTiming :data="backtest" :loading="backtestLoading" />

        <!-- 1c. Score history — where does today's score sit vs its own past? -->
        <ScoreHistory :data="backtest" :loading="backtestLoading" />

        <!-- 2. Two-column: Charts (left) + Sidebar (right) -->
        <div id="section-graphiques" class="scroll-mt-28 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-3">
          <TickerCharts v-model:period="period" :data="chartData" :loading="chartLoading" />
          <div class="space-y-3">
            <IndicatorsCard :indicators="d.indicators" />
            <KeyLevelsCard :indicators="d.indicators" :distances="d.distances" />
          </div>
        </div>

        <!-- Fundamentals (async) -->
        <FundamentalsCard
          v-if="fundamentalsLoading || fundamentalsReady"
          :fundamentals="fundamentals"
          :loading="fundamentalsLoading"
        />

        <!-- 3. Analysis narrative -->
        <AnalysisNarrative :analysis="d.analysis" />

        <!-- 4. Score breakdown -->
        <ScoreBreakdown
          v-if="scoreContribs.length"
          :contribs="scoreContribs"
          :max="scoreContribMax"
          :score="d.analysis.score"
        />

        <!-- 5. Strengths vs Watch-outs -->
        <DiagnosticsCards
          v-if="d.analysis.diagnostics?.length"
          :diagnostics="d.analysis.diagnostics"
        />

        <!-- Backtest — score credibility check -->
        <BacktestPanel :data="backtest" :loading="backtestLoading" :error="backtestError" />

        <!-- Strategy backtest — score-timed exposure vs buy & hold (equity curve) -->
        <StrategyBacktest :data="backtest" :loading="backtestLoading" />

        <!-- News — last content block -->
        <NewsList
          v-if="newsLoading || newsReady"
          :items="news?.items || []"
          :loading="newsLoading"
          :unavailable="newsReady && !news"
        />

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
      class="flex-1"
      @analyse="goToAnalyse"
    />
    <!-- ═════ PORTFOLIO ═══════════════════════════ -->
    <PortfolioView
      v-else-if="view === 'portfolio'"
      class="flex-1"
      @analyse="goToAnalyse"
    />
    <!-- ═════ FOOTER ═══════════════════════════════════════════ -->
    <footer class="border-t border-zinc-800/60 px-4 md:px-6 xl:px-8 py-5">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-zinc-500">
        <a href="https://github.com/comassky/hodler-scanner" target="_blank" rel="noopener noreferrer"
          class="inline-flex items-center gap-1.5 hover:text-indigo-400 transition-colors">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z" />
          </svg>
          <span>{{ t('app.footerSource') }}</span>
        </a>
        <span class="font-mono">v{{ appVersion }}</span>
      </div>
    </footer>

    <!-- Global quick-search modal (Ctrl/Cmd + F) -->
    <SearchModal
      :open="searchModalOpen"
      @close="searchModalOpen = false"
      @search="onModalSearch"
    />

    <!-- Reset data modal (per-type toggles) -->
    <ResetModal
      :open="resetModalOpen"
      @close="resetModalOpen = false"
      @confirm="onResetConfirm"
    />

  </div>
</template>
