import { useEffect, useState } from 'react'
import { api, request, type AlgorithmMetadata } from './api/client'
import { BenchmarkPage } from './benchmark/BenchmarkPage'
import { errorMessage } from './shared/lab'
import { initialTheme, rememberTheme, THEMES, type ThemeId } from './shared/themes'
import { SuitePage } from './suite/SuitePage'
import { Visualizer } from './visualizer/Visualizer'
import './shared/app.css'
import './shared/themes.css'
import './shared/charts.css'

const PAGES = [
  { id: 'visualize', label: 'Visualize' },
  { id: 'benchmark', label: 'Benchmark' },
  { id: 'suite', label: 'Suite' },
] as const

type PageId = (typeof PAGES)[number]['id']

function pageFromHash(): PageId {
  const id = window.location.hash.replace(/^#\/?/, '')
  return PAGES.find((page) => page.id === id)?.id ?? 'visualize'
}

export default function App() {
  const [page, setPage] = useState<PageId>(pageFromHash)
  const [theme, setTheme] = useState<ThemeId>(initialTheme)
  const [algorithms, setAlgorithms] = useState<AlgorithmMetadata[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    const onHash = () => setPage(pageFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  useEffect(() => {
    request(api.GET('/api/v1/algorithms'))
      .then(setAlgorithms)
      .catch((cause: unknown) => setLoadError(errorMessage(cause)))
  }, [])

  return (
    <div className="app" data-theme={theme}>
      <header className="topbar">
        <span className="topbar__brand">AlgoLab</span>
        <nav className="topbar__nav" aria-label="Sections">
          {PAGES.map((item) => (
            <a key={item.id} href={`#/${item.id}`} aria-current={item.id === page ? 'page' : undefined}>
              {item.label}
            </a>
          ))}
        </nav>
        <label className="topbar__theme">
          Design
          <select
            value={theme}
            onChange={(event) => {
              const next = event.target.value as ThemeId
              setTheme(next)
              rememberTheme(next)
            }}
          >
            {THEMES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </header>

      {loadError && (
        <p className="error app__error" role="alert">
          {loadError}
        </p>
      )}

      {/* Pages stay mounted so results survive switching tabs during a demo. */}
      <div className="page" hidden={page !== 'visualize'}>
        <Visualizer algorithms={algorithms} active={page === 'visualize'} />
      </div>
      <div className="page" hidden={page !== 'benchmark'}>
        <BenchmarkPage algorithms={algorithms} />
      </div>
      <div className="page" hidden={page !== 'suite'}>
        <SuitePage algorithms={algorithms} />
      </div>
    </div>
  )
}
