import { useState } from 'react'
import { api, request, type AlgorithmMetadata, type BenchmarkSuiteResult } from '../api/client'
import { compactNumber } from '../charts/scale'
import { LineChart, type LineSeries } from '../charts/LineChart'
import { useText } from '../i18n/language'
import type { Messages } from '../i18n/en'
import { AlgorithmPicker } from '../shared/AlgorithmPicker'
import { DISTRIBUTIONS, distributionLabel, errorMessage, formatCount, formatDuration, integerText, type Distribution } from '../shared/lab'

const SIZE_PRESETS = [10, 25, 50, 100, 250, 500, 1000]
const MAX_CASES = 12
const MAX_ALGORITHMS = 10
// Only three lines get a colour at once; the rest stay grey for context until picked in the legend.
const COLOURED_LINES = 3

type Metric = 'time' | 'comparisons' | 'array_writes' | 'swaps'

const METRICS: { id: Metric; label: keyof Messages & string }[] = [
  { id: 'comparisons', label: 'comparisons' },
  { id: 'array_writes', label: 'arrayWrites' },
  { id: 'swaps', label: 'swaps' },
  { id: 'time', label: 'medianTime' },
]

interface SuiteSectionProps {
  algorithms: AlgorithmMetadata[]
  selected: string[]
  onSelect: (selected: string[]) => void
}

