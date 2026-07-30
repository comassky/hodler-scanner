<script setup>
import { ref, computed } from 'vue'
import { usePortfolio } from '../composables/usePortfolio.js'
import { useFormatters } from '../composables/useFormatters.js'
import { useI18n } from '../composables/useI18n.js'
import TickerAutocomplete from './TickerAutocomplete.vue'

const emit = defineEmits(['analyse'])

const { positions, totals, loading, refreshing, errorMsg, lastRefresh, refetch, upsert, remove } = usePortfolio()
const { fmt, fmtPct, varColor } = useFormatters()
const { t, locale } = useI18n()

// ── Add / edit form ───────────────────────────────────────────────
const form = ref({ ticker: '', quantity: '', avg_cost: '', note: '' })
const editing = ref(false)
const submitting = ref(false)

const canSubmit = computed(() =>
  form.value.ticker.trim() &&
  Number(form.value.quantity) > 0 &&
  Number(form.value.avg_cost) >= 0
)

function resetForm() {
  form.value = { ticker: '', quantity: '', avg_cost: '', note: '' }
  editing.value = false
}

function startEdit(p) {
  form.value = {
    ticker: p.ticker,
    quantity: String(p.quantity),
    avg_cost: String(p.avg_cost),
    note: p.note || '',
  }
  editing.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function submit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    await upsert(form.value.ticker, form.value.quantity, form.value.avg_cost, form.value.note || null)
    resetForm()
  } finally {
    submitting.value = false
  }
}

const money = (v) => (v == null ? '—' : Number(v).toLocaleString(locale.value, { maximumFractionDigits: 2 }))
</script>

