<script setup lang="ts">
import InfoTip from '../InfoTip.vue'
import { useFormatters } from '../../composables/useFormatters'
import { useI18n } from '../../composables/useI18n'
import type { AnalysisIndicators } from '../../types/analysis'

defineProps<{
  indicators: AnalysisIndicators
}>()

const { t } = useI18n()
const { fmt, rsiClass, rsiBarClass, macdClass } = useFormatters()
</script>

<template>
  <div id="section-indicateurs" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.indicators') }}<InfoTip v-bind="t('info.indicators')" /></h2>
    <div class="space-y-4">
      <!-- RSI Daily -->
      <div>
        <div class="flex justify-between items-center mb-1.5">
          <span class="flex items-center text-xs text-zinc-400">{{ t('ind.rsiDaily') }}<InfoTip v-bind="t('info.rsiDaily')" /></span>
          <span :class="['text-sm font-semibold font-mono', rsiClass(indicators.rsi_daily)]">
            {{ fmt(indicators.rsi_daily, 1) }}
            <span class="text-xs opacity-60">
              {{ indicators.rsi_daily <= 35 ? t('ind.oversold') : indicators.rsi_daily >= 70 ? t('ind.overbought') : t('ind.neutral') }}
            </span>
          </span>
        </div>
        <div class="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div class="absolute inset-y-0 left-0 bg-emerald-500/15 rounded-l-full" style="width:35%"></div>
          <div class="absolute inset-y-0 right-0 bg-red-500/15 rounded-r-full" style="width:30%"></div>
          <div :class="['absolute top-0 h-full w-1 rounded-full -translate-x-1/2', rsiBarClass(indicators.rsi_daily)]"
               :style="{ left: Math.min(100, indicators.rsi_daily) + '%' }"></div>
        </div>
      </div>
      <!-- RSI Weekly -->
      <div>
        <div class="flex justify-between items-center mb-1.5">
          <span class="flex items-center text-xs text-zinc-400">{{ t('ind.rsiWeekly') }}<InfoTip v-bind="t('info.rsiWeekly')" /></span>
          <span :class="['text-sm font-semibold font-mono', rsiClass(indicators.rsi_weekly)]">{{ fmt(indicators.rsi_weekly, 1) }}</span>
        </div>
        <div class="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div class="absolute inset-y-0 left-0 bg-emerald-500/15 rounded-l-full" style="width:35%"></div>
          <div class="absolute inset-y-0 right-0 bg-red-500/15 rounded-r-full" style="width:30%"></div>
          <div :class="['absolute top-0 h-full w-1 rounded-full -translate-x-1/2', rsiBarClass(indicators.rsi_weekly)]"
               :style="{ left: Math.min(100, indicators.rsi_weekly) + '%' }"></div>
        </div>
      </div>
      <!-- BB %B -->
      <div>
        <div class="flex justify-between items-center mb-1.5">
          <span class="flex items-center text-xs text-zinc-400">{{ t('ind.bbPct') }}<InfoTip v-bind="t('info.bbPct')" /></span>
          <span :class="['text-sm font-semibold font-mono', indicators.bb_pct < 0.2 ? 'text-emerald-400' : indicators.bb_pct > 0.8 ? 'text-amber-400' : 'text-zinc-300']">
            {{ fmt(indicators.bb_pct, 3) }}
          </span>
        </div>
        <div class="relative h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div class="absolute inset-y-0 left-0 bg-emerald-500/15 rounded-l-full" style="width:20%"></div>
          <div class="absolute inset-y-0 right-0 bg-amber-500/15 rounded-r-full" style="width:20%"></div>
          <div class="absolute top-0 h-full w-1 bg-zinc-400 rounded-full -translate-x-1/2"
               :style="{ left: Math.max(0, Math.min(100, indicators.bb_pct * 100)) + '%' }"></div>
        </div>
        <div class="flex justify-between text-zinc-700 text-xs mt-1 font-mono">
          <span>0</span><span>0.5</span><span>1</span>
        </div>
      </div>
      <!-- RVOL -->
      <div class="flex justify-between items-center">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.rvol') }}<InfoTip v-bind="t('info.rvol')" /></span>
        <span :class="['text-sm font-semibold font-mono', indicators.rvol >= 2 ? 'text-amber-400' : indicators.rvol < 0.8 ? 'text-emerald-400' : 'text-zinc-300']">
          {{ fmt(indicators.rvol, 2) }}×
        </span>
      </div>
      <!-- MACD -->
      <div class="flex justify-between items-center">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.macdWeekly') }}<InfoTip v-bind="t('info.macdWeekly')" /></span>
        <div class="flex items-center gap-2">
          <span v-if="indicators.macd_w_cross_up"
            class="text-xs bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded">{{ t('ind.crossUp') }}</span>
          <span :class="['text-sm font-semibold font-mono', macdClass(indicators.macd_w_hist)]">
            {{ indicators.macd_w_hist >= 0 ? '+' : '' }}{{ fmt(indicators.macd_w_hist, 4) }}
          </span>
        </div>
      </div>
      <!-- SMA slope -->
      <div class="flex justify-between items-center">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.smaSlope') }}<InfoTip v-bind="t('info.smaSlope')" /></span>
        <span :class="['text-sm font-semibold font-mono', indicators.sma200_slope_20j_pct > 0.3 ? 'text-emerald-400' : indicators.sma200_slope_20j_pct < -0.3 ? 'text-red-400' : 'text-zinc-400']">
          {{ indicators.sma200_slope_20j_pct >= 0 ? '+' : '' }}{{ fmt(indicators.sma200_slope_20j_pct, 2) }}%
        </span>
      </div>
      <!-- ATR 14 -->
      <div v-if="indicators.atr14 != null" class="flex justify-between items-center border-t border-zinc-800/40 pt-2 mt-1">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.atr14') }}<InfoTip v-bind="t('info.atr14')" /></span>
        <div class="flex items-center gap-1.5">
          <span class="text-sm font-semibold font-mono text-zinc-300">{{ fmt(indicators.atr14) }}</span>
          <span class="text-xs text-zinc-600">({{ fmt(indicators.atr14_pct, 1) }}%)</span>
        </div>
      </div>
      <!-- ADX 14 -->
      <div v-if="indicators.adx14 != null" class="flex justify-between items-center">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.adx14') }}<InfoTip v-bind="t('info.adx14')" /></span>
        <span :class="['text-sm font-semibold font-mono', indicators.adx14 >= 25 ? 'text-emerald-400' : indicators.adx14 < 20 ? 'text-zinc-500' : 'text-zinc-300']">
          {{ fmt(indicators.adx14, 1) }}
        </span>
      </div>
      <!-- Choppiness 14 -->
      <div v-if="indicators.chop14 != null" class="flex justify-between items-center">
        <span class="flex items-center text-xs text-zinc-400">{{ t('ind.chop14') }}<InfoTip v-bind="t('info.chop14')" /></span>
        <span :class="['text-sm font-semibold font-mono', indicators.chop14 >= 61.8 ? 'text-sky-400' : indicators.chop14 < 38.2 ? 'text-emerald-400' : 'text-zinc-300']">
          {{ fmt(indicators.chop14, 1) }}
        </span>
      </div>
    </div>
  </div>
</template>
