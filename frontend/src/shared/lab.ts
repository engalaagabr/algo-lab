import { ApiError } from '../api/client'
import type { Messages } from '../i18n/en'

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

/** Each pattern with the message key of its label. */
export const DISTRIBUTIONS = [
  { value: 'random', label: 'random' },
  { value: 'sorted', label: 'sorted' },
  { value: 'reversed', label: 'reversed' },
  { value: 'nearly_sorted', label: 'nearlySorted' },
  { value: 'few_unique', label: 'fewUnique' },
] as const satisfies readonly { value: Distribution; label: keyof Messages }[]

export const distributionLabel = (text: Messages, value: string) => {
  const found = DISTRIBUTIONS.find((item) => item.value === value)
  return found ? text[found.label] : value
}

/** A user-facing sentence for a failed request; server messages arrive in English. */
export function errorMessage(cause: unknown, text: Messages): string {
  if (cause instanceof ApiError) {
    if (cause.retryable) return text.apiBusy
    if (cause.code === 'network_error') return text.apiUnreachable
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
