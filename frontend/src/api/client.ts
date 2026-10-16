import createClient from 'openapi-fetch'
import type { components, paths } from './schema'

type Schemas = components['schemas']

export type AlgorithmMetadata = Schemas['AlgorithmMetadata']
export type DatasetResult = Schemas['DatasetResult']
export type SortExperiment = Schemas['SortExperiment']
export type SortResult = Schemas['SortResult']
export type SortEvent = Schemas['SortEvent']
export type OperationMetrics = Schemas['OperationMetrics']
export type BenchmarkResult = Schemas['BenchmarkResult']
export type BenchmarkSuiteResult = Schemas['BenchmarkSuiteResult']

/** Documented `error.code` values, plus client-side failures that never reached the API. */
export type ApiErrorCode =
  | 'unknown_algorithm'
  | 'request_too_large'
  | 'validation_error'
  | 'invalid_experiment'
  | 'limit_exceeded'
  | 'trace_limit_exceeded'
  | 'execution_busy'
  | 'execution_unavailable'
  | 'invalid_algorithm_result'
  | 'internal_error'
  | 'network_error'
  | 'unexpected_response'

export class ApiError extends Error {
  readonly status: number
  readonly code: ApiErrorCode

  constructor(status: number, code: ApiErrorCode, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }

  /** 503 `execution_busy` clears once a running experiment finishes; retrying is useful. */
  get retryable(): boolean {
    return this.code === 'execution_busy'
  }
}

// Empty base URL keeps requests same-origin, which the Vite dev proxy forwards to the API.
export const api = createClient<paths>({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' })

interface FetchResult<T> {
  data?: T
  error?: unknown
  response: Response
}

function isErrorEnvelope(body: unknown): body is Schemas['ErrorResponse'] {
  const error = (body as { error?: { code?: unknown; message?: unknown } } | null)?.error
  return typeof error?.code === 'string' && typeof error.message === 'string'
}

/** Returns the response data or throws an `ApiError`, including for network failures. */
export async function request<T>(call: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>
  try {
    result = await call
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : 'The API could not be reached.'
    throw new ApiError(0, 'network_error', message)
  }
  const { data, error, response } = result
  if (response.ok && data !== undefined) return data
  if (isErrorEnvelope(error)) {
    throw new ApiError(response.status, error.error.code as ApiErrorCode, error.error.message)
  }
  throw new ApiError(
    response.status,
    'unexpected_response',
    `Unexpected API response (HTTP ${response.status}).`,
  )
}
