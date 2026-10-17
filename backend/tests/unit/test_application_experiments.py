from collections.abc import Callable
from dataclasses import asdict, replace
from random import Random

import pytest

from application.models import SuiteSpec
from application.services import ExperimentService
from domain.errors import (
    DomainError,
    InvalidResult,
    LimitExceeded,
    TraceLimitExceeded,
    UnknownAlgorithm,
)
from domain.models import Algorithm, AlgorithmMetadata, Complexity
from domain.operations import SortContext
from domain.registry import AlgorithmRegistry


class FakeClock:
    def __init__(self, ticks: list[int] | None = None) -> None:
        self.calls = 0
        self.ticks = iter(ticks) if ticks is not None else None

    def now_ns(self) -> int:
        self.calls += 1
        return next(self.ticks) if self.ticks is not None else self.calls * 100


def algorithm(
    identifier: str = "test",
    sort: Callable[[SortContext], None] | None = None,
    **metadata: object,
) -> Algorithm:
    def bubble(context: SortContext) -> None:
        for end in range(len(context.values) - 1, 0, -1):
            for index in range(end):
                if (
                    context.compare(
                        context.values[index], context.values[index + 1], (index, index + 1)
                    )
                    > 0
                ):
                    context.swap(index, index + 1)

    meta = AlgorithmMetadata(
        identifier,
        identifier,
        "Test algorithm",
        Complexity("O(n)", "O(n^2)", "O(n^2)", "O(1)"),
        stable=True,
        in_place=True,
    )
    return Algorithm(replace(meta, **metadata), sort or bubble)  # type: ignore[arg-type]


def service(*algorithms: Algorithm, clock: FakeClock | None = None) -> ExperimentService:
    return ExperimentService(AlgorithmRegistry(algorithms or [algorithm()]), clock or FakeClock())


def test_sort_returns_independent_copies_metrics_and_replayable_trace() -> None:
    source = [3, -2, 3, 0]
    result = service(algorithm("first"), algorithm("second")).sort(
        source, ["first", "second"], trace=True
    )
    assert source == result.input_values == [3, -2, 3, 0]
    assert all(row.output_values == [-2, 0, 3, 3] for row in result.results)
    for row in result.results:
        reconstructed = source.copy()
        assert row.events is not None
        for event in row.events:
            if event.kind in ("write", "swap"):
                for index, value in zip(event.indices, event.values, strict=True):
                    reconstructed[index] = value
        assert reconstructed == row.output_values
        assert row.metrics.comparisons == 6
        assert row.metrics.writes == row.metrics.array_writes + row.metrics.auxiliary_writes
        assert asdict(row)["metrics"]["writes"] == row.metrics.writes
    result.results[0].output_values[0] = 99
    assert result.results[1].output_values == [-2, 0, 3, 3]
    assert source == [3, -2, 3, 0]


def test_trace_and_counting_are_separate_passes_and_not_clocked() -> None:
    calls: list[tuple[bool, bool, list[int]]] = []
    base = algorithm()

    def record(context: SortContext) -> None:
        calls.append((context.count, context.trace, context.values.copy()))
        base.sort(context)

    clock = FakeClock()
    engine = service(algorithm(sort=record), clock=clock)
    engine.sort([2, 1], ["test"], trace=True)
    assert calls == [(True, False, [2, 1]), (False, True, [2, 1])]
    assert clock.calls == 0
    assert engine.sort([2, 1], ["test"]).results[0].events is None


def test_benchmark_only_times_uninstrumented_runs_from_identical_input() -> None:
    calls: list[tuple[bool, bool, list[int], int]] = []
    base = algorithm()
    clock = FakeClock([100, 112, 200, 220, 300, 316])

    def record(context: SortContext) -> None:
        calls.append((context.count, context.trace, context.values.copy(), clock.calls))
        base.sort(context)

    source = [4, -2, 4, 1]
    result = service(algorithm(sort=record), clock=clock).benchmark(
        source, ["test"], repeats=3, warmups=2, seed=6
    )
    assert all(start == source for _, _, start, _ in calls)
    assert [(count, trace) for count, trace, _, _ in calls] == [(True, False)] + [
        (False, False)
    ] * 5
    assert [clock_calls for *_, clock_calls in calls] == [0, 0, 0, 1, 3, 5]
    assert clock.calls == 6
    measured = result.results[0]
    assert measured.samples_ns == [12, 20, 16]
    assert measured.median_ns == 16
    assert measured.min_ns == 12
    assert measured.max_ns == 20
    assert measured.spread_ns == 8
    assert measured.output_values == [-2, 1, 4, 4]
    assert measured.metrics.comparisons == 6
    assert result.fastest_algorithm_ids == ["test"]
    assert not result.noise_warning


