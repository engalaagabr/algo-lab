from collections.abc import Sequence
from random import Random
from statistics import median

from application.datasets import concrete_seed, generate_dataset
from application.models import (
    AlgorithmBenchmark,
    BenchmarkCase,
    BenchmarkResult,
    BenchmarkSuiteResult,
    DatasetSpec,
    OperationMetrics,
    SortExperiment,
    SortResult,
    SuiteSpec,
)
from application.ports import Clock
from application.validation import (
    MAX_ALGORITHMS,
    MAX_DATASET_SIZE,
    MAX_SEED,
    MAX_SUITE_CASES,
    MAX_TRACE_EVENTS,
    MAX_TRACE_SIZE,
    check_work_budget,
    require_integer,
    validate_distribution,
    validate_range,
    validate_repetitions,
    validate_values,
)
from domain.errors import DomainError, InvalidResult, LimitExceeded
from domain.models import Algorithm, Metrics
from domain.operations import SortContext
from domain.registry import AlgorithmRegistry


def _metrics(metrics: Metrics) -> OperationMetrics:
    return OperationMetrics(
        comparisons=metrics.comparisons,
        swaps=metrics.swaps,
        array_writes=metrics.array_writes,
        auxiliary_writes=metrics.auxiliary_writes,
        writes=metrics.writes,
    )


def _validate_output(context: SortContext, expected: list[int], identifier: str) -> None:
    # Equality alone would accept True in place of 1, so preserve the integer contract too.
    if context.values != expected or any(type(value) is not int for value in context.values):
        raise InvalidResult(f"Algorithm {identifier} did not produce the correct sorted output.")


def _value_span(values: list[int]) -> int:
    return max(values) - min(values) + 1 if values else 0


def _validate_algorithm_input(algorithm: Algorithm, values: list[int]) -> None:
    metadata = algorithm.metadata
    if len(values) > metadata.max_size:
        raise LimitExceeded(
            f"Algorithm {metadata.id} supports at most {metadata.max_size} elements."
        )
    if metadata.max_value_range is not None and _value_span(values) > metadata.max_value_range:
        raise LimitExceeded(
            f"Algorithm {metadata.id} supports a value range of at most {metadata.max_value_range}."
        )


def _work_units(algorithms: Sequence[Algorithm], values: list[int], runs: int) -> int:
    size = len(values)
    span = _value_span(values)
    costs = {
        "quadratic": max(1, size * size),
        "n_log_n": max(1, size * max(1, size.bit_length())),
        "linear_range": max(1, size + span),
    }
    return runs * sum(costs[algorithm.metadata.workload] for algorithm in algorithms)


