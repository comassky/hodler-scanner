<script setup>
import { ref, watch } from 'vue'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: String,  default: '' },
  loading:    { type: Boolean, default: false },
  hasResult:  { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'search'])

// Local copy synced with parent via v-model
const localInput = ref(props.modelValue)
watch(() => props.modelValue, v => { localInput.value = v })

const acItems   = ref([])
const acIdx     = ref(-1)
const acLoading = ref(false)
let acTimer = null
let acSeq   = 0

function onInput(e) {
  localInput.value = e.target.value
  emit('update:modelValue', localInput.value)
  acIdx.value = -1
  const q = localInput.value.trim()
  clearTimeout(acTimer)
  if (q.length < 2) { acItems.value = []; return }
  acTimer = setTimeout(async () => {
    const seq = ++acSeq           // anti-race token
    acLoading.value = true
    try {
      const r = await fetch(`/search?q=${encodeURIComponent(q)}`)
      const items = r.ok ? await r.json() : []
      if (seq === acSeq) acItems.value = items   // ignore stale responses
    } catch { if (seq === acSeq) acItems.value = [] }
    finally { if (seq === acSeq) acLoading.value = false }
  }, 350)
}

function closeAc() {
  setTimeout(() => { acItems.value = []; acIdx.value = -1 }, 150)
}

function pickAc(ticker) {
  localInput.value = ticker
  emit('update:modelValue', ticker)
  acItems.value = []
  acIdx.value   = -1
  emit('search', ticker)
}

function onKeydown(e) {
  if (!acItems.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    acIdx.value = Math.min(acIdx.value + 1, acItems.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    acIdx.value = Math.max(acIdx.value - 1, -1)
  } else if (e.key === 'Enter' && acIdx.value >= 0) {
    e.preventDefault()
    pickAc(acItems.value[acIdx.value].ticker)
  } else if (e.key === 'Escape') {
    acItems.value = []
    acIdx.value   = -1
  }
}

function submit() {
  const code = localInput.value.trim().toUpperCase()
  if (!code) return
  acItems.value = []
  emit('search', code)
}

const POPULAR = ['MC.PA','AIR.PA','OR.PA','TTE.PA','RMS.PA','AAPL','NVDA','ASML.AS','BTC-USD']
</script>

<template>
  <div>
    <div class="relative">
      <div class="flex gap-2">
        <!-- Input -->
        <div class="relative flex-1">
          <input
            :value="localInput"
            @input="onInput"
            @keydown="onKeydown"
            @keyup.enter="acIdx < 0 && submit()"
            @blur="closeAc"
            :placeholder="t('search.placeholder')"
            autocomplete="off" spellcheck="false"
            class="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 text-sm transition-colors font-mono"
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
          <span v-else>{{ t('search.analyze') }}</span>
        </button>
      </div>

      <!-- Autocomplete dropdown -->
      <div v-if="acItems.length"
        class="absolute z-50 left-0 right-[4.5rem] top-full mt-1.5 bg-zinc-900 border border-zinc-700/80 rounded-xl overflow-hidden shadow-2xl shadow-black/60">
        <button
          v-for="(item, i) in acItems" :key="item.ticker"
          @mousedown.prevent="pickAc(item.ticker)"
          :class="['w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
            acIdx === i ? 'bg-indigo-600/20' : 'hover:bg-zinc-800/80']">
          <span class="font-mono text-sm font-semibold text-zinc-100 w-24 shrink-0">{{ item.ticker }}</span>
          <span class="text-sm text-zinc-400 flex-1 truncate">{{ item.name }}</span>
          <span class="text-xs text-zinc-600 shrink-0 hidden sm:block">{{ item.exchange }}</span>
          <span class="text-xs bg-zinc-800 text-zinc-500 px-1.5 py-0.5 rounded shrink-0">{{ item.type }}</span>
        </button>
      </div>
    </div>

    <!-- Popular suggestions -->
    <div v-if="!hasResult && !loading" class="mt-3 flex flex-wrap gap-1.5">
      <span class="text-zinc-600 text-xs self-center mr-1">{{ t('search.popular') }}</span>
      <button v-for="s in POPULAR" :key="s" @click="$emit('search', s)"
        class="px-2.5 py-1 text-xs bg-zinc-900 hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors font-mono">
        {{ s }}
      </button>
    </div>
  </div>
</template>
