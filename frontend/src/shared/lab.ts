import { ApiError } from '../api/client'

/** The page starts with these selected in every section. */
export const DEFAULT_ALGORITHMS = ['bubble_sort', 'insertion_sort', 'quick_sort']

export type Distribution = 'random' | 'sorted' | 'reversed' | 'nearly_sorted' | 'few_unique'

export interface DatasetSettings {
  size: number
  minimum: number
  maximum: number
  distribution: Distribution
  /** Digits only; empty asks the server for a fresh seed. */
  seed: string
}

export const DISTRIBUTIONS: { value: Distribution; label: string }[] = [
  { value: 'random', label: 'Random' },
  { value: 'sorted', label: 'Sorted' },
  { value: 'reversed', label: 'Reversed' },
  { value: 'nearly_sorted', label: 'Nearly sorted' },
  { value: 'few_unique', label: 'Few unique' },
]

export const distributionLabel = (value: string) =>
  DISTRIBUTIONS.find((item) => item.value === value)?.label ?? value

/** A user-facing sentence for a failed request. */
export function errorMessage(cause: unknown): string {
  if (cause instanceof ApiError) {
    if (cause.retryable) return 'The server is busy with other experiments. Try again in a moment.'
    if (cause.code === 'network_error') return 'The API could not be reached. Is the backend running?'
    return cause.message
  }
  return String(cause)
}

const numberFormat = new Intl.NumberFormat('en-US')

export const formatCount = (value: number) => numberFormat.format(value)

/** Nanoseconds as the largest readable unit, e.g. 1.24 ms. */
export function formatDuration(ns: number): string {
  if (ns >= 1e9) return `${(ns / 1e9).toFixed(2)} s`
  if (ns >= 1e6) return `${(ns / 1e6).toFixed(2)} ms`
  if (ns >= 1e3) return `${(ns / 1e3).toFixed(1)} µs`
  return `${Math.round(ns)} ns`
}

/** Integer text field helper: keeps digits and one leading minus sign. */
export const integerText = (text: string, allowNegative = true) =>
  allowNegative ? text.replace(/(?!^-)\D/g, '') : text.replace(/\D/g, '')

export const datasetBody = (settings: DatasetSettings) => ({
  size: settings.size,
  minimum: settings.minimum,
  maximum: settings.maximum,
  distribution: settings.distribution,
  seed: settings.seed === '' ? null : Number(settings.seed),
})
