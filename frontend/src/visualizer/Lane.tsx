import type { CSSProperties } from 'react'
import type { AlgorithmMetadata, OperationMetrics } from '../api/client'
import type { Replay } from '../replay/engine'
import { formatCount } from '../shared/lab'
import { useWidth } from '../shared/useWidth'

interface LaneProps {
  algorithm: AlgorithmMetadata
  replay: Replay
  metrics: OperationMetrics
  cursor: number
  /** Animation length in ms; 0 disables movement when playback is too fast to follow. */
  duration: number
  /** Finishing position in the race; lanes with equal trace lengths share a place. */
  place: number
}

/** Minimum slot width in px before per-bar labels would collide. */
const VALUE_LABEL_MIN = 22
const INDEX_LABEL_MIN = 16

const ordinal = (place: number) => {
  const suffix = place % 100 >= 11 && place % 100 <= 13 ? 'th' : ['th', 'st', 'nd', 'rd'][place % 10] ?? 'th'
  return `${place}${suffix}`
}

export function Lane({ algorithm, replay, metrics, cursor, duration, place }: LaneProps) {
  const [stageRef, stageWidth] = useWidth<HTMLDivElement>()
  const position = Math.min(cursor, replay.length)
  const bars = replay.barsAt(position)
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
  const progress = replay.length ? (position / replay.length) * 100 : 100

  return (
    <article className={`lane${done ? ' lane--done' : ''}${done && place === 1 ? ' lane--first' : ''}`}>
      <header className="lane__head">
        <h3>{algorithm.name}</h3>
        {done ? (
          <span className="lane__place">{ordinal(place)}</span>
        ) : (
          <span className="lane__status">
            {formatCount(position)} / {formatCount(replay.length)}
          </span>
        )}
      </header>
      <div className="lane__progress" aria-hidden="true">
        <span style={{ width: `${progress}%` }} />
      </div>

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

      <p className="lane__op">
        {event ? (
          <>
            <span className={`tag tag--${event.kind}`}>{event.kind}</span>
            {event.indices.map((index) => `[${index}]`).join(event.kind === 'swap' ? ' ↔ ' : ' · ')}
          </>
        ) : done ? (
          `Sorted in ${formatCount(replay.length)} steps`
        ) : (
          'Ready'
        )}
      </p>

      <dl className="lane__specs">
        <div>
          <dt>Comparisons</dt>
          <dd>
            {formatCount(counts.compare)} <small>/ {formatCount(metrics.comparisons)}</small>
          </dd>
        </div>
        <div>
          <dt>Swaps</dt>
          <dd>
            {formatCount(counts.swap)} <small>/ {formatCount(metrics.swaps)}</small>
          </dd>
        </div>
        <div>
          <dt>Array writes</dt>
          <dd>
            {formatCount(counts.write + counts.swap * 2)} <small>/ {formatCount(metrics.array_writes)}</small>
          </dd>
        </div>
        <div>
          <dt>Average</dt>
          <dd>{algorithm.complexity.average}</dd>
        </div>
        <div>
          <dt>Worst</dt>
          <dd>{algorithm.complexity.worst}</dd>
        </div>
        <div>
          <dt>Space</dt>
          <dd>{algorithm.complexity.auxiliary_space}</dd>
        </div>
      </dl>
      <p className="lane__traits">
        <span>best {algorithm.complexity.best}</span>
        <span>{algorithm.stable ? 'stable' : 'not stable'}</span>
        <span>{algorithm.in_place ? 'in place' : 'extra memory'}</span>
        <span>aux writes {formatCount(metrics.auxiliary_writes)}</span>
      </p>
    </article>
  )
}
