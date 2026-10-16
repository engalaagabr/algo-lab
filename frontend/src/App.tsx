import { useEffect, useState } from 'react'
import { api, request, type AlgorithmMetadata } from './api/client'
import { BenchmarkSection } from './benchmark/BenchmarkSection'
import { initialLanguage, MESSAGES, rememberLanguage, TextContext, type Language } from './i18n/language'
import { DEFAULT_ALGORITHMS, errorMessage } from './shared/lab'
import { initialMode, rememberMode, type Mode } from './shared/mode'
import { SuiteSection } from './suite/SuiteSection'
import { RaceSection } from './visualizer/RaceSection'
import './shared/app.css'
import './shared/charts.css'

export default function App() {
  const [mode, setMode] = useState<Mode>(initialMode)
  const [language, setLanguage] = useState<Language>(initialLanguage)
  const [algorithms, setAlgorithms] = useState<AlgorithmMetadata[]>([])
  // One selection for the whole page, so the benchmark and suite measure the algorithms in the race.
  const [selected, setSelected] = useState<string[]>(DEFAULT_ALGORITHMS)
  const [loadError, setLoadError] = useState<unknown>(null)
  const text = MESSAGES[language]

  useEffect(() => {
    request(api.GET('/api/v1/algorithms'))
      .then(setAlgorithms)
      .catch((cause: unknown) => setLoadError(cause))
  }, [])

  // The document carries the direction so native controls and scrollbars follow it too.
  useEffect(() => {
    document.documentElement.lang = language
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr'
  }, [language])

  const toggleMode = () => {
    const next = mode === 'dark' ? 'light' : 'dark'
    setMode(next)
    rememberMode(next)
  }

  const toggleLanguage = () => {
    const next = language === 'en' ? 'ar' : 'en'
    setLanguage(next)
    rememberLanguage(next)
  }

  const otherMode = mode === 'dark' ? text.lightMode : text.darkMode

  return (
    <TextContext.Provider value={text}>
      <div className="app" data-mode={mode}>
        <header className="topbar">
          <span className="topbar__brand">AlgoLab</span>
          <button type="button" className="topbar__language" onClick={toggleLanguage} aria-label={text.switchLanguage}>
            {text.otherLanguage}
          </button>
          <button type="button" className="topbar__mode" onClick={toggleMode} aria-label={text.switchMode(otherMode)}>
            {otherMode}
          </button>
        </header>

        <div className="page">
          {loadError !== null && (
            <p className="error" role="alert">
              {errorMessage(loadError, text)}
            </p>
          )}
          <RaceSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
          <BenchmarkSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
          <SuiteSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
        </div>
      </div>
    </TextContext.Provider>
  )
}
