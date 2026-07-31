<script setup lang="ts">
import { computed, ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'
import type { ThemeId } from '../types/ui'

defineProps<{
  view: string
  watchlistCount?: number
  history?: string[]
}>()
defineEmits<{
  'update:view': [view: string]
  search: [ticker: string]
  'open-search': []
  reset: []
}>()

const { theme, THEMES, setTheme } = useTheme()
const { t, locale, setLocale, LOCALES } = useI18n()

const themeLabel = (id: ThemeId) => (({ dark: t('header.themeDark'), gray: t('header.themeGray'), light: t('header.themeLight') } as Record<ThemeId, string>)[id] ?? id)

// Platform-aware shortcut hint (⌘K on macOS, Ctrl K elsewhere).
const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform || '')
const shortcutLabel = computed(() => (isMac ? '⌘K' : 'Ctrl K'))

// Mobile: collapse theme / language / reset behind a single settings button.
const settingsRef = ref<HTMLElement | null>(null)
const showSettings = ref(false)
onClickOutside(settingsRef, () => { showSettings.value = false })
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-zinc-800/60 bg-zinc-950/90 backdrop-blur-md">
    <div class="px-3 sm:px-4 md:px-6 xl:px-8 h-14 flex items-center gap-2 sm:gap-3">

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
           class="hidden lg:flex items-center gap-1.5 flex-1 min-w-0">
        <span class="text-zinc-600 text-xs shrink-0">{{ t('header.recent') }}</span>
        <div class="flex items-center gap-1.5 overflow-x-auto min-w-0 scroll-fade-x">
          <button v-for="h in history" :key="h" @click="$emit('search', h)"
            class="text-xs font-mono bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 px-2 py-1 rounded-md transition-colors shrink-0">
            {{ h }}
          </button>
        </div>
      </div>

      <!-- Quick-search shortcut -->
      <button @click="$emit('open-search')" :title="t('search.modalTitle')"
        class="ml-auto shrink-0 flex items-center gap-2 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 rounded-xl pl-2.5 pr-2 h-9 transition-colors">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"/>
        </svg>
        <kbd class="hidden sm:block text-[10px] font-mono bg-zinc-800 text-zinc-400 rounded px-1.5 py-0.5 leading-none">{{ shortcutLabel }}</kbd>
      </button>

      <!-- Settings: theme / language / reset — inline on md+, collapsed behind one button on mobile -->
      <div ref="settingsRef" class="relative md:contents shrink-0">
        <button @click="showSettings = !showSettings" aria-label="Settings"
          class="md:hidden w-9 h-9 rounded-xl flex items-center justify-center bg-zinc-900/60 text-zinc-500 hover:text-zinc-300 transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
        <div :class="[showSettings ? 'flex' : 'hidden',
          'md:flex items-center gap-1.5 md:gap-2',
          'max-md:absolute max-md:right-0 max-md:top-full max-md:mt-2 max-md:flex-col max-md:items-end max-md:bg-zinc-900 max-md:border max-md:border-zinc-800/80 max-md:rounded-xl max-md:p-2 max-md:shadow-2xl max-md:shadow-black/60 max-md:z-50']">

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

      <!-- Reset data (danger) -->
      <button @click="$emit('reset')" :title="t('reset.title')"
        class="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center bg-zinc-900/60 text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
        </svg>
      </button>
      </div>
      </div>
    </div>
  </header>
</template>
