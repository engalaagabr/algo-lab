"""Correctness, instrumentation, and replay contracts shared by every algorithm."""

from collections import Counter
from itertools import product
from random import Random

import pytest

from algorithms import build_registry
from domain.errors import LimitExceeded, TraceLimitExceeded
from domain.models import Metrics, SortEvent
from domain.operations import SortContext

ALGORITHM_IDS = (
    "selection_sort",
    "bubble_sort",
    "odd_even_sort",
    "cocktail_sort",
    "insertion_sort",
    "binary_insertion_sort",
    "frequency_sort",
    "shell_sort",
    "heap_sort",
    "quick_sort",
    "merge_sort",
)

EDGE_CASES = (
    [],
    [7],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [0] * 12,
    [-8, -3, -3, 0, 9, -8],
    [-9, -1, -5, -9, -2],
    [99, -99, 0],
    [1, 2, 1, 2, 1, 2],
    [8, 0, 7, 1, 6, 2, 5, 3, 4],
)


def _replay(original: list[int], events: list[SortEvent]) -> list[int]:
    replayed = original.copy()
    for sequence, event in enumerate(events):
        assert event.sequence == sequence
        assert all(0 <= index < len(replayed) for index in event.indices)
        if event.kind == "compare":
            assert len(event.values) == 2
            if len(event.indices) == 2:
                assert tuple(replayed[index] for index in event.indices) == event.values
            elif len(event.indices) == 1:
                assert replayed[event.indices[0]] == event.values[0]
        elif event.kind == "swap":
            assert len(event.indices) == len(event.values) == 2
            first, second = event.indices
            assert first != second
            replayed[first], replayed[second] = replayed[second], replayed[first]
            assert (replayed[first], replayed[second]) == event.values
        else:
            assert event.kind == "write"
            assert len(event.indices) == len(event.values) == 1
            replayed[event.indices[0]] = event.values[0]
    return replayed


def test_registry_has_exactly_the_supported_algorithms_and_limits() -> None:
    registry = build_registry()
    metadata = registry.list_metadata()
    assert tuple(item.id for item in metadata) == ALGORITHM_IDS
    for item in metadata:
        assert item.max_size == (
            10_000
            if item.id in {"heap_sort", "quick_sort", "merge_sort", "frequency_sort"}
            else 1000
        )
        assert item.max_value_range == (100_000 if item.id == "frequency_sort" else None)
        assert registry.get(item.id).metadata is item


@pytest.mark.parametrize("identifier", ALGORITHM_IDS)
@pytest.mark.parametrize("original", EDGE_CASES)
@pytest.mark.parametrize("count", [True, False])
def test_edge_cases_sort_the_callers_copy_without_changing_original(
    identifier: str, original: list[int], count: bool
) -> None:
    unchanged = original.copy()
    working = original.copy()
    context = SortContext(working, count=count)
    build_registry().get(identifier).sort(context)
    assert context.values is working
    assert working == sorted(original)
    assert Counter(working) == Counter(original)
    assert original == unchanged
    assert context.events == []
    if not count:
        assert context.metrics == Metrics()


@pytest.mark.parametrize("identifier", ALGORITHM_IDS)
def test_exhaustive_short_arrays_and_seeded_random_inputs(identifier: str) -> None:
    algorithm = build_registry().get(identifier)
    rng = Random(832_451)
    cases = [list(values) for size in range(6) for values in product((-1, 0, 1), repeat=size)]
    cases.extend([rng.randint(-1000, 1000) for _ in range(size)] for size in range(1, 81))
    cases.extend([rng.randint(-3, 3) for _ in range(96)] for _ in range(20))
    for original in cases:
        counted = SortContext(original.copy())
        raw = SortContext(original.copy(), count=False)
        algorithm.sort(counted)
        algorithm.sort(raw)
        assert counted.values == raw.values == sorted(original), (identifier, original)
        assert raw.metrics == Metrics()


@pytest.mark.parametrize("identifier", ALGORITHM_IDS)
@pytest.mark.parametrize("original", EDGE_CASES)
def test_complete_traces_reconstruct_output_and_agree_with_metrics(
    identifier: str, original: list[int]
) -> None:
    context = SortContext(original.copy(), trace=True)
    build_registry().get(identifier).sort(context)
    assert _replay(original, context.events) == context.values == sorted(original)
    event_counts = Counter(event.kind for event in context.events)
    assert context.metrics.comparisons == event_counts["compare"]
    assert context.metrics.swaps == event_counts["swap"]
    assert context.metrics.array_writes == 2 * event_counts["swap"] + event_counts["write"]


@pytest.mark.parametrize("identifier", ALGORITHM_IDS)
def test_trace_events_do_not_depend_on_metric_collection(identifier: str) -> None:
    original = [3, -1, 3, 0, -1, 2]
    counted = SortContext(original.copy(), trace=True)
    uncounted = SortContext(original.copy(), count=False, trace=True)
    algorithm = build_registry().get(identifier)
    algorithm.sort(counted)
    algorithm.sort(uncounted)
    assert counted.events == uncounted.events
    assert _replay(original, uncounted.events) == sorted(original)
    assert uncounted.metrics == Metrics()