def test_round_order_is_seeded_and_all_samples_are_attributed_correctly() -> None:
    calls: list[tuple[str, bool, list[int]]] = []
    base = algorithm()

    def make(identifier: str) -> Algorithm:
        def record(context: SortContext) -> None:
            calls.append((identifier, context.count, context.values.copy()))
            base.sort(context)

        return algorithm(identifier, record)

    identifiers = ["a", "b", "c"]
    result = service(*(make(identifier) for identifier in identifiers)).benchmark(
        [3, 1, 2], identifiers, repeats=4, warmups=1, seed=17
    )
    rng = Random(17)
    expected = []
    for _ in range(5):
        ordered = identifiers.copy()
        rng.shuffle(ordered)
        expected.extend(ordered)
    assert [identifier for identifier, counted, _ in calls if not counted] == expected
    assert all(start == [3, 1, 2] for _, _, start in calls)
    assert all(row.samples_ns == [100] * 4 for row in result.results)
    assert result.fastest_algorithm_ids == identifiers
    assert result.noise_warning


@pytest.mark.parametrize("values", [[], [0], [-4, -4, -4]])
def test_empty_singleton_and_duplicates_are_valid(values: list[int]) -> None:
    engine = service()
    assert engine.sort(values, ["test"]).results[0].output_values == sorted(values)
    assert engine.benchmark(values, ["test"], repeats=1, warmups=0).results[
        0
    ].output_values == sorted(values)


@pytest.mark.parametrize("values", [[True], [1.0], [10**9 + 1], [-(10**9) - 1], [1] * 10001])
def test_values_are_strict_and_bounded(values: list[int]) -> None:
    with pytest.raises(DomainError):
        service().sort(values, ["test"])


@pytest.mark.parametrize("identifiers", [[], ["test", "test"], [""], [True], ["test"] * 11])
def test_algorithm_selection_is_strict_and_bounded(identifiers: list[str]) -> None:
    with pytest.raises(DomainError):
        service().sort([2, 1], identifiers)


def test_unknown_algorithm_has_a_specific_domain_error() -> None:
    with pytest.raises(UnknownAlgorithm):
        service().sort([], ["missing"])


@pytest.mark.parametrize("repeats,warmups", [(0, 0), (16, 0), (1, -1), (1, 4), (True, 1), (1, 1.5)])
def test_repetition_limits_are_validated(repeats: int, warmups: int) -> None:
    with pytest.raises(DomainError):
        service().benchmark([], ["test"], repeats=repeats, warmups=warmups)


@pytest.mark.parametrize("seed", [-1, 2**32, True, 2.0])
def test_benchmark_seed_limits(seed: int) -> None:
    with pytest.raises(DomainError):
        service().benchmark([], ["test"], seed=seed)


def test_algorithm_metadata_limits_are_checked_before_any_algorithm_runs() -> None:
    calls = []

    def record(context: SortContext) -> None:
        calls.append(context)

    engine = service(algorithm("first", record), algorithm("limited", record, max_size=1))
    with pytest.raises(LimitExceeded):
        engine.sort([2, 1], ["first", "limited"])
    assert calls == []
    ranged = service(algorithm(max_value_range=5))
    with pytest.raises(LimitExceeded):
        ranged.sort([-5, 0], ["test"])
    assert ranged.sort([-5, -1], ["test"]).results[0].output_values == [-5, -1]
    assert ranged.sort([], ["test"]).results[0].output_values == []


def test_trace_limits_fail_explicitly_instead_of_truncating() -> None:
    with pytest.raises(LimitExceeded):
        service().sort(list(range(129)), ["test"], trace=True)

    def many_events(context: SortContext) -> None:
        for _ in range(20001):
            context.compare(1, 1)

    with pytest.raises(TraceLimitExceeded):
        service(algorithm(sort=many_events)).sort([1], ["test"], trace=True)


@pytest.mark.parametrize("result", [[1, 1], [2, 1], [1], [True, 2]])
def test_invalid_algorithm_output_is_rejected_including_multiplicity(result: list[int]) -> None:
    def broken(context: SortContext) -> None:
        context.values[:] = result

    with pytest.raises(InvalidResult):
        service(algorithm(sort=broken)).sort([2, 1], ["test"])


def test_invalid_measured_output_is_checked_after_the_timer() -> None:
    clock = FakeClock()

    def broken_when_uninstrumented(context: SortContext) -> None:
        if context.count:
            context.values.sort()
        else:
            context.values.pop()

    with pytest.raises(InvalidResult):
        service(algorithm(sort=broken_when_uninstrumented), clock=clock).benchmark(
            [2, 1], ["test"], warmups=0, repeats=1
        )
    assert clock.calls == 2


def test_invalid_warmup_output_is_rejected_without_timing() -> None:
    clock = FakeClock()

    def broken_when_uninstrumented(context: SortContext) -> None:
        if context.count:
            context.values.sort()
        else:
            context.values.clear()

    with pytest.raises(InvalidResult):
        service(algorithm(sort=broken_when_uninstrumented), clock=clock).benchmark(
            [2, 1], ["test"], warmups=1
        )
    assert clock.calls == 0


def test_nonmonotonic_clock_is_rejected() -> None:
    with pytest.raises(DomainError, match="monotonic"):
        service(clock=FakeClock([100, 99])).benchmark([], ["test"], repeats=1, warmups=0)


