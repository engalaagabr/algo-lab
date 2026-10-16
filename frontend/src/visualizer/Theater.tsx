import { useEffect, useMemo } from 'react'
import type { AlgorithmMetadata, SortExperiment } from '../api/client'
import { Replay } from '../replay/engine'
import { Lane } from './Lane'
import { SPEEDS, usePlayback } from './usePlayback'

interface TheaterProps {
  experiment: SortExperiment
  algorithms: AlgorithmMetadata[]
}

/** Race lanes for one experiment plus the shared transport; remount it for each new experiment. */
export function Theater({ experiment, algorithms }: TheaterProps) {
  const lanes = useMemo(
    () =>
      experiment.results.map((result) => ({
        result,
        algorithm: algorithms.find((item) => item.id === result.algorithm_id),
        replay: new Replay(experiment.input_values, result.events ?? []),
      })),
    [experiment, algorithms],
  )
  const longest = Math.max(0, ...lanes.map((lane) => lane.replay.length))
  // Every lane advances one event per step, so a shorter trace finishes earlier.
  const placeOf = (length: number) => 1 + lanes.filter((lane) => lane.replay.length < length).length
  const playback = usePlayback(longest)
  const interval = 1000 / playback.speed
  const duration = interval < 40 ? 0 : Math.min(320, interval * 0.8)

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target
      if (target instanceof HTMLInputElement && target.type !== 'range') return
      if (target instanceof HTMLSelectElement) return
      // A focused button already answers Space with its own click.
      if (target instanceof HTMLButtonElement && event.key === ' ') return
      if (event.key === ' ') {
        event.preventDefault()
        playback.togglePlay()
      } else if (event.key === 'ArrowRight') {
        event.preventDefault()
        playback.stepForward()
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault()
        playback.stepBack()
      } else if (event.key === 'Home' || event.key.toLowerCase() === 'r') playback.reset()
      else if (event.key === 'End') playback.seek(longest)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [playback, longest])

  return (
    <>
      <div className="transport">
        <button type="button" onClick={playback.reset} title="Reset (R)">
          Reset
        </button>
        <button type="button" onClick={playback.stepBack} title="Step back (←)">
          ◀
        </button>
        <button type="button" className="primary" onClick={playback.togglePlay} title="Play / pause (Space)">
          {playback.playing ? 'Pause' : playback.cursor >= longest ? 'Replay' : 'Play'}
        </button>
        <button type="button" onClick={playback.stepForward} title="Step forward (→)">
          ▶
        </button>
        <input
          className="transport__scrub"
          type="range"
          min={0}
          max={longest}
          value={playback.cursor}
          onChange={(event) => {
            playback.pause()
            playback.seek(Number(event.target.value))
          }}
          aria-label="Step"
        />
        <span className="transport__pos">
          {playback.cursor} / {longest}
        </span>
        <label className="transport__speed">
          Speed
          <select value={playback.speed} onChange={(event) => playback.setSpeed(Number(event.target.value))}>
            {SPEEDS.map((speed) => (
              <option key={speed} value={speed}>
                {speed} steps/s
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="race">
        {lanes.map(({ result, algorithm, replay }) =>
          algorithm ? (
            <Lane
              key={result.algorithm_id}
              algorithm={algorithm}
              replay={replay}
              metrics={result.metrics}
              cursor={playback.cursor}
              duration={duration}
              place={placeOf(replay.length)}
            />
          ) : null,
        )}
      </div>
    </>
  )
}
