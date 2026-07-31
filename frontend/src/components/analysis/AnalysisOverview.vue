<script setup lang="ts">
import { computed } from 'vue'
import InfoTip from '../InfoTip.vue'
import { useFormatters } from '../../composables/useFormatters'
import { useI18n } from '../../composables/useI18n'
import type { Analysis } from '../../types/analysis'

const props = defineProps<{
  data: Analysis
  isWatchlisted?: boolean
  loading?: boolean
}>()
const emit = defineEmits<{
  toggle: [ticker: string]
  refresh: [ticker: string]
}>()

const { t } = useI18n()
const { fmt, varColor, tendanceBadgeClass, regimeBadgeClass, scoreStatus } = useFormatters()

const d = computed(() => props.data)
const score = computed(() => scoreStatus(d.value?.analysis?.score))
</script>

<template>
  <div id="section-apercu" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div class="min-w-0 lg:max-w-md">
        <div class="flex flex-wrap items-center gap-2 mb-1">
          <span class="text-2xl font-bold tracking-tight font-mono">{{ d.ticker }}</span>
          <button @click="emit('toggle', d.ticker)"
            :class="['px-2.5 py-1 rounded-lg text-xs font-medium transition-all border',
              isWatchlisted
                ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-400 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400'
                : 'border-zinc-700 text-zinc-500 hover:border-indigo-500/40 hover:text-indigo-400']">
            {{ isWatchlisted ? t('app.following') : t('app.follow') }}
          </button>
          <button @click="emit('refresh', d.ticker)" :disabled="loading"
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
        <p :class="['text-sm font-semibold mb-2', score.text]">{{ d.analysis.synthese.verdict }}</p>
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
        <div :class="['flex flex-col items-center justify-center px-5 py-4 rounded-2xl', score.ring, score.bg]">
          <span :class="['text-4xl font-bold tabular-nums font-mono', score.text]">{{ d.analysis.score }}</span>
          <span class="text-zinc-500 text-xs mt-1">{{ t('app.outOf100') }}</span>
          <span :class="['text-xs font-semibold mt-2 tracking-wide', score.text]">{{ t(score.labelKey) }}</span>
          <div class="relative w-20 h-1 bg-zinc-800 rounded-full mt-3">
            <div :class="['h-full rounded-full transition-all duration-700', score.bar]"
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
        <span v-if="d.signals.regime"
          :class="['inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium', regimeBadgeClass(d.signals.regime)]">
          <span class="opacity-60 text-xs uppercase tracking-wide">{{ t('regime.label') }}</span>{{ t('regime.' + d.signals.regime) }}<InfoTip v-bind="t('info.regime')" />
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
</template>
