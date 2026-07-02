<script setup>
import { useFormatters } from '../composables/useFormatters.js'
import { useI18n } from '../composables/useI18n.js'

defineProps({ item: { type: Object, required: true } })
defineEmits(['analyse', 'remove'])

const { fmt, fmtPct, varColor, rsiClass, distClass, scoreColorFor } = useFormatters()
const { t } = useI18n()
</script>

<template>
  <div
    class="group relative bg-zinc-900 border border-zinc-800 hover:border-zinc-600 rounded-2xl p-4 transition-all hover:shadow-lg hover:shadow-black/20"
    :class="item.error ? '' : 'cursor-pointer'"
    @click="!item.error && $emit('analyse', item.ticker)">

    <!-- Error state -->
    <template v-if="item.error">
      <div class="h-36 flex flex-col items-center justify-center text-center gap-1.5">
        <span class="font-mono font-bold text-zinc-400 text-sm">{{ item.ticker }}</span>
        <span class="text-xs text-red-400/70 max-w-[10rem] leading-tight">{{ item.error }}</span>
      </div>
      <button @click.stop="$emit('remove', item.ticker)"
        class="w-full text-xs text-zinc-600 hover:text-red-400 transition-colors pt-2 border-t border-zinc-800">
        {{ t('dash.remove') }}
      </button>
    </template>

    <!-- Data state -->
    <template v-else>
      <!-- Delete button on hover -->
      <button @click.stop="$emit('remove', item.ticker)"
        class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center text-zinc-600 hover:text-red-400 transition-all text-base rounded-lg hover:bg-zinc-800">×</button>

      <!-- Header: ticker + score badge -->
      <div class="flex items-start justify-between mb-2 pr-4">
        <div class="min-w-0 flex-1">
          <p class="font-mono font-bold text-zinc-100 text-sm leading-tight">{{ item.ticker }}</p>
          <p class="text-xs text-zinc-500 truncate leading-snug">{{ item.name }}</p>
        </div>
        <div :class="['ml-2 px-2 py-1 rounded-lg shrink-0', scoreColorFor(item.analysis.score).bg]">
          <span :class="['text-sm font-bold font-mono', scoreColorFor(item.analysis.score).text]">{{ item.analysis.score }}</span>
        </div>
      </div>

      <!-- Price + change -->
      <div class="flex items-baseline gap-2 mb-2">
        <span class="text-xl font-bold font-mono text-zinc-100">{{ fmt(item.price.last) }}</span>
        <span :class="['text-sm font-semibold font-mono', varColor(item.price.var_jour_pct)]">
          {{ item.price.var_jour_pct >= 0 ? '+' : '' }}{{ fmt(item.price.var_jour_pct, 2) }}%
        </span>
      </div>

      <p class="text-xs text-zinc-500 mb-3 leading-tight line-clamp-1">{{ item.analysis.statut }}</p>

      <!-- Mini metrics -->
      <div class="space-y-1.5 text-xs border-t border-zinc-800/60 pt-3">
        <div class="flex justify-between">
          <span class="text-zinc-500">{{ t('dash.rsiD') }}</span>
          <span :class="['font-mono font-medium', rsiClass(item.indicators.rsi_daily)]">{{ fmt(item.indicators.rsi_daily, 1) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-zinc-500">{{ t('dash.dSma200') }}</span>
          <span :class="['font-mono font-medium', distClass(item.distances.ecart_sma200_pct)]">{{ fmtPct(item.distances.ecart_sma200_pct) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-zinc-500">{{ t('dash.trend') }}</span>
          <span :class="item.signals.tendance?.startsWith('↑') ? 'text-emerald-400' : 'text-red-400'" class="text-xs">{{ item.signals.tendance }}</span>
        </div>
      </div>

      <!-- Signal badges -->
      <div class="flex flex-wrap gap-1 mt-2.5 min-h-[20px]">
        <span v-if="item.signals.alerte_sma200 || item.signals.alerte_w50"
          class="text-xs bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded-md">{{ t('dash.alert') }}</span>
        <span v-if="item.indicators.macd_w_cross_up"
          class="text-xs bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded-md">MACD ↑</span>
        <span v-if="item.signals.divergence_rsi"
          class="text-xs bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded-md">Div RSI</span>
        <span v-if="item.cached"
          class="text-xs bg-zinc-800 text-zinc-600 px-1.5 py-0.5 rounded-md">{{ t('dash.cache') }}</span>
      </div>
    </template>
  </div>
</template>
