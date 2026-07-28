<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import InfoTip from '../InfoTip.vue'
import { useTheme } from '../../composables/useTheme.js'
import { useI18n } from '../../composables/useI18n.js'

const { theme } = useTheme()
const { t, locale } = useI18n()

const props = defineProps({
  data:    { type: Object,  default: null },
  loading: { type: Boolean, default: false },
})

const threshold = ref(60)
const series = computed(() =>
  (props.data?.series ?? []).filter(p => p.price > 0 && p.score != null)
)
const hasData = computed(() => series.value.length >= 24)

function maxDrawdown(equity) {
  let peak = -Infinity, dd = 0
  for (const v of equity) {
    if (v > peak) peak = v
    if (peak > 0) dd = Math.min(dd, v / peak - 1)
  }
  return dd
}

// ── Weekly simulation: in-market when score >= threshold, else in cash ──
const sim = computed(() => {
  const s = series.value
  if (s.length < 24) return null
  const thr = threshold.value
  const dates = [s[0].date]
  const strat = [1], bh = [1]
  let eqS = 1, eqB = 1, weeksIn = 0, trades = 0, prevIn = false
  for (let i = 1; i < s.length; i++) {
    const ret = s[i].price / s[i - 1].price - 1
    const inMkt = s[i - 1].score >= thr        // decision from last week's score
    eqB *= (1 + ret)
    if (inMkt) { eqS *= (1 + ret); weeksIn++ }
    if (inMkt !== prevIn) { trades++; prevIn = inMkt }
    dates.push(s[i].date); strat.push(eqS); bh.push(eqB)
  }
  const steps = s.length - 1
  const years = (new Date(s[s.length - 1].date) - new Date(s[0].date)) / (365.25 * 864e5)
  const cagr = (final) => (years > 0 && final > 0 ? Math.pow(final, 1 / years) - 1 : null)
  return {
    dates, strat, bh,
    stratReturn: eqS - 1, bhReturn: eqB - 1,
    stratCagr: cagr(eqS), bhCagr: cagr(eqB),
    stratDD: maxDrawdown(strat), bhDD: maxDrawdown(bh),
    exposure: steps ? weeksIn / steps : 0,
    trades,
    years,
  }
})

const pct = (v) => (v == null ? '—' : (v > 0 ? '+' : '') + (v * 100).toFixed(1) + '%')
const stratBeats = computed(() => sim.value && sim.value.stratReturn > sim.value.bhReturn)

// ── Equity curve chart ────────────────────────────────────────────
const canvas = ref(null)
let chart = null

function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}
function destroy() { chart?.destroy(); chart = null }

function render() {
  if (!sim.value || !canvas.value) return
  destroy()
  const tick = cssVar('--color-zinc-500', '#71717a')
  const grid = 'rgba(113,113,122,0.18)'
  const panel = cssVar('--color-zinc-900', '#18181b')
  const border = cssVar('--color-zinc-700', '#3f3f46')
  const s = sim.value

  chart = new Chart(canvas.value, {
    type: 'line',
    data: {
      labels: s.dates,
      datasets: [
        {
          label: t('strategy.strategy'), data: s.strat.map(v => v * 100),
          borderColor: '#818cf8', backgroundColor: 'rgba(129,140,248,0.10)',
          borderWidth: 1.8, tension: 0.15, fill: true, pointRadius: 0, pointHitRadius: 6, order: 1,
        },
        {
          label: t('strategy.buyHold'), data: s.bh.map(v => v * 100),
          borderColor: '#71717a', borderWidth: 1.3, borderDash: [4, 3], tension: 0.15,
          fill: false, pointRadius: 0, pointHitRadius: 6, order: 2,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true, position: 'top', align: 'end',
          labels: { color: tick, boxWidth: 18, boxHeight: 2, padding: 12, font: { size: 10 } },
        },
        tooltip: {
          backgroundColor: panel, borderColor: border, borderWidth: 1,
          titleColor: tick, bodyColor: cssVar('--color-zinc-100', '#f4f4f5'), padding: 10,
          callbacks: { label: (i) => ` ${i.dataset.label}: ${i.parsed.y.toFixed(1)}` },
        },
      },
      scales: {
        x: { ticks: { color: tick, maxTicksLimit: 8, maxRotation: 0, font: { size: 10 } }, grid: { color: grid }, border: { display: false } },
        y: { ticks: { color: tick, maxTicksLimit: 5, font: { size: 10 } }, grid: { color: grid }, border: { display: false } },
      },
    },
  })
}

