<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from '../lib/chart'
import zoomPlugin from 'chartjs-plugin-zoom'
import InfoTip from './InfoTip.vue'
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'
import type { ChartData } from '../types/market'

Chart.register(zoomPlugin)

const { theme } = useTheme()
const { t, locale } = useI18n()

const props = defineProps<{
  data?: ChartData | null
  loading?: boolean
  period?: string
}>()
defineEmits<{ 'update:period': [period: string] }>()

// ── Canvas refs ───────────────────────────────────────────────────
const chartCanvas = ref<HTMLCanvasElement | null>(null)
const rsiCanvas   = ref<HTMLCanvasElement | null>(null)
const macdCanvas  = ref<HTMLCanvasElement | null>(null)
const divCanvas   = ref<HTMLCanvasElement | null>(null)
const divInfo     = ref<HTMLElement | null>(null)
const zoomed      = ref(false)
const showFib     = ref(true)
const showBoll    = ref(false)
let priceChart: Chart | null = null, rsiChart: Chart | null = null, macdChart: Chart | null = null, divChart: Chart | null = null

function resetZoom() {
  priceChart?.resetZoom()
  zoomed.value = false
}

function toggleFib() {
  showFib.value = !showFib.value
  priceChart?.update('none')
}

function toggleBoll() {
  showBoll.value = !showBoll.value
  if (!priceChart) return
  priceChart.data.datasets.forEach(ds => {
    if (ds.label?.startsWith('BB')) ds.hidden = !showBoll.value
  })
  priceChart.update('none')
}

// ── Chart theme (resolved from the active theme's CSS variables) ──
function cssVar(name: string, fallback: string, style?: CSSStyleDeclaration) {
  const s = style || getComputedStyle(document.documentElement)
  const v = s.getPropertyValue(name).trim()
  return v || fallback
}

