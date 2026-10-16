"""Stable odd-even transposition sort."""

from domain.models import AlgorithmMetadata, Complexity
from domain.operations import SortContext

metadata: AlgorithmMetadata = AlgorithmMetadata(
    id="odd_even_sort",
    name="Odd-Even Sort",
    description="Alternate even and odd adjacent pairs until neither phase swaps values.",
    complexity=Complexity(
        best="O(n)",
        average="O(n^2)",
        worst="O(n^2)",
        auxiliary_space="O(1)",
        notes="Both phases run sequentially; one unchanged cycle ends the sort.",
    ),
    stable=True,
    in_place=True,
    max_size=1000,
)


def sort(context: SortContext) -> None:
    """Sort with alternating even-indexed and odd-indexed adjacent comparisons."""
    values = context.values
    changed = True
    while changed:
        changed = False
        for start in range(2):
            for index in range(start, len(values) - 1, 2):
                if context.compare(values[index], values[index + 1], (index, index + 1)) > 0:
                    context.swap(index, index + 1)
                    changed = True
