"""Selection sort with one exchange per unsorted suffix."""

from algolab.domain.models import AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext

metadata = AlgorithmMetadata(
    id="selection_sort",
    name="Selection Sort",
    description="Select the smallest remaining value and exchange it into position.",
    complexity=Complexity("O(n^2)", "O(n^2)", "O(n^2)", "O(1)"),
    stable=False,
    in_place=True,
)


def sort(context: SortContext) -> None:
    values = context.values
    for first in range(len(values) - 1):
        smallest = first
        for candidate in range(first + 1, len(values)):
            if context.compare(values[candidate], values[smallest], (candidate, smallest)) < 0:
                smallest = candidate
        context.swap(first, smallest)