class ExperimentService:
    """Stateless use cases; HTTP and concrete algorithm registration are outer concerns."""

    def __init__(self, registry: AlgorithmRegistry, clock: Clock) -> None:
        self._registry = registry
        self._clock = clock

    def _algorithms(self, identifiers: list[str]) -> list[Algorithm]:
        if not isinstance(identifiers, list):
            raise DomainError("algorithm_ids must be a list of strings.")
        require_integer(len(identifiers), "algorithm count", 1, MAX_ALGORITHMS)
        if any(not isinstance(identifier, str) or not identifier for identifier in identifiers):
            raise DomainError("algorithm_ids must contain nonempty strings.")
        if len(set(identifiers)) != len(identifiers):
            raise DomainError("algorithm_ids must not contain duplicates.")
        return [self._registry.get(identifier) for identifier in identifiers]

    def _prepare(self, values: list[int], identifiers: list[str]) -> list[Algorithm]:
        validate_values(values)
        algorithms = self._algorithms(identifiers)
        for algorithm in algorithms:
            _validate_algorithm_input(algorithm, values)
        return algorithms

    def sort(
        self, values: list[int], algorithm_ids: list[str], *, trace: bool = False
    ) -> SortExperiment:
        if type(trace) is not bool:
            raise DomainError("trace must be a boolean.")
        algorithms = self._prepare(values, algorithm_ids)
        if trace and len(values) > MAX_TRACE_SIZE:
            raise LimitExceeded(f"Traces support at most {MAX_TRACE_SIZE} elements.")
        check_work_budget(_work_units(algorithms, values, 2 if trace else 1))
        original = values.copy()
        expected = sorted(original)
        results: list[SortResult] = []
        for algorithm in algorithms:
            counted = SortContext(original.copy(), count=True, trace=False)
            algorithm.sort(counted)
            _validate_output(counted, expected, algorithm.metadata.id)
            events = None
            if trace:
                traced = SortContext(
                    original.copy(), count=False, trace=True, max_events=MAX_TRACE_EVENTS
                )
                algorithm.sort(traced)
                _validate_output(traced, expected, algorithm.metadata.id)
                events = traced.events.copy()
            results.append(
                SortResult(
                    algorithm.metadata.id, counted.values.copy(), _metrics(counted.metrics), events
                )
            )
        return SortExperiment(original, results)

    def benchmark(
        self,
        values: list[int],
        algorithm_ids: list[str],
        *,
        repeats: int = 5,
        warmups: int = 1,
        seed: int | None = None,
    ) -> BenchmarkResult:
        validate_repetitions(repeats, warmups)
        seed = concrete_seed(seed)
        algorithms = self._prepare(values, algorithm_ids)
        check_work_budget(_work_units(algorithms, values, repeats + warmups + 1))
        original = values.copy()
        expected = sorted(original)
        metrics: dict[str, OperationMetrics] = {}
        for algorithm in algorithms:
            counted = SortContext(original.copy(), count=True, trace=False)
            algorithm.sort(counted)
            _validate_output(counted, expected, algorithm.metadata.id)
            metrics[algorithm.metadata.id] = _metrics(counted.metrics)

        samples: dict[str, list[int]] = {algorithm.metadata.id: [] for algorithm in algorithms}
        rng = Random(seed)
        for round_number in range(warmups + repeats):
            # Shuffle every round to avoid always giving the same algorithm the first position.
            ordered = list(algorithms)
            rng.shuffle(ordered)
            for algorithm in ordered:
                # Context creation and the input copy happen before either clock call.
                context = SortContext(original.copy(), count=False, trace=False)
                if round_number < warmups:
                    algorithm.sort(context)
                else:
                    started = self._clock.now_ns()
                    algorithm.sort(context)
                    elapsed = self._clock.now_ns() - started
                    if elapsed < 0:
                        raise DomainError("The measurement clock must be monotonic.")
                    samples[algorithm.metadata.id].append(elapsed)
                # Validate every warmup and timed run outside the measured interval.
                _validate_output(context, expected, algorithm.metadata.id)

        results: list[AlgorithmBenchmark] = []
        for algorithm in algorithms:
            identifier = algorithm.metadata.id
            timings = samples[identifier]
            minimum, maximum = min(timings), max(timings)
            results.append(
                AlgorithmBenchmark(
                    algorithm_id=identifier,
                    output_values=expected.copy(),
                    metrics=metrics[identifier],
                    samples_ns=timings,
                    median_ns=float(median(timings)),
                    min_ns=minimum,
                    max_ns=maximum,
                    spread_ns=maximum - minimum,
                )
            )
        best_median = min(result.median_ns for result in results)
        fastest = [result.algorithm_id for result in results if result.median_ns == best_median]
        best_results = [result for result in results if result.algorithm_id in fastest]
        # This is a conservative warning, not a statistical significance test.
        overlap = any(
            winner.algorithm_id != contender.algorithm_id
            and max(winner.min_ns, contender.min_ns) <= min(winner.max_ns, contender.max_ns)
            for winner in best_results
            for contender in results
        )
        return BenchmarkResult(original, seed, repeats, warmups, results, fastest, overlap)

    def suite(self, spec: SuiteSpec) -> BenchmarkSuiteResult:
        validate_repetitions(spec.repeats, spec.warmups)
        validate_range(spec.minimum, spec.maximum)
        algorithms = self._algorithms(spec.algorithm_ids)
        if not isinstance(spec.sizes, list) or not spec.sizes:
            raise DomainError("sizes must be a nonempty list of integers.")
        if not isinstance(spec.distributions, list) or not spec.distributions:
            raise DomainError("distributions must be a nonempty list of distribution names.")
        require_integer(
            len(spec.sizes) * len(spec.distributions), "suite cases", 1, MAX_SUITE_CASES
        )
        for size in spec.sizes:
            require_integer(size, "size", 0, MAX_DATASET_SIZE)
        for distribution in spec.distributions:
            validate_distribution(distribution)
        if len(set(spec.sizes)) != len(spec.sizes):
            raise DomainError("sizes must not contain duplicates.")
        if len(set(spec.distributions)) != len(spec.distributions):
            raise DomainError("distributions must not contain duplicates.")
        seed = concrete_seed(spec.seed)
        rng = Random(seed)
        datasets = [
            generate_dataset(
                DatasetSpec(
                    size=size,
                    minimum=spec.minimum,
                    maximum=spec.maximum,
                    distribution=distribution,
                    seed=rng.randrange(MAX_SEED + 1),
                )
            )
            for size in spec.sizes
            for distribution in spec.distributions
        ]
        # Reject the entire suite before invoking any algorithm, including later-case failures.
        for dataset in datasets:
            for algorithm in algorithms:
                _validate_algorithm_input(algorithm, dataset.values)
        check_work_budget(
            sum(
                _work_units(algorithms, dataset.values, spec.repeats + spec.warmups + 1)
                for dataset in datasets
            )
        )
        cases = [
            BenchmarkCase(
                dataset=dataset,
                benchmark=self.benchmark(
                    dataset.values,
                    spec.algorithm_ids,
                    repeats=spec.repeats,
                    warmups=spec.warmups,
                    seed=dataset.seed,
                ),
            )
            for dataset in datasets
        ]
        return BenchmarkSuiteResult(seed, cases)
