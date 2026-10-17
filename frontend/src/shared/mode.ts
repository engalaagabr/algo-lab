/** Colour modes of the Graphite design; both share every layout rule. */
export type Mode = 'dark' | 'light'

const STORAGE_KEY = 'algolab-mode'

/** The last choice here, then the system preference; dark when neither says otherwise. */
export function initialMode(): Mode {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // Storage can be unavailable (private mode); fall back to the system preference.
  }
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

export function rememberMode(mode: Mode): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, mode)
  } catch {
    // Not persisting is acceptable; the page still switches.
  }
}
