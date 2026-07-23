export function useFormatters() {
  function fmt(v, dec = 2) {
    if (v === null || v === undefined) return '—'
    return typeof v === 'number' ? v.toFixed(dec) : String(v)
  }

  function fmtPct(v, showPlus = true) {
    if (v === null || v === undefined) return '—'
    const s = v.toFixed(2) + '%'
    return showPlus && v > 0 ? '+' + s : s
  }

  const varColor       = v => v >= 0 ? 'text-emerald-400' : 'text-red-400'
  const rsiClass       = v => v <= 35 ? 'text-emerald-400' : v >= 70 ? 'text-red-400' : 'text-zinc-300'
  const rsiBarClass    = v => v <= 35 ? 'bg-emerald-500'   : v >= 70 ? 'bg-red-500'   : 'bg-indigo-400'
  const distClass      = v => v == null ? 'text-zinc-500' : v >= 2 ? 'text-emerald-400' : v >= -3 ? 'text-amber-400' : 'text-red-400'
  const macdClass      = v => v >= 0 ? 'text-emerald-400' : 'text-red-400'
  const scoreCompClass = v => v > 0 ? 'text-emerald-400' : v < 0 ? 'text-red-400' : 'text-zinc-500'

  function scoreColorFor(s) {
    if (s >= 80) return { text: 'text-emerald-400', bg: 'bg-emerald-500/15 ring-1 ring-emerald-500/30' }
    if (s >= 60) return { text: 'text-sky-400',     bg: 'bg-sky-500/15 ring-1 ring-sky-500/30' }
    return             { text: 'text-amber-400',   bg: 'bg-amber-500/15 ring-1 ring-amber-500/30' }
  }

  // Full status palette for the analysis view (ring + solid bar + status label key).
  function scoreStatus(score) {
    const s = score ?? 0
    if (s >= 80) return { ring: 'ring-1 ring-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10', bar: 'bg-emerald-500', labelKey: 'scoreLabel.strong' }
    if (s >= 60) return { ring: 'ring-1 ring-sky-500',     text: 'text-sky-400',     bg: 'bg-sky-500/10',     bar: 'bg-sky-500',     labelKey: 'scoreLabel.accumulate' }
    if (s >= 40) return { ring: 'ring-1 ring-amber-500',   text: 'text-amber-400',   bg: 'bg-amber-500/10',   bar: 'bg-amber-500',   labelKey: 'scoreLabel.watch' }
    return             { ring: 'ring-1 ring-red-500',      text: 'text-red-400',     bg: 'bg-red-500/10',     bar: 'bg-red-500',     labelKey: 'scoreLabel.avoid' }
  }

  function fmtMarketCap(v) {
    if (v == null) return '—'
    if (v >= 1e12) return (v / 1e12).toFixed(2) + ' T'
    if (v >= 1e9)  return (v / 1e9).toFixed(2)  + ' Md'
    if (v >= 1e6)  return (v / 1e6).toFixed(2)  + ' M'
    return v.toLocaleString()
  }

  const tendanceBadgeClass = t => t?.startsWith('↑')
    ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/30'
    : 'bg-red-500/10 text-red-400 ring-1 ring-red-500/30'

  const regimeBadgeClass = code => ({
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
