import { useState } from 'react'
import { api, request, type AlgorithmMetadata, type BenchmarkResult } from '../api/client'
import { BarChart, type BarRow } from '../charts/BarChart'
import { compactNumber } from '../charts/scale'
import { useText } from '../i18n/language'
import type { Messages } from '../i18n/en'
import { AlgorithmPicker } from '../shared/AlgorithmPicker'
import { DatasetFields } from '../shared/DatasetFields'
import { datasetBody, errorMessage, formatCount, formatDuration, type DatasetSettings } from '../shared/lab'

const MAX_DATASET_SIZE = 10_000
const MAX_ALGORITHMS = 10

type Metric = 'time' | 'comparisons' | 'array_writes' | 'swaps'

const METRICS: { id: Metric; label: keyof Messages & string }[] = [
  { id: 'time', label: 'medianTime' },
  { id: 'comparisons', label: 'comparisons' },
  { id: 'array_writes', label: 'arrayWrites' },
  { id: 'swaps', label: 'swaps' },
]

interface BenchmarkSectionProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
  onSelect: (selected: string[]) => void
}

export function BenchmarkSection({ algorithms, selected, onSelect }: BenchmarkSectionProps) {
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
  const [error, setError] = useState<unknown>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      const dataset = await request(api.POST('/api/v1/datasets', { body: datasetBody(settings) }))
      setSettings((current) => ({ ...current, seed: String(dataset.seed) }))
      const body = { values: dataset.values, algorithm_ids: selected, repeats, warmups }
      setResult(await request(api.POST('/api/v1/benchmarks', { body })))
    } catch (cause) {
      setError(cause)
    } finally {
      setBusy(false)
    }
  }

  const text = useText()
  const metricLabel = (id: Metric) => text[METRICS.find((entry) => entry.id === id)!.label] as string
  const name = (id: string) => algorithms.find((item) => item.id === id)?.name ?? id
  const tooLarge = selected.filter((id) => (algorithms.find((item) => item.id === id)?.max_size ?? Infinity) < settings.size)
  const fastest = new Set(result?.fastest_algorithm_ids)

  const rows: BarRow[] = (result?.results ?? [])
    .map((item) => {
      const value = metric === 'time' ? item.median_ns : item.metrics[metric]
      return {
        id: item.algorithm_id,
        label: name(item.algorithm_id),
        badge: metric === 'time' && fastest.has(item.algorithm_id) ? text.fastest : undefined,
        value,
        low: metric === 'time' ? item.min_ns : undefined,
        high: metric === 'time' ? item.max_ns : undefined,
        details:
          metric === 'time'
            ? [
                text.medianDetail(formatDuration(item.median_ns)),
                text.rangeDetail(formatDuration(item.min_ns), formatDuration(item.max_ns)),
                text.samplesDetail(item.samples_ns.map(formatDuration).join(', ')),
              ]
            : [text.countDetail(formatCount(value), metricLabel(metric))],
      }
    })
    .sort((left, right) => left.value - right.value)

  return (
    <section className="section" aria-labelledby="benchmark-title">
      <header className="section__head">
        <h2 id="benchmark-title">{text.benchmarkTitle}</h2>
        <p>{text.benchmarkIntro(repeats)}</p>
      </header>

      <div className="controls">
        <DatasetFields value={settings} onChange={setSettings} maxSize={MAX_DATASET_SIZE} sizeControl="number" />
        <div className="controls__row">
          <label>
            {text.repeats}
            <input type="number" min={1} max={15} value={repeats} onChange={(event) => setRepeats(Math.max(1, Math.min(15, Number(event.target.value) || 1)))} />
          </label>
          <label>
            {text.warmups}
            <input type="number" min={0} max={3} value={warmups} onChange={(event) => setWarmups(Math.max(0, Math.min(3, Number(event.target.value) || 0)))} />
          </label>
        </div>
        <AlgorithmPicker
          algorithms={algorithms}
          selected={selected}
          onChange={onSelect}
          max={MAX_ALGORITHMS}
          inputSize={settings.size}
        />
        <div className="controls__actions">
          {tooLarge.length > 0 && (
            <p className="controls__hint">{text.unselectOrShrink(tooLarge.map(name).join(', '))}</p>
          )}
          <button type="button" className="primary" disabled={busy || !selected.length || tooLarge.length > 0} onClick={run}>
            {busy ? text.measuring : text.runBenchmark}
          </button>
        </div>
      </div>

      {error !== null && (
        <p className="error" role="alert">
          {errorMessage(error, text)}
        </p>
      )}
      {!result && error === null && <p className="empty">{busy ? text.measuring : text.chooseBenchmark}</p>}

      {result && (
        <>
          <div className="summary">
            <div className="summary__item">
              <span>{text.fastestMedian}</span>
              <strong>{result.fastest_algorithm_ids.map(name).join(', ')}</strong>
            </div>
            <div className="summary__item">
              <span>{text.input}</span>
              <strong>
                {text.valuesAndSeed(formatCount(result.input_values.length), settings.seed)}
              </strong>
            </div>
            <div className="summary__item">
              <span>{text.runs}</span>
              <strong>
                {text.measuredRuns(result.repeats, result.warmups)}
              </strong>
            </div>
          </div>
          {result.noise_warning && (
            <p className="notice" role="status">
              <span className="notice__icon" aria-hidden="true">!</span>
              <span>
                <strong>{text.tooClose}</strong> {text.tooCloseDetail}
              </span>
            </p>
          )}

          <div className="segmented" role="tablist" aria-label={text.measure}>
            {METRICS.map((entry) => (
              <button
                key={entry.id}
                type="button"
                role="tab"
                aria-selected={metric === entry.id}
                onClick={() => setMetric(entry.id)}
              >
                {text[entry.label] as string}
              </button>
            ))}
          </div>

          <BarChart
            title={metric === 'time' ? text.medianPerRun : text.forOneSort(metricLabel(metric))}
            rows={rows}
            format={metric === 'time' ? formatDuration : formatCount}
            tickFormat={metric === 'time' ? formatDuration : compactNumber}
            caption={metric === 'time' ? text.medianCaption : text.countsCaption}
          />

          <details className="table-view">
            <summary>{text.showAllNumbers}</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">{text.algorithm}</th>
                    <th scope="col">{text.median}</th>
                    <th scope="col">{text.min}</th>
                    <th scope="col">{text.max}</th>
                    <th scope="col">{text.spread}</th>
                    <th scope="col">{text.comparisons}</th>
                    <th scope="col">{text.swaps}</th>
                    <th scope="col">{text.arrayWrites}</th>
                    <th scope="col">{text.auxWrites}</th>
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
