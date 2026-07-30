import { watch } from 'vue'
import { useLocalStorage } from '@vueuse/core'

// Available themes — remap the "zinc" scale via CSS variables (see style.css)
export const THEMES = [
  { id: 'dark',  label: 'Noir' },
  { id: 'gray',  label: 'Gris' },
  { id: 'light', label: 'Clair' },
]

const _ids = THEMES.map(t => t.id)
const theme = useLocalStorage('smm_theme', 'dark')
if (!_ids.includes(theme.value)) theme.value = 'dark'

function apply(t) {
  document.documentElement.setAttribute('data-theme', t)
}
apply(theme.value)

watch(theme, apply)

export function useTheme() {
  function setTheme(t) {
    if (_ids.includes(t)) theme.value = t
  }
  function cycle() {
    theme.value = _ids[(_ids.indexOf(theme.value) + 1) % _ids.length]
  }
  return { theme, THEMES, setTheme, cycle }
}
