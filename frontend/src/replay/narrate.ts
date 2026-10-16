import type { SortEvent } from '../api/client'

/**
 * For a comparison against a value held outside the array (an insertion key or a pivot),
 * returns that held value; otherwise null. `before` is the array before the event.
 */
export function heldOperand(event: SortEvent | null, before: readonly number[]): number | null {
  if (event?.kind !== 'compare' || event.indices.length !== 1) return null
  const [left, right] = event.values
  return before[event.indices[0]] === left ? right : left
}

/**
 * Explains one event in plain English using only what the event states. `before` is the
 * displayed array before the event was applied.
 */
export function narrate(event: SortEvent | null, before: readonly number[]): string {
  if (event === null) return 'Ready. Press play or step forward to start.'
  const { kind, indices, values } = event
  if (kind === 'compare') {
    const [left, right] = values
    const relation =
      left > right ? `${left} is larger` : left < right ? `${left} is smaller` : 'they are equal'
    if (indices.length === 2) {
      return `Compare ${left} at index ${indices[0]} with ${right} at index ${indices[1]}: ${relation}.`
    }
    if (indices.length === 1) {
      // The other operand is held outside the array (an insertion key or a pivot).
      const [index] = indices
      const held = heldOperand(event, before)
      const atIndex = before[index]
      return `Compare ${atIndex} at index ${index} with the held value ${held}: ${relation}.`
    }
    return `Compare ${left} with ${right}: ${relation}.`
  }
  if (kind === 'swap') {
    const [first, second] = indices
    return `Swap indices ${first} and ${second}: ${before[first]} and ${before[second]} trade places.`
  }
  const [index] = indices
  return `Write ${values[0]} into index ${index}, replacing ${before[index]}.`
}
