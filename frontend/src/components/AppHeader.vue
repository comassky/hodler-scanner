<script setup>
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme.js'
import { useI18n } from '../composables/useI18n.js'

defineProps({
  view:           { type: String,  required: true },
  watchlistCount: { type: Number,  default: 0 },
  history:        { type: Array,   default: () => [] },
})
defineEmits(['update:view', 'search', 'open-search'])

const { theme, THEMES, setTheme } = useTheme()
const { t, locale, setLocale, LOCALES } = useI18n()

const themeLabel = id => ({ dark: t('header.themeDark'), gray: t('header.themeGray'), light: t('header.themeLight') }[id] ?? id)

// Platform-aware shortcut hint (⌘K on macOS, Ctrl K elsewhere).
const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform || '')
const shortcutLabel = computed(() => (isMac ? '⌘K' : 'Ctrl K'))
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-zinc-800/60 bg-zinc-950/90 backdrop-blur-md">
    <div class="px-4 md:px-6 xl:px-8 h-14 flex items-center gap-3">

      <!-- Logo -->
      <div class="flex items-center gap-2.5 shrink-0">
        <svg class="w-7 h-7 select-none" viewBox="0 0 64 64" role="img" aria-label="Hodler Scanner">
          <defs>
            <linearGradient id="hdr-bg" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#111a26" />
              <stop offset="1" stop-color="#0a0f16" />
            </linearGradient>
            <linearGradient id="hdr-acc" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0" stop-color="#10b981" />
              <stop offset="1" stop-color="#34d399" />
            </linearGradient>
          </defs>
          <rect width="64" height="64" rx="15" fill="url(#hdr-bg)" />
          <rect x="1.5" y="1.5" width="61" height="61" rx="13.5" fill="none" stroke="#ffffff" stroke-opacity="0.06" />
          <polyline points="12,46 26,34 36,40 51,19" fill="none" stroke="url(#hdr-acc)" stroke-width="5"
            stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="12" cy="46" r="2.8" fill="#10b981" />
          <path d="M51 11 L58 19 L51 27 L44 19 Z" fill="url(#hdr-acc)" />
          <path d="M51 15 L54.5 19 L51 23 L47.5 19 Z" fill="#0a0f16" fill-opacity="0.35" />
        </svg>
        <span class="font-semibold text-zinc-100 tracking-tight text-sm hidden sm:block">Hodler Scanner</span>
      </div>

      <!-- Nav tabs -->
      <nav class="flex gap-1 bg-zinc-900/60 rounded-xl p-1 shrink-0">
        <button @click="$emit('update:view', 'analyse')"
          :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
            view === 'analyse' ? 'bg-zinc-800 text-zinc-100 shadow' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t('header.analysis') }}
        </button>
        <button @click="$emit('update:view', 'watchlist')"
          :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5',
            view === 'watchlist' ? 'bg-zinc-800 text-zinc-100 shadow' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t('header.dashboard') }}
          <span class="bg-zinc-700/80 text-zinc-400 px-1.5 rounded-full text-xs leading-none"
                style="padding-top:2px;padding-bottom:2px">{{ watchlistCount }}</span>
        </button>
        <button @click="$emit('update:view', 'portfolio')"
          :class="['px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
            view === 'portfolio' ? 'bg-zinc-800 text-zinc-100 shadow' : 'text-zinc-500 hover:text-zinc-300']">
          {{ t('header.portfolio') }}
        </button>
      </nav>

      <!-- Recent tickers (analyse view only) -->
      <div v-if="view === 'analyse' && history.length"
           class="flex items-center gap-1.5 overflow-x-auto flex-1 min-w-0 scroll-fade-x">
        <span class="text-zinc-600 text-xs shrink-0">{{ t('header.recent') }}</span>
        <button v-for="h in history" :key="h" @click="$emit('search', h)"
          class="text-xs font-mono bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 px-2 py-1 rounded-md transition-colors shrink-0">
          {{ h }}
        </button>
      </div>

      <!-- Quick-search shortcut -->
      <button @click="$emit('open-search')" :title="t('search.modalTitle')"
        class="ml-auto shrink-0 flex items-center gap-2 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 rounded-xl pl-2.5 pr-2 h-9 transition-colors">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"/>
        </svg>
        <kbd class="hidden sm:block text-[10px] font-mono bg-zinc-800 text-zinc-400 rounded px-1.5 py-0.5 leading-none">{{ shortcutLabel }}</kbd>
      </button>

      <!-- Theme switcher -->
      <div class="flex gap-0.5 bg-zinc-900/60 rounded-xl p-1 shrink-0">
        <button v-for="t2 in THEMES" :key="t2.id" @click="setTheme(t2.id)"
          :title="themeLabel(t2.id)"
          :class="['w-7 h-7 rounded-lg flex items-center justify-center transition-all',
            theme === t2.id ? 'bg-zinc-800 text-zinc-100 shadow' : 'text-zinc-500 hover:text-zinc-300']">
          <!-- Black: moon -->
          <svg v-if="t2.id === 'dark'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z"/>
          </svg>
          <!-- Gray: half-circle -->
          <svg v-else-if="t2.id === 'gray'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none" />
          </svg>
          <!-- Light: sun -->
          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="4" />
            <path stroke-linecap="round" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </svg>
        </button>
      </div>

      <!-- Language switcher -->
      <div class="flex gap-0.5 bg-zinc-900/60 rounded-xl p-1 shrink-0">
        <button v-for="l in LOCALES" :key="l.id" @click="setLocale(l.id)"
          :title="l.name"
          :class="['px-2 h-7 rounded-lg text-xs font-semibold transition-all',
            locale === l.id ? 'bg-zinc-800 text-zinc-100 shadow' : 'text-zinc-500 hover:text-zinc-300']">
          {{ l.label }}
        </button>
      </div>
    </div>
  </header>
</template>