function withAlpha(hex: string, a: number) {
  const h = hex.replace('#', '')
  if (h.length !== 6) return hex
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${a})`
}

let GRID, AXIS_X, AXIS_Y, TOOLTIP, PRICE_COLOR

function refreshChartTheme() {
  const cs     = getComputedStyle(document.documentElement)
  const tick   = cssVar('--color-zinc-500', '#71717a', cs)
  const grid   = cssVar('--color-zinc-800', '#27272a', cs)
  const panel  = cssVar('--color-zinc-900', '#18181b', cs)
  const border = cssVar('--color-zinc-700', '#3f3f46', cs)
  const title  = cssVar('--color-zinc-500', '#71717a', cs)
  const body   = cssVar('--color-zinc-100', '#f4f4f5', cs)
  PRICE_COLOR  = cssVar('--color-zinc-100', '#e4e4e7', cs)
  GRID = withAlpha(grid, 0.5)
  AXIS_X = {
    ticks:  { color: tick, maxTicksLimit: 8, maxRotation: 0, font: { size: 10 } },
    grid:   { color: GRID },
    border: { display: false },
  }
  AXIS_Y = {
    position: 'right',
    ticks:  { color: tick, maxTicksLimit: 5, font: { size: 10 } },
    grid:   { color: GRID },
    border: { display: false },
  }
  TOOLTIP = {
    mode: 'index', intersect: false,
    backgroundColor: panel, borderColor: border, borderWidth: 1,
    titleColor: title, bodyColor: body,
    padding: 10, titleFont: { size: 10 }, bodyFont: { size: 11 },
  }
}
refreshChartTheme()

// ── Lifecycle ─────────────────────────────────────────────────────
// Watch data changes (period reload etc.)
watch(() => props.data, v => {
  if (!v) { destroyCharts(); return }
  // Only render when loading is already false (canvas visible)
  if (!props.loading) nextTick(() => renderCharts(v))
}, { flush: 'post' })

// Watch loading → render when it transitions to false and data is ready
// (this handles the first load: data arrives while loading is still true)
watch(() => props.loading, loading => {
  if (!loading && props.data) nextTick(() => renderCharts(props.data))
}, { flush: 'post' })

// Render on mount when the component appears with data already present
// (the component only mounts after loading turned false, so no watcher fires)
onMounted(() => {
  if (props.data && !props.loading) nextTick(() => renderCharts(props.data))
})

// Re-render charts when the theme changes (to pick up new CSS colors)
watch(theme, () => {
  if (props.data && !props.loading) nextTick(() => renderCharts(props.data))
})

// Re-render charts when the locale changes (to update dataset labels)
watch(locale, () => {
  if (props.data && !props.loading) updateChartLabels()
})

onUnmounted(destroyCharts)

// ── Fibonacci plugin ───────────────────────────────────────────────
function makeFibPlugin(h52w, l52w) {
  const range = h52w - l52w
  const levels = [
    { pct: 0,     label: '0',    color: '#a1a1aa', key: false },
    { pct: 0.236, label: '23.6', color: '#a1a1aa', key: false },
    { pct: 0.382, label: '38.2', color: '#f59e0b', key: true },
    { pct: 0.5,   label: '50',   color: '#6366f1', key: true },
    { pct: 0.618, label: '61.8', color: '#f97316', key: true },
    { pct: 0.786, label: '78.6', color: '#a1a1aa', key: false },
    { pct: 1,     label: '100',  color: '#a1a1aa', key: false },
  ]
  return {
    id: 'fibonacci',
    afterDatasetsDraw(chart) {
      if (!showFib.value) return
      const { ctx, scales: { y }, chartArea } = chart
      if (!chartArea) return
      ctx.save()
      for (const fib of levels) {
        const price = h52w - range * fib.pct
        const yPx = y.getPixelForValue(price)
        if (yPx < chartArea.top || yPx > chartArea.bottom) continue

        // Line
        ctx.beginPath()
        ctx.strokeStyle = withAlpha(fib.color, fib.key ? 0.95 : 0.55)
        ctx.lineWidth = fib.key ? 1.8 : 1
        ctx.setLineDash(fib.key ? [] : [5, 4])
        ctx.moveTo(chartArea.left, yPx)
        ctx.lineTo(chartArea.right, yPx)
        ctx.stroke()
        ctx.setLineDash([])

        // Label
        const text = fib.key ? `${fib.label}%  ${price.toFixed(2)}` : `${fib.label}%`
        ctx.font = `${fib.key ? '700 ' : ''}10px ui-monospace, monospace`
        const tw = ctx.measureText(text).width
        if (fib.key) {
          // Solid pill
          const padX = 5, padY = 3, h = 15, r = 4
          const bx = chartArea.left + 4, by = yPx - h / 2
          ctx.beginPath()
          ctx.fillStyle = fib.color
          ctx.roundRect(bx, by, tw + padX * 2, h, r)
          ctx.fill()
          ctx.fillStyle = '#ffffff'
          ctx.textBaseline = 'middle'
          ctx.textAlign = 'left'
          ctx.fillText(text, bx + padX, yPx + 0.5)
        } else {
          ctx.fillStyle = withAlpha(fib.color, 0.85)
          ctx.textBaseline = 'middle'
          ctx.textAlign = 'left'
          ctx.fillText(text, chartArea.left + 6, yPx - 7)
        }
      }
      ctx.restore()
    }
  }
}

// ── Chart functions ───────────────────────────────────────────────
// Update only the translated labels without rebuilding the charts
function updateChartLabels() {
  if (priceChart) {
    const ds = priceChart.data.datasets
    if (ds[0]) ds[0].label = t('charts.price')
    if (ds[3]) ds[3].label = t('charts.bbUpper')
    if (ds[4]) ds[4].label = t('charts.bbLower')
    if (ds[5]) ds[5].label = t('charts.volume')
    priceChart.update('none')
  }
  if (divChart) {
    const ds = divChart.data.datasets
    if (ds[0]) ds[0].label = t('charts.price')
    if (ds[1]) ds[1].label = t('charts.rsi14')
    divChart.update('none')
  }
}

function destroyCharts() {
  priceChart?.destroy(); rsiChart?.destroy(); macdChart?.destroy(); divChart?.destroy()
  priceChart = rsiChart = macdChart = divChart = null
  divInfo.value = null
  zoomed.value  = false
}

function renderCharts(data) {
  if (!chartCanvas.value) return
  destroyCharts()
  refreshChartTheme()

  // Volume colors (green if day up, red if day down)
  const volColors = (data.volume ?? []).map((v, i) => {
    if (v == null) return 'transparent'
    const c = data.close[i], p = data.close[i - 1]
    return (c != null && p != null && c >= p) ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)'
  })
  const volMax = (data.volume ?? []).reduce((m, v) => (v != null && v > m ? v : m), 0)

  // Standard Fibonacci: anchored on the highest / lowest of the displayed data
  let fibPlugin = null
  {
    let hi = -Infinity, lo = Infinity
    for (const v of data.close) {
      if (v == null) continue
      if (v > hi) hi = v
      if (v < lo) lo = v
    }
    if (hi > lo) fibPlugin = makeFibPlugin(hi, lo)
  }

  // Price + SMAs + Volume
  priceChart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels: data.dates,
      datasets: [
        { label: t('charts.price'),   data: data.close,         borderColor: PRICE_COLOR, borderWidth: 1.5, tension: 0.1, fill: false, pointRadius: 0, pointHitRadius: 8, order: 1 },
        { label: 'SMA 200', data: data.sma200,        borderColor: '#f97316', borderWidth: 1.5, borderDash: [5,3], tension: 0.3, fill: false, pointRadius: 0, order: 2 },
        { label: 'SMA 50',  data: data.sma50,         borderColor: '#38bdf8', borderWidth: 1.5, borderDash: [5,3], tension: 0.3, fill: false, pointRadius: 0, order: 3 },
        { label: t('charts.bbUpper'), data: data.bb_upper ?? [], borderColor: 'rgba(167,139,250,0.7)', borderWidth: 1, tension: 0.3, fill: false, pointRadius: 0, hidden: !showBoll.value, order: 4 },
        { label: t('charts.bbLower'), data: data.bb_lower ?? [], borderColor: 'rgba(167,139,250,0.7)', borderWidth: 1, tension: 0.3, fill: '-1', backgroundColor: 'rgba(167,139,250,0.08)', pointRadius: 0, hidden: !showBoll.value, order: 5 },
        { label: t('charts.volume'),  type: 'bar', data: data.volume ?? [], backgroundColor: volColors, borderWidth: 0, barPercentage: 1, categoryPercentage: 1, yAxisID: 'yVol', order: 10 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true, position: 'top', align: 'end',
          labels: { color: '#71717a', boxWidth: 18, boxHeight: 2, padding: 14, font: { size: 10 }, filter: item => item.text !== 'Volume' && !item.text.startsWith('BB') },
        },
        tooltip: { ...TOOLTIP, callbacks: { label: i => i.dataset.label === 'Volume' ? '' : ` ${i.dataset.label}: ${i.parsed.y?.toFixed(2) ?? '—'}` } },
        zoom: {
          pan:  { enabled: true, mode: 'x', modifierKey: 'shift', onPanComplete: () => { zoomed.value = true } },
          zoom: {
            wheel: { enabled: true, speed: 0.08 },
            pinch: { enabled: true },
            drag:  { enabled: true, backgroundColor: 'rgba(99,102,241,0.15)', borderColor: 'rgba(99,102,241,0.5)', borderWidth: 1 },
            mode: 'x',
            onZoomComplete: () => { zoomed.value = true },
          },
          limits: { x: { minRange: 5 } },
        },
      },
      scales: {
        x: AXIS_X,
        y: AXIS_Y,
        yVol: { position: 'left', max: volMax * 5, ticks: { display: false }, grid: { display: false }, border: { display: false } },
      },
    },
    plugins: fibPlugin ? [fibPlugin] : [],
  })

  if (!rsiCanvas.value || !macdCanvas.value) return
  const n = data.dates.length

  // RSI
  rsiChart = new Chart(rsiCanvas.value, {
    type: 'line',
    data: {
      labels: data.dates,
      datasets: [
        { label: 'RSI', data: data.rsi, borderColor: '#818cf8', borderWidth: 1.5, tension: 0.2, fill: false, pointRadius: 0, pointHitRadius: 6, order: 0 },
        { label: '70',  data: Array(n).fill(70), borderColor: 'rgba(248,113,113,0.4)', borderWidth: 1, borderDash: [3,3], fill: false, pointRadius: 0, order: 1 },
        { label: '30',  data: Array(n).fill(30), borderColor: 'rgba(52,211,153,0.4)',  borderWidth: 1, borderDash: [3,3], fill: false, pointRadius: 0, order: 1 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { ...TOOLTIP, filter: i => i.datasetIndex === 0,
          callbacks: { label: i => ` RSI: ${i.parsed.y?.toFixed(1) ?? '—'}` } },
      },
      scales: {
        x: { ...AXIS_X, ticks: { ...AXIS_X.ticks, display: false }, grid: { display: false } },
        y: { ...AXIS_Y, min: 0, max: 100, ticks: { ...AXIS_Y.ticks, maxTicksLimit: 4 } },
      },
    },
  })

  // MACD histogram
  macdChart = new Chart(macdCanvas.value, {
    type: 'bar',
    data: {
      labels: data.dates,
      datasets: [{
        label: 'MACD',
        data: data.macd_hist,
        backgroundColor: data.macd_hist.map(v =>
          v == null ? 'transparent' : v >= 0 ? 'rgba(52,211,153,0.7)' : 'rgba(248,113,113,0.7)'),
        borderWidth: 0,
        barPercentage: 0.9, categoryPercentage: 0.95,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: { ...TOOLTIP, callbacks: { label: i => ` MACD: ${i.parsed.y?.toFixed(4) ?? '—'}` } },
      },
      scales: {
        x: { ...AXIS_X, ticks: { ...AXIS_X.ticks, display: false }, grid: { display: false } },
        y: { ...AXIS_Y, ticks: { ...AXIS_Y.ticks, maxTicksLimit: 3 } },
      },
    },
  })

  renderDivChart(data)
}

// ── Divergence detection ─────────────────────────────────────────
function nearest(arr, idx, maxDist) {
  let best = null, bestD = Infinity
  for (const r of arr) { const d = Math.abs(r - idx); if (d < bestD) { bestD = d; best = r } }
  return bestD <= maxDist ? best : null
}

function pivotLows(series, win) {
  const res = []
  for (let i = win; i < series.length - win; i++) {
    const v = series[i]; if (v == null) continue
    let ok = true
    for (let j = i - win; j <= i + win; j++) { if (j !== i && series[j] != null && series[j] < v) { ok = false; break } }
    if (ok) res.push(i)
  }
  return res
}

function pivotHighs(series, win) {
  const res = []
  for (let i = win; i < series.length - win; i++) {
    const v = series[i]; if (v == null) continue
    let ok = true
    for (let j = i - win; j <= i + win; j++) { if (j !== i && series[j] != null && series[j] > v) { ok = false; break } }
    if (ok) res.push(i)
  }
  return res
}

function detectDivergences(close, rsi, win = 7) {
  const bullish = [], bearish = []
  const pLows = pivotLows(close, win), rLows = pivotLows(rsi, win)
  for (let i = 1; i < pLows.length; i++) {
    const i1 = pLows[i-1], i2 = pLows[i]
    if (i2 - i1 < win * 3 || close[i2] >= close[i1]) continue
    const r1 = nearest(rLows, i1, win * 2), r2 = nearest(rLows, i2, win * 2)
    if (r1 == null || r2 == null || r1 === r2) continue
    if (rsi[r2] <= rsi[r1]) continue
    bullish.push({ pi1: i1, pi2: i2, ri1: r1, ri2: r2 })
  }
  const pHighs = pivotHighs(close, win), rHighs = pivotHighs(rsi, win)
  for (let i = 1; i < pHighs.length; i++) {
    const i1 = pHighs[i-1], i2 = pHighs[i]
    if (i2 - i1 < win * 3 || close[i2] <= close[i1]) continue
    const r1 = nearest(rHighs, i1, win * 2), r2 = nearest(rHighs, i2, win * 2)
    if (r1 == null || r2 == null || r1 === r2) continue
    if (rsi[r2] >= rsi[r1]) continue
    bearish.push({ pi1: i1, pi2: i2, ri1: r1, ri2: r2 })
  }
  return { bullish, bearish }
}

function makeDivPlugin(close, rsi, divs) {
  return {
    id: 'divergence',
    afterDatasetsDraw(chart) {
      const ctx = chart.ctx, xS = chart.scales.x
      const yP = chart.scales.yPrice, yR = chart.scales.yRsi
      function line(x1, y1, x2, y2, col) {
        ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.setLineDash([5, 3])
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore()
      }
      function dot(x, y, col) {
        ctx.save(); ctx.fillStyle = col
        ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill(); ctx.restore()
      }
      for (const d of divs.bullish) {
        const col = 'rgba(52,211,153,0.85)'
        line(xS.getPixelForValue(d.pi1), yP.getPixelForValue(close[d.pi1]),
             xS.getPixelForValue(d.pi2), yP.getPixelForValue(close[d.pi2]), col)
        dot(xS.getPixelForValue(d.pi1), yP.getPixelForValue(close[d.pi1]), col)
        dot(xS.getPixelForValue(d.pi2), yP.getPixelForValue(close[d.pi2]), col)
        line(xS.getPixelForValue(d.ri1), yR.getPixelForValue(rsi[d.ri1]),
             xS.getPixelForValue(d.ri2), yR.getPixelForValue(rsi[d.ri2]), col)
        dot(xS.getPixelForValue(d.ri1), yR.getPixelForValue(rsi[d.ri1]), col)
        dot(xS.getPixelForValue(d.ri2), yR.getPixelForValue(rsi[d.ri2]), col)
      }
      for (const d of divs.bearish) {
        const col = 'rgba(248,113,113,0.85)'
        line(xS.getPixelForValue(d.pi1), yP.getPixelForValue(close[d.pi1]),
             xS.getPixelForValue(d.pi2), yP.getPixelForValue(close[d.pi2]), col)
        dot(xS.getPixelForValue(d.pi1), yP.getPixelForValue(close[d.pi1]), col)
        dot(xS.getPixelForValue(d.pi2), yP.getPixelForValue(close[d.pi2]), col)
        line(xS.getPixelForValue(d.ri1), yR.getPixelForValue(rsi[d.ri1]),
             xS.getPixelForValue(d.ri2), yR.getPixelForValue(rsi[d.ri2]), col)
        dot(xS.getPixelForValue(d.ri1), yR.getPixelForValue(rsi[d.ri1]), col)
        dot(xS.getPixelForValue(d.ri2), yR.getPixelForValue(rsi[d.ri2]), col)
      }
    }
  }
}

function renderDivChart(data) {
  if (!divCanvas.value) return
  divChart?.destroy(); divChart = null
  const { close, rsi, dates } = data
  const divs = detectDivergences(close, rsi)
  divInfo.value = { bullish: divs.bullish.length, bearish: divs.bearish.length }
  const n = dates.length
  divChart = new Chart(divCanvas.value, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        { label: t('charts.price'), data: close, borderColor: '#52525b', borderWidth: 1.2, tension: 0.1, fill: false, pointRadius: 0, pointHitRadius: 6, yAxisID: 'yPrice' },
        { label: t('charts.rsi14'), data: rsi, borderColor: '#818cf8', borderWidth: 1.5, tension: 0.2, fill: false, pointRadius: 0, pointHitRadius: 6, yAxisID: 'yRsi' },
        { label: '70', data: Array(n).fill(70), borderColor: 'rgba(248,113,113,0.2)', borderWidth: 1, borderDash: [3,3], fill: false, pointRadius: 0, yAxisID: 'yRsi' },
        { label: '30', data: Array(n).fill(30), borderColor: 'rgba(52,211,153,0.2)', borderWidth: 1, borderDash: [3,3], fill: false, pointRadius: 0, yAxisID: 'yRsi' },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true, position: 'top', align: 'end',
          labels: { color: '#71717a', boxWidth: 18, boxHeight: 2, padding: 12, font: { size: 10 },
            filter: item => item.datasetIndex < 2 },
        },
        tooltip: { ...TOOLTIP, filter: i => i.datasetIndex < 2,
          callbacks: { label: i => i.datasetIndex === 0
            ? ` ${t('charts.price')}: ${i.parsed.y?.toFixed(2) ?? '—'}`
            : ` RSI: ${i.parsed.y?.toFixed(1) ?? '—'}` } },
      },
      scales: {
        x: AXIS_X,
        yPrice: { position: 'right', ticks: { color: '#52525b', maxTicksLimit: 5, font: { size: 10 } }, grid: { color: GRID }, border: { display: false } },
        yRsi:   { position: 'left',  min: 0, max: 100, ticks: { color: '#818cf8', maxTicksLimit: 4, font: { size: 10 } }, grid: { display: false }, border: { display: false } },
      },
    },
    plugins: [makeDivPlugin(close, rsi, divs)],
  })
}

const PERIODS = [['3mo','3M'],['6mo','6M'],['1y','1Y'],['2y','2Y'],['max','Max']]
</script>

<template>
  <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <!-- Period selector -->
    <div class="flex flex-wrap items-center justify-between gap-2 mb-4">
      <h2 class="text-xs font-semibold text-zinc-500 uppercase tracking-widest">{{ t('charts.title') }}</h2>
      <div class="flex flex-wrap items-center gap-2">
        <button @click="toggleFib"
          :class="['flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
            showFib ? 'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30' : 'bg-zinc-800/80 text-zinc-500 hover:text-zinc-300']">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" d="M4 7h16M4 12h16M4 17h16"/>
          </svg>
          {{ t('charts.fibonacci') }}
        </button>
        <button @click="toggleBoll"
          :class="['flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
            showBoll ? 'bg-violet-500/20 text-violet-300 hover:bg-violet-500/30' : 'bg-zinc-800/80 text-zinc-500 hover:text-zinc-300']">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16" opacity="0.4"/>
            <path stroke-linecap="round" d="M4 12h16"/>
          </svg>
          {{ t('charts.bollinger') }}
        </button>
        <button v-if="zoomed" @click="resetZoom"
          class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 transition-all">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 9V4.5M9 9H4.5M9 9 3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5 5.25 5.25"/>
          </svg>
          {{ t('charts.resetZoom') }}
        </button>
        <div class="flex gap-1">
          <button v-for="[p, label] in PERIODS" :key="p"
            @click="$emit('update:period', p)"
            :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
              period === p ? 'bg-indigo-600 text-white' : 'bg-zinc-800/80 text-zinc-500 hover:text-zinc-300']">
            {{ label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="h-96 flex items-center justify-center">
      <div class="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <!-- Charts -->
    <template v-else-if="data">
      <div class="h-96 mb-1"><canvas ref="chartCanvas"></canvas></div>
      <p class="text-xs text-zinc-700 mb-2 text-right">{{ t('charts.zoomHint') }}</p>
      <div class="grid grid-cols-2 gap-4 mt-3">
        <div>
          <p class="flex items-center text-xs text-zinc-600 mb-1.5">{{ t('charts.rsi14') }}<InfoTip v-bind="t('info.chartRsi14')" /></p>
          <div class="h-28"><canvas ref="rsiCanvas"></canvas></div>
        </div>
        <div>
          <p class="flex items-center text-xs text-zinc-600 mb-1.5">{{ t('charts.macdHist') }}<InfoTip v-bind="t('info.chartMacd')" /></p>
          <div class="h-28"><canvas ref="macdCanvas"></canvas></div>
        </div>
      </div>

      <!-- RSI divergence -->
      <div class="mt-4 border-t border-zinc-800/60 pt-4">
        <div class="flex items-center gap-2 mb-2">
          <p class="flex items-center text-xs text-zinc-600">{{ t('charts.divergences') }}<InfoTip v-bind="t('info.chartDiv')" /></p>
          <template v-if="divInfo">
            <span v-if="divInfo.bullish" class="text-xs bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded">↑ {{ divInfo.bullish }} {{ t('charts.bullish') }}{{ locale === 'fr' && divInfo.bullish > 1 ? 's' : '' }}</span>
            <span v-if="divInfo.bearish" class="text-xs bg-red-500/10 text-red-400 px-1.5 py-0.5 rounded">↓ {{ divInfo.bearish }} {{ t('charts.bearish') }}{{ locale === 'fr' && divInfo.bearish > 1 ? 's' : '' }}</span>
            <span v-if="!divInfo.bullish && !divInfo.bearish" class="text-xs text-zinc-700">{{ t('charts.none') }}</span>
          </template>
        </div>
        <div class="h-64"><canvas ref="divCanvas"></canvas></div>
      </div>
    </template>

    <!-- Empty -->
    <div v-else class="h-20 flex items-center justify-center text-zinc-700 text-sm">
      {{ t('charts.loadError') }}
    </div>
  </div>
</template>
