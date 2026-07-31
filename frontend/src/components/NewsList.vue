<script setup lang="ts">
import { useI18n } from '../composables/useI18n'
import InfoTip from './InfoTip.vue'
import type { NewsItem } from '../types/market'

defineProps<{
  items?: NewsItem[]
  loading?: boolean
  unavailable?: boolean
}>()
const { t, locale } = useI18n()

// Relative "x minutes ago" label, localized.
function timeAgo(iso?: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  const rtf = new Intl.RelativeTimeFormat(locale.value, { numeric: 'auto' })
  if (s < 60) return rtf.format(-s, 'second')
  const m = Math.floor(s / 60); if (m < 60) return rtf.format(-m, 'minute')
  const h = Math.floor(m / 60); if (h < 24) return rtf.format(-h, 'hour')
  const j = Math.floor(h / 24); if (j < 30) return rtf.format(-j, 'day')
  const mo = Math.floor(j / 30); return rtf.format(-mo, 'month')
}
</script>

<template>
  <div id="section-actualites" class="scroll-mt-28 bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
    <h2 class="flex items-center text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">{{ t('app.news') }}<InfoTip v-bind="t('info.news')" /></h2>
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
      <div v-for="n in 4" :key="n" class="flex gap-2.5 items-center py-1.5">
        <div class="w-9 h-9 rounded-md bg-zinc-800/60 animate-pulse shrink-0"></div>
        <div class="flex-1 space-y-1.5">
          <div class="h-3.5 w-3/4 bg-zinc-800/60 rounded animate-pulse"></div>
          <div class="h-3 w-1/3 bg-zinc-800/60 rounded animate-pulse"></div>
        </div>
      </div>
    </div>
    <p v-else-if="unavailable" class="text-sm text-zinc-500">{{ t('app.newsUnavailable') }}</p>
    <p v-else-if="!items.length" class="text-sm text-zinc-500">{{ t('app.newsEmpty') }}</p>
    <ul v-else class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-0.5">
      <li v-for="(n, i) in items" :key="i">
        <a :href="n.url" target="_blank" rel="noopener noreferrer"
           class="group flex gap-2.5 items-center hover:bg-zinc-800/40 rounded-lg -mx-2 px-2 py-1.5 transition-colors">
          <img v-if="n.thumbnail" :src="n.thumbnail" alt=""
               class="w-9 h-9 rounded-md object-cover shrink-0 bg-zinc-800" loading="lazy" />
          <div class="min-w-0 flex-1">
            <p class="text-sm text-zinc-200 group-hover:text-white leading-snug line-clamp-1">{{ n.title }}</p>
            <p class="text-xs text-zinc-500">
              <span v-if="n.publisher" class="text-zinc-400">{{ n.publisher }}</span>
              <span v-if="n.publisher && timeAgo(n.published)"> · </span>
              <span>{{ timeAgo(n.published) }}</span>
            </p>
          </div>
          <svg class="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17L17 7M17 7H8M17 7v9" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </a>
      </li>
    </ul>
  </div>
</template>
