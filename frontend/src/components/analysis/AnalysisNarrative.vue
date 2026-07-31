<script setup lang="ts">
import { computed } from 'vue'
import InfoTip from '../InfoTip.vue'
import { useFormatters } from '../../composables/useFormatters'
import { useI18n } from '../../composables/useI18n'
import type { AnalysisBlock } from '../../types/analysis'

const props = defineProps<{
  analysis: AnalysisBlock
}>()

const { t } = useI18n()
const { scoreStatus } = useFormatters()
const score = computed(() => scoreStatus(props.analysis?.score))
</script>

<template>
  <div id="section-analyse" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">{{ t('app.analysis') }}<InfoTip v-bind="t('info.analysis')" /></h2>
    <div v-if="analysis.synthese"
      :class="['rounded-xl p-4 mb-5 ring-1', score.bg, score.ring]">
      <div class="flex items-center gap-2 mb-3">
        <span :class="['w-1.5 h-1.5 rounded-full shrink-0', score.bar]"></span>
        <p :class="['text-sm font-bold tracking-wide', score.text]">{{ analysis.synthese.verdict }}</p>
        <InfoTip v-bind="t('info.synthese')" />
      </div>
      <div class="space-y-1.5 pl-3.5">
        <div v-if="analysis.synthese.atout" class="flex items-baseline gap-2.5 text-sm">
          <span class="text-emerald-400 text-xs shrink-0">▲</span>
          <span class="text-zinc-500 shrink-0 w-14">{{ t('app.asset') }}</span>
          <span class="text-zinc-200">{{ analysis.synthese.atout }}</span>
        </div>
        <div v-if="analysis.synthese.risque" class="flex items-baseline gap-2.5 text-sm">
          <span class="text-amber-400 text-xs shrink-0">▼</span>
          <span class="text-zinc-500 shrink-0 w-14">{{ t('app.risk') }}</span>
          <span class="text-zinc-200">{{ analysis.synthese.risque }}</span>
        </div>
      </div>
    </div>
    <div class="space-y-5">
      <div class="flex items-start gap-3">
        <div :class="['w-1.5 h-1.5 mt-2 rounded-full shrink-0', score.bar]"></div>
        <div>
          <p class="text-xs text-zinc-500 mb-1">{{ t('app.status') }}</p>
          <p class="text-zinc-100 font-semibold">{{ analysis.statut }}</p>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <div class="w-1.5 h-1.5 mt-2 rounded-full shrink-0 bg-zinc-600"></div>
        <div>
          <p class="text-xs text-zinc-500 mb-1">{{ t('app.explanation') }}</p>
          <p class="text-zinc-300 text-sm leading-relaxed">{{ analysis.explication }}</p>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <div class="w-1.5 h-1.5 mt-2 rounded-full shrink-0 bg-indigo-500"></div>
        <div>
          <p class="text-xs text-zinc-500 mb-1">{{ t('app.strategy') }}</p>
          <p class="text-zinc-300 text-sm leading-relaxed">{{ analysis.strategie }}</p>
        </div>
      </div>
      <div class="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800/50">
        <p class="text-xs text-zinc-500 mb-2">{{ t('app.targetsStop') }}</p>
        <p class="text-zinc-300 text-sm leading-relaxed whitespace-pre-line font-mono">{{ analysis.objectifs }}</p>
      </div>
    </div>
  </div>
</template>
