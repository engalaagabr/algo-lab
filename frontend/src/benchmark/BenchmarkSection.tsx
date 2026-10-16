import { useState } from 'react'
import { api, request, type AlgorithmMetadata, type BenchmarkResult } from '../api/client'
import { BarChart, type BarRow } from '../charts/BarChart'
import { compactNumber } from '../charts/scale'
import { DatasetFields } from '../shared/DatasetFields'
import { SelectedAlgorithms } from '../shared/SelectedAlgorithms'
import { datasetBody, errorMessage, formatCount, formatDuration, type DatasetSettings } from '../shared/lab'

const MAX_DATASET_SIZE = 10_000

type Metric = 'time' | 'comparisons' | 'array_writes' | 'swaps'

const METRICS: { id: Metric; label: string }[] = [
  { id: 'time', label: 'Median time' },
  { id: 'comparisons', label: 'Comparisons' },
  { id: 'array_writes', label: 'Array writes' },
  { id: 'swaps', label: 'Swaps' },
]

interface BenchmarkSectionProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
}

export function BenchmarkSection({ algorithms, selected }: BenchmarkSectionProps) {
  const [settings, setSettings] = useState<DatasetSettings>({
    size: 500,
    minimum: 1,
    maximum: 10_000,
    distribution: 'random',
    seed: '42',
  })
  const [repeats, setRepeats] = useState(5)
  const [warmups, setWarmups] = useState(1)
  const [result, setResult] = useState<BenchmarkResult | null>(null)
  const [metric, setMetric] = useState<Metric>('time')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      const dataset = await request(api.POST('/api/v1/datasets', { body: datasetBody(settings) }))
      setSettings((current) => ({ ...current, seed: String(dataset.seed) }))
      const body = { values: dataset.values, algorithm_ids: selected, repeats, warmups }
      setResult(await request(api.POST('/api/v1/benchmarks', { body })))
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setBusy(false)
    }
  }

  const name = (id: string) => algorithms.find((item) => item.id === id)?.name ?? id
  const tooLarge = selected.filter((id) => (algorithms.find((item) => item.id === id)?.max_size ?? Infinity) < settings.size)
  const fastest = new Set(result?.fastest_algorithm_ids)

  const rows: BarRow[] = (result?.results ?? [])
    .map((item) => {
      const value = metric === 'time' ? item.median_ns : item.metrics[metric]
      return {
        id: item.algorithm_id,
        label: name(item.algorithm_id),
        badge: metric === 'time' && fastest.has(item.algorithm_id) ? 'Fastest' : undefined,
        value,
        low: metric === 'time' ? item.min_ns : undefined,
        high: metric === 'time' ? item.max_ns : undefined,
        details:
          metric === 'time'
            ? [
                `Median ${formatDuration(item.median_ns)}`,
                `Range ${formatDuration(item.min_ns)} – ${formatDuration(item.max_ns)}`,
                `Samples ${item.samples_ns.map(formatDuration).join(', ')}`,
              ]
            : [`${formatCount(value)} ${METRICS.find((entry) => entry.id === metric)?.label.toLowerCase()}`],
      }
    })
    .sort((left, right) => left.value - right.value)

  return (
    <section className="section" aria-labelledby="benchmark-title">
      <header className="section__head">
        <h2 id="benchmark-title">Benchmark</h2>
        <p>Compare measured performance on one dataset.</p>
      </header>

      <div className="controls">
        <DatasetFields value={settings} onChange={setSettings} maxSize={MAX_DATASET_SIZE} sizeControl="number" />
        <div className="controls__row">
          <label>
            Repeats
            <input type="number" min={1} max={15} value={repeats} onChange={(event) => setRepeats(Math.max(1, Math.min(15, Number(event.target.value) || 1)))} />
          </label>
          <label>
            Warm-ups
            <input type="number" min={0} max={3} value={warmups} onChange={(event) => setWarmups(Math.max(0, Math.min(3, Number(event.target.value) || 0)))} />
          </label>
        </div>
        <SelectedAlgorithms algorithms={algorithms} selected={selected} />
        <div className="controls__actions">
          {tooLarge.length > 0 && (
            <p className="controls__hint">Unselect {tooLarge.map(name).join(', ')} or use a smaller size.</p>
          )}
          <button type="button" className="primary" disabled={busy || !selected.length || tooLarge.length > 0} onClick={run}>
            {busy ? 'Measuring…' : 'Run benchmark'}
          </button>
        </div>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!result && !error && <p className="empty">{busy ? 'Measuring…' : 'Choose benchmark settings, then run the selected algorithms.'}</p>}

      {result && (
        <>
          <div className="summary">
            <div className="summary__item">
              <span>Fastest median</span>
              <strong>{result.fastest_algorithm_ids.map(name).join(', ')}</strong>
            </div>
            <div className="summary__item">
              <span>Input</span>
              <strong>
                {formatCount(result.input_values.length)} values · seed {settings.seed}
              </strong>
            </div>
            <div className="summary__item">
              <span>Runs</span>
              <strong>
                {result.repeats} measured + {result.warmups} warm-up
              </strong>
            </div>
          </div>
          {result.noise_warning && (
            <p className="notice" role="status">
              <span className="notice__icon" aria-hidden="true">!</span>
              <span>
                <strong>Too close to call.</strong> The fastest algorithm's timing range overlaps another one's, so
                the ranking may change on another run.
              </span>
            </p>
          )}

          <div className="segmented" role="tablist" aria-label="Measure">
            {METRICS.map((entry) => (
              <button
                key={entry.id}
                type="button"
                role="tab"
                aria-selected={metric === entry.id}
                onClick={() => setMetric(entry.id)}
              >
                {entry.label}
              </button>
            ))}
          </div>

          <BarChart
            title={metric === 'time' ? 'Median time per run (lower is faster)' : `${METRICS.find((entry) => entry.id === metric)?.label} for one sort`}
            rows={rows}
            format={metric === 'time' ? formatDuration : formatCount}
            tickFormat={metric === 'time' ? formatDuration : compactNumber}
            caption={metric === 'time' ? 'Bar: median. Line: fastest to slowest sample.' : 'Operation counts are exact and do not vary between runs.'}
          />

          <details className="table-view">
            <summary>Show all numbers</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Algorithm</th>
                    <th scope="col">Median</th>
                    <th scope="col">Min</th>
                    <th scope="col">Max</th>
                    <th scope="col">Spread</th>
                    <th scope="col">Comparisons</th>
                    <th scope="col">Swaps</th>
                    <th scope="col">Array writes</th>
                    <th scope="col">Aux writes</th>
                  </tr>
                </thead>
                <tbody>
                  {[...result.results]
                    .sort((left, right) => left.median_ns - right.median_ns)
                    .map((item) => (
                      <tr key={item.algorithm_id}>
                        <th scope="row">{name(item.algorithm_id)}</th>
                        <td>{formatDuration(item.median_ns)}</td>
                        <td>{formatDuration(item.min_ns)}</td>
                        <td>{formatDuration(item.max_ns)}</td>
                        <td>{formatDuration(item.spread_ns)}</td>
                        <td>{formatCount(item.metrics.comparisons)}</td>
                        <td>{formatCount(item.metrics.swaps)}</td>
                        <td>{formatCount(item.metrics.array_writes)}</td>
                        <td>{formatCount(item.metrics.auxiliary_writes)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </section>
  )
}
