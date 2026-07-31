<script setup lang="ts">
import InfoTip from '../InfoTip.vue'
import { useFormatters } from '../../composables/useFormatters'
import { useI18n } from '../../composables/useI18n'
import type { AnalysisIndicators, AnalysisDistances } from '../../types/analysis'

defineProps<{
  indicators: AnalysisIndicators
  distances: AnalysisDistances
}>()

const { t } = useI18n()
const { fmt, fmtPct, distClass } = useFormatters()
</script>

<template>
  <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.keyLevels') }}<InfoTip v-bind="t('info.keyLevels')" /></h2>
    <div class="space-y-3">
      <div class="flex justify-between items-center">
        <div>
          <p class="flex items-center text-xs text-zinc-400">{{ t('ind.sma200d') }}<InfoTip v-bind="t('info.sma200')" /></p>
          <p class="text-sm font-semibold text-zinc-200 font-mono">{{ fmt(indicators.sma200) }}</p>
        </div>
        <span :class="['text-sm font-semibold tabular-nums font-mono', distClass(distances.ecart_sma200_pct)]">
          {{ fmtPct(distances.ecart_sma200_pct) }}
        </span>
      </div>
      <div class="flex justify-between items-center">
        <div>
          <p class="flex items-center text-xs text-zinc-400">{{ t('ind.sma50w') }}<InfoTip v-bind="t('info.sma50w')" /></p>
          <p class="text-sm font-semibold text-zinc-200 font-mono">
            {{ indicators.w50 !== null ? fmt(indicators.w50) : '—' }}
          </p>
        </div>
        <span :class="['text-sm font-semibold tabular-nums font-mono', distances.ecart_w50_pct !== null ? distClass(distances.ecart_w50_pct) : 'text-zinc-500']">
          {{ distances.ecart_w50_pct !== null ? fmtPct(distances.ecart_w50_pct) : '—' }}
        </span>
      </div>
      <div class="border-t border-zinc-800 pt-3 flex justify-between items-center">
        <div>
          <p class="flex items-center text-xs text-zinc-400">{{ t('ind.high52') }}<InfoTip v-bind="t('info.high52')" /></p>
          <p class="text-sm font-semibold text-zinc-200 font-mono">{{ fmt(distances.h52w_price) }}</p>
        </div>
        <span class="text-sm font-semibold tabular-nums text-red-400 font-mono">
          {{ fmtPct(distances.dist_52w_high_pct) }}
        </span>
      </div>
      <div class="flex justify-between items-center">
        <div>
          <p class="flex items-center text-xs text-zinc-400">{{ t('ind.low52') }}<InfoTip v-bind="t('info.low52')" /></p>
          <p class="text-sm font-semibold text-zinc-200 font-mono">{{ fmt(distances.l52w_price) }}</p>
        </div>
        <span class="text-sm font-semibold tabular-nums text-emerald-400 font-mono">
          +{{ fmt(distances.dist_52w_low_pct, 1) }}%
        </span>
      </div>
      <div class="border-t border-zinc-800 pt-3 flex justify-between items-center">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.sma50d') }}<InfoTip v-bind="t('info.sma50')" /></span>
        <span class="text-sm font-semibold text-zinc-300 font-mono">{{ fmt(indicators.sma50) }}</span>
      </div>
    </div>
  </div>
</template>
