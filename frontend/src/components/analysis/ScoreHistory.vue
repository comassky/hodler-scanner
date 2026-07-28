<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import InfoTip from '../InfoTip.vue'
import { useTheme } from '../../composables/useTheme.js'
import { useI18n } from '../../composables/useI18n.js'

const { theme } = useTheme()
const { t } = useI18n()

const props = defineProps({
  data:    { type: Object,  default: null },
  loading: { type: Boolean, default: false },
})

const timing = computed(() => props.data?.timing ?? null)
const scores = computed(() => (props.data?.series ?? []).map(p => p.score).filter(s => s != null))
const hasData = computed(() => scores.value.length >= 12 && timing.value != null)

// Band thresholds mirror the backend (_BANDS: 80 / 60 / 40).
function bandColor(s) {
  if (s >= 80) return '#34d399'
  if (s >= 60) return '#38bdf8'
  if (s >= 40) return '#fbbf24'
  return '#f87171'
}

// ── Distribution stats ────────────────────────────────────────────
const stats = computed(() => {
  const arr = [...scores.value].sort((a, b) => a - b)
  if (!arr.length) return null
  const mid = Math.floor(arr.length / 2)
  const median = arr.length % 2 ? arr[mid] : Math.round((arr[mid - 1] + arr[mid]) / 2)
  return { min: arr[0], median, max: arr[arr.length - 1] }
})

const current = computed(() => timing.value?.current_score ?? null)
const percentile = computed(() => timing.value?.percentile ?? null)

// ── Histogram (10-point bins) ─────────────────────────────────────
const canvas = ref(null)
let chart = null

function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

function destroy() { chart?.destroy(); chart = null }

function render() {
  if (!hasData.value || !canvas.value) return
  destroy()
  const tick = cssVar('--color-zinc-500', '#71717a')
  const grid = 'rgba(113,113,122,0.18)'
  const panel = cssVar('--color-zinc-900', '#18181b')
  const border = cssVar('--color-zinc-700', '#3f3f46')

  const bins = new Array(10).fill(0)
  for (const s of scores.value) bins[Math.min(9, Math.max(0, Math.floor(s / 10)))]++
  const labels = bins.map((_, i) => `${i * 10}`)
  const centers = bins.map((_, i) => i * 10 + 5)
  const curBin = current.value == null ? -1 : Math.min(9, Math.floor(current.value / 10))

  chart = new Chart(canvas.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: bins,
        backgroundColor: centers.map((c, i) => bandColor(c) + (i === curBin ? 'ff' : '66')),
        borderColor: centers.map(c => bandColor(c)),
        borderWidth: centers.map((_, i) => (i === curBin ? 2 : 1)),
        borderRadius: 4,
        categoryPercentage: 1.0,
        barPercentage: 0.98,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: panel, borderColor: border, borderWidth: 1,
          titleColor: tick, bodyColor: cssVar('--color-zinc-100', '#f4f4f5'), padding: 10,
          callbacks: {
            title: (items) => {
              const i = items[0].dataIndex
              return `${i * 10}–${i * 10 + 10}`
            },
            label: (i) => ` ${t('scoreHist.weeks', { n: i.parsed.y })}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: tick, font: { size: 10 } }, grid: { display: false }, border: { display: false } },
        y: { ticks: { color: tick, font: { size: 10 }, precision: 0 }, grid: { color: grid }, border: { display: false }, title: { display: false } },
      },
    },
  })
}

watch(() => props.data, () => { if (!props.loading) nextTick(render) }, { flush: 'post' })
watch(() => props.loading, l => { if (!l) nextTick(render) }, { flush: 'post' })
watch(theme, () => { if (hasData.value) nextTick(render) })
onMounted(() => { if (!props.loading) nextTick(render) })
onUnmounted(destroy)
</script>

<template>
  <div id="section-scorehist" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-1">
      {{ t('scoreHist.title') }}<InfoTip v-bind="t('info.scoreHist')" />
    </h2>
    <p class="text-xs text-zinc-600 mb-4">{{ t('scoreHist.subtitle') }}</p>

    <div v-if="loading" class="h-40 flex items-center justify-center">
      <div class="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <template v-else-if="hasData">
      <!-- Stats -->
      <div class="grid grid-cols-3 sm:grid-cols-5 gap-3 mb-5">
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('scoreHist.current') }}</p>
          <p class="text-lg font-bold font-mono" :style="{ color: bandColor(current) }">{{ current }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5 col-span-2 sm:col-span-1">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('scoreHist.percentile') }}</p>
          <p class="text-lg font-bold font-mono text-indigo-300">{{ percentile }}<span class="text-xs text-zinc-500">e</span></p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('scoreHist.min') }}</p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ stats.min }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('scoreHist.median') }}</p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ stats.median }}</p>
        </div>
        <div class="bg-zinc-950/40 border border-zinc-800 rounded-xl px-3 py-2.5 hidden sm:block">
          <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('scoreHist.max') }}</p>
          <p class="text-lg font-bold font-mono text-zinc-300">{{ stats.max }}</p>
        </div>
      </div>

      <div class="h-52"><canvas ref="canvas"></canvas></div>
      <p class="text-[11px] text-zinc-500 mt-3 leading-relaxed">
        {{ t('scoreHist.guide', { pct: percentile }) }}
      </p>
    </template>

    <div v-else class="h-20 flex items-center justify-center text-zinc-700 text-sm text-center px-4">
      {{ t('scoreHist.unavailable') }}
    </div>
  </div>
</template>
