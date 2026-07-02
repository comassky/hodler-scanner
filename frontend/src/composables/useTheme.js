import { ref, watch } from 'vue'

// Available themes — remap the "zinc" scale via CSS variables (see style.css)
export const THEMES = [
  { id: 'dark',  label: 'Noir' },
  { id: 'gray',  label: 'Gris' },
  { id: 'light', label: 'Clair' },
]

const _ids = THEMES.map(t => t.id)
const stored = localStorage.getItem('smm_theme')
const theme = ref(_ids.includes(stored) ? stored : 'dark')

function apply(t) {
  document.documentElement.setAttribute('data-theme', t)
}
apply(theme.value)

watch(theme, t => {
  apply(t)
  localStorage.setItem('smm_theme', t)
})

export function useTheme() {
  function setTheme(t) {
    if (_ids.includes(t)) theme.value = t
  }
  function cycle() {
    theme.value = _ids[(_ids.indexOf(theme.value) + 1) % _ids.length]
  }
  return { theme, THEMES, setTheme, cycle }
}
