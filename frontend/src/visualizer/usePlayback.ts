import { useCallback, useEffect, useState } from 'react'

export const SPEEDS = [1, 2, 5, 10, 25, 50, 100, 250] as const

/**
 * Shared playback cursor for every lane; `length` is the longest trace. Mount it under a key
 * that changes with each experiment so a new trace starts from the beginning.
 */
export function usePlayback(length: number) {
  const [cursor, setCursor] = useState(0)
  const [wantsPlay, setWantsPlay] = useState(false)
  const [speed, setSpeed] = useState<number>(5)
  const playing = wantsPlay && cursor < length

  useEffect(() => {
    if (!playing) return
    let frame = 0
    let last = performance.now()
    let carry = 0
    const tick = (now: number) => {
      carry += ((now - last) / 1000) * speed
      last = now
      const steps = Math.floor(carry)
      if (steps > 0) {
        carry -= steps
        setCursor((current) => Math.min(length, current + steps))
      }
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [playing, speed, length])

  const seek = useCallback(
    (next: number) => setCursor(Math.max(0, Math.min(length, next))),
    [length],
  )

  return {
    cursor,
    playing,
    speed,
    setSpeed,
    seek,
    togglePlay: () => {
      if (playing) return setWantsPlay(false)
      if (cursor >= length) setCursor(0)
      setWantsPlay(true)
    },
    pause: () => setWantsPlay(false),
    stepForward: () => {
      setWantsPlay(false)
      seek(cursor + 1)
    },
    stepBack: () => {
      setWantsPlay(false)
      seek(cursor - 1)
    },
    reset: () => {
      setWantsPlay(false)
      seek(0)
    },
  }
}
