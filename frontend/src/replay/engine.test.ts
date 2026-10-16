import { describe, expect, it } from 'vitest'
import type { SortEvent, SortExperiment } from '../api/client'
import { Replay } from './engine'
import recorded from './__fixtures__/sort-trace.json'

// Real /sort trace for all ten algorithms on 14 negative and duplicate values. Sequence
// numbers were stripped from the fixture to keep it small; they equal the event position.
const experiment = recorded as unknown as SortExperiment
const traces = experiment.results.map((result) => ({
  id: result.algorithm_id,
  output: result.output_values,
  events: (result.events ?? []).map((event, sequence) => ({ ...event, sequence })) as SortEvent[],
}))

const values = (replay: Replay, cursor: number) => replay.barsAt(cursor).map((bar) => bar.value)

describe('Replay', () => {
  it.each(traces)('$id replays to its sorted output', ({ events, output }) => {
    const replay = new Replay(experiment.input_values, events)
    expect(values(replay, replay.length)).toEqual(output)
  })

  it.each(traces)('$id gives the same state from checkpoints as from the start', ({ events }) => {
    const checkpointed = new Replay(experiment.input_values, events, 7)
    const linear = new Replay(experiment.input_values, events, Number.MAX_SAFE_INTEGER)
    for (let cursor = 0; cursor <= events.length; cursor += 1) {
      expect(values(checkpointed, cursor)).toEqual(values(linear, cursor))
    }
  })

  it.each(traces)('$id counts match the replayed event kinds', ({ events }) => {
    const replay = new Replay(experiment.input_values, events)
    const kinds = { compare: 0, swap: 0, write: 0 }
    for (const event of events) kinds[event.kind] += 1
    expect(replay.countsAt(replay.length)).toEqual(kinds)
    expect(replay.countsAt(0)).toEqual({ compare: 0, swap: 0, write: 0 })
  })

  it('moves bar identities on swaps and keeps them on writes', () => {
    const events: SortEvent[] = [
      { sequence: 0, kind: 'swap', indices: [0, 2], values: [3, 1] },
      { sequence: 1, kind: 'write', indices: [1], values: [9] },
    ]
    const replay = new Replay([1, 2, 3], events)
    expect(replay.barsAt(1)).toEqual([
      { id: 2, value: 3 },
      { id: 1, value: 2 },
      { id: 0, value: 1 },
    ])
    expect(replay.barsAt(2)[1]).toEqual({ id: 1, value: 9 })
    expect(replay.eventAt(0)).toBeNull()
    expect(replay.eventAt(2)).toBe(events[1])
  })

  it('clamps cursors outside the trace', () => {
    const replay = new Replay([2, 1], [{ sequence: 0, kind: 'swap', indices: [0, 1], values: [1, 2] }])
    expect(values(replay, -5)).toEqual([2, 1])
    expect(values(replay, 99)).toEqual([1, 2])
  })
})
