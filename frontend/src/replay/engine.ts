import type { SortEvent } from '../api/client'

/** One displayed array element. `id` follows the element through swaps so it can animate. */
export interface Bar {
  id: number
  value: number
}

export interface OperationCounts {
  compare: number
  swap: number
  write: number
}

function applyEvent(bars: Bar[], event: SortEvent): void {
  if (event.kind === 'swap') {
    const [first, second] = event.indices
    const moved = bars[first]
    bars[first] = bars[second]
    bars[second] = moved
  } else if (event.kind === 'write') {
    // A write replaces the value in place; the slot keeps its identity so its height animates.
    const [index] = event.indices
    bars[index] = { id: bars[index].id, value: event.values[0] }
  }
  // `compare` never mutates the displayed array.
}

/**
 * Rebuilds the displayed array for any cursor (number of applied events) by replaying the
 * trace from the nearest checkpoint, so stepping backward and scrubbing need no server call.
 */
export class Replay {
  readonly input: readonly number[]
  readonly events: readonly SortEvent[]
  private readonly interval: number
  private readonly checkpoints: Bar[][]
  private readonly counts: OperationCounts[]

  constructor(input: readonly number[], events: readonly SortEvent[], checkpointInterval = 256) {
    this.input = input
    this.events = events
    this.interval = checkpointInterval
    const bars = input.map((value, id) => ({ id, value }))
    const running: OperationCounts = { compare: 0, swap: 0, write: 0 }
    this.checkpoints = [bars.slice()]
    this.counts = [{ ...running }]
    events.forEach((event, index) => {
      applyEvent(bars, event)
      running[event.kind] += 1
      this.counts.push({ ...running })
      if ((index + 1) % this.interval === 0) this.checkpoints.push(bars.slice())
    })
  }

  get length(): number {
    return this.events.length
  }

  /** The array after the first `cursor` events have been applied. */
  barsAt(cursor: number): Bar[] {
    const target = Math.max(0, Math.min(cursor, this.events.length))
    const checkpoint = Math.floor(target / this.interval)
    const bars = this.checkpoints[checkpoint].slice()
    for (let index = checkpoint * this.interval; index < target; index += 1) {
      applyEvent(bars, this.events[index])
    }
    return bars
  }

  /** The event applied most recently at `cursor`, or null before the first event. */
  eventAt(cursor: number): SortEvent | null {
    return cursor > 0 && cursor <= this.events.length ? this.events[cursor - 1] : null
  }

  /** Operations replayed so far; auxiliary writes have no events, so they are not included. */
  countsAt(cursor: number): OperationCounts {
    return this.counts[Math.max(0, Math.min(cursor, this.events.length))]
  }
}
