# Phase 3 — Dataset and benchmark engine

Branch: `feat/benchmark-engine`.

Added framework-independent application dataclasses, validation, a clock port, reproducible
integer data generation, sorting, repeated sequential benchmarking, and bounded benchmark
suites. FastAPI, Pydantic, concrete algorithms, and infrastructure are absent from this layer.
The registry and clock are injected into `ExperimentService`.

## Delivered behavior

- Random, sorted, reversed, nearly sorted, and few-unique distributions return concrete seeds.
- Independent input copies and full sorted-result validation protect every execution pass.
- Counting, tracing, warmups, and timed runs use explicit modes; only algorithm execution is timed.
- Benchmarks return all nanosecond samples, median/min/max/spread, per-run fastest IDs, and a
  conservative observed-range overlap warning.
- Traces are optional, complete, bounded, and separate from metric collection.
- Suites prevalidate every generated case and their aggregate cost before invoking algorithms.
- Domain errors enforce strict integer inputs, unique algorithm IDs, algorithm metadata limits,
  trace limits, repetition limits, suite limits, and aggregate admission units.
- No persistence or job lifecycle is introduced.

## Public application interfaces

- `generate_dataset(spec: DatasetSpec) -> DatasetResult`
- `ExperimentService(registry: AlgorithmRegistry, clock: Clock)`
- `service.sort(values, algorithm_ids, *, trace=False) -> SortExperiment`
- `service.benchmark(values, algorithm_ids, *, repeats=5, warmups=1, seed=None) -> BenchmarkResult`
- `service.suite(spec: SuiteSpec) -> BenchmarkSuiteResult`

All results are dataclasses convertible through `dataclasses.asdict`. Metrics include an explicit
`writes` field for serialization. The `Clock` protocol exposes `now_ns() -> int`.

## Validation

Application tests use fake algorithms and clocks to check deterministic generation, strict
validation, input isolation, event replay, independent counting/tracing/timing modes, timing
statistics, tied and overlapping results, validation of measured outputs, and whole-suite
admission before execution. The suite also covers empty input, negatives, duplicates, seeds,
metadata range/size limits, trace overflow, and the distinct admission workload classes.
Ruff lint/format and strict mypy checks cover the implementation.

See [BENCHMARKING.md](../BENCHMARKING.md) for measurement semantics, interpretation, and limits.
