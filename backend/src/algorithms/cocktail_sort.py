"""Stable bidirectional bubble sort."""

from domain.models import AlgorithmMetadata, Complexity
from domain.operations import SortContext

metadata: AlgorithmMetadata = AlgorithmMetadata(
    id="cocktail_sort",
    name="Cocktail Sort",
    description="Sweep adjacent inversions in both directions across a shrinking interval.",
    complexity=Complexity(
        best="O(n)",
        average="O(n^2)",
        worst="O(n^2)",
        auxiliary_space="O(1)",
        notes="A sweep with no swaps ends the sort immediately.",
    ),
    stable=True,
    in_place=True,
    max_size=1000,
)


def sort(context: SortContext) -> None:
    """Move the largest value rightward, then the smallest value leftward."""
    values = context.values
    start = 0
    end = len(values) - 1
    while start < end:
        changed = False
        for index in range(start, end):
            if context.compare(values[index], values[index + 1], (index, index + 1)) > 0:
                context.swap(index, index + 1)
                changed = True
        if not changed:
            return
        end -= 1
        changed = False
        for index in range(end, start, -1):
            if context.compare(values[index - 1], values[index], (index - 1, index)) > 0:
                context.swap(index - 1, index)
                changed = True
        if not changed:
            return
        start += 1
