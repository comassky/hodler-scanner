<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'confirm'])

const panelEl = ref(null)
let _prevFocus = null
const busy = ref(false)

// One switch per data type. Caches & stored backtests default ON (safe / rebuildable);
// user data (watchlist, portfolio) and the ticker dictionary default OFF.
const options = ref({
  caches:    true,
  backtests: true,
  watchlist: false,
  portfolio: false,
  tickers:   false,
})

const TYPES = [
  { key: 'caches',    danger: false },
  { key: 'backtests', danger: false },
  { key: 'watchlist', danger: true },
  { key: 'portfolio', danger: true },
  { key: 'tickers',   danger: true },
]

const anySelected = computed(() => Object.values(options.value).some(Boolean))

watch(() => props.open, (v) => {
  if (v) {
    _prevFocus = document.activeElement
    busy.value = false
    nextTick(() => panelEl.value?.querySelector('button')?.focus())
  } else if (_prevFocus && typeof _prevFocus.focus === 'function') {
    _prevFocus.focus()
    _prevFocus = null
  }
})

async function confirm() {
  if (!anySelected.value || busy.value) return
  busy.value = true
  // Parent awaits the request; keep the modal busy until it resolves the promise.
  emit('confirm', { ...options.value }, () => { busy.value = false; emit('close') })
}

function trapTab(e) {
  const root = panelEl.value
  if (!root) return
  const nodes = root.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
  if (!nodes.length) return
  const first = nodes[0]
  const last  = nodes[nodes.length - 1]
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault(); last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault(); first.focus()
  }
}

function onKeydown(e) {
  if (e.key === 'Escape' && !busy.value) { emit('close'); return }
  if (e.key === 'Tab') trapTab(e)
}
</script>

<template>
  <Transition name="fade">
    <div v-if="open"
      class="fixed inset-0 z-[100] flex items-start justify-center px-4 pt-[12vh] bg-black/60 backdrop-blur-sm"
      @mousedown.self="!busy && emit('close')">
      <div ref="panelEl" role="dialog" aria-modal="true" :aria-label="t('reset.title')"
        class="w-full max-w-lg bg-zinc-900 border border-zinc-700/80 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden"
        @keydown="onKeydown">

        <!-- Header -->
        <div class="flex items-start gap-3 px-5 pt-5 pb-4 border-b border-zinc-800">
          <div class="w-9 h-9 rounded-xl bg-red-500/10 text-red-400 flex items-center justify-center shrink-0">
            <svg class="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
            </svg>
          </div>
          <div class="min-w-0">
            <h2 class="text-sm font-semibold text-zinc-100">{{ t('reset.title') }}</h2>
            <p class="text-xs text-zinc-500 mt-0.5">{{ t('reset.subtitle') }}</p>
          </div>
        </div>

        <!-- Toggles -->
        <div class="px-5 py-4 space-y-1.5">
          <label v-for="o in TYPES" :key="o.key"
            class="flex items-center gap-3 py-2 px-3 rounded-xl hover:bg-zinc-800/50 cursor-pointer transition-colors">
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-zinc-200 flex items-center gap-2">
                {{ t(`reset.${o.key}`) }}
                <span v-if="o.danger"
                  class="text-[10px] font-semibold uppercase tracking-wide text-red-400/80 bg-red-500/10 px-1.5 py-0.5 rounded">
                  {{ t('reset.userData') }}
                </span>
              </p>
              <p class="text-xs text-zinc-500 mt-0.5">{{ t(`reset.${o.key}Desc`) }}</p>
            </div>
            <!-- Switch -->
            <button type="button" role="switch" :aria-checked="options[o.key]"
              @click="options[o.key] = !options[o.key]"
              :class="['relative w-10 h-6 rounded-full shrink-0 transition-colors',
                options[o.key] ? (o.danger ? 'bg-red-500' : 'bg-indigo-500') : 'bg-zinc-700']">
              <span :class="['absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform',
                options[o.key] ? 'translate-x-4' : 'translate-x-0']"></span>
            </button>
          </label>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between gap-3 px-5 py-3.5 border-t border-zinc-800 bg-zinc-950/40">
          <p class="text-[11px] text-zinc-600">
            {{ anySelected ? t('reset.irreversible') : t('reset.none') }}
          </p>
          <div class="flex gap-2 shrink-0">
            <button @click="emit('close')" :disabled="busy"
              class="h-9 px-4 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm transition-colors disabled:opacity-50">
              {{ t('reset.cancel') }}
            </button>
            <button @click="confirm" :disabled="!anySelected || busy"
              class="h-9 px-4 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2">
              <svg v-if="busy" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ t('reset.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