export function SuiteSection({ algorithms, selected, onSelect }: SuiteSectionProps) {
  const [sizes, setSizes] = useState([50, 100, 250, 500])
  const [distributions, setDistributions] = useState<Distribution[]>(['random', 'reversed', 'nearly_sorted'])
  const [minimum, setMinimum] = useState(1)
  const [maximum, setMaximum] = useState(1000)
  const [seed, setSeed] = useState('42')
  const [repeats, setRepeats] = useState(3)
  const [result, setResult] = useState<BenchmarkSuiteResult | null>(null)
  const [ranWith, setRanWith] = useState<{ ids: string[]; sizes: number[]; distributions: Distribution[] } | null>(null)
  /** Palette slots in order; an algorithm keeps its slot until it is unpicked. */
  const [coloured, setColoured] = useState<(string | null)[]>([])
  const [metric, setMetric] = useState<Metric>('comparisons')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const text = useText()
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
      setColoured(selected.slice(0, COLOURED_LINES))
    } catch (cause) {
      setError(cause)
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

  // Slot 0 is the grey context line.
  const slotOf = (id: string) => coloured.indexOf(id) + 1

  const toggleColour = (id: string) => {
    const next = Array.from({ length: COLOURED_LINES }, (_, index) => coloured[index] ?? null)
    const at = next.indexOf(id)
    if (at >= 0) next[at] = null
    else {
      const free = next.indexOf(null)
      next[free >= 0 ? free : 0] = id
    }
    setColoured(next)
  }

  const panels =
    ranWith?.distributions.map((distribution) => ({
      distribution,
      series: ranWith.ids.map<LineSeries>((id) => ({
        id,
        label: name(id),
        slot: slotOf(id),
        values: ranWith.sizes.map((size) => valueOf(distribution, size, id)),
      })),
    })) ?? []
  const yMax = Math.max(1, ...panels.flatMap((panel) => panel.series.flatMap((item) => item.values.map((value) => value ?? 0))))
  const format = metric === 'time' ? formatDuration : formatCount
  const metricLabel = text[METRICS.find((entry) => entry.id === metric)!.label] as string

  return (
    <section className="section" aria-labelledby="suite-title">
      <header className="section__head">
        <h2 id="suite-title">{text.suiteTitle}</h2>
        <p>{text.suiteIntro}</p>
      </header>

      <div className="controls">
        <div className="controls__wide">
          <span className="controls__heading">
            {text.sizes} <small>{text.cases(cases, MAX_CASES)}</small>
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
          <span className="controls__heading">{text.patterns}</span>
          <div className="chips">
            {DISTRIBUTIONS.map((item) => (
              <button
                key={item.value}
                type="button"
                className="chip"
                aria-pressed={distributions.includes(item.value)}
                onClick={() => setDistributions(toggle(distributions, item.value))}
              >
                {text[item.label]}
              </button>
            ))}
          </div>
        </div>
        <div className="controls__row">
          <label>
            {text.min}
            <input type="number" value={minimum} onChange={(event) => setMinimum(Number(event.target.value))} />
          </label>
          <label>
            {text.max}
            <input type="number" value={maximum} onChange={(event) => setMaximum(Number(event.target.value))} />
          </label>
        </div>
        <label>
          {text.seed}
          <input value={seed} placeholder={text.seedPlaceholder} inputMode="numeric" onChange={(event) => setSeed(integerText(event.target.value, false))} />
        </label>
        <label>
          {text.repeats}
          <input type="number" min={1} max={15} value={repeats} onChange={(event) => setRepeats(Math.max(1, Math.min(15, Number(event.target.value) || 1)))} />
        </label>
        <AlgorithmPicker algorithms={algorithms} selected={selected} onChange={onSelect} max={MAX_ALGORITHMS} inputSize={largest} />
        <div className="controls__actions">
          {cases > MAX_CASES && <p className="controls__hint">{text.tooManyCases(MAX_CASES)}</p>}
          {tooLarge.length > 0 && (
            <p className="controls__hint">
              {text.supportsAtMost(
                tooLarge.map(name).join(', '),
                formatCount(Math.min(...tooLarge.map((id) => algorithms.find((item) => item.id === id)!.max_size))),
              )}
            </p>
          )}
          <button
            type="button"
            className="primary"
            disabled={busy || !selected.length || !cases || cases > MAX_CASES || tooLarge.length > 0}
            onClick={run}
          >
            {busy ? text.runningSuite : text.runSuite}
          </button>
        </div>
      </div>

      {error !== null && (
        <p className="error" role="alert">
          {errorMessage(error, text)}
        </p>
      )}
      {!result && error === null && <p className="empty">{busy ? text.runningSuite : text.chooseSuite}</p>}

      {result && ranWith && (
        <>
          <div className="segmented" role="tablist" aria-label={text.measure}>
            {METRICS.map((entry) => (
              <button key={entry.id} type="button" role="tab" aria-selected={metric === entry.id} onClick={() => setMetric(entry.id)}>
                {text[entry.label] as string}
              </button>
            ))}
          </div>
          <ul className="chart-legend" aria-label={text.algorithms}>
            {ranWith.ids.map((id) => (
              <li key={id}>
                <button type="button" className="chart-legend__item" aria-pressed={slotOf(id) > 0} onClick={() => toggleColour(id)}>
                  <i className={`swatch swatch--line series--${slotOf(id)}`} aria-hidden="true" />
                  {name(id)}
                </button>
              </li>
            ))}
          </ul>
          {ranWith.ids.length > COLOURED_LINES && (
            <p className="chart__caption">{text.colourHint(COLOURED_LINES)}</p>
          )}
          <div className="small-multiples">
            {panels.map((panel) => (
              <LineChart
                key={panel.distribution}
                title={text.patternInput(distributionLabel(text, panel.distribution))}
                xValues={ranWith.sizes}
                xLabel={text.inputSize}
                series={panel.series}
                yMax={yMax}
                format={format}
                tickFormat={metric === 'time' ? formatDuration : compactNumber}
              />
            ))}
          </div>
          <p className="chart__caption">
            {metric === 'time'
              ? text.timeCaption
              : text.exactCountsCaption(metricLabel)}
          </p>

          <details className="table-view">
            <summary>{text.showAllNumbers}</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">{text.pattern}</th>
                    <th scope="col">{text.size}</th>
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
                        <th scope="row">{distributionLabel(text, distribution)}</th>
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
