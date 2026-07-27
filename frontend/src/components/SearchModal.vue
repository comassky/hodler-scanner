<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { refDebounced } from '@vueuse/core'
import { useQuery } from '@tanstack/vue-query'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'search'])

const inputEl = ref(null)
const panelEl = ref(null)
const term    = ref('')
const acIdx   = ref(-1)
let _prevFocus = null

// Debounced query term (≥ 2 chars) drives the search request.
const query      = computed(() => term.value.trim())
const debouncedQ = refDebounced(query, 300)
const enabled    = computed(() => debouncedQ.value.length >= 2)

const { data: acData, isFetching: acLoading } = useQuery({
  queryKey: ['search', debouncedQ],
  enabled,
  placeholderData: prev => prev,
  queryFn: async () => {
    const r = await fetch(`/search?q=${encodeURIComponent(debouncedQ.value)}`)
    return r.ok ? await r.json() : []
  },
})

const items     = computed(() => (enabled.value ? (acData.value ?? []) : []))
const noResults = computed(() => enabled.value && !acLoading.value && items.value.length === 0)

// Type → colored badge (mirrors TickerSearch).
const TYPE_STYLES = {
  Equity:         'bg-sky-500/15 text-sky-300',
  ETF:            'bg-violet-500/15 text-violet-300',
  Index:          'bg-amber-500/15 text-amber-300',
  Cryptocurrency: 'bg-emerald-500/15 text-emerald-300',
  Currency:       'bg-teal-500/15 text-teal-300',
  Fund:           'bg-indigo-500/15 text-indigo-300',
  Future:         'bg-rose-500/15 text-rose-300',
}
const typeClass = ty => TYPE_STYLES[ty] || 'bg-zinc-800 text-zinc-500'

// Highlight the typed term inside a label.
function parts(text) {
  const s = String(text ?? '')
  const q = query.value
  if (!q) return [{ t: s, hit: false }]
  const i = s.toLowerCase().indexOf(q.toLowerCase())
  if (i < 0) return [{ t: s, hit: false }]
  return [
    { t: s.slice(0, i),          hit: false },
    { t: s.slice(i, i + q.length), hit: true },
    { t: s.slice(i + q.length),  hit: false },
  ]
}

watch(debouncedQ, () => { acIdx.value = -1 })

// Reset + focus each time the modal opens; restore focus to the trigger on close.
watch(() => props.open, (v) => {
  if (v) {
    _prevFocus = document.activeElement
    term.value = ''
    acIdx.value = -1
    nextTick(() => inputEl.value?.focus())
  } else if (_prevFocus && typeof _prevFocus.focus === 'function') {
    _prevFocus.focus()
    _prevFocus = null
  }
})

function pick(ticker) {
  if (!ticker) return
  emit('search', ticker)
  emit('close')
}

function submitRaw() {
  const code = term.value.trim().toUpperCase()
  if (code) pick(code)
}

// Keep Tab focus inside the dialog (basic focus trap).
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
  if (e.key === 'Escape') { emit('close'); return }
  if (e.key === 'Tab') { trapTab(e); return }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (items.value.length) acIdx.value = Math.min(acIdx.value + 1, items.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    acIdx.value = Math.max(acIdx.value - 1, -1)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (acIdx.value >= 0 && items.value[acIdx.value]) pick(items.value[acIdx.value].ticker)
    else submitRaw()
  }
}
</script>

<template>
  <Transition name="fade">
    <div v-if="open"
      class="fixed inset-0 z-[100] flex items-start justify-center px-4 pt-[12vh] bg-black/60 backdrop-blur-sm"
      @mousedown.self="emit('close')">
      <div ref="panelEl" role="dialog" aria-modal="true" :aria-label="t('search.modalTitle')"
        class="w-full max-w-xl bg-zinc-900 border border-zinc-700/80 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden"
        @keydown="onKeydown">
        <!-- Input -->
        <div class="relative border-b border-zinc-800">
          <svg class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600 pointer-events-none"
               fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"/>
          </svg>
          <input
            ref="inputEl"
            v-model="term"
            :placeholder="t('search.placeholder')"
            autocomplete="off" spellcheck="false"
            class="w-full bg-transparent pl-11 pr-10 py-4 text-zinc-100 placeholder-zinc-600 focus:outline-none text-sm font-mono"
          />
          <div v-if="acLoading" class="absolute right-4 top-1/2 -translate-y-1/2">
            <div class="w-3.5 h-3.5 border border-zinc-600 border-t-indigo-400 rounded-full animate-spin"></div>
          </div>
        </div>

        <!-- Results -->
        <div v-if="items.length" class="max-h-80 overflow-y-auto py-1.5">
          <button
            v-for="(item, i) in items" :key="item.ticker"
            @mousedown.prevent="pick(item.ticker)"
            @mousemove="acIdx = i"
            :class="['w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
              acIdx === i ? 'bg-indigo-600/20' : 'hover:bg-zinc-800/70']">
            <span class="font-mono text-sm font-semibold text-zinc-100 w-24 shrink-0 truncate">
              <template v-for="(p, k) in parts(item.ticker)" :key="k"><span :class="p.hit ? 'text-indigo-300' : ''">{{ p.t }}</span></template>
            </span>
            <span class="text-sm text-zinc-400 flex-1 truncate">
              <template v-for="(p, k) in parts(item.name)" :key="k"><span :class="p.hit ? 'text-zinc-100 font-medium' : ''">{{ p.t }}</span></template>
            </span>
            <span v-if="item.exchange" class="text-xs text-zinc-600 shrink-0 hidden sm:block">{{ item.exchange }}</span>
            <span v-if="item.type"
              :class="['text-[10px] font-medium px-1.5 py-0.5 rounded shrink-0', typeClass(item.type)]">{{ item.type }}</span>
          </button>
        </div>
        <div v-else-if="acLoading" class="flex items-center gap-2 px-4 py-4 text-xs text-zinc-500">
          <div class="w-3 h-3 border border-zinc-600 border-t-indigo-400 rounded-full animate-spin"></div>
          {{ t('search.searching') }}
        </div>
        <div v-else-if="noResults" class="px-4 py-4 text-xs text-zinc-500">
          {{ t('search.noResults') }}
        </div>

        <!-- Footer hints -->
        <div class="flex items-center gap-4 px-4 py-2.5 border-t border-zinc-800 text-[11px] text-zinc-600">
          <span class="flex items-center gap-1"><kbd class="px-1.5 py-0.5 bg-zinc-800 rounded text-zinc-400 font-mono">↑↓</kbd>{{ t('search.navHint') }}</span>
          <span class="flex items-center gap-1"><kbd class="px-1.5 py-0.5 bg-zinc-800 rounded text-zinc-400 font-mono">↵</kbd>{{ t('search.selectHint') }}</span>
          <span class="flex items-center gap-1"><kbd class="px-1.5 py-0.5 bg-zinc-800 rounded text-zinc-400 font-mono">esc</kbd>{{ t('search.closeHint') }}</span>
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
