<script setup>
import { useTheme } from '../composables/useTheme.js'
import { useI18n } from '../composables/useI18n.js'

defineProps({
  view:           { type: String,  required: true },
  watchlistCount: { type: Number,  default: 0 },
  history:        { type: Array,   default: () => [] },
})
defineEmits(['update:view', 'search'])

const { theme, THEMES, setTheme } = useTheme()
const { t, locale, setLocale, LOCALES } = useI18n()

const themeLabel = id => ({ dark: t('header.themeDark'), gray: t('header.themeGray'), light: t('header.themeLight') }[id] ?? id)
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-zinc-800/60 bg-zinc-950/90 backdrop-blur-md">
    <div class="px-4 md:px-6 xl:px-8 h-14 flex items-center gap-3">

      <!-- Logo -->
      <div class="flex items-center gap-2.5 shrink-0">
        <div class="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-xs select-none">S</div>
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
      </nav>

      <!-- Recent tickers (analyse view only) -->
      <div v-if="view === 'analyse' && history.length"
           class="flex items-center gap-1.5 overflow-x-auto flex-1 min-w-0">
        <span class="text-zinc-600 text-xs shrink-0">{{ t('header.recent') }}</span>
        <button v-for="h in history" :key="h" @click="$emit('search', h)"
          class="text-xs font-mono bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 px-2 py-1 rounded-md transition-colors shrink-0">
          {{ h }}
        </button>
      </div>

      <!-- Theme switcher -->
      <div class="flex gap-0.5 bg-zinc-900/60 rounded-xl p-1 shrink-0 ml-auto">
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
