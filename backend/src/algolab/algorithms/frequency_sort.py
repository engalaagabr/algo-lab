"""Ascending integer counting sort, not ordering values by their frequency."""

from algolab.domain.errors import LimitExceeded
from algolab.domain.models import AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext

MAX_VALUE_RANGE = 100_000

metadata = AlgorithmMetadata(
    id="frequency_sort",
    name="Frequency Sort (Counting Sort)",
    description=(
        "Count each integer value and reconstruct ascending order; supports negative integers. "
        "This does not sort values by occurrence frequency."
    ),
    complexity=Complexity(
        "O(n + k)",
        "O(n + k)",
        "O(n + k)",
        "O(k)",
        "k = max(values) - min(values) + 1. Reconstructs integer values, not stable records. "
        "Finding the bounds still performs key comparisons.",
    ),
    stable=False,
    in_place=False,
    comparison_based=False,
    max_size=10_000,
    max_value_range=MAX_VALUE_RANGE,
    workload="linear_range",
)


def sort(context: SortContext) -> None:
    values = context.values
    if len(values) < 2:
        return

    smallest = largest = values[0]
    for index in range(1, len(values)):
        value = values[index]
        if context.compare(value, smallest, (index,)) < 0:
            smallest = value
        if context.compare(value, largest, (index,)) > 0:
            largest = value

    span = largest - smallest + 1
    if span > MAX_VALUE_RANGE:
        raise LimitExceeded(f"Frequency Sort supports a value range of at most {MAX_VALUE_RANGE}.")

    frequencies = [0] * span
    context.auxiliary_write(span)
    for value in values:
        frequencies[value - smallest] += 1
        context.auxiliary_write()

    target = 0
    for offset, frequency in enumerate(frequencies):
        for _ in range(frequency):
            context.write(target, smallest + offset)
            target += 1
