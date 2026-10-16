import { useState } from 'react'
import { useWidth } from '../shared/useWidth'
import { niceTicks } from './scale'

export interface LineSeries {
  id: string
  label: string
  /** Fixed palette slot (1-based) so an algorithm keeps its colour across charts; 0 is a grey context line. */
  slot: number
  /** One value per x position; null where the case was not measured. */
  values: (number | null)[]
}

interface LineChartProps {
  title: string
  xValues: number[]
  xLabel: string
  series: LineSeries[]
  /** Shared upper bound so small multiples compare on one scale. */
  yMax: number
  format: (value: number) => string
  tickFormat: (value: number) => string
}

const HEIGHT = 240
const MARGIN = { top: 14, right: 16, bottom: 34, left: 56 }

/** One panel of a small-multiples line chart with a crosshair tooltip. */
export function LineChart({ title, xValues, xLabel, series, yMax, format, tickFormat }: LineChartProps) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const [hover, setHover] = useState<number | null>(null)
  const ticks = niceTicks(yMax || 1, 4)
  const domain = ticks[ticks.length - 1]
  const plotWidth = Math.max(10, width - MARGIN.left - MARGIN.right)
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom
  const xMin = Math.min(...xValues)
  const xMax = Math.max(...xValues)
  const x = (value: number) => MARGIN.left + (xMax === xMin ? plotWidth / 2 : ((value - xMin) / (xMax - xMin)) * plotWidth)
  const y = (value: number) => MARGIN.top + plotHeight - (value / domain) * plotHeight

  const nearest = (clientX: number, element: SVGSVGElement) => {
    const offset = clientX - element.getBoundingClientRect().left
    let best = 0
    xValues.forEach((value, index) => {
      if (Math.abs(x(value) - offset) < Math.abs(x(xValues[best]) - offset)) best = index
    })
    return best
  }

  return (
    <figure className="chart line-chart">
      <figcaption className="chart__title">{title}</figcaption>
      <div ref={ref} className="line-chart__plot">
        {width > 0 && (
          <svg
            width={width}
            height={HEIGHT}
            role="img"
            aria-label={`${title}: ${series.map((item) => item.label).join(', ')}`}
            onMouseMove={(event) => setHover(nearest(event.clientX, event.currentTarget))}
            onMouseLeave={() => setHover(null)}
          >
            {ticks.map((tick) => (
              <g key={tick}>
                <line className="chart__gridline" x1={MARGIN.left} x2={MARGIN.left + plotWidth} y1={y(tick)} y2={y(tick)} />
                <text className="chart__axis-text" x={MARGIN.left - 8} y={y(tick)} textAnchor="end" dominantBaseline="middle">
                  {tickFormat(tick)}
                </text>
              </g>
            ))}
            {xValues.map((value) => (
              <text key={value} className="chart__axis-text" x={x(value)} y={HEIGHT - MARGIN.bottom + 16} textAnchor="middle">
                {value}
              </text>
            ))}
            <text className="chart__axis-text" x={MARGIN.left + plotWidth / 2} y={HEIGHT - 2} textAnchor="middle">
              {xLabel}
            </text>
            {hover !== null && (
              <line className="chart__crosshair" x1={x(xValues[hover])} x2={x(xValues[hover])} y1={MARGIN.top} y2={MARGIN.top + plotHeight} />
            )}
            {/* Grey context lines go underneath the coloured ones. */}
            {[...series].sort((left, right) => Number(left.slot > 0) - Number(right.slot > 0)).map((item) => {
              const points = item.values
                .map((value, index) => (value === null ? null : ([x(xValues[index]), y(value)] as const)))
                .filter((point): point is readonly [number, number] => point !== null)
              return (
                <g key={item.id} className={`series series--${item.slot}`}>
                  <polyline className="series__line" points={points.map((point) => point.join(',')).join(' ')} />
                  {points.map(([cx, cy], index) => (
                    <circle key={index} className="series__dot" cx={cx} cy={cy} r={hover === index ? 6 : 4} />
                  ))}
                </g>
              )
            })}
          </svg>
        )}
        {hover !== null && width > 0 && (
          <div
            className="chart__tooltip chart__tooltip--floating"
            role="tooltip"
            style={{ left: Math.min(x(xValues[hover]) + 12, width - 190), top: MARGIN.top }}
          >
            <strong>
              {xLabel} {xValues[hover]}
            </strong>
            {[...series]
              .sort((left, right) => (right.values[hover] ?? -1) - (left.values[hover] ?? -1))
              .map((item) => (
                <span key={item.id} className="chart__tooltip-row">
                  <i className={`swatch series--${item.slot}`} aria-hidden="true" />
                  {item.label}
                  <b>{item.values[hover] === null ? '—' : format(item.values[hover]!)}</b>
                </span>
              ))}
          </div>
        )}
      </div>
    </figure>
  )
}
