import type { CSSProperties } from 'react'
import type { AlgorithmMetadata, OperationMetrics } from '../api/client'
import type { Replay } from '../replay/engine'
import { heldOperand, narrate } from '../replay/narrate'
import { useWidth } from '../shared/useWidth'

interface LaneProps {
  algorithm: AlgorithmMetadata
  replay: Replay
  metrics: OperationMetrics
  cursor: number
  /** Animation length in ms; 0 disables movement when playback is too fast to follow. */
  duration: number
}

/** Minimum slot width in px before per-bar labels would collide. */
const VALUE_LABEL_MIN = 26
const INDEX_LABEL_MIN = 18

export function Lane({ algorithm, replay, metrics, cursor, duration }: LaneProps) {
  const [stageRef, stageWidth] = useWidth<HTMLDivElement>()
  const position = Math.min(cursor, replay.length)
  const bars = replay.barsAt(position)
  const before = replay.barsAt(position - 1).map((bar) => bar.value)
  const done = position >= replay.length && position > 0
  // Once a lane has finished, its last event is history, not the current step.
  const event = done ? null : replay.eventAt(position)
  const counts = replay.countsAt(position)

  const low = Math.min(0, ...replay.input)
  const high = Math.max(0, ...replay.input)
  const span = high - low || 1
  const zero = (high / span) * 100
  const width = 100 / Math.max(1, bars.length)
  const slot = stageWidth / Math.max(1, bars.length)
  const showValues = slot >= VALUE_LABEL_MIN
  const showIndices = slot >= INDEX_LABEL_MIN

  const active = new Set(event?.indices ?? [])
  const heldValue = heldOperand(event, before)
  const narration = done
    ? `Sorted after ${replay.length} steps.`
    : narrate(event, before)

  return (
    <section className={`lane${done ? ' lane--done' : ''}`}>
      <header className="lane__head">
        <h2>{algorithm.name}</h2>
        <span className="lane__complexity">
          avg {algorithm.complexity.average} · worst {algorithm.complexity.worst}
        </span>
        <span className="lane__status">
          {done ? 'Sorted' : `step ${position} / ${replay.length}`}
        </span>
      </header>

      <div
        ref={stageRef}
        className={`lane__stage${showValues ? ' lane__stage--values' : ''}${low < 0 ? ' lane__stage--negative' : ''}`}
        style={{ '--zero': `${zero}%`, '--duration': `${duration}ms` } as CSSProperties}
      >
        <div className="lane__zero" />
        {bars.map((bar, index) => {
          const top = ((high - Math.max(bar.value, 0)) / span) * 100
          const height = (Math.abs(bar.value) / span) * 100
          const role = active.has(index) && event ? ` bar--${event.kind}` : ''
          return (
            <div
              key={bar.id}
              className={`bar${role}${bar.value < 0 ? ' bar--neg' : ''}`}
              style={{ left: `${index * width}%`, width: `${width}%`, top: `${top}%`, height: `${height}%` }}
            >
              <span className="bar__fill" />
              {showValues && <span className="bar__value">{bar.value}</span>}
            </div>
          )
        })}
      </div>
      {showIndices && (
        <div className="lane__indices" aria-hidden="true">
          {bars.map((_, index) => (
            <span key={index} className={active.has(index) ? 'is-active' : undefined}>
              {index}
            </span>
          ))}
        </div>
      )}

      <p className="lane__narration" aria-live="polite">
        {event && <span className={`tag tag--${event.kind}`}>{event.kind}</span>}
        <span className="lane__sentence">{narration}</span>
        {heldValue !== null && <span className="lane__held">held value {heldValue}</span>}
      </p>

      <dl className="lane__metrics">
        <div>
          <dt>Comparisons</dt>
          <dd>
            {counts.compare} <small>/ {metrics.comparisons}</small>
          </dd>
        </div>
        <div>
          <dt>Swaps</dt>
          <dd>
            {counts.swap} <small>/ {metrics.swaps}</small>
          </dd>
        </div>
        <div>
          <dt>Array writes</dt>
          <dd>
            {counts.write + counts.swap * 2} <small>/ {metrics.array_writes}</small>
          </dd>
        </div>
        <div>
          <dt>Auxiliary writes</dt>
          <dd>{metrics.auxiliary_writes}</dd>
        </div>
      </dl>
    </section>
  )
}
