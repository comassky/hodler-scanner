<script setup lang="ts">
import { ref, computed } from 'vue'
import type { InfoTipLevel } from '../types/ui'

const props = defineProps<{
  text?: string
  title?: string
  formula?: string
  levels?: InfoTipLevel[]
  tip?: string
}>()

const show = ref(false)
const shift = ref(0)
const btnRef = ref<HTMLElement | null>(null)

// Reposition the bubble horizontally so it stays within the viewport
function updatePos() {
  const el = btnRef.value
  if (!el) return
  const W = 288, margin = 8, half = W / 2      // w-72 = 288px
  const r = el.getBoundingClientRect()
  const center = r.left + r.width / 2
  let s = 0
  if (center - half < margin) s = margin - (center - half)
  else if (center + half > window.innerWidth - margin) s = (window.innerWidth - margin) - (center + half)
  shift.value = s
}
function open()   { updatePos(); show.value = true }
function close()  { show.value = false }
function toggle() { show.value ? close() : open() }

const TONE = {
  good:    'bg-emerald-500',
  bad:     'bg-red-500',
  warn:    'bg-amber-500',
  neutral: 'bg-zinc-500',
}

const structured = computed(() =>
  Boolean(props.title || props.formula || props.levels?.length || props.tip)
)
</script>

<template>
  <span class="relative inline-flex items-center ml-1 shrink-0 align-middle">
    <button
      type="button"
      ref="btnRef"
      @mouseenter="open"
      @mouseleave="close"
      @focus="open"
      @blur="close"
      @click.stop="toggle"
      class="w-3.5 h-3.5 rounded-full bg-zinc-800 text-zinc-500 hover:bg-zinc-700 hover:text-zinc-200 text-[9px] font-bold inline-flex items-center justify-center transition-colors cursor-help outline-none select-none"
      tabindex="-1">?</button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 translate-y-1 scale-95"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0 translate-y-1 scale-95">
      <div
        v-if="show"
        :style="{ marginLeft: `${shift}px` }"
        class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 bg-zinc-950 border border-zinc-700/80 rounded-xl p-3 text-xs z-50 pointer-events-none shadow-xl shadow-black/70 origin-bottom font-normal normal-case tracking-normal">
        <!-- Arrow (always points to the button) -->
        <span :style="{ marginLeft: `${-shift}px` }"
          class="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-zinc-700/80 block"></span>

        <!-- Structured mode -->
        <template v-if="structured">
          <p v-if="title" class="text-zinc-100 font-semibold text-[13px] leading-snug mb-1">{{ title }}</p>
          <p v-if="text" class="text-zinc-300 leading-relaxed">{{ text }}</p>

          <div v-if="formula"
            class="mt-2 font-mono text-[10px] text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-md px-2 py-1 leading-relaxed">
            {{ formula }}
          </div>

          <ul v-if="levels.length" class="mt-2.5 space-y-1.5">
            <li v-for="(l, i) in levels" :key="i" class="flex items-start gap-2 leading-snug">
              <span :class="['mt-1 w-1.5 h-1.5 rounded-full shrink-0', TONE[l.tone] || TONE.neutral]"></span>
              <span class="text-zinc-400">
                <span class="font-mono text-zinc-200">{{ l.range }}</span>
                <span class="text-zinc-500"> — </span>{{ l.label }}
              </span>
            </li>
          </ul>

          <p v-if="tip" class="mt-2.5 flex gap-1.5 text-zinc-400 border-t border-zinc-800 pt-2 leading-snug">
            <span class="shrink-0">💡</span><span>{{ tip }}</span>
          </p>
        </template>

        <!-- Mode texte simple -->
        <p v-else class="text-zinc-300 leading-relaxed">{{ text }}</p>
      </div>
    </Transition>
  </span>
</template>
