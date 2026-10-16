import pytest

from algolab.domain.errors import TraceLimitExceeded, UnknownAlgorithm
from algolab.domain.models import Algorithm, AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext
from algolab.domain.registry import AlgorithmRegistry


def test_metrics_and_replay_semantics():
    context = SortContext([3, 1, 2], trace=True)
    assert context.compare(3, 1, (0, 1)) == 1
    context.swap(0, 1)
    context.swap(1, 1)
    context.write(2, 3)
    context.auxiliary_write(2)
    assert context.values == [1, 3, 3]
    assert context.metrics.comparisons == 1
    assert context.metrics.swaps == 1
    assert context.metrics.array_writes == 3
    assert context.metrics.writes == 5
    assert [event.sequence for event in context.events] == [0, 1, 2]
    assert context.events[1].values == (1, 3)


def test_disabled_instrumentation_still_performs_operations():
    context = SortContext([2, 1], count=False)
    context.compare(2, 1)
    context.swap(0, 1)
    context.write(0, 1)
    context.auxiliary_write()
    assert context.values == [1, 2]
    assert context.metrics.writes == context.metrics.comparisons == 0
    assert context.events == []


def test_trace_limit_is_explicit():
    context = SortContext([2, 1], trace=True, max_events=1)
    context.compare(2, 1)
    with pytest.raises(TraceLimitExceeded):
        context.swap(0, 1)


def test_registry_rejects_unknown_and_duplicate_ids():
    algorithm = Algorithm(
        AlgorithmMetadata("test", "Test", "test", Complexity("1", "1", "1", "1"), True, True),
        lambda context: None,
    )
    registry = AlgorithmRegistry([algorithm])
    assert registry.get("test") is algorithm
    with pytest.raises(UnknownAlgorithm):
        registry.get("missing")
    with pytest.raises(ValueError, match="Duplicate"):
        AlgorithmRegistry([algorithm, algorithm])
