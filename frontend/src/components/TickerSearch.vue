<script setup>
import { ref, computed, watch } from 'vue'
import { refDebounced, onClickOutside } from '@vueuse/core'
import { useQuery } from '@tanstack/vue-query'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: String,  default: '' },
  loading:    { type: Boolean, default: false },
  hasResult:  { type: Boolean, default: false },
  submitLabel:{ type: String,  default: '' },
  showPopular:{ type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'search'])

// Local copy synced with parent via v-model
const localInput = ref(props.modelValue)

const rootRef   = ref(null)
const acIdx     = ref(-1)
const dismissed = ref(false)   // true once the user picked/closed the dropdown
const typing    = ref(false)   // true only after a real keystroke

// A programmatic value change (dashboard navigation, history) must not open
// the autocomplete dropdown — only real typing does. Our own input events echo
// back through modelValue with the same value, so we ignore those.
watch(() => props.modelValue, v => {
  if (v === localInput.value) return   // echo of our own keystroke → keep dropdown state
  localInput.value = v
  typing.value = false
  dismissed.value = true
})

// Debounced query term (≥ 2 chars) drives the autocomplete request.
const query      = computed(() => localInput.value.trim())
const debouncedQ = refDebounced(query, 350)
const acEnabled  = computed(() => debouncedQ.value.length >= 2)

const { data: acData, isFetching: acLoading } = useQuery({
  queryKey: ['search', debouncedQ],
  enabled: acEnabled,
  placeholderData: prev => prev,   // keep previous results while typing (no flicker)
  queryFn: async () => {
    const r = await fetch(`/search?q=${encodeURIComponent(debouncedQ.value)}`)
    return r.ok ? await r.json() : []
  },
})

// Items rendered in the dropdown: fetched matches, unless dismissed or too short.
const dropdownOpen = computed(() => !dismissed.value && acEnabled.value)
const visibleItems = computed(() => (dropdownOpen.value ? (acData.value ?? []) : []))
const noResults    = computed(() =>
  dropdownOpen.value && !acLoading.value && visibleItems.value.length === 0
)

// Type → colored badge in the dropdown.
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

// Split a label into [before, match, after] to highlight the typed term.
function parts(text) {
  const s = String(text ?? '')
  const term = query.value.trim()
  if (!term) return [{ t: s, hit: false }]
  const i = s.toLowerCase().indexOf(term.toLowerCase())
  if (i < 0) return [{ t: s, hit: false }]
  return [
    { t: s.slice(0, i),               hit: false },
    { t: s.slice(i, i + term.length), hit: true  },
    { t: s.slice(i + term.length),    hit: false },
  ]
}

// A new query term (from typing) re-opens the dropdown and resets the row.
watch(debouncedQ, () => { acIdx.value = -1; if (typing.value) dismissed.value = false })
// Close the dropdown when clicking outside the component.
onClickOutside(rootRef, () => { dismissed.value = true; acIdx.value = -1 })

function onInput(e) {
  typing.value = true
  localInput.value = e.target.value
  emit('update:modelValue', localInput.value)
}

function pickAc(ticker) {
  localInput.value = ticker
  emit('update:modelValue', ticker)
  typing.value    = false
  dismissed.value = true
  acIdx.value     = -1
  emit('search', ticker)
}

function onKeydown(e) {
  if (!visibleItems.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    acIdx.value = Math.min(acIdx.value + 1, visibleItems.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    acIdx.value = Math.max(acIdx.value - 1, -1)
  } else if (e.key === 'Enter' && acIdx.value >= 0) {
    e.preventDefault()
    pickAc(visibleItems.value[acIdx.value].ticker)
  } else if (e.key === 'Escape') {
    dismissed.value = true
    acIdx.value     = -1
  }
}

function submit() {
  const code = localInput.value.trim().toUpperCase()
  if (!code) return
  typing.value    = false
  dismissed.value = true
  emit('search', code)
}

const POPULAR = ['MC.PA','AIR.PA','OR.PA','TTE.PA','RMS.PA','AAPL','NVDA','ASML.AS','BTC-USD']
</script>

<template>
  <div ref="rootRef">
    <div class="relative">
      <div class="flex gap-2">
        <!-- Input -->
        <div class="relative flex-1">
          <svg class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-600 pointer-events-none"
               fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"/>
          </svg>
          <input
            :value="localInput"
            @input="onInput"
            @keydown="onKeydown"
            @keyup.enter="acIdx < 0 && submit()"
            :placeholder="t('search.placeholder')"
            autocomplete="off" spellcheck="false"
            class="w-full bg-zinc-900 border border-zinc-700 rounded-xl pl-10 pr-9 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 text-sm transition-colors font-mono"
          />
          <div v-if="acLoading" class="absolute right-3 top-1/2 -translate-y-1/2">
            <div class="w-3.5 h-3.5 border border-zinc-600 border-t-indigo-400 rounded-full animate-spin"></div>
          </div>
        </div>

        <!-- Submit -->
        <button @click="submit()" :disabled="loading"
          class="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-40 text-white px-5 py-3 rounded-xl font-medium text-sm transition-colors whitespace-nowrap">
          <span v-if="loading" class="flex items-center gap-2">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            {{ t('search.analyzing') }}
          </span>
          <span v-else>{{ submitLabel || t('search.analyze') }}</span>
        </button>
      </div>

      <!-- Autocomplete dropdown -->
      <div v-if="dropdownOpen"
        class="absolute z-50 left-0 right-[4.5rem] top-full mt-1.5 bg-zinc-900 border border-zinc-700/80 rounded-xl overflow-hidden shadow-2xl shadow-black/60">
        <template v-if="visibleItems.length">
          <button
            v-for="(item, i) in visibleItems" :key="item.ticker"
            @mousedown.prevent="pickAc(item.ticker)"
            @mousemove="acIdx = i"
            :class="['w-full flex items-center gap-3 px-3.5 py-2.5 text-left transition-colors',
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
        </template>
        <div v-else-if="acLoading" class="flex items-center gap-2 px-4 py-3 text-xs text-zinc-500">
          <div class="w-3 h-3 border border-zinc-600 border-t-indigo-400 rounded-full animate-spin"></div>
          {{ t('search.searching') }}
        </div>
        <div v-else class="px-4 py-3 text-xs text-zinc-500">
          {{ t('search.noResults') }}
        </div>
      </div>
    </div>

    <!-- Popular suggestions -->
    <div v-if="showPopular && !hasResult && !loading" class="mt-3 flex flex-wrap gap-1.5">
      <span class="text-zinc-600 text-xs self-center mr-1">{{ t('search.popular') }}</span>
      <button v-for="s in POPULAR" :key="s" @click="$emit('search', s)"
        class="px-2.5 py-1 text-xs bg-zinc-900 hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors font-mono">
        {{ s }}
      </button>
    </div>
  </div>
</template>
