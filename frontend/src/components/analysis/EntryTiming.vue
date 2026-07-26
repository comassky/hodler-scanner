<script setup>
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n.js'

const { t, locale } = useI18n()

const props = defineProps({
  data:    { type: Object,  default: null },
  loading: { type: Boolean, default: false },
})

const timing = computed(() => props.data?.timing ?? null)

// Trading days → short horizon label (mirror of BacktestPanel).
const horizonLabel = computed(() => {
  const y = locale.value === 'fr' ? 'A' : 'Y'
  const map = { 63: '3M', 126: '6M', 252: '12M', 756: `3${y}`, 1260: `5${y}` }
  return map[timing.value?.horizon] ?? `${timing.value?.horizon ?? ''}d`
})

const pct = (v) => (v == null ? '—' : (v > 0 ? '+' : '') + v.toFixed(2) + '%')

// Level → visual style + icon.
const LEVELS = {
  excellent:  { ring: 'bg-emerald-500/10 border-emerald-500/40', dot: 'text-emerald-300', icon: 'star' },
  good:       { ring: 'bg-sky-500/10 border-sky-500/40',         dot: 'text-sky-300',     icon: 'check' },
  fair:       { ring: 'bg-amber-500/10 border-amber-500/40',     dot: 'text-amber-300',   icon: 'minus' },
  poor:       { ring: 'bg-zinc-700/20 border-zinc-600/50',       dot: 'text-zinc-300',    icon: 'wait' },
  unreliable: { ring: 'bg-zinc-700/20 border-zinc-600/50',       dot: 'text-zinc-400',    icon: 'question' },
}
const style = computed(() => LEVELS[timing.value?.level] ?? LEVELS.unreliable)

const edgeColor = computed(() => {
  const e = timing.value?.edge
  if (e == null) return 'text-zinc-400'
  return e > 0 ? 'text-emerald-400' : e < 0 ? 'text-red-400' : 'text-zinc-300'
})
</script>

<template>
  <div id="section-timing" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">{{ t('timing.title') }}</h2>

    <!-- Loading -->
    <div v-if="loading && !timing" class="flex items-center gap-2 text-sm text-zinc-600 py-2">
      <div class="w-4 h-4 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin"></div>
      {{ t('timing.loading') }}
    </div>

    <div v-else-if="timing" :class="['flex items-start gap-3 border rounded-xl px-4 py-3.5', style.ring]">
      <svg :class="['w-5 h-5 mt-0.5 shrink-0', style.dot]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path v-if="style.icon === 'star'" stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.5a.56.56 0 0 1 1.04 0l2.13 5.11 5.52.44c.5.04.7.66.32.99l-4.2 3.6 1.28 5.39a.56.56 0 0 1-.84.6L12 17.35l-4.73 2.87a.56.56 0 0 1-.84-.6l1.28-5.39-4.2-3.6a.56.56 0 0 1 .32-.99l5.52-.44 2.13-5.11Z"/>
        <path v-else-if="style.icon === 'check'" stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
        <path v-else-if="style.icon === 'minus'" stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
        <path v-else-if="style.icon === 'wait'" stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l3.75 2.25M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
        <path v-else stroke-linecap="round" stroke-linejoin="round" d="M9.88 9.05a2.25 2.25 0 1 1 3.4 2.3c-.66.5-1.28 1.1-1.28 1.9v.5M12 17h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
      </svg>

      <div class="min-w-0">
        <p :class="['text-sm font-semibold', style.dot]">{{ t(`timing.level_${timing.level}`) }}</p>
        <p class="text-xs text-zinc-400 leading-relaxed mt-0.5">{{ t(`timing.desc_${timing.level}`) }}</p>

        <!-- Signals -->
        <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2.5 text-[11px]">
          <span class="text-zinc-400">{{ t('timing.historyPct', { pct: timing.percentile }) }}</span>
          <span v-if="timing.edge != null" :class="edgeColor">
            {{ t('timing.edge', { edge: pct(timing.edge), h: horizonLabel }) }}
          </span>
        </div>

        <p v-if="!timing.reliable" class="text-[11px] text-amber-400/80 mt-2">{{ t('timing.unreliableNote') }}</p>
      </div>
    </div>
  </div>
</template>
