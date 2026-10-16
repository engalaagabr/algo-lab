import { niceTicks } from './scale'

export interface BarRow {
  id: string
  label: string
  badge?: string
  value: number
  /** Optional range drawn as a whisker, e.g. min and max of the timing samples. */
  low?: number
  high?: number
  details: string[]
}

interface BarChartProps {
  title: string
  rows: BarRow[]
  format: (value: number) => string
  tickFormat: (value: number) => string
  caption?: string
}

/** Horizontal single-series bars; the label column carries identity, so one colour suffices. */
export function BarChart({ title, rows, format, tickFormat, caption }: BarChartProps) {
  const ticks = niceTicks(Math.max(1, ...rows.map((row) => Math.max(row.value, row.high ?? 0))))
  const domain = ticks[ticks.length - 1]
  const percent = (value: number) => `${(value / domain) * 100}%`

  return (
    <figure className="chart bar-chart">
      <figcaption className="chart__title">{title}</figcaption>
      <div className="bar-chart__rows">
        {rows.map((row) => (
          <div key={row.id} className="bar-chart__row" tabIndex={0}>
            <span className="bar-chart__label">
              {row.label}
              {row.badge && <span className="chart__badge">{row.badge}</span>}
            </span>
            <span className="bar-chart__track">
              {ticks.map((tick) => (
                <span key={tick} className="chart__grid" style={{ left: percent(tick) }} />
              ))}
              <span className="bar-chart__bar" style={{ width: percent(row.value) }} />
              {row.low !== undefined && row.high !== undefined && (
                <span className="bar-chart__whisker" style={{ left: percent(row.low), width: `calc(${percent(row.high)} - ${percent(row.low)})` }} />
              )}
              <span className="chart__tooltip" role="tooltip">
                <strong>{row.label}</strong>
                {row.details.map((line) => (
                  <span key={line}>{line}</span>
                ))}
              </span>
            </span>
            <span className="bar-chart__value">{format(row.value)}</span>
          </div>
        ))}
        <div className="bar-chart__row bar-chart__axis" aria-hidden="true">
          <span />
          <span className="bar-chart__track">
            {ticks.map((tick) => (
              <span key={tick} className="chart__tick" style={{ left: percent(tick) }}>
                {tickFormat(tick)}
              </span>
            ))}
          </span>
          <span />
        </div>
      </div>
      {caption && <p className="chart__caption">{caption}</p>}
    </figure>
  )
}
