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
        <div className="topbar__identity">
          <span className="topbar__mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" className="topbar__mark-icon">
              <path className="topbar__mark-edges" d="M7 9 16 6l9 5M7 9l6 14 12-3M16 6l-3 17m3-17 9 14M7 9l18 2" />
              <circle cx="7" cy="9" r="3" className="topbar__mark-node topbar__mark-node--lime" />
              <circle cx="16" cy="6" r="3" className="topbar__mark-node topbar__mark-node--blue" />
              <circle cx="25" cy="11" r="3" className="topbar__mark-node topbar__mark-node--mint" />
              <circle cx="13" cy="23" r="3" className="topbar__mark-node topbar__mark-node--rose" />
              <circle cx="25" cy="20" r="3" className="topbar__mark-node topbar__mark-node--lime" />
            </svg>
          </span>
          <span className="topbar__brand">Algo<span>Lab</span></span>
          <span className="topbar__tagline">ALGORITHM LAB</span>
        </div>
        <nav className="topbar__tabs" aria-label="Algorithm categories" role="tablist">
          <button type="button" className="topbar__tab topbar__tab--active" role="tab" aria-selected="true" aria-controls="sorting-panel">
            Sorting
          </button>
          <button type="button" className="topbar__tab" role="tab" aria-selected="false" disabled title="Coming soon">
            Searching
          </button>
          <button type="button" className="topbar__tab" role="tab" aria-selected="false" disabled title="Coming soon">
            Graphs
          </button>
          <button type="button" className="topbar__tab" role="tab" aria-selected="false" disabled title="Coming soon">
            Dynamic Programming
          </button>
          <button type="button" className="topbar__tab" role="tab" aria-selected="false" disabled title="Coming soon">
            Backtracking
          </button>
        </nav>
        <button type="button" className="topbar__mode" onClick={toggleMode} aria-label={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
          <svg viewBox="0 0 20 20" aria-hidden="true">
            {mode === 'dark' ? (
              <>
                <circle cx="10" cy="10" r="3.5" />
                <path d="M10 1.5v2M10 16.5v2M18.5 10h-2M3.5 10h-2m14.5-6-1.4 1.4M5.4 14.6 4 16m12 0-1.4-1.4M5.4 5.4 4 4" />
              </>
            ) : (
              <path d="M16.7 13.1A7 7 0 0 1 6.9 3.3 7 7 0 1 0 16.7 13Z" />
            )}
          </svg>
          {mode === 'dark' ? 'Light' : 'Dark'} mode
        </button>
      </header>

      <div className="page" id="sorting-panel" role="tabpanel" aria-label="Sorting algorithms">
        {loadError && (
          <p className="error" role="alert">
            {loadError}
          </p>
        )}
        <RaceSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
        <BenchmarkSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
        <SuiteSection algorithms={algorithms} selected={selected} onSelect={setSelected} />
      </div>
    </div>
  )
}
