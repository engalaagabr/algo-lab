"""Stable insertion sort with an upper-bound binary search."""

from algolab.domain.models import AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext

metadata: AlgorithmMetadata = AlgorithmMetadata(
    id="binary_insertion_sort",
    name="Binary Insertion Sort",
    description="Find each insertion position by binary search, then shift larger values right.",
    complexity=Complexity(
        best="O(n)",
        average="O(n^2)",
        worst="O(n^2)",
        auxiliary_space="O(1)",
        notes=(
            "The ordered-prefix fast path makes the best case linear. "
            "Binary search uses O(n log n) comparisons overall, but shifts can be quadratic."
        ),
    ),
    stable=True,
    in_place=True,
    max_size=1000,
)


def sort(context: SortContext) -> None:
    """Insert after equal values so binary search preserves stability."""
    values = context.values
    for index in range(1, len(values)):
        key = values[index]
        if context.compare(values[index - 1], key, (index - 1,)) <= 0:
            continue
        left = 0
        right = index - 1
        while left < right:
            middle = (left + right) // 2
            if context.compare(values[middle], key, (middle,)) <= 0:
                left = middle + 1
            else:
                right = middle
        for position in range(index, left, -1):
            context.write(position, values[position - 1])
        context.write(left, key)
