"""Stable bubble sort with a shrinking unsorted suffix."""

from domain.models import AlgorithmMetadata, Complexity
from domain.operations import SortContext

metadata: AlgorithmMetadata = AlgorithmMetadata(
    id="bubble_sort",
    name="Bubble Sort",
    description="Swap adjacent inversions and stop when a pass makes no swaps.",
    complexity=Complexity(
        best="O(n)",
        average="O(n^2)",
        worst="O(n^2)",
        auxiliary_space="O(1)",
        notes="The last swap bounds the next pass; an ordered input needs one pass.",
    ),
    stable=True,
    in_place=True,
    max_size=1000,
)


def sort(context: SortContext) -> None:
    """Sort by bubbling the largest remaining value toward the end."""
    values = context.values
    end = len(values) - 1
    while end > 0:
        last_swap = 0
        for index in range(end):
            if context.compare(values[index], values[index + 1], (index, index + 1)) > 0:
                context.swap(index, index + 1)
                last_swap = index
        end = last_swap
