<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import InfoTip from './InfoTip.vue'
import { useTheme } from '../composables/useTheme.js'
import { useI18n } from '../composables/useI18n.js'

const { theme } = useTheme()
const { t, locale } = useI18n()

const props = defineProps({
  data:    { type: Object,  default: null },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: null },
})

// ── Horizon selector (trading days → ≈ months/years label) ────────
const yearUnit = computed(() => (locale.value === 'fr' ? 'A' : 'Y'))
const HORIZON_LABELS = computed(() => ({
  63: '3M', 126: '6M', 252: '12M',
  756: `3${yearUnit.value}`, 1260: `5${yearUnit.value}`,
}))
const horizon = ref('126')
const horizons = computed(() => props.data?.horizons_days ?? [63, 126, 252])
watch(() => props.data, v => {
  if (v?.primary_horizon) horizon.value = String(v.primary_horizon)
})

// ── Band presentation (aligned with the score status colors) ──────
const BANDS = {
  strong:     { color: '#34d399', label: () => t('backtest.bandStrong') },
  accumulate: { color: '#38bdf8', label: () => t('backtest.bandAccumulate') },
  watch:      { color: '#fbbf24', label: () => t('backtest.bandWatch') },
  avoid:      { color: '#f87171', label: () => t('backtest.bandAvoid') },
}

// Score → decision band (thresholds mirror the backend _BANDS: 80 / 60 / 40).
function bandForScore(s) {
  if (s == null) return null
  if (s >= 80) return 'strong'
  if (s >= 60) return 'accumulate'
  if (s >= 40) return 'watch'
  return 'avoid'
}
const scoreColor = (s) => BANDS[bandForScore(s)]?.color ?? '#818cf8'

// Legend chips explaining the score line color code.
const bandLegend = computed(() =>
  ['strong', 'accumulate', 'watch', 'avoid'].map(k => ({
    key: k, color: BANDS[k].color, label: BANDS[k].label(),
  }))
)

function pct(v) {
  if (v == null) return '—'
  return (v > 0 ? '+' : '') + v.toFixed(2) + '%'
}

// ── Summary derived from the selected horizon ─────────────────────
const summary = computed(() => {
  const d = props.data
  if (!d) return null
  const h = horizon.value
  return {
    correlation: d.correlation?.[h] ?? null,
    baseline: d.baseline?.by_horizon?.[h]?.avg_return ?? null,
    baselineWin: d.baseline?.by_horizon?.[h]?.win_rate ?? null,
    samples: d.samples,
    start: d.period_start,
    end: d.period_end,
  }
})

// ── Verdict for the user's goal: "good moments to buy for a hold?" ──
// What matters is NOT whether returns are positive (a rising asset is positive
// almost everywhere) but whether buying on the actionable "buy" bands
// (Strong + Accumulate) beat buying at *any* random time (the baseline).
const verdict = computed(() => {
  const d = props.data
  if (!d) return null
  const h = horizon.value
  const base = d.baseline?.by_horizon?.[h]?.avg_return
  if (base == null) return { tone: 'nodata' }
  let wSum = 0, cSum = 0
  for (const b of d.bands) {
    if (b.key !== 'strong' && b.key !== 'accumulate') continue
    const st = b.by_horizon?.[h]
    if (!st || st.avg_return == null || !st.count) continue
    wSum += st.avg_return * st.count
    cSum += st.count
  }
  if (!cSum) return { tone: 'nodata' }
  const buyReturn = wSum / cSum
  const delta = buyReturn - base
  const tone = delta >= 2 ? 'good' : delta <= -2 ? 'bad' : 'neutral'
  return { tone, delta, buyReturn, base }
})

const VERDICT_STYLES = {
  good:    'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
  neutral: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
  bad:     'bg-red-500/10 border-red-500/30 text-red-300',
  nodata:  'bg-zinc-800/40 border-zinc-700/50 text-zinc-400',
}

