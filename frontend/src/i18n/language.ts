import { createContext, useContext } from 'react'
import { ar } from './ar'
import { en, type Messages } from './en'

export type Language = 'en' | 'ar'

export const MESSAGES: Record<Language, Messages> = { en, ar }

/** The interface text for the current language. */
export const TextContext = createContext<Messages>(en)

export const useText = () => useContext(TextContext)

const STORAGE_KEY = 'algolab-language'

export function initialLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'ar') return stored
  } catch {
    // Storage can be unavailable (private mode); fall back to English.
  }
  return 'en'
}

export function rememberLanguage(language: Language): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, language)
  } catch {
    // Not persisting is acceptable; the page still switches.
  }
}
