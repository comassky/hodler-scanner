<script setup>
import { computed } from 'vue'
import InfoTip from '../InfoTip.vue'
import { useFormatters } from '../../composables/useFormatters.js'
import { useI18n } from '../../composables/useI18n.js'

const props = defineProps({
  contribs: { type: Array,  required: true },   // [{ key, val, label }]
  max:      { type: Number, default: 1 },
  score:    { type: Number, default: 0 },
})

const { t } = useI18n()
const { scoreCompClass, scoreStatus } = useFormatters()
const status = computed(() => scoreStatus(props.score))
</script>

<template>
  <div id="section-score" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-1">{{ t('app.scoreContribution') }}<InfoTip v-bind="t('info.scoreContribution')" /></h2>
    <p class="text-xs text-zinc-600 mb-4">{{ t('app.neutralBase') }} <span class="font-mono text-zinc-500">40</span> · {{ t('app.result') }} <span :class="['font-mono font-semibold', status.text]">{{ score }}/100</span></p>
    <div class="space-y-1.5">
      <div v-for="c in contribs" :key="c.key" class="flex items-center gap-2">
        <span class="w-20 shrink-0 text-xs text-zinc-400 text-right truncate">{{ c.label }}</span>
        <div class="relative flex-1 h-5">
          <div class="absolute inset-y-0 left-1/2 w-px bg-zinc-700/70"></div>
          <div v-if="c.val > 0" class="absolute inset-y-1 left-1/2 rounded-r bg-emerald-500/70"
               :style="{ width: (c.val / max * 50) + '%' }"></div>
          <div v-else-if="c.val < 0" class="absolute inset-y-1 rounded-l bg-red-500/70"
               :style="{ right: '50%', width: (Math.abs(c.val) / max * 50) + '%' }"></div>
          <div v-else class="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center">
            <span class="w-1 h-1 rounded-full bg-zinc-600"></span>
          </div>
        </div>
        <span :class="['w-9 shrink-0 text-xs font-mono font-semibold text-right', scoreCompClass(c.val)]">
          {{ c.val > 0 ? '+' : '' }}{{ c.val }}
        </span>
      </div>
    </div>
  </div>
</template>
