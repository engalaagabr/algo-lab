import { useCallback, useEffect, useState } from 'react'
import { api, request, type AlgorithmMetadata, type SortExperiment } from '../api/client'
import { useText } from '../i18n/language'
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
  const [error, setError] = useState<unknown>(null)
  const [runId, setRunId] = useState(0)

  const race = useCallback(async (input: number[], ids: string[]) => {
    setBusy(true)
    setError(null)
    try {
      const body = { values: input, algorithm_ids: ids, trace: true }
      setExperiment(await request(api.POST('/api/v1/sort', { body })))
      setRunId((id) => id + 1)
    } catch (cause) {
      setError(cause)
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
      setError(cause)
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
      .catch((cause: unknown) => setError(cause))
  }, [race])

  const text = useText()
  const name = (id: string) => algorithms.find((item) => item.id === id)?.name ?? id
  const available = algorithms.filter((item) => !racers.includes(item.id))

  return (
    <section className="section" aria-labelledby="race-title">
      <header className="section__head">
        <h2 id="race-title">{text.raceTitle}</h2>
        <p>{text.raceIntro}</p>
      </header>

      <div className="controls">
        <DatasetFields value={settings} onChange={setSettings} maxSize={MAX_TRACE_SIZE} sizeControl="slider" />
        <div className="controls__wide">
          <span className="controls__heading">{text.array}</span>
          <p className="controls__values" dir="ltr">
            {values.length ? values.join(', ') : text.noData}
          </p>
        </div>
        <div className="controls__wide">
          <span className="controls__heading">
            {text.algorithms} <small>{text.upTo(MAX_RACERS)}</small>
          </span>
          <div className="racers">
            {racers.map((id) => (
              <span key={id} className="racer">
                {name(id)}
                <button type="button" aria-label={text.remove(name(id))} onClick={() => setRacers(racers.filter((item) => item !== id))}>
                  ×
                </button>
              </span>
            ))}
            {available.length > 0 && racers.length < MAX_RACERS && (
              <select
                className="racers__add"
                value=""
                aria-label={text.addAlgorithm}
                onChange={(event) => event.target.value && setRacers([...racers, event.target.value])}
              >
                <option value="">+ {text.addAlgorithm}</option>
                {available.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
        <div className="controls__actions">
          <button type="button" disabled={busy} onClick={generate}>
            {text.newArray}
          </button>
          <button type="button" className="primary" disabled={busy || !values.length || !racers.length} onClick={() => race(values, racers)}>
            {busy ? text.working : text.startRace}
          </button>
        </div>
      </div>

      {error !== null && (
        <p className="error" role="alert">
          {errorMessage(error, text)}
        </p>
      )}
      <div className="legend" aria-label={text.traceColours}>
        <span>
          <i className="legend__compare" /> {text.compare}
        </span>
        <span>
          <i className="legend__swap" /> {text.swap}
        </span>
        <span>
          <i className="legend__write" /> {text.write}
        </span>
        <span>
          <i className="legend__done" /> {text.sortedState}
        </span>
      </div>
      {experiment && algorithms.length ? (
        <Theater key={runId} experiment={experiment} algorithms={algorithms} />
      ) : (
        error === null && <p className="empty">{busy ? text.runningAlgorithms : text.pickAndStart}</p>
      )}
    </section>
  )
}