watch(() => props.data, () => { if (!props.loading) nextTick(render) }, { flush: 'post' })
watch(() => props.loading, l => { if (!l) nextTick(render) }, { flush: 'post' })
watch(threshold, () => nextTick(render))
watch([theme, locale], () => { if (hasData.value) nextTick(render) })
onMounted(() => { if (!props.loading) nextTick(render) })
onUnmounted(destroy)
</script>

<template>
  <div id="section-strategy" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-1">
      {{ t('strategy.title') }}<InfoTip v-bind="t('info.strategy')" />
    </h2>
    <p class="text-xs text-zinc-600 mb-4">{{ t('strategy.subtitle') }}</p>

    <div v-if="loading" class="h-40 flex items-center justify-center">
      <div class="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <template v-else-if="hasData && sim">
      <!-- Threshold control -->
      <div class="flex items-center gap-3 mb-5 flex-wrap">
        <label class="text-xs text-zinc-500">{{ t('strategy.threshold') }}</label>
        <input v-model.number="threshold" type="range" min="40" max="90" step="5"
          class="flex-1 min-w-[140px] accent-indigo-500" />
        <span class="font-mono text-sm font-semibold text-indigo-300 w-8 text-right">{{ threshold }}</span>
        <span class="text-[11px] text-zinc-600">{{ t('strategy.exposure', { pct: (sim.exposure * 100).toFixed(0) }) }}</span>
      </div>

      <!-- Verdict -->
      <div :class="['flex items-start gap-2.5 border rounded-xl px-3.5 py-3 mb-5',
        stratBeats ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-zinc-800/40 border-zinc-700/50 text-zinc-400']">
        <svg class="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4 4 8.5-8.5M21.75 6.75V12M21.75 6.75H16.5"/>
        </svg>
        <p class="text-xs leading-relaxed">
          {{ t(stratBeats ? 'strategy.verdictBeat' : 'strategy.verdictLag',
             { s: pct(sim.stratReturn), b: pct(sim.bhReturn), thr: threshold }) }}
        </p>
      </div>

      <!-- Stats grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('strategy.stratReturn') }}</p>
          <p :class="['text-lg font-bold font-mono', sim.stratReturn >= 0 ? 'text-emerald-400' : 'text-red-400']">{{ pct(sim.stratReturn) }}</p>
          <p class="text-[11px] font-mono text-zinc-500">{{ t('strategy.cagr') }} {{ pct(sim.stratCagr) }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('strategy.buyHold') }}</p>
          <p :class="['text-lg font-bold font-mono', sim.bhReturn >= 0 ? 'text-emerald-400' : 'text-red-400']">{{ pct(sim.bhReturn) }}</p>
          <p class="text-[11px] font-mono text-zinc-500">{{ t('strategy.cagr') }} {{ pct(sim.bhCagr) }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('strategy.maxDD') }}</p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ pct(sim.stratDD) }}</p>
          <p class="text-[11px] font-mono text-zinc-500">{{ t('strategy.buyHold') }} {{ pct(sim.bhDD) }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('strategy.trades') }}</p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ sim.trades }}</p>
          <p class="text-[11px] font-mono text-zinc-500">{{ sim.years.toFixed(1) }} {{ t('strategy.years') }}</p>
        </div>
      </div>

      <div class="h-64"><canvas ref="canvas"></canvas></div>
      <p class="text-[11px] text-zinc-600 mt-4 leading-relaxed border-t border-zinc-800/60 pt-3">
        {{ t('strategy.disclaimer') }}
      </p>
    </template>

    <div v-else class="h-20 flex items-center justify-center text-zinc-700 text-sm text-center px-4">
      {{ t('strategy.unavailable') }}
    </div>
  </div>
</template>