<template>
  <div class="px-4 md:px-6 xl:px-8 py-8 pb-20 max-w-6xl mx-auto w-full">
    <div class="flex items-center justify-between mb-1 flex-wrap gap-2">
      <div>
        <h1 class="text-xl font-bold tracking-tight">{{ t('portfolio.title') }}</h1>
        <p class="text-zinc-500 text-sm">{{ t('portfolio.subtitle') }}</p>
      </div>
      <button @click="refetch()" :disabled="refreshing"
        class="shrink-0 flex items-center gap-2 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-xl px-3 h-9 text-xs font-medium transition-colors disabled:opacity-50">
        <svg :class="['w-3.5 h-3.5', refreshing && 'animate-spin']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        {{ t('portfolio.refresh') }}
      </button>
    </div>

    <!-- Totals -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5 mb-6">
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3">
        <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('portfolio.totalValue') }}</p>
        <p class="text-lg font-bold font-mono text-zinc-100">{{ money(totals?.value) }}</p>
      </div>
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3">
        <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('portfolio.totalCost') }}</p>
        <p class="text-lg font-bold font-mono text-zinc-300">{{ money(totals?.cost) }}</p>
      </div>
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3">
        <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('portfolio.totalPnl') }}</p>
        <p :class="['text-lg font-bold font-mono', totals && totals.pnl >= 0 ? 'text-emerald-400' : 'text-red-400']">
          {{ totals && totals.pnl > 0 ? '+' : '' }}{{ money(totals?.pnl) }}
        </p>
      </div>
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3">
        <p class="text-[10px] uppercase tracking-wider text-zinc-500 mb-0.5">{{ t('portfolio.totalPnlPct') }}</p>
        <p :class="['text-lg font-bold font-mono', totals && (totals.pnl_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400']">
          {{ fmtPct(totals?.pnl_pct) }}
        </p>
      </div>
    </div>

    <!-- Add / edit form -->
    <form @submit.prevent="submit"
      class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 mb-6 grid grid-cols-2 md:grid-cols-[1.4fr_1fr_1fr_1.6fr_auto] gap-3 items-end">
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1">{{ t('portfolio.ticker') }}</label>
        <TickerAutocomplete v-model="form.ticker" :disabled="editing"
          :placeholder="t('portfolio.tickerPlaceholder')" />
      </div>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1">{{ t('portfolio.quantity') }}</label>
        <input v-model="form.quantity" type="number" step="any" min="0" placeholder="0"
          class="w-full bg-zinc-950/60 border border-zinc-800 rounded-lg px-3 py-2 text-sm font-mono text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500" />
      </div>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1">{{ t('portfolio.avgCost') }}</label>
        <input v-model="form.avg_cost" type="number" step="any" min="0" placeholder="0.00"
          class="w-full bg-zinc-950/60 border border-zinc-800 rounded-lg px-3 py-2 text-sm font-mono text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500" />
      </div>
      <div>
        <label class="block text-[10px] uppercase tracking-wider text-zinc-500 mb-1">{{ t('portfolio.note') }}</label>
        <input v-model="form.note" :placeholder="t('portfolio.notePlaceholder')" maxlength="80"
          class="w-full bg-zinc-950/60 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500" />
      </div>
      <div class="flex gap-2">
        <button type="submit" :disabled="!canSubmit || submitting"
          class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap">
          {{ editing ? t('portfolio.save') : t('portfolio.add') }}
        </button>
        <button v-if="editing" type="button" @click="resetForm"
          class="h-9 px-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm transition-colors">
          {{ t('portfolio.cancel') }}
        </button>
      </div>
    </form>

    <!-- Error -->
    <div v-if="errorMsg" class="text-sm text-red-400 mb-4">{{ errorMsg }}</div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 4" :key="n" class="h-14 rounded-xl bg-zinc-900 border border-zinc-800 animate-pulse"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="!positions.length" class="text-center py-16 text-zinc-500">
      <p class="text-sm">{{ t('portfolio.empty') }}</p>
    </div>

    <!-- Positions table -->
    <div v-else class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
      <div class="overflow-x-auto scroll-fade-x">
        <table class="w-full text-sm min-w-[720px]">
          <thead>
            <tr class="text-[10px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
              <th class="text-left font-medium px-4 py-2.5">{{ t('portfolio.ticker') }}</th>
              <th class="text-right font-medium px-3 py-2.5">{{ t('portfolio.quantity') }}</th>
              <th class="text-right font-medium px-3 py-2.5">{{ t('portfolio.avgCost') }}</th>
              <th class="text-right font-medium px-3 py-2.5">{{ t('portfolio.price') }}</th>
              <th class="text-right font-medium px-3 py-2.5">{{ t('portfolio.value') }}</th>
              <th class="text-right font-medium px-3 py-2.5">{{ t('portfolio.pnl') }}</th>
              <th class="text-left font-medium px-3 py-2.5 w-32">{{ t('portfolio.weight') }}</th>
              <th class="px-3 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in positions" :key="p.ticker" class="border-b border-zinc-800/60 last:border-0 hover:bg-zinc-800/30">
              <td class="px-4 py-3">
                <button @click="emit('analyse', p.ticker)" class="text-left group">
                  <span class="font-mono font-semibold text-zinc-100 group-hover:text-indigo-300">{{ p.ticker }}</span>
                  <span v-if="p.note" class="block text-[11px] text-zinc-600 truncate max-w-[160px]">{{ p.note }}</span>
                </button>
              </td>
              <td class="px-3 py-3 text-right font-mono text-zinc-300">{{ fmt(p.quantity, p.quantity % 1 ? 4 : 0) }}</td>
              <td class="px-3 py-3 text-right font-mono text-zinc-400">{{ money(p.avg_cost) }}</td>
              <td class="px-3 py-3 text-right font-mono text-zinc-300">{{ money(p.price) }}</td>
              <td class="px-3 py-3 text-right font-mono text-zinc-100">{{ money(p.value) }}</td>
              <td class="px-3 py-3 text-right font-mono">
                <span :class="p.pnl == null ? 'text-zinc-500' : varColor(p.pnl)">
                  {{ p.pnl == null ? '—' : (p.pnl > 0 ? '+' : '') + money(p.pnl) }}
                </span>
                <span v-if="p.pnl_pct != null" :class="['block text-[11px]', varColor(p.pnl_pct)]">{{ fmtPct(p.pnl_pct) }}</span>
              </td>
              <td class="px-3 py-3">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                    <div class="h-full bg-indigo-500 rounded-full" :style="{ width: (p.weight || 0) + '%' }"></div>
                  </div>
                  <span class="text-[11px] font-mono text-zinc-500 w-10 text-right">{{ p.weight == null ? '—' : p.weight + '%' }}</span>
                </div>
              </td>
              <td class="px-3 py-3">
                <div class="flex items-center gap-1 justify-end">
                  <button @click="startEdit(p)" :title="t('portfolio.edit')"
                    class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-indigo-300 hover:bg-zinc-800 transition-colors">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z"/>
                    </svg>
                  </button>
                  <button @click="remove(p.ticker)" :title="t('portfolio.remove')"
                    class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-colors">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="totals && !totals.priced" class="text-[11px] text-amber-400/80 px-4 py-2 border-t border-zinc-800/60">
        {{ t('portfolio.pricingWarning') }}
      </p>
    </div>

    <p v-if="lastRefresh" class="text-[11px] text-zinc-600 mt-3 text-right">
      {{ t('portfolio.updated') }} {{ lastRefresh.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' }) }}
    </p>
  </div>
</template>
