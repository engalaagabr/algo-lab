import { useState } from 'react'
import { api, request, type AlgorithmMetadata, type BenchmarkSuiteResult } from '../api/client'
import { compactNumber } from '../charts/scale'
import { LineChart, type LineSeries } from '../charts/LineChart'
import { AlgorithmPicker } from '../shared/AlgorithmPicker'
import { DISTRIBUTIONS, distributionLabel, errorMessage, formatCount, formatDuration, integerText, type Distribution } from '../shared/lab'

const SIZE_PRESETS = [10, 25, 50, 100, 250, 500, 1000]
const MAX_CASES = 12
// Lines in small multiples stay legible up to three series; more fold into another run.
const MAX_SERIES = 3

type Metric = 'time' | 'comparisons' | 'array_writes' | 'swaps'

const METRICS: { id: Metric; label: string }[] = [
  { id: 'comparisons', label: 'Comparisons' },
  { id: 'array_writes', label: 'Array writes' },
  { id: 'swaps', label: 'Swaps' },
  { id: 'time', label: 'Median time' },
]

interface SuiteSectionProps {
  algorithms: AlgorithmMetadata[]
}

export function SuiteSection({ algorithms }: SuiteSectionProps) {
  const [selected, setSelected] = useState(['insertion_sort', 'heap_sort', 'quick_sort'])
  const [sizes, setSizes] = useState([50, 100, 250, 500])
  const [distributions, setDistributions] = useState<Distribution[]>(['random', 'reversed', 'nearly_sorted'])
  const [minimum, setMinimum] = useState(1)
  const [maximum, setMaximum] = useState(1000)
  const [seed, setSeed] = useState('42')
  const [repeats, setRepeats] = useState(3)
  const [result, setResult] = useState<BenchmarkSuiteResult | null>(null)
  const [ranWith, setRanWith] = useState<{ ids: string[]; sizes: number[]; distributions: Distribution[] } | null>(null)
  const [metric, setMetric] = useState<Metric>('comparisons')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cases = sizes.length * distributions.length
  const largest = Math.max(0, ...sizes)
  const tooLarge = selected.filter((id) => (algorithms.find((item) => item.id === id)?.max_size ?? Infinity) < largest)
  const toggle = <T,>(list: T[], item: T) => (list.includes(item) ? list.filter((entry) => entry !== item) : [...list, item])
  const name = (id: string) => algorithms.find((item) => item.id === id)?.name ?? id

  const run = async () => {
    setBusy(true)
    setError(null)
    const sortedSizes = [...sizes].sort((left, right) => left - right)
    try {
      const body = {
        algorithm_ids: selected,
        sizes: sortedSizes,
        distributions,
        minimum,
        maximum,
        seed: seed === '' ? null : Number(seed),
        repeats,
        warmups: 1,
      }
      const response = await request(api.POST('/api/v1/benchmark-suites', { body }))
      setResult(response)
      setSeed(String(response.seed))
      setRanWith({ ids: selected, sizes: sortedSizes, distributions })
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setBusy(false)
    }
  }

  const valueOf = (distribution: Distribution, size: number, id: string): number | null => {
    const found = result?.cases?.find((item) => item.dataset.distribution === distribution && item.dataset.size === size)
    const entry = found?.benchmark.results.find((item) => item.algorithm_id === id)
    if (!entry) return null
    return metric === 'time' ? entry.median_ns : entry.metrics[metric]
  }

  const panels =
    ranWith?.distributions.map((distribution) => ({
      distribution,
      series: ranWith.ids.map<LineSeries>((id, index) => ({
        id,
        label: name(id),
        slot: index + 1,
        values: ranWith.sizes.map((size) => valueOf(distribution, size, id)),
      })),
    })) ?? []
  const yMax = Math.max(1, ...panels.flatMap((panel) => panel.series.flatMap((item) => item.values.map((value) => value ?? 0))))
  const format = metric === 'time' ? formatDuration : formatCount
  const metricLabel = METRICS.find((entry) => entry.id === metric)?.label ?? ''

  return (
    <section className="section" aria-labelledby="suite-title">
      <header className="section__head">
        <h2 id="suite-title">Suite</h2>
        <p>
          How does the work grow with the input? Each pattern gets its own chart, all on the same scale; within a
          case every algorithm sorts the same array.
        </p>
      </header>

      <div className="controls">
        <div className="controls__wide">
          <span className="controls__heading">
            Sizes <small>{cases} / {MAX_CASES} cases</small>
          </span>
          <div className="chips">
            {SIZE_PRESETS.map((size) => (
              <button key={size} type="button" className="chip" aria-pressed={sizes.includes(size)} onClick={() => setSizes(toggle(sizes, size))}>
                {size}
              </button>
            ))}
          </div>
        </div>
        <div className="controls__wide">
          <span className="controls__heading">Patterns</span>
          <div className="chips">
            {DISTRIBUTIONS.map((item) => (
              <button
                key={item.value}
                type="button"
                className="chip"
                aria-pressed={distributions.includes(item.value)}
                onClick={() => setDistributions(toggle(distributions, item.value))}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <div className="controls__row">
          <label>
            Min
            <input type="number" value={minimum} onChange={(event) => setMinimum(Number(event.target.value))} />
          </label>
          <label>
            Max
            <input type="number" value={maximum} onChange={(event) => setMaximum(Number(event.target.value))} />
          </label>
        </div>
        <label>
          Seed
          <input value={seed} placeholder="random" inputMode="numeric" onChange={(event) => setSeed(integerText(event.target.value, false))} />
        </label>
        <label>
          Repeats
          <input type="number" min={1} max={15} value={repeats} onChange={(event) => setRepeats(Math.max(1, Math.min(15, Number(event.target.value) || 1)))} />
        </label>
        <AlgorithmPicker algorithms={algorithms} selected={selected} onChange={setSelected} max={MAX_SERIES} inputSize={largest} />
        <div className="controls__actions">
          {cases > MAX_CASES && <p className="controls__hint">Pick at most {MAX_CASES} size × pattern combinations.</p>}
          {tooLarge.length > 0 && (
            <p className="controls__hint">
              {tooLarge.map(name).join(', ')} supports at most {formatCount(Math.min(...tooLarge.map((id) => algorithms.find((item) => item.id === id)!.max_size)))} values.
            </p>
          )}
          <button
            type="button"
            className="primary"
            disabled={busy || !selected.length || !cases || cases > MAX_CASES || tooLarge.length > 0}
            onClick={run}
          >
            {busy ? 'Running suite…' : 'Run suite'}
          </button>
        </div>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!result && !error && <p className="empty">{busy ? 'Running suite…' : 'Choose sizes, patterns and up to three algorithms, then run the suite.'}</p>}

      {result && ranWith && (
        <>
          <div className="segmented" role="tablist" aria-label="Measure">
            {METRICS.map((entry) => (
              <button key={entry.id} type="button" role="tab" aria-selected={metric === entry.id} onClick={() => setMetric(entry.id)}>
                {entry.label}
              </button>
            ))}
          </div>
          <ul className="chart-legend" aria-label="Algorithms">
            {ranWith.ids.map((id, index) => (
              <li key={id}>
                <i className={`swatch swatch--line series--${index + 1}`} aria-hidden="true" />
                {name(id)}
              </li>
            ))}
          </ul>
          <div className="small-multiples">
            {panels.map((panel) => (
              <LineChart
                key={panel.distribution}
                title={`${distributionLabel(panel.distribution)} input`}
                xValues={ranWith.sizes}
                xLabel="Input size"
                series={panel.series}
                yMax={yMax}
                format={format}
                tickFormat={metric === 'time' ? formatDuration : compactNumber}
              />
            ))}
          </div>
          <p className="chart__caption">
            {metric === 'time'
              ? 'Median of the measured runs; timings depend on this machine and vary between runs.'
              : `${metricLabel} are exact counts for one sort of each case.`}
          </p>

          <details className="table-view">
            <summary>Show all numbers</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Pattern</th>
                    <th scope="col">Size</th>
                    {ranWith.ids.map((id) => (
                      <th key={id} scope="col">
                        {name(id)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ranWith.distributions.flatMap((distribution) =>
                    ranWith.sizes.map((size) => (
                      <tr key={`${distribution}-${size}`}>
                        <th scope="row">{distributionLabel(distribution)}</th>
                        <td>{size}</td>
                        {ranWith.ids.map((id) => {
                          const value = valueOf(distribution, size, id)
                          return <td key={id}>{value === null ? '—' : format(value)}</td>
                        })}
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </section>
  )
}
