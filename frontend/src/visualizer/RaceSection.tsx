import { useCallback, useEffect, useState } from 'react'
import { api, request, type AlgorithmMetadata, type SortExperiment } from '../api/client'
import { AlgorithmSelection } from '../shared/AlgorithmSelection'
import { DatasetFields } from '../shared/DatasetFields'
import { datasetBody, DEFAULT_ALGORITHMS, errorMessage, type DatasetSettings } from '../shared/lab'
import { Theater } from './Theater'

const MAX_TRACE_SIZE = 128
const MAX_RACERS = 10

interface RaceSectionProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
  onSelect: (selected: string[]) => void
}

export function RaceSection({ algorithms, selected: racers, onSelect: setRacers }: RaceSectionProps) {
  const [settings, setSettings] = useState<DatasetSettings>({
    size: 24,
    minimum: 1,
    maximum: 50,
    distribution: 'random',
    seed: '42',
  })
  const [values, setValues] = useState<number[]>([])
  const [experiment, setExperiment] = useState<SortExperiment | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [runId, setRunId] = useState(0)

  const race = useCallback(async (input: number[], ids: string[]) => {
    setBusy(true)
    setError(null)
    try {
      const body = { values: input, algorithm_ids: ids, trace: true }
      setExperiment(await request(api.POST('/api/v1/sort', { body })))
      setRunId((id) => id + 1)
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setBusy(false)
    }
  }, [])

  const generate = async () => {
    setBusy(true)
    setError(null)
    try {
      const dataset = await request(api.POST('/api/v1/datasets', { body: datasetBody(settings) }))
      setValues(dataset.values)
      setSettings((current) => ({ ...current, seed: String(dataset.seed) }))
      setExperiment(null)
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setBusy(false)
    }
  }

  // First load: show the default race right away so the demo starts with motion.
  useEffect(() => {
    const body = { size: 24, minimum: 1, maximum: 50, distribution: 'random' as const, seed: 42 }
    request(api.POST('/api/v1/datasets', { body }))
      .then((dataset) => {
        setValues(dataset.values)
        return race(dataset.values, DEFAULT_ALGORITHMS)
      })
      .catch((cause: unknown) => setError(errorMessage(cause)))
  }, [race])

  return (
    <section className="section section--race" aria-labelledby="race-title">
      <header className="section__head">
        <h2 id="race-title">Race</h2>
        <p>Watch the selected algorithms sort the same array step by step.</p>
      </header>
      <div className="controls controls--race">
        <DatasetFields value={settings} onChange={setSettings} maxSize={MAX_TRACE_SIZE} sizeControl="slider" />
        <div className="controls__wide">
          <span className="controls__heading">Array</span>
          <p className="controls__values">{values.length ? values.join(', ') : 'No data yet'}</p>
        </div>
        <AlgorithmSelection algorithms={algorithms} selected={racers} onChange={setRacers} max={MAX_RACERS} />
        <div className="controls__actions">
          <button type="button" disabled={busy} onClick={generate}>
            New array
          </button>
          <button type="button" className="primary" disabled={busy || !values.length || !racers.length} onClick={() => race(values, racers)}>
            {busy ? 'Working…' : 'Start race'}
          </button>
        </div>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="legend" aria-label="Trace colours">
        <span>
          <i className="legend__compare" /> compare
        </span>
        <span>
          <i className="legend__swap" /> swap
        </span>
        <span>
          <i className="legend__write" /> write
        </span>
        <span>
          <i className="legend__done" /> sorted
        </span>
      </div>
      {experiment && algorithms.length ? (
        <Theater key={runId} experiment={experiment} algorithms={algorithms} />
      ) : (
        !error && <p className="empty">{busy ? 'Running the algorithms…' : 'Pick algorithms and press Start race.'}</p>
      )}
    </section>
  )
}
