<script setup>
import { ref, computed, watch } from 'vue'
import { refDebounced, onClickOutside } from '@vueuse/core'
import { useQuery } from '@tanstack/vue-query'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

const props = defineProps({
  modelValue:  { type: String,  default: '' },
  disabled:    { type: Boolean, default: false },
  placeholder: { type: String,  default: '' },
})
const emit = defineEmits(['update:modelValue', 'select'])

const rootRef   = ref(null)
const acIdx     = ref(-1)
const dismissed = ref(true)   // closed until the user types
const typing    = ref(false)

// Keep the field in sync when the parent sets the value programmatically
// (e.g. clearing the form). Echoes of our own keystrokes are ignored.
const localInput = ref(props.modelValue)
watch(() => props.modelValue, v => {
  if (v === localInput.value) return
  localInput.value = v
  typing.value = false
  dismissed.value = true
})

const query      = computed(() => localInput.value.trim())
const debouncedQ = refDebounced(query, 350)
const acEnabled  = computed(() => debouncedQ.value.length >= 2)

const { data: acData, isFetching: acLoading } = useQuery({
  queryKey: ['search', debouncedQ],
  enabled: acEnabled,
  placeholderData: prev => prev,
  queryFn: async () => {
    const r = await fetch(`/search?q=${encodeURIComponent(debouncedQ.value)}`)
    return r.ok ? await r.json() : []
  },
})

const dropdownOpen  = computed(() => !dismissed.value && acEnabled.value && !props.disabled)
const visibleItems  = computed(() => (dropdownOpen.value ? (acData.value ?? []) : []))

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

watch(debouncedQ, () => { acIdx.value = -1; if (typing.value) dismissed.value = false })
onClickOutside(rootRef, () => { dismissed.value = true; acIdx.value = -1 })

function onInput(e) {
  typing.value = true
  localInput.value = e.target.value
  emit('update:modelValue', localInput.value)
}

function pick(ticker) {
  localInput.value = ticker
  emit('update:modelValue', ticker)
  emit('select', ticker)
  typing.value    = false
  dismissed.value = true
  acIdx.value     = -1
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
    pick(visibleItems.value[acIdx.value].ticker)
  } else if (e.key === 'Escape') {
    dismissed.value = true
    acIdx.value     = -1
  }
}
</script>

<template>
  <div ref="rootRef" class="relative">
    <input
      :value="localInput"
      @input="onInput"
      @keydown="onKeydown"
      :disabled="disabled"
      :placeholder="placeholder"
      autocomplete="off" spellcheck="false"
      class="w-full bg-zinc-950/60 border border-zinc-800 rounded-lg px-3 py-2 text-sm font-mono text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 disabled:opacity-60" />
    <div v-if="acLoading && dropdownOpen" class="absolute right-3 top-1/2 -translate-y-1/2">
      <div class="w-3.5 h-3.5 border border-zinc-600 border-t-indigo-400 rounded-full animate-spin"></div>
    </div>

    <!-- Autocomplete dropdown -->
    <div v-if="dropdownOpen"
      class="absolute z-50 left-0 right-0 top-full mt-1.5 bg-zinc-900 border border-zinc-700/80 rounded-xl overflow-hidden shadow-2xl shadow-black/60">
      <template v-if="visibleItems.length">
        <button
          v-for="(item, i) in visibleItems" :key="item.ticker" type="button"
          @mousedown.prevent="pick(item.ticker)"
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
</template>