@pytest.mark.parametrize(
    ("identifier", "expected_reverse", "expected_sorted"),
    [
        ("selection_sort", (1, 1, 2, 0), (1, 0, 0, 0)),
        ("bubble_sort", (1, 1, 2, 0), (1, 0, 0, 0)),
        ("odd_even_sort", (2, 1, 2, 0), (1, 0, 0, 0)),
        ("cocktail_sort", (1, 1, 2, 0), (1, 0, 0, 0)),
        ("insertion_sort", (1, 0, 2, 0), (1, 0, 0, 0)),
        ("binary_insertion_sort", (1, 0, 2, 0), (1, 0, 0, 0)),
        ("frequency_sort", (2, 0, 2, 4), (2, 0, 2, 4)),
        ("shell_sort", (1, 0, 2, 0), (1, 0, 0, 0)),
        ("heap_sort", (1, 1, 2, 0), (1, 2, 4, 0)),
        ("quick_sort", (5, 1, 2, 0), (4, 0, 0, 0)),
        ("merge_sort", (1, 0, 2, 4), (1, 0, 2, 4)),
    ],
)
def test_known_two_element_metrics(
    identifier: str,
    expected_reverse: tuple[int, int, int, int],
    expected_sorted: tuple[int, int, int, int],
) -> None:
    algorithm = build_registry().get(identifier)
    for original, expected in (([2, 1], expected_reverse), ([1, 2], expected_sorted)):
        context = SortContext(original.copy())
        algorithm.sort(context)
        actual = context.metrics
        assert (actual.comparisons, actual.swaps, actual.array_writes, actual.auxiliary_writes) == (
            expected
        )


@pytest.mark.parametrize("identifier", ALGORITHM_IDS)
@pytest.mark.parametrize("original", [[], [5]])
def test_trivial_inputs_do_not_perform_operations(identifier: str, original: list[int]) -> None:
    context = SortContext(original.copy(), trace=True)
    build_registry().get(identifier).sort(context)
    assert context.metrics == Metrics()
    assert context.events == []


@pytest.mark.parametrize("identifier", ALGORITHM_IDS)
def test_trace_limit_is_not_silently_truncated(identifier: str) -> None:
    context = SortContext([3, 2, 1], trace=True, max_events=1)
    with pytest.raises(TraceLimitExceeded):
        build_registry().get(identifier).sort(context)


def test_frequency_sort_counts_negative_offsets_and_rejects_large_ranges() -> None:
    algorithm = build_registry().get("frequency_sort")
    context = SortContext([-2, 0, -2])
    algorithm.sort(context)
    assert context.values == [-2, -2, 0]
    assert context.metrics == Metrics(comparisons=4, array_writes=3, auxiliary_writes=6)

    for count in (True, False):
        invalid = SortContext([-50_000, 50_000], count=count)
        with pytest.raises(LimitExceeded, match="100000"):
            algorithm.sort(invalid)
        assert invalid.values == [-50_000, 50_000]
        assert invalid.metrics.auxiliary_writes == 0

    boundary = SortContext([-50_000, 49_999])
    algorithm.sort(boundary)
    assert boundary.values == [-50_000, 49_999]
    assert boundary.metrics.auxiliary_writes == 100_002


@pytest.mark.parametrize("identifier", ["quick_sort", "heap_sort", "merge_sort", "frequency_sort"])
def test_large_inputs_at_the_declared_limit(identifier: str) -> None:
    algorithm = build_registry().get(identifier)
    rng = Random(29)
    cases = [
        list(range(10_000)),
        list(range(9999, -1, -1)),
        [4] * 10_000,
        [rng.randint(-20, 20) for _ in range(10_000)],
    ]
    for original in cases:
        context = SortContext(original.copy(), count=False)
        algorithm.sort(context)
        assert context.values == sorted(original)


def test_quicksort_counts_pending_stack_bounds_and_equal_keys_are_linear() -> None:
    algorithm = build_registry().get("quick_sort")
    balanced = SortContext([3, 1, 5, 2, 4, 0, 6])
    algorithm.sort(balanced)
    assert balanced.values == list(range(7))
    assert balanced.metrics.auxiliary_writes > 0
    assert balanced.metrics.auxiliary_writes % 2 == 0

    equal = SortContext([9] * 1000)
    algorithm.sort(equal)
    assert equal.metrics == Metrics(comparisons=1002)


def test_variant_specific_complexity_and_frequency_semantics_are_explicit() -> None:
    registry = build_registry()
    quick = registry.get("quick_sort").metadata
    assert quick.complexity.auxiliary_space == "O(log n)"
    assert quick.complexity.worst == "O(n^2)"
    assert "Unknown" in registry.get("shell_sort").metadata.complexity.average
    frequency = registry.get("frequency_sort").metadata
    assert "Counting" in frequency.name
    assert "not sort values by occurrence frequency" in frequency.description
    assert not frequency.comparison_based
    assert not frequency.stable
    assert not frequency.in_place

    merge = registry.get("merge_sort").metadata
    assert merge.complexity.worst == "O(n log n)"
    assert merge.complexity.auxiliary_space == "O(n)"
    assert merge.stable
    assert not merge.in_place
