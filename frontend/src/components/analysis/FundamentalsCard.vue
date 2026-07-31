<script setup lang="ts">
import InfoTip from '../InfoTip.vue'
import { useFormatters } from '../../composables/useFormatters'
import { useI18n } from '../../composables/useI18n'
import type { Fundamentals } from '../../types/market'

defineProps<{
  fundamentals?: Fundamentals | null
  loading?: boolean
}>()

const { t } = useI18n()
const { fmt, fmtMarketCap } = useFormatters()
</script>

<template>
  <div id="section-fondamentaux" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.fundamentals') }}<InfoTip v-bind="t('info.fundamentals')" /></h2>
    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-7 gap-3">
      <div v-for="n in 7" :key="n" class="space-y-1.5">
        <div class="h-3 w-16 bg-zinc-800/60 rounded animate-pulse"></div>
        <div class="h-4 w-20 bg-zinc-800/60 rounded animate-pulse"></div>
      </div>
    </div>
    <p v-else-if="!fundamentals" class="text-sm text-zinc-500">{{ t('app.fundamentalsUnavailable') }}</p>
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-7 gap-3">
      <div v-if="fundamentals.market_cap">
        <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.marketCap') }}</p>
        <p class="text-sm font-semibold font-mono text-zinc-100">{{ fmtMarketCap(fundamentals.market_cap) }}</p>
      </div>
      <div v-if="fundamentals.pe_trailing != null">
        <p class="flex items-center text-xs text-zinc-500 mb-0.5">{{ t('fund.peTtm') }}<InfoTip v-bind="t('info.peTtm')" /></p>
        <p class="text-sm font-semibold font-mono text-zinc-100">{{ fmt(fundamentals.pe_trailing, 1) }}×</p>
      </div>
      <div v-if="fundamentals.pe_forward != null">
        <p class="flex items-center text-xs text-zinc-500 mb-0.5">{{ t('fund.peForward') }}<InfoTip v-bind="t('info.peForward')" /></p>
        <p class="text-sm font-semibold font-mono text-zinc-100">{{ fmt(fundamentals.pe_forward, 1) }}×</p>
      </div>
      <div v-if="fundamentals.sector">
        <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.sector') }}</p>
        <p class="text-sm text-zinc-200 truncate">{{ fundamentals.sector }}</p>
      </div>
      <div v-if="fundamentals.industry">
        <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.industry') }}</p>
        <p class="text-sm text-zinc-300 truncate">{{ fundamentals.industry }}</p>
      </div>
      <div v-if="fundamentals.country">
        <p class="text-xs text-zinc-500 mb-0.5">{{ t('fund.country') }}</p>
        <p class="text-sm text-zinc-200">{{ fundamentals.country }}</p>
      </div>
      <div v-if="fundamentals.earnings_date">
        <p class="flex items-center text-xs text-zinc-500 mb-0.5">{{ t('fund.earnings') }}<InfoTip v-bind="t('info.earnings')" /></p>
        <p class="text-sm font-semibold text-indigo-400">{{ fundamentals.earnings_date }}</p>
      </div>
    </div>
  </div>
</template>
