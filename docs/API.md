# API guide

For an end-to-end Arabic explanation of the frontend request flow and each algorithm, see
[Frontend-to-algorithm flow (Arabic)](FRONTEND-FLOW-AR.md).

Start AlgoLab using [RUNNING.md](RUNNING.md). The examples below use
`http://127.0.0.1:8000`. All POST bodies are JSON objects with
`Content-Type: application/json`; unknown fields are rejected.

The running service provides [Swagger UI](http://127.0.0.1:8000/docs),
[ReDoc](http://127.0.0.1:8000/redoc), and
[OpenAPI JSON](http://127.0.0.1:8000/openapi.json). These describe the actual request and
response schemas. The API returns completed responses rather than job IDs or streamed events.

## Endpoints

All successful endpoints below return HTTP 200.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | API process liveness and version |
| GET | `/api/v1/algorithms` | List all eleven algorithm metadata objects |
| GET | `/api/v1/algorithms/{algorithm_id}` | Get one algorithm's metadata |
| POST | `/api/v1/datasets` | Generate a reproducible integer dataset |
| POST | `/api/v1/sort` | Sort identical input copies, count operations, optionally capture traces |
| POST | `/api/v1/benchmarks` | Measure repeated runs on one shared input |
| POST | `/api/v1/benchmark-suites` | Benchmark a matrix of sizes and distributions |

## Discover algorithms

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/api/v1/algorithms
curl -sS http://127.0.0.1:8000/api/v1/algorithms/quick_sort
```

Algorithm IDs are:

```text
selection_sort        bubble_sort          odd_even_sort
cocktail_sort         insertion_sort       binary_insertion_sort
frequency_sort        shell_sort           heap_sort
quick_sort             merge_sort
```

Metadata fields are `id`, `name`, `description`, `complexity`, `stable`, `in_place`,
`comparison_based`, `max_size`, `max_value_range`, and `workload`. `complexity` contains
`best`, `average`, `worst`, `auxiliary_space`, and `notes`. A null `max_value_range` means
there is no algorithm-specific span cap beyond the common input limits. `workload` selects
resource admission cost; it is separate from the displayed complexity.

Frequency Sort means Counting Sort that reconstructs ascending numeric order. It does not
rank values by frequency. See [ALGORITHMS.md](ALGORITHMS.md) for variant-specific semantics.

`/health` returns `status`, `service`, and `version`. It checks process liveness, not whether
the CPU execution queue is available.

## Generate a dataset

```bash
curl -sS http://127.0.0.1:8000/api/v1/datasets \
  -H 'Content-Type: application/json' \
  -d '{"size":12,"minimum":-10,"maximum":10,"distribution":"few_unique","seed":42}'
```

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `size` | No | `50` | Number of elements, from 0 to 10,000 |
| `minimum` | No | `1` | Inclusive lower value bound |
| `maximum` | No | `100` | Inclusive upper value bound; must be at least `minimum` |
| `distribution` | No | `"random"` | `random`, `sorted`, `reversed`, `nearly_sorted`, or `few_unique` |
| `seed` | No | `null` | Integer from 0 to 4,294,967,295; omitted/null generates a seed |

The response contains `values`, the concrete `seed`, `size`, `minimum`, `maximum`, and
`distribution`. Send the returned `values` to sort or benchmark endpoints; there is no stored
dataset ID. Reusing the seed and all generation settings reproduces the dataset within this
implementation version. Keep the actual values if reproducibility must survive version changes.
The distribution definitions are documented in [BENCHMARKING.md](BENCHMARKING.md#reproducible-data).

## Sort and capture a trace

```bash
curl -sS http://127.0.0.1:8000/api/v1/sort \
  -H 'Content-Type: application/json' \
  -d '{"values":[5,-2,3,3,0],"algorithm_ids":["insertion_sort","quick_sort"],"trace":true}'
```

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `values` | Yes | — | Integer array; empty input is valid |
| `algorithm_ids` | Yes | — | One to ten distinct registered IDs |
| `trace` | No | `false` | Whether to return complete replay events |

The response has `input_values` and `results`. Results preserve the requested algorithm
order. Each entry contains:

- `algorithm_id`: the selected ID.
- `output_values`: the validated sorted array, including duplicate values.
- `metrics`: `comparisons`, `swaps`, `array_writes`, `auxiliary_writes`, and `writes`.
- `events`: `null` when tracing was not requested; an ordered array when it was requested.
  A successful trace with no operations is `[]`.

This endpoint does not return execution timings. Counting and trace capture use separate
passes; their overhead should not be presented as benchmark time. For precise metric
definitions, see [the shared contracts](ARCHITECTURE.md#metrics-and-trace-semantics).

### Replay events

For each result, initialize an independent displayed array from `input_values`, then consume
that result's events in `sequence` order. Sequences and indices start at zero.

| `kind` | `indices` | `values` | Replay action |
| --- | --- | --- | --- |
| `compare` | Available array operand indices | The two operand values | Highlight operands; do not mutate the displayed array |
| `swap` | Two distinct indices | Values at those indices after the swap | Exchange those displayed elements, or assign the supplied post-swap values |
| `write` | One destination index | One newly assigned value | Assign the value at that index |

A held insertion key, pivot, or remembered bound may not have a current array index. Do not
assume each comparison has two indices, or look up both operands solely from `indices`.
Use `values` to display the actual comparison operands. Auxiliary writes contribute to the
metrics but have no main-array mutation event.

An exact small example is:

```bash
curl -sS http://127.0.0.1:8000/api/v1/sort \
  -H 'Content-Type: application/json' \
  -d '{"values":[2,1],"algorithm_ids":["insertion_sort"],"trace":true}'
```

Its sole result has output `[1,2]`, one comparison, zero swaps, two array writes, and these
events:

```json
[
  {"sequence":0,"kind":"compare","indices":[0],"values":[2,1]},
  {"sequence":1,"kind":"write","indices":[1],"values":[2]},
  {"sequence":2,"kind":"write","indices":[0],"values":[1]}
]
```

Successful traces are complete. Trace overflow returns an error instead of a truncated event
list. Start, pause, resume, speed, and reset are client-side playback operations on the returned
data; there are no server playback-control endpoints.

## Benchmark one input

```bash
curl -sS http://127.0.0.1:8000/api/v1/benchmarks \
  -H 'Content-Type: application/json' \
  -d '{"values":[8,-3,5,0,8,2,-1],"algorithm_ids":["insertion_sort","heap_sort","quick_sort"],"repeats":5,"warmups":1,"seed":42}'
```

`values` and `algorithm_ids` are required and follow the sort request rules. Additional fields:

| Field | Default | Allowed values |
| --- | --- | --- |
| `repeats` | `5` | Integers from 1 to 15 |
| `warmups` | `1` | Integers from 0 to 3 |
| `seed` | `null` | Null or integer from 0 to 4,294,967,295 |

Here the seed controls per-round algorithm order; it does not generate or alter the supplied
array. Reusing it does not make elapsed timings deterministic.

The response includes `input_values`, the concrete `seed`, `repeats`, `warmups`, `results`,
`fastest_algorithm_ids`, and `noise_warning`. Each result includes `algorithm_id`,
`output_values`, `metrics`, `samples_ns`, `median_ns`, `min_ns`, `max_ns`, and `spread_ns`.
There are exactly `repeats` samples per algorithm; warmups do not appear in `samples_ns`.

Timings are in nanoseconds, with the median used to select the fastest algorithm or exact
ties in this experiment. `noise_warning` reports overlap between an observed fastest sample
range and another algorithm's range; it is not a statistical significance test. The
[benchmark guide](BENCHMARKING.md#execution-and-measurement) explains the measured interval,
independent counting, ordering, and interpretation limits.

## Benchmark a suite

```bash
curl -sS http://127.0.0.1:8000/api/v1/benchmark-suites \
  -H 'Content-Type: application/json' \
  -d '{"algorithm_ids":["insertion_sort","heap_sort","quick_sort"],"sizes":[10,50],"distributions":["random","reversed","few_unique"],"minimum":-100,"maximum":100,"seed":42,"repeats":3,"warmups":1}'
```

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `algorithm_ids` | Yes | — | One to ten distinct registered IDs |
| `sizes` | Yes | — | Nonempty list of distinct sizes from 0 to 10,000 |
| `distributions` | Yes | — | Nonempty list of distinct supported distribution names |
| `minimum`, `maximum` | No | `1`, `100` | Inclusive generation bounds |
| `seed` | No | `null` | Seed used to derive a separate seed for each case |
| `repeats`, `warmups` | No | `5`, `1` | Repetition settings shared by all cases |

The Cartesian product of `sizes` and `distributions` must contain at most twelve cases.
The response contains the concrete suite `seed` and `cases`. Each case has a `dataset`
response and a `benchmark` response with the same fields described above. Case order follows
the requested size order, then the requested distribution order. The example has six cases.

All algorithms within a case receive the same input. Per-algorithm limits and the total work
budget are checked for every case before any algorithm in the suite executes. An invalid
suite returns an error, not partial case results. Nothing is stored after the response.

## Input and admission limits

| Limit | Value |
| --- | --- |
| Request body | At most 1,000,000 bytes, including JSON formatting |
| Integer values and generation bounds | −1,000,000,000 through 1,000,000,000, inclusive |
| General array size | 0–10,000 elements |
| Selection, Bubble, Odd-Even, Cocktail, Insertion, Binary Insertion, Shell | At most 1,000 elements each |
| Heap, Quick, Merge, Frequency | At most 10,000 elements each, also subject to the aggregate budget |
| Frequency's actual inclusive value span | At most 100,000 |
| Selected algorithms | 1–10 unique registered IDs |
| Algorithm ID text | 1–64 characters |
| Seed | Integer from 0 to 4,294,967,295, or null |
| Measured repeats / warmups | 1–15 / 0–3 |
| Trace size / events | At most 128 input elements / 20,000 events per algorithm |
| Suite cases | At most 12 distinct size/distribution combinations |
| Aggregate admission work | At most 50,000,000 units per experiment request |
| Unfinished experiment requests | Four total, including the running request |

Integer fields reject booleans, fractional values, and numeric strings. `trace` must be a JSON
boolean. Negative and repeated integer values are supported.

Per-algorithm size caps are independent of the aggregate budget. Quick uses quadratic
admission cost to account for adversarial inputs even though its average theoretical time
is O(n log n). A large Quick request can therefore be rejected below its 10,000-element
metadata cap. Selecting more algorithms, increasing repeats, or adding suite cases also
consumes more budget. See [the admission formulas](BENCHMARKING.md#suites-and-admission-limits).

## Errors and retrying

Documented endpoint errors use this envelope:

```json
{"error":{"code":"unknown_algorithm","message":"Unknown algorithm: missing_sort"}}
```

Use the HTTP status and `error.code` for client decisions; message wording can change.

| HTTP status | `error.code` | Meaning |
| --- | --- | --- |
| 404 | `unknown_algorithm` | Requested algorithm ID is not registered |
| 413 | `request_too_large` | Request body exceeds 1,000,000 bytes |
| 422 | `validation_error` | Invalid JSON structure, field type, value, extra field, or schema constraint |
| 422 | `invalid_experiment` | Application-level input or experiment rule rejected |
| 422 | `limit_exceeded` | Per-algorithm, range, or aggregate work limit exceeded |
| 422 | `trace_limit_exceeded` | Complete trace would exceed the event cap |
| 503 | `execution_busy` | Four experiment requests are already unfinished |
| 503 | `execution_unavailable` | CPU executor is closed or has failed |
| 500 | `invalid_algorithm_result` | An algorithm failed sorted-output validation |
| 500 | `internal_error` | Unexpected server failure |

Examples that intentionally produce errors:

```bash
curl -sS -i http://127.0.0.1:8000/api/v1/algorithms/missing_sort

curl -sS -i http://127.0.0.1:8000/api/v1/sort \
  -H 'Content-Type: application/json' \
  -d '{"values":[true,2],"algorithm_ids":["heap_sort"]}'

curl -sS -i http://127.0.0.1:8000/api/v1/sort \
  -H 'Content-Type: application/json' \
  -d '{"values":[-50000,50000],"algorithm_ids":["frequency_sort"]}'
```

These return 404, 422, and 422 respectively. Both 503 responses include `Retry-After: 1`.
Use delayed retries for `execution_busy`; persistent `execution_unavailable` requires
operator attention. Retrying a malformed or oversized request without changing it will
not help. Cancelling an HTTP await does not terminate an already running CPU experiment;
see [execution and cancellation](RUNNING.md#execution-and-cancellation).