const verdictMessage = computed(() => {
  const v = verdict.value
  if (!v) return null
  if (v.tone === 'nodata') return t('backtest.verdictNoData')
  const params = { delta: pct(v.delta), h: HORIZON_LABELS.value[horizon.value] }
  return t(`backtest.verdict_${v.tone}`, params)
})

// ── Charts ────────────────────────────────────────────────────────
const barCanvas = ref(null)
const lineCanvas = ref(null)
let barChart = null
let lineChart = null

function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

function themeColors() {
  return {
    tick:  cssVar('--color-zinc-500', '#71717a'),
    grid:  'rgba(113,113,122,0.18)',
    panel: cssVar('--color-zinc-900', '#18181b'),
    border: cssVar('--color-zinc-700', '#3f3f46'),
    body:  cssVar('--color-zinc-100', '#f4f4f5'),
  }
}

function destroy() {
  barChart?.destroy(); lineChart?.destroy()
  barChart = lineChart = null
}

function renderCharts() {
  if (!props.data || !barCanvas.value || !lineCanvas.value) return
  destroy()
  const c = themeColors()
  const h = horizon.value
  const d = props.data

  // ── Bar chart: average forward return per score band ────────────
  const bands = d.bands.filter(b => b.count > 0)
  const barLabels = bands.map(b => BANDS[b.key]?.label() ?? b.key)
  const barValues = bands.map(b => b.by_horizon?.[h]?.avg_return ?? null)
  const barColors = bands.map(b => (BANDS[b.key]?.color ?? '#a1a1aa'))
  const baseline = d.baseline?.by_horizon?.[h]?.avg_return ?? null

  const baselinePlugin = {
    id: 'baselineLine',
    afterDatasetsDraw(chart) {
      if (baseline == null) return
      const { ctx, chartArea, scales: { y } } = chart
      if (!chartArea) return
      const yPx = y.getPixelForValue(baseline)
      ctx.save()
      ctx.strokeStyle = 'rgba(161,161,170,0.7)'
      ctx.lineWidth = 1.2
      ctx.setLineDash([5, 4])
      ctx.beginPath(); ctx.moveTo(chartArea.left, yPx); ctx.lineTo(chartArea.right, yPx); ctx.stroke()
      ctx.setLineDash([])
      ctx.fillStyle = 'rgba(161,161,170,0.9)'
      ctx.font = '10px ui-monospace, monospace'
      ctx.textAlign = 'right'
      ctx.fillText(`${t('backtest.baseline')} ${pct(baseline)}`, chartArea.right - 4, yPx - 4)
      ctx.restore()
    },
  }

  barChart = new Chart(barCanvas.value, {
    type: 'bar',
    data: {
      labels: barLabels,
      datasets: [{
        data: barValues,
        backgroundColor: barColors.map(col => col + 'cc'),
        borderColor: barColors,
        borderWidth: 1,
        borderRadius: 5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: c.panel, borderColor: c.border, borderWidth: 1,
          titleColor: c.tick, bodyColor: c.body, padding: 10,
          callbacks: {
            afterLabel: (i) => {
              const b = bands[i.dataIndex]
              const st = b.by_horizon?.[h] ?? {}
              const delta = (st.avg_return != null && baseline != null) ? st.avg_return - baseline : null
              return [
                `${t('backtest.vsBaseline')}: ${pct(delta)}`,
                `${t('backtest.samples')}: ${st.count ?? 0}`,
                `${t('backtest.winRate')}: ${st.win_rate ?? '—'}%`,
                `${t('backtest.median')}: ${pct(st.median_return)}`,
              ]
            },
            label: (i) => ` ${t('backtest.avgReturn')}: ${pct(i.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: c.tick, font: { size: 11 } }, grid: { display: false }, border: { display: false } },
        y: {
          ticks: { color: c.tick, font: { size: 10 }, callback: v => v + '%' },
          grid: { color: c.grid }, border: { display: false },
        },
      },
    },
    plugins: [baselinePlugin],
  })

  // ── Line chart: score over time + price (dual axis) ─────────────
  const dates = d.series.map(p => p.date)
  const scores = d.series.map(p => p.score)
  const prices = d.series.map(p => p.price)
  const sma200 = d.series.map(p => p.sma200 ?? null)

  lineChart = new Chart(lineCanvas.value, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        {
          label: t('backtest.score'), data: scores, yAxisID: 'yScore',
          borderColor: '#818cf8', backgroundColor: 'rgba(129,140,248,0.08)',
          borderWidth: 1.8, tension: 0.25, fill: true, pointRadius: 0, pointHitRadius: 6, order: 1,
          pointBackgroundColor: scores.map(scoreColor),
          pointBorderColor: scores.map(scoreColor),
          pointHoverRadius: 4,
          segment: { borderColor: (ctx) => scoreColor(ctx.p1.parsed.y) },
        },
        {
          label: t('backtest.price'), data: prices, yAxisID: 'yPrice',
          borderColor: '#52525b', borderWidth: 1.2, tension: 0.1, fill: false, pointRadius: 0, pointHitRadius: 6, order: 2,
        },
        {
          label: t('backtest.sma200'), data: sma200, yAxisID: 'yPrice',
          borderColor: '#f59e0b', borderWidth: 1.2, borderDash: [4, 3], tension: 0.1,
          fill: false, pointRadius: 0, pointHitRadius: 6, spanGaps: true, order: 3,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true, position: 'top', align: 'end',
          labels: { color: c.tick, boxWidth: 18, boxHeight: 2, padding: 12, font: { size: 10 } },
        },
        tooltip: {
          backgroundColor: c.panel, borderColor: c.border, borderWidth: 1,
          titleColor: c.tick, bodyColor: c.body, padding: 10,
          callbacks: {
            label: (i) => {
              if (i.datasetIndex === 0) {
                const key = bandForScore(i.parsed.y)
                return ` ${t('backtest.score')}: ${i.parsed.y} — ${BANDS[key]?.label() ?? ''}`
              }
              const lbl = i.datasetIndex === 1 ? t('backtest.price') : t('backtest.sma200')
              return ` ${lbl}: ${i.parsed.y?.toFixed(2) ?? '—'}`
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: c.tick, maxTicksLimit: 8, maxRotation: 0, font: { size: 10 } }, grid: { color: c.grid }, border: { display: false } },
        yScore: { position: 'left', min: 0, max: 100, ticks: { color: '#818cf8', maxTicksLimit: 5, font: { size: 10 } }, grid: { color: c.grid }, border: { display: false } },
        yPrice: { position: 'right', ticks: { color: '#52525b', maxTicksLimit: 5, font: { size: 10 } }, grid: { display: false }, border: { display: false } },
      },
    },
  })
}

watch(() => props.data, () => { if (!props.loading) nextTick(renderCharts) }, { flush: 'post' })
watch(() => props.loading, l => { if (!l && props.data) nextTick(renderCharts) }, { flush: 'post' })
watch(horizon, () => { if (props.data) nextTick(renderCharts) })
watch([theme, locale], () => { if (props.data && !props.loading) nextTick(renderCharts) })
onMounted(() => { if (props.data && !props.loading) nextTick(renderCharts) })
onUnmounted(destroy)
</script>

<template>
  <div id="section-backtest" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <div class="flex items-center justify-between mb-1 flex-wrap gap-2">
      <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest">
        {{ t('backtest.title') }}<InfoTip v-bind="t('info.backtest')" />
      </h2>
      <div v-if="data" class="flex gap-1">
        <button v-for="hz in horizons" :key="hz"
          @click="horizon = String(hz)"
          :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
            horizon === String(hz) ? 'bg-indigo-600 text-white' : 'bg-zinc-800/80 text-zinc-500 hover:text-zinc-300']">
          {{ HORIZON_LABELS[hz] }}
        </button>
      </div>
    </div>
    <p class="text-xs text-zinc-600 mb-4">{{ t('backtest.subtitle') }}</p>

    <!-- Loading -->
    <div v-if="loading" class="h-40 flex items-center justify-center">
      <div class="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <!-- Error / insufficient history -->
    <div v-else-if="error" class="h-20 flex items-center justify-center text-center text-sm text-zinc-600 px-4">
      {{ error }}
    </div>

    <template v-else-if="data">
      <!-- Verdict: does the score help time entries on THIS ticker? -->
      <div v-if="verdictMessage" :class="['flex items-start gap-2.5 border rounded-xl px-3.5 py-3 mb-5', VERDICT_STYLES[verdict.tone]]">
        <svg class="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path v-if="verdict.tone === 'good'" stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
          <path v-else-if="verdict.tone === 'bad'" stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"/>
          <path v-else stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"/>
        </svg>
        <div>
          <p class="text-[10px] uppercase tracking-wider opacity-70 mb-0.5">{{ t('backtest.verdictLabel') }}</p>
          <p class="text-xs leading-relaxed">{{ verdictMessage }}</p>
        </div>
      </div>

      <!-- Summary stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="flex items-center text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('backtest.correlation') }}<InfoTip v-bind="t('info.btCorrelation')" /></p>
          <p :class="['text-lg font-bold font-mono', summary.correlation >= 0.2 ? 'text-emerald-400' : summary.correlation >= 0 ? 'text-zinc-300' : 'text-red-400']">
            {{ summary.correlation == null ? '—' : summary.correlation.toFixed(2) }}
          </p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="flex items-center text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('backtest.baseline') }}<InfoTip v-bind="t('info.btBaseline')" /></p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ pct(summary.baseline) }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="flex items-center text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('backtest.samples') }}<InfoTip v-bind="t('info.btSamples')" /></p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ summary.samples }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="flex items-center text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('backtest.period') }}<InfoTip v-bind="t('info.btPeriod')" /></p>
          <p class="text-xs font-mono text-zinc-400 mt-1">{{ summary.start }}<br>→ {{ summary.end }}</p>
        </div>
      </div>

      <!-- Average forward return per band -->
      <p class="flex items-center text-xs text-zinc-500 mb-2">{{ t('backtest.avgReturnByBand', { h: HORIZON_LABELS[horizon] }) }}<InfoTip v-bind="t('info.btBands')" /></p>
      <div class="h-56 mb-2"><canvas ref="barCanvas"></canvas></div>
      <p class="text-[11px] text-zinc-500 mb-6 leading-relaxed">{{ t('backtest.bandsGuide') }}</p>

      <!-- Score over time vs price -->
      <p class="flex items-center text-xs text-zinc-500 mb-2">{{ t('backtest.scoreOverTime') }}<InfoTip v-bind="t('info.btScoreTime')" /></p>
      <div class="h-64"><canvas ref="lineCanvas"></canvas></div>

      <!-- Decision color code for the score line -->
      <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2.5">
        <span class="text-[10px] uppercase tracking-wider text-zinc-500">{{ t('backtest.decisionLegend') }}</span>
        <span v-for="b in bandLegend" :key="b.key" class="flex items-center gap-1.5 text-[10px] text-zinc-400">
          <span class="inline-block w-3.5 h-[3px] rounded-full" :style="{ background: b.color }"></span>{{ b.label }}
        </span>
      </div>

      <p class="text-[11px] text-zinc-600 mt-4 leading-relaxed border-t border-zinc-800/60 pt-3">
        {{ t('backtest.disclaimer') }}
      </p>
    </template>

    <div v-else class="h-20 flex items-center justify-center text-zinc-700 text-sm">
      {{ t('backtest.loadError') }}
    </div>
  </div>
</template>
