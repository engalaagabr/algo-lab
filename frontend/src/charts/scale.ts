/** Round tick values from 0 up to at least `max`, stepping by 1, 2 or 5 × 10^k. */
export function niceTicks(max: number, target = 5): number[] {
  if (!(max > 0)) return [0, 1]
  const rough = max / target
  const magnitude = 10 ** Math.floor(Math.log10(rough))
  const step = [1, 2, 5, 10].map((factor) => factor * magnitude).find((value) => value >= rough) ?? rough
  const ticks: number[] = []
  for (let value = 0; value < max + step * 0.5; value += step) ticks.push(Number(value.toPrecision(12)))
  if (ticks[ticks.length - 1] < max) ticks.push(ticks[ticks.length - 1] + step)
  return ticks
}

/** Compact axis label, e.g. 12,000 → 12k. */
export function compactNumber(value: number): string {
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
}
