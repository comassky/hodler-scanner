<script setup>
import { computed } from 'vue'
import InfoTip from '../InfoTip.vue'
import { useI18n } from '../../composables/useI18n.js'

const props = defineProps({
  diagnostics: { type: Array, default: () => [] },
})

const { t } = useI18n()
const forces     = computed(() => props.diagnostics.filter(x => x.impact > 0))
const vigilances = computed(() => props.diagnostics.filter(x => x.impact < 0))
const neutres    = computed(() => props.diagnostics.filter(x => x.impact === 0))
</script>

<template>
  <div id="section-forces" class="scroll-mt-28 grid grid-cols-1 md:grid-cols-2 gap-3">
    <!-- Strengths -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <h2 class="flex items-center text-xs font-semibold text-emerald-400/90 uppercase tracking-widest mb-4">
        {{ t('app.forces') }}
        <span class="ml-2 bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded text-xs">{{ forces.length }}</span>
        <InfoTip v-bind="t('info.forces')" />
      </h2>
      <ul v-if="forces.length" class="space-y-3">
        <li v-for="(diag, i) in forces" :key="i" class="flex gap-2.5 text-sm text-zinc-300 leading-relaxed">
          <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 bg-emerald-500"></span>
          <span class="flex-1">{{ diag.text }}</span>
          <span class="text-emerald-400 font-mono text-xs font-semibold shrink-0">+{{ diag.impact }}</span>
        </li>
      </ul>
      <p v-else class="text-sm text-zinc-600">{{ t('app.noForce') }}</p>
    </div>
    <!-- Watch-outs -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <h2 class="flex items-center text-xs font-semibold text-amber-400/90 uppercase tracking-widest mb-4">
        {{ t('app.watchpoints') }}
        <span class="ml-2 bg-amber-500/15 text-amber-400 px-1.5 py-0.5 rounded text-xs">{{ vigilances.length }}</span>
        <InfoTip v-bind="t('info.watchpoints')" />
      </h2>
      <ul v-if="vigilances.length" class="space-y-3">
        <li v-for="(diag, i) in vigilances" :key="i" class="flex gap-2.5 text-sm text-zinc-300 leading-relaxed">
          <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 bg-red-500"></span>
          <span class="flex-1">{{ diag.text }}</span>
          <span class="text-red-400 font-mono text-xs font-semibold shrink-0">{{ diag.impact }}</span>
        </li>
      </ul>
      <p v-else class="text-sm text-zinc-600">{{ t('app.noRisk') }}</p>
    </div>
    <!-- Neutral context -->
    <div v-if="neutres.length" class="md:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">{{ t('app.context') }}<InfoTip v-bind="t('info.context')" /></h2>
      <ul class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
        <li v-for="(diag, i) in neutres" :key="i" class="flex gap-2.5 text-sm text-zinc-400 leading-relaxed">
          <span class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 bg-zinc-600"></span>
          <span>{{ diag.text }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
