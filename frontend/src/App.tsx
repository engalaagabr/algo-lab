import { useEffect, useState } from 'react'
import { api, request, type AlgorithmMetadata } from './api/client'
import { BenchmarkSection } from './benchmark/BenchmarkSection'
import { DEFAULT_ALGORITHMS, errorMessage } from './shared/lab'
import { initialMode, rememberMode, type Mode } from './shared/mode'
import { SuiteSection } from './suite/SuiteSection'
import { RaceSection } from './visualizer/RaceSection'
import './shared/app.css'
import './shared/charts.css'

export default function App() {
  const [mode, setMode] = useState<Mode>(initialMode)
  const [algorithms, setAlgorithms] = useState<AlgorithmMetadata[]>([])
  // One selection for the whole page, shared by the race, benchmark, and suite.
  const [selected, setSelected] = useState<string[]>(DEFAULT_ALGORITHMS)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    request(api.GET('/api/v1/algorithms'))
      .then(setAlgorithms)
      .catch((cause: unknown) => setLoadError(errorMessage(cause)))
  }, [])

  const toggleMode = () => {
    const next = mode === 'dark' ? 'light' : 'dark'
    setMode(next)
    rememberMode(next)
  }

  return (
    <div className="app" data-mode={mode}>
      <header className="topbar">
        <span className="topbar__brand">AlgoLab</span>
        <button type="button" className="topbar__mode" onClick={toggleMode} aria-label={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
          {mode === 'dark' ? 'Light' : 'Dark'} mode
        </button>
      </header>

      <div className="page">
        {loadError && (
          <p className="error" role="alert">
            {loadError}
          </p>
        )}
        <RaceSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
        <BenchmarkSection algorithms={algorithms} selected={selected} />
        <SuiteSection algorithms={algorithms} selected={selected} />
      </div>
    </div>
  )
}