def test_nonoverlapping_timings_identify_fastest_in_this_run() -> None:
    # Seed 0 leaves [fast, slow] in that order for the first shuffle.
    result = service(
        algorithm("fast"), algorithm("slow"), clock=FakeClock([0, 10, 20, 50])
    ).benchmark([2, 1], ["fast", "slow"], repeats=1, warmups=0, seed=0)
    assert result.fastest_algorithm_ids == ["fast"]
    assert not result.noise_warning


def test_large_n_log_n_algorithm_respects_distinct_admission_class() -> None:
    def native(context: SortContext) -> None:
        context.values.sort()

    result = service(algorithm(sort=native, max_size=10000, workload="n_log_n")).benchmark(
        list(range(10000, 0, -1)), ["test"], repeats=1, warmups=0
    )
    assert result.results[0].output_values == list(range(1, 10001))


def test_suite_reproduces_cases_and_records_seeds() -> None:
    engine = service()
    spec = SuiteSpec(
        ["test"],
        [0, 10],
        ["random", "reversed"],
        minimum=-8,
        maximum=8,
        seed=7,
        repeats=1,
        warmups=0,
    )
    first = engine.suite(spec)
    assert first == service().suite(spec)
    assert len(first.cases) == 4
    assert [case.dataset.size for case in first.cases] == [0, 0, 10, 10]
    assert [case.dataset.distribution for case in first.cases] == ["random", "reversed"] * 2
    assert all(case.dataset.values == case.benchmark.input_values for case in first.cases)
    assert all(case.dataset.seed == case.benchmark.seed for case in first.cases)


@pytest.mark.parametrize(
    "overrides",
    [
        {"sizes": []},
        {"distributions": []},
        {"sizes": [True]},
        {"sizes": [2.0]},
        {"sizes": [1, 1]},
        {"distributions": ["random", "random"]},
        {"sizes": list(range(13))},
        {"distributions": ["invalid"]},
        {"minimum": 8, "maximum": 7},
        {"warmups": 4},
        {"repeats": 0},
    ],
)
def test_suite_rejects_invalid_spec(overrides: dict[str, object]) -> None:
    with pytest.raises(DomainError):
        service().suite(replace(SuiteSpec(["test"], [1], ["random"]), **overrides))  # type: ignore[arg-type]


def test_suite_validates_later_case_limits_before_running_first_case() -> None:
    calls: list[SortContext] = []
    engine = service(algorithm(sort=calls.append, max_size=10))
    with pytest.raises(LimitExceeded):
        engine.suite(SuiteSpec(["test"], [1, 11], ["random"], repeats=1, warmups=0))
    assert calls == []


def test_suite_validates_aggregate_budget_before_running_first_case() -> None:
    calls: list[SortContext] = []
    engine = service(algorithm(sort=calls.append, max_size=5000))
    # Each individual case fits 50m; their combined 64m does not.
    with pytest.raises(LimitExceeded, match="work budget"):
        engine.suite(SuiteSpec(["test"], [4000], ["random", "sorted"], repeats=1, warmups=0))
    assert calls == []


def test_trace_flag_does_not_accept_truthy_nonbooleans() -> None:
    with pytest.raises(DomainError):
        service().sort([], ["test"], trace=1)  # type: ignore[arg-type]


def test_distinct_medians_warn_when_observed_ranges_overlap() -> None:
    durations = {"fast": iter([10, 30, 15]), "slow": iter([20, 40, 35])}
    ticks = []
    now = 0
    rng = Random(3)
    for _ in range(3):
        order = ["fast", "slow"]
        rng.shuffle(order)
        for identifier in order:
            duration = next(durations[identifier])
            ticks.extend([now, now + duration])
            now += duration + 5
    result = service(algorithm("fast"), algorithm("slow"), clock=FakeClock(ticks)).benchmark(
        [2, 1], ["fast", "slow"], repeats=3, warmups=0, seed=3
    )
    assert result.fastest_algorithm_ids == ["fast"]
    assert result.results[0].median_ns == 15
    assert result.results[1].median_ns == 35
    assert result.noise_warning


def test_trace_output_is_validated_independently_of_counted_output() -> None:
    def broken_trace(context: SortContext) -> None:
        if context.trace:
            context.values.clear()
        else:
            context.values.sort()

    with pytest.raises(InvalidResult):
        service(algorithm(sort=broken_trace)).sort([2, 1], ["test"], trace=True)


def test_suite_uses_actual_span_and_rejects_later_span_before_any_execution() -> None:
    calls: list[SortContext] = []
    engine = service(algorithm(sort=calls.append, max_value_range=1, workload="linear_range"))
    with pytest.raises(LimitExceeded, match="value range"):
        engine.suite(
            SuiteSpec(
                ["test"], [0, 20], ["random"], minimum=-5, maximum=5, seed=8, repeats=1, warmups=0
            )
        )
    assert calls == []


def test_suite_unseeded_result_can_be_reproduced() -> None:
    spec = SuiteSpec(["test"], [3], ["few_unique"], repeats=1, warmups=0)
    first = service().suite(spec)
    assert first == service().suite(replace(spec, seed=first.seed))
