# Benchmarking and interpretation

AlgoLab measures the registered Python implementations on the server. Results apply to the
selected input, implementation, server, and run. They do not establish a universally fastest
algorithm, measure browser animation, or experimentally prove a complexity class.

## Reproducible data

`generate_dataset(DatasetSpec(...))` returns integers, an explicit seed, and the generation
settings. Seeded generation uses a local random generator; requests do not alter global random
state. A missing seed is generated and returned. Reuse the seed **and all generation settings**
to reconstruct a dataset with this version of AlgoLab. Seeds are integers from 0 to 4,294,967,295.
Store the actual returned values when reproducibility must survive changes to implementation
or Python versions.

The inclusive minimum and maximum may be negative or equal. Duplicate values and empty arrays
are supported. Distributions are:

| Distribution | Construction |
| --- | --- |
| `random` | Independent uniform integer samples in the requested inclusive range |
| `sorted` | The same seeded random sample, sorted ascending |
| `reversed` | The same seeded random sample, sorted descending |
| `nearly_sorted` | The sorted sample with `max(1, size // 20)` random transpositions for size > 1 |
| `few_unique` | Uniform draws from up to five distinct values sampled from the requested range |

Nearly sorted data may remain sorted when duplicates are exchanged. Few-unique generation
uses at most five distinct values; small samples need not contain every selected value.

## Execution and measurement

Every selected algorithm receives a fresh independent copy of the original input on every
pass. The original request is never sorted in place. The reference answer is computed once
with Python's `sorted` before execution. The full output of each pass must match it, preserving
both values and multiplicity. A failing algorithm aborts the experiment with a domain error;
an invalid output cannot win a benchmark.

A benchmark has three kinds of pass:

1. One instrumentation pass per algorithm, with operation counting enabled and tracing off.
2. Zero to three warmup passes, with both counting and tracing disabled.
3. One to fifteen measured passes, with both counting and tracing disabled.

The same algorithm implementation is used for all passes. Per-round algorithm order is
shuffled deterministically using the benchmark seed. Algorithms run sequentially, avoiding
competition between algorithms within one experiment. Instrumentation runs follow the
requested algorithm order. Response rows also preserve that order.

Only the call to the algorithm is inside the timed interval. Input copying, context creation,
reference sorting, output validation, data generation, metric collection, trace collection,
serialization, and any future playback are outside it. Warmup results and measured results
are validated after each run. The shared operation method calls and disabled-instrumentation
branches still contribute overhead; AlgoLab does not claim to measure bare textbook operations.
Algorithm-owned allocations remain inside the measured interval.

The application uses an injected monotonic `Clock.now_ns()` port. A production adapter should
use a high-resolution elapsed-time clock such as `time.perf_counter_ns`. Nanosecond **units** do
not imply nanosecond **resolution**. The outer API may report the clock's actual implementation
and resolution. Negative elapsed durations are rejected.

## Reading results

Each algorithm reports all measured samples in nanoseconds, their median, minimum, maximum,
and spread (`max - min`). Median is used for the per-run ranking. Every algorithm tied for
the smallest median appears in `fastest_algorithm_ids`.

`noise_warning` is true when a fastest algorithm's observed sample range overlaps another
algorithm's observed range, including equal endpoints and exact ties. This is a simple warning,
not a confidence interval or significance test. A false flag is not proof of a meaningful
performance difference. Single-sample measurements cannot estimate variation; short runs can
be dominated by clock or function-call overhead. Server load, interpreter state, hardware,
and operating-system scheduling can also change the outcome.

Theoretical best, average, and worst time complexity and auxiliary space describe growth under
stated assumptions. They do not directly predict these finite-input wall-clock durations.

## Metrics and visualization

Instrumentation reports input-value comparisons, index swaps, main-array writes, auxiliary
container writes, and total writes. A swap of different indices is two main-array writes;
local scalar assignments and loop/index checks are excluded. See [ARCHITECTURE.md](ARCHITECTURE.md)
for event and metric contracts.

Sort requests optionally run an additional pass with tracing enabled and counting disabled.
Without a trace request, `events` is null. With a trace request, successful results include the
complete ordered trace, including an empty list when no operation occurred. Exceeding the
trace limit fails explicitly rather than returning a truncated animation. Trace output has
no measured runtime; use a separate benchmark for performance measurements.

## Suites and admission limits

A suite runs the Cartesian product of requested sizes and distributions, preserving size order
first and distribution order second. A returned suite seed determines a separate seed for each
case; each case returns its dataset and benchmark. All algorithms in a case use identical data.
All settings, metadata size/range constraints, and aggregate work limits are checked before any
algorithm in the suite runs. A later invalid case cannot leave a partially executed suite.
Results are returned directly; AlgoLab stores no experiment history.

| Limit | Value |
| --- | --- |
| Dataset size | 0–10,000 integers, also constrained by each algorithm's metadata |
| Integer values | −1,000,000,000 through 1,000,000,000 |
| Algorithms per experiment | 1–10 distinct registered IDs |
| Measured repetitions | 1–15 |
| Warmups | 0–3 |
| Trace size | At most 128 input elements |
| Trace operations | At most 20,000 events per algorithm |
| Suite size | At most 12 distinct size/distribution combinations |
| Aggregate admission work | At most 50,000,000 units per request |

Boolean and floating-point values are rejected where integers are required. Algorithm-specific
maximum input size and maximum value range are metadata; frequency counting's actual span is
`max(values) - min(values) + 1`, or zero for empty input. A large magnitude alone is not a large
span: `[-1_000_000, -999_999]` has span two.

Admission work is a conservative resource heuristic selected by algorithm metadata, separate
from theoretical complexity or measured duration:

| Workload class | Units per algorithm pass |
| --- | --- |
| `quadratic` | `max(1, n * n)` |
| `n_log_n` | `max(1, n * max(1, n.bit_length()))` |
| `linear_range` | `max(1, n + actual_value_span)` |

A sort consumes one instrumentation pass plus one optional trace pass. A benchmark consumes
`1 + warmups + repeats` passes. Suite costs sum every case. The heap and quick implementations
may use the `n_log_n` admission class while Quick Sort still documents quadratic theoretical
worst-case time. Hard per-algorithm size limits and outer execution limits remain necessary;
the work heuristic is not a hard CPU-time guarantee.
