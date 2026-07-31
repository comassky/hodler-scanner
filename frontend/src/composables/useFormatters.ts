// Shared type definitions.
import type { ScoreColor, ScoreStatus } from '../types'
import { useI18n } from './useI18n'

export function useFormatters() {
  const { locale } = useI18n()

  function fmt(v: number | string | null | undefined, dec = 2): string {
    if (v === null || v === undefined) return '—'
    return typeof v === 'number' ? v.toFixed(dec) : String(v)
  }

  function fmtPct(v: number | null | undefined, showPlus = true): string {
    if (v === null || v === undefined) return '—'
    const s = v.toFixed(2) + '%'
    return showPlus && v > 0 ? '+' + s : s
  }

  const varColor       = (v: number) => v >= 0 ? 'text-emerald-400' : 'text-red-400'
  const rsiClass       = (v: number) => v <= 35 ? 'text-emerald-400' : v >= 70 ? 'text-red-400' : 'text-zinc-300'
  const rsiBarClass    = (v: number) => v <= 35 ? 'bg-emerald-500'   : v >= 70 ? 'bg-red-500'   : 'bg-indigo-400'
  const distClass      = (v: number | null | undefined) => v == null ? 'text-zinc-500' : v >= 2 ? 'text-emerald-400' : v >= -3 ? 'text-amber-400' : 'text-red-400'
  const macdClass      = (v: number) => v >= 0 ? 'text-emerald-400' : 'text-red-400'
  const scoreCompClass = (v: number) => v > 0 ? 'text-emerald-400' : v < 0 ? 'text-red-400' : 'text-zinc-500'

  function scoreColorFor(s: number): ScoreColor {
    if (s >= 80) return { text: 'text-emerald-400', bg: 'bg-emerald-500/15 ring-1 ring-emerald-500/30' }
    if (s >= 60) return { text: 'text-sky-400',     bg: 'bg-sky-500/15 ring-1 ring-sky-500/30' }
    return             { text: 'text-amber-400',   bg: 'bg-amber-500/15 ring-1 ring-amber-500/30' }
  }

  // Full status palette for the analysis view (ring + solid bar + status label key).
  function scoreStatus(score: number | null | undefined): ScoreStatus {
    const s = score ?? 0
    if (s >= 80) return { ring: 'ring-1 ring-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10', bar: 'bg-emerald-500', labelKey: 'scoreLabel.strong' }
    if (s >= 60) return { ring: 'ring-1 ring-sky-500',     text: 'text-sky-400',     bg: 'bg-sky-500/10',     bar: 'bg-sky-500',     labelKey: 'scoreLabel.accumulate' }
    if (s >= 40) return { ring: 'ring-1 ring-amber-500',   text: 'text-amber-400',   bg: 'bg-amber-500/10',   bar: 'bg-amber-500',   labelKey: 'scoreLabel.watch' }
    return             { ring: 'ring-1 ring-red-500',      text: 'text-red-400',     bg: 'bg-red-500/10',     bar: 'bg-red-500',     labelKey: 'scoreLabel.avoid' }
  }

  function fmtMarketCap(v: number | null | undefined): string {
    if (v == null) return '—'
    return new Intl.NumberFormat(locale.value, { notation: 'compact', maximumFractionDigits: 2 }).format(v)
  }

  const tendanceBadgeClass = (t: string | null | undefined) => t?.startsWith('↑')
    ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/30'
    : 'bg-red-500/10 text-red-400 ring-1 ring-red-500/30'

  const regimeBadgeClass = (code: string) => ({
    trend_up:   'bg-violet-500/10 text-violet-300 ring-1 ring-violet-500/30',
    trend_down: 'bg-violet-500/10 text-violet-300 ring-1 ring-violet-500/30',
    range:      'bg-sky-500/10 text-sky-400 ring-1 ring-sky-500/30',
    transition: 'bg-zinc-700/30 text-zinc-400 ring-1 ring-zinc-600/40',
  }[code] || 'bg-zinc-700/30 text-zinc-400 ring-1 ring-zinc-600/40')

  return {
    fmt, fmtPct,
    varColor, rsiClass, rsiBarClass, distClass, macdClass,
    scoreCompClass, scoreColorFor, scoreStatus, fmtMarketCap,
    tendanceBadgeClass, regimeBadgeClass,
  }
}
