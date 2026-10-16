/** Visual directions under evaluation; each is a CSS theme over the same working screen. */
export const THEMES = [
  { id: 'standard', label: 'Category standard' },
  { id: 'card-sorter', label: 'Card Sorter' },
  { id: 'textbook', label: 'Textbook Figure' },
  { id: 'terminal-yellow', label: 'Terminal Yellow' },
  { id: 'graphite', label: 'Graphite Console' },
] as const

export type ThemeId = (typeof THEMES)[number]['id']

const STORAGE_KEY = 'algolab-theme'

function isTheme(value: string | null): value is ThemeId {
  return THEMES.some((theme) => theme.id === value)
}

/** `?theme=` wins so a shared link opens the same direction; then the last choice here. */
export function initialTheme(): ThemeId {
  const fromUrl = new URLSearchParams(window.location.search).get('theme')
  if (isTheme(fromUrl)) return fromUrl
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (isTheme(stored)) return stored
  } catch {
    // Storage can be unavailable (private mode); fall back to the default.
  }
  return 'standard'
}

export function rememberTheme(theme: ThemeId): void {
  const url = new URL(window.location.href)
  url.searchParams.set('theme', theme)
  window.history.replaceState(null, '', url)
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Not persisting is acceptable; the URL still carries the choice.
  }
}
