import { useCallback, useEffect, useState } from 'react'
import { api, request, type AlgorithmMetadata, type SortExperiment } from '../api/client'
import { AlgorithmPicker } from '../shared/AlgorithmPicker'
import { DatasetFields } from '../shared/DatasetFields'
import { datasetBody, errorMessage, type DatasetSettings } from '../shared/lab'
import { Theater } from './Theater'

const MAX_TRACE_SIZE = 128
const MAX_LANES = 3
const DEFAULT_SELECTION = ['bubble_sort', 'quick_sort']

interface VisualizerProps {
  algorithms: AlgorithmMetadata[]
  /** Only the visible page listens to playback shortcuts. */
  active: boolean
}

export function Visualizer({ algorithms, active }: VisualizerProps) {
  const [selected, setSelected] = useState<string[]>(DEFAULT_SELECTION)
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

  const visualize = useCallback(async (input: number[], ids: string[]) => {
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

  // First load: show the default comparison right away so the demo starts with motion.
  useEffect(() => {
    const body = { size: 24, minimum: 1, maximum: 50, distribution: 'random' as const, seed: 42 }
    request(api.POST('/api/v1/datasets', { body }))
      .then((dataset) => {
        setValues(dataset.values)
        return visualize(dataset.values, DEFAULT_SELECTION)
      })
      .catch((cause: unknown) => setError(errorMessage(cause)))
  }, [visualize])

  return (
    <>
      <aside className="setup">
        <h2>Dataset</h2>
        <DatasetFields value={settings} onChange={setSettings} maxSize={MAX_TRACE_SIZE} sizeControl="slider" />
        <button type="button" disabled={busy} onClick={generate}>
          Generate data
        </button>
        <p className="setup__values">{values.length ? values.join(', ') : 'No data yet'}</p>
        <AlgorithmPicker algorithms={algorithms} selected={selected} onChange={setSelected} max={MAX_LANES} />
        <button
          type="button"
          className="primary"
          disabled={busy || !values.length || !selected.length}
          onClick={() => visualize(values, selected)}
        >
          {busy ? 'Working…' : 'Visualize'}
        </button>
      </aside>

      <main className="stage">
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <div className="legend">
          <span className="tag tag--compare">compare</span> highlight only, nothing moves
          <span className="tag tag--swap">swap</span> two bars trade places
          <span className="tag tag--write">write</span> one slot takes a new value
        </div>
        {experiment && algorithms.length ? (
          <Theater key={runId} experiment={experiment} algorithms={algorithms} active={active} />
        ) : (
          !error && <p className="empty">{busy ? 'Running the algorithms…' : 'Pick algorithms and press Visualize.'}</p>
        )}
      </main>
    </>
  )
}
